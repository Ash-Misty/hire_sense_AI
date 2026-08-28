import uuid
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from app.core.security import create_access_token, hash_password
from app.database.session import SessionLocal
from app.main import app
from app.models.user import User
from app.repositories.user_repository import UserRepository
from app.services.auth_service import AuthService

client = TestClient(app)


@pytest.fixture()
def db():
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture()
def user(db):
    u = User(
        full_name="Test User",
        email=f"emailtest_{uuid.uuid4().hex}@example.com",
        hashed_password=hash_password("Test@123"),
        role="candidate",
    )
    saved = UserRepository(db).create(u)
    yield saved
    db.query(User).filter(User.id == saved.id).delete()
    db.commit()


class TestEmailService:
    @patch("app.services.email_service.settings")
    def test_disabled_when_no_mailjet_config(self, mock_settings):
        mock_settings.MAILJET_API_KEY = ""
        mock_settings.MAILJET_SECRET_KEY = ""
        mock_settings.MAIL_FROM_EMAIL = ""

        from app.services.email_service import EmailService
        service = EmailService()
        assert service.enabled is False

    @patch("app.services.email_service.settings")
    def test_enabled_with_valid_mailjet_config(self, mock_settings):
        mock_settings.MAILJET_API_KEY = "api_key"
        mock_settings.MAILJET_SECRET_KEY = "secret_key"
        mock_settings.MAIL_FROM_EMAIL = "test@example.com"
        mock_settings.MAIL_FROM_NAME = "Test"

        from app.services.email_service import EmailService
        service = EmailService()
        assert service.enabled is True

    @patch("httpx.Client.post")
    @patch("app.services.email_service.settings")
    def test_send_email_success(self, mock_settings, mock_post):
        mock_settings.MAILJET_API_KEY = "api_key"
        mock_settings.MAILJET_SECRET_KEY = "secret_key"
        mock_settings.MAIL_FROM_EMAIL = "from@example.com"
        mock_settings.MAIL_FROM_NAME = "Test"

        mock_response = type("Response", (), {"raise_for_status": lambda self: None})()
        mock_post.return_value = mock_response

        from app.services.email_service import EmailService
        service = EmailService()
        service.send_email(
            to_email="to@example.com",
            subject="Test",
            template_name="emails/welcome.html",
            context={"name": "Test", "frontend_url": "http://localhost:3000"},
        )

        mock_post.assert_called_once()
        call_kwargs = mock_post.call_args
        assert call_kwargs.kwargs["auth"] == ("api_key", "secret_key")
        payload = call_kwargs.kwargs["json"]
        assert payload["Messages"][0]["To"][0]["Email"] == "to@example.com"
        assert payload["Messages"][0]["Subject"] == "Test"

    @patch("httpx.Client.post")
    @patch("app.services.email_service.settings")
    def test_send_email_handles_api_failure(self, mock_settings, mock_post):
        mock_post.side_effect = Exception("HTTP error")

        mock_settings.MAILJET_API_KEY = "api_key"
        mock_settings.MAILJET_SECRET_KEY = "secret_key"
        mock_settings.MAIL_FROM_EMAIL = "from@example.com"
        mock_settings.MAIL_FROM_NAME = "Test"

        from app.services.email_service import EmailService
        service = EmailService()
        with pytest.raises(Exception):
            service.send_email(
                to_email="to@example.com",
                subject="Test",
                template_name="emails/welcome.html",
                context={"name": "Test", "frontend_url": "http://localhost:3000"},
            )


class TestAuthEmailEndpoints:
    @patch("app.api.v1.auth.EmailService.send_email")
    def test_resend_verification_returns_generic_message(self, mock_send_email, user):
        token = create_access_token(data={"sub": str(user.id)})
        headers = {"Authorization": f"Bearer {token}"}

        response = client.post(
            "/api/v1/auth/resend-verification",
            json={"email": user.email},
            headers=headers,
        )
        assert response.status_code == 200
        assert "verification email has been sent" in response.json()["message"]

    def test_verify_email_marks_user_verified(self, db, user):
        assert user.is_verified is False

        service = AuthService(db)
        token = service.create_verification_token(user.id)

        response = client.get(
            f"/api/v1/auth/verify-email?token={token}"
        )
        assert response.status_code == 200
        assert response.json()["message"] == "Email verified successfully."

        db.refresh(user)
        assert user.is_verified is True

    def test_verify_email_invalid_token(self):
        response = client.get(
            "/api/v1/auth/verify-email?token=invalid-token"
        )
        assert response.status_code == 400

    def test_verify_email_already_verified(self, db, user):
        user.is_verified = True
        db.commit()

        service = AuthService(db)
        token = service.create_verification_token(user.id)

        response = client.get(
            f"/api/v1/auth/verify-email?token={token}"
        )
        assert response.status_code == 400
        assert "already verified" in response.json()["detail"]

    @patch("app.api.v1.auth.EmailService.send_email")
    def test_forgot_password_returns_generic_message(self, mock_send_email):
        response = client.post(
            "/api/v1/auth/forgot-password",
            json={"email": "nonexistent@example.com"},
        )
        assert response.status_code == 200
        assert "reset link has been sent" in response.json()["message"]

    def test_reset_password_success(self, db, user):
        service = AuthService(db)
        token = service.create_password_reset_token(user.id)

        response = client.post(
            "/api/v1/auth/reset-password",
            json={"token": token, "new_password": "NewPass@123"},
        )
        assert response.status_code == 200
        assert response.json()["message"] == "Password reset successfully."

        db.refresh(user)
        assert user.hashed_password != hash_password("Test@123")

    def test_reset_password_invalid_token(self):
        response = client.post(
            "/api/v1/auth/reset-password",
            json={"token": "invalid", "new_password": "NewPass@123"},
        )
        assert response.status_code == 400

    def test_reset_password_invalidates_sessions(self, db, user):
        service = AuthService(db)

        raw_refresh = service._issue_refresh_token(user.id)
        token_hash = service._hash_token(raw_refresh)
        stored = service.refresh_repo.get_by_token_hash(token_hash)
        assert stored is not None
        assert stored.revoked is False

        token = service.create_password_reset_token(user.id)

        response = client.post(
            "/api/v1/auth/reset-password",
            json={"token": token, "new_password": "NewPass@123"},
        )
        assert response.status_code == 200

        db.refresh(stored)
        assert stored.revoked is True

    @patch("app.api.v1.auth.EmailService.send_email")
    def test_register_creates_unverified_user(self, mock_send_email):
        response = client.post(
            "/api/v1/auth/register",
            json={
                "full_name": "New User",
                "email": f"newuser_{uuid.uuid4().hex}@example.com",
                "password": "NewPass@123",
            },
        )
        assert response.status_code == 201
        assert response.json()["is_verified"] is False

    @patch("app.api.v1.auth.EmailService.send_email")
    def test_login_works_after_registration(self, mock_send_email):
        email = f"loginuser_{uuid.uuid4().hex}@example.com"
        register_response = client.post(
            "/api/v1/auth/register",
            json={
                "full_name": "Login User",
                "email": email,
                "password": "LoginPass@123",
            },
        )
        assert register_response.status_code == 201

        login_response = client.post(
            "/api/v1/auth/login",
            json={"email": email, "password": "LoginPass@123"},
        )
        assert login_response.status_code == 200
        assert "access_token" in login_response.json()
