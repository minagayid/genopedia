from __future__ import annotations
import unittest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from app.db.base import Base
from app.db.session import get_db
from app.main import app
from app.models.user import AuthSession, User

class ApiAuthTests(unittest.TestCase):
    def setUp(self) -> None:
        self.engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
        Base.metadata.create_all(self.engine)
        self.SessionTesting = sessionmaker(bind=self.engine, autoflush=False, expire_on_commit=False)
        def override_get_db():
            db = self.SessionTesting()
            try:
                yield db
            finally:
                db.close()
        app.dependency_overrides[get_db] = override_get_db
        self.client = TestClient(app)

    def tearDown(self) -> None:
        self.client.close()
        app.dependency_overrides.clear()
        Base.metadata.drop_all(self.engine)
        self.engine.dispose()

    def test_health_endpoints(self) -> None:
        self.assertEqual(self.client.get("/health/live").json(), {"status": "alive"})
        response = self.client.get("/health/ready")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["database"], "connected")

    def test_signup_hashes_password_and_starts_session(self) -> None:
        response = self.client.post("/api/auth/signup", json={"email": "Mina@example.com", "display_name": " Mina Gayid ", "password": "a-long-test-password-123"})
        self.assertEqual(response.status_code, 201, response.text)
        body = response.json()
        self.assertEqual(body["email"], "mina@example.com")
        self.assertEqual(body["display_name"], "Mina Gayid")
        self.assertNotIn("password_hash", body)
        self.assertIn("genopedia_session", response.cookies)
        self.assertIn("genopedia_csrf", response.cookies)
        self.assertIn("httponly", response.headers.get("set-cookie", "").lower())
        with self.SessionTesting() as db:
            user = db.scalar(select(User).where(User.email == "mina@example.com"))
            self.assertIsNotNone(user)
            self.assertNotEqual(user.password_hash, "a-long-test-password-123")
            self.assertTrue(user.password_hash.startswith("$argon2"))
            session_row = db.scalar(select(AuthSession).where(AuthSession.user_id == user.id))
            self.assertEqual(len(session_row.token_hash), 64)
            self.assertNotEqual(session_row.token_hash, response.cookies["genopedia_session"])

    def test_signup_rejects_duplicate_email_and_short_password(self) -> None:
        payload = {"email": "one@example.com", "display_name": "Test User", "password": "long-password-123"}
        self.assertEqual(self.client.post("/api/auth/signup", json=payload).status_code, 201)
        self.assertEqual(self.client.post("/api/auth/signup", json={**payload, "email": "ONE@example.com"}).status_code, 409)
        self.assertEqual(self.client.post("/api/auth/signup", json={**payload, "email": "new@example.com", "password": "short"}).status_code, 422)

    def test_login_profile_update_and_csrf_protected_logout(self) -> None:
        payload = {"email": "one@example.com", "display_name": "Test User", "password": "long-password-123"}
        self.client.post("/api/auth/signup", json=payload)
        self.client.cookies.clear()
        login = self.client.post("/api/auth/login", json={"email": payload["email"], "password": payload["password"]})
        self.assertEqual(login.status_code, 200, login.text)
        self.assertEqual(self.client.get("/api/auth/me").status_code, 200)
        self.assertEqual(self.client.patch("/api/users/me", json={"display_name": "Updated User"}, headers={"X-CSRF-Token": "wrong"}).status_code, 403)
        csrf = self.client.cookies.get("genopedia_csrf")
        update = self.client.patch("/api/users/me", json={"display_name": "  Updated User  "}, headers={"X-CSRF-Token": csrf})
        self.assertEqual(update.status_code, 200, update.text)
        self.assertEqual(update.json()["display_name"], "Updated User")
        self.assertEqual(self.client.post("/api/auth/logout", headers={"X-CSRF-Token": csrf}).status_code, 204)
        self.assertEqual(self.client.get("/api/auth/me").status_code, 401)

    def test_login_error_does_not_disclose_account_existence(self) -> None:
        response = self.client.post("/api/auth/login", json={"email": "unknown@example.com", "password": "incorrect-password"})
        self.assertEqual(response.status_code, 401)
        self.assertEqual(response.json()["detail"], "Email or password is incorrect")

    def test_protected_routes_reject_anonymous_requests(self) -> None:
        self.assertEqual(self.client.get("/api/auth/me").status_code, 401)
        self.assertEqual(self.client.get("/api/users/me").status_code, 401)

    def test_front_page_is_served(self) -> None:
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        self.assertIn("Genopedia", response.text)
        self.assertIn("Create account", response.text)
