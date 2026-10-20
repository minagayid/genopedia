import os,unittest
os.environ.setdefault("JWT_SECRET_KEY","test-secret-key-with-more-than-32-characters")
os.environ.setdefault("SESSION_SECRET_KEY","test-session-secret-with-more-than-32-characters")
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from genopedia.api.app import app
from genopedia.api.database import Base,get_db
class AuthApiTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.engine=create_engine("sqlite://",connect_args={"check_same_thread":False},poolclass=StaticPool)
  cls.Session=sessionmaker(bind=cls.engine,autoflush=False,autocommit=False,expire_on_commit=False)
  Base.metadata.create_all(cls.engine)
  def override():
   db=cls.Session()
   try:yield db
   finally:db.close()
  app.dependency_overrides[get_db]=override
  cls.client=TestClient(app)
 @classmethod
 def tearDownClass(cls):
  cls.client.close();app.dependency_overrides.clear();Base.metadata.drop_all(cls.engine);cls.engine.dispose()
 def setUp(self):
  with self.Session() as db:
   for table in reversed(Base.metadata.sorted_tables):db.execute(table.delete())
   db.commit()
  self.client.cookies.clear()
 def test_signup_login_me_and_refresh_rotation(self):
  r=self.client.post("/auth/signup",json={"email":"researcher@example.com","password":"Long-Test-Passphrase-123!","full_name":"Researcher"})
  self.assertEqual(r.status_code,201,r.text);access=r.json()["access_token"]
  self.assertEqual(self.client.get("/auth/me",headers={"Authorization":f"Bearer {access}"}).status_code,200)
  old=self.client.cookies.get("genopedia_refresh");fresh=self.client.post("/auth/refresh")
  self.assertEqual(fresh.status_code,200,fresh.text);self.assertNotEqual(old,self.client.cookies.get("genopedia_refresh"))
  self.assertEqual(self.client.post("/auth/refresh",cookies={"genopedia_refresh":old}).status_code,401)
  self.assertEqual(self.client.post("/auth/login",json={"email":"researcher@example.com","password":"Long-Test-Passphrase-123!"}).status_code,200)
 def test_duplicate_signup_and_bad_password(self):
  p={"email":"duplicate@example.com","password":"Long-Test-Passphrase-123!"}
  self.assertEqual(self.client.post("/auth/signup",json=p).status_code,201)
  self.assertEqual(self.client.post("/auth/signup",json=p).status_code,409)
  self.assertEqual(self.client.post("/auth/login",json={"email":p["email"],"password":"bad-password"}).status_code,401)
 def test_health(self):
  self.assertEqual(self.client.get("/health/live").json(),{"status":"ok"})
  self.assertEqual(self.client.get("/health/ready").json(),{"status":"ready"})
if __name__=="__main__":unittest.main()
