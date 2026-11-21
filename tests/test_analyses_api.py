import os,unittest
os.environ.setdefault("JWT_SECRET_KEY","test-secret-key-with-more-than-32-characters")
os.environ.setdefault("SESSION_SECRET_KEY","test-session-secret-with-more-than-32-characters")
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from genopedia.api.app import app
from genopedia.api.database import Base,get_db
from genopedia.api.app import limiter as _limiter
_limiter.enabled=False
FASTA=b">seq1 test record\nACGTACGTACGTACGTACGTACGTACGTACGTNNNNACGT\n>seq2\nTTTTGGGGCCCCAAAA\n"
class AnalysesApiTests(unittest.TestCase):
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
  r=self.client.post("/auth/signup",json={"email":"a@example.com","password":"Long-Test-Passphrase-123!"})
  self.token=r.json()["access_token"];self.auth={"Authorization":f"Bearer {self.token}"}
 def test_create_list_get_report_delete(self):
  r=self.client.post("/analyses",json={"name":"demo","content":FASTA.decode(),"format":"fasta"},headers=self.auth)
  self.assertEqual(r.status_code,201,r.text);item=r.json()
  self.assertEqual(item["record_count"],2);self.assertEqual(item["input_format"],"fasta")
  self.assertIn("summary",item);self.assertEqual(len(item["records"]),2)
  aid=item["id"]
  listing=self.client.get("/analyses",headers=self.auth).json()
  self.assertEqual(listing["count"],1);self.assertNotIn("summary",listing["analyses"][0])
  detail=self.client.get(f"/analyses/{aid}",headers=self.auth)
  self.assertEqual(detail.status_code,200);self.assertEqual(detail.json()["summary"]["records"][0]["length"],40)
  report=self.client.get(f"/analyses/{aid}/report",headers=self.auth)
  self.assertEqual(report.status_code,200);self.assertIn("text/html",report.headers["content-type"])
  self.assertEqual(self.client.delete(f"/analyses/{aid}",headers=self.auth).status_code,204)
  self.assertEqual(self.client.get(f"/analyses/{aid}",headers=self.auth).status_code,404)
 def test_multipart_upload_and_auto_format(self):
  r=self.client.post("/analyses",files={"file":("sample.fasta",FASTA,"text/plain")},data={"name":"upload"},headers=self.auth)
  self.assertEqual(r.status_code,201,r.text);self.assertEqual(r.json()["input_format"],"fasta")
 def test_ownership_is_enforced(self):
  r=self.client.post("/analyses",json={"name":"mine","content":FASTA.decode()},headers=self.auth)
  aid=r.json()["id"]
  self.client.post("/auth/signup",json={"email":"b@example.com","password":"Long-Test-Passphrase-123!"})
  login=self.client.post("/auth/login",json={"email":"b@example.com","password":"Long-Test-Passphrase-123!"})
  other={"Authorization":f"Bearer {login.json()['access_token']}"}
  self.assertEqual(self.client.get(f"/analyses/{aid}",headers=other).status_code,404)
  self.assertEqual(self.client.delete(f"/analyses/{aid}",headers=other).status_code,404)
 def test_invalid_input_is_422(self):
  r=self.client.post("/analyses",json={"name":"empty","content":">header-only\n","format":"fasta"},headers=self.auth)
  self.assertEqual(r.status_code,422,r.text)
 def test_garbage_text_is_flagged_not_rejected(self):
  r=self.client.post("/analyses",json={"name":"bad","content":"not a sequence at all!!!"},headers=self.auth)
  self.assertEqual(r.status_code,201,r.text)
  rec=r.json()["summary"]["records"][0];self.assertEqual(rec["status"],"fail");self.assertTrue(rec["invalid_symbols"])
 def test_compare(self):
  a=self.client.post("/analyses",json={"name":"a","content":">a\nACGTACGT\n"},headers=self.auth).json()
  b=self.client.post("/analyses",json={"name":"b","content":">b\nACGTTCGT\n"},headers=self.auth).json()
  r=self.client.post("/analyses/compare",json={"reference_id":a["id"],"sample_id":b["id"]},headers=self.auth)
  self.assertEqual(r.status_code,200,r.text)
  self.assertGreaterEqual(r.json()["variant_count"],1);self.assertTrue(any(v["observed"]=="T" for v in r.json()["variants"]))
 def test_ai_endpoints_unavailable_until_configured(self):
  self.assertEqual(self.client.get("/ai/status").json()["available"],False)
  r=self.client.post("/ai/query",json={"question":"what is the GC content?"},headers=self.auth)
  self.assertEqual(r.status_code,503);self.assertIn("state",r.json()["detail"])
 def test_analyses_require_auth(self):
  self.assertEqual(self.client.get("/analyses").status_code,401)
  self.assertEqual(self.client.post("/analyses",json={"name":"x","content":">a\nACGT\n"}).status_code,401)
if __name__=="__main__":unittest.main()
