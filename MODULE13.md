# Module 13: Email Services

## Purpose

Build a production-ready, reusable email service for HireSense AI. The email system provides a centralized way to send emails for authentication events without placing SMTP logic directly inside API routes.

## Architecture

```
FastAPI Router (app/api/v1/auth.py)
  ↓
Auth Service / Email Service
  ↓
Mailjet HTTP API
```

## Configuration

Email settings are managed through `app/core/config.py` and `.env`:

| Environment Variable | Description | Required |
|---------------------|-------------|----------|
| `MAILJET_API_KEY` | Mailjet API key | Yes |
| `MAILJET_SECRET_KEY` | Mailjet secret key | Yes |
| `MAIL_FROM_EMAIL` | Sender email address | Yes |
| `MAIL_FROM_NAME` | Sender display name | No (default: `HireSense AI`) |
| `EMAIL_VERIFICATION_TOKEN_EXPIRE_MINUTES` | Verification token TTL | No (default: `30`) |
| `PASSWORD_RESET_TOKEN_EXPIRE_MINUTES` | Password reset token TTL | No (default: `30`) |

### Example `.env` configuration

```env
MAILJET_API_KEY=your_mailjet_api_key
MAILJET_SECRET_KEY=your_mailjet_secret_key
MAIL_FROM_EMAIL=your_verified_sender_email
MAIL_FROM_NAME=HireSense AI
```

Get your API keys from: https://app.mailjet.com/app/developer/api-keys

## Email Service

`app/services/email_service.py` is the central email service. It provides:

- `send_email(to_email, subject, template_name, context)` — Core HTTP email sending with Jinja2 HTML templates via Mailjet API
- `send_welcome_email(to_email, name)` — Welcome email for new registrations
- `send_verification_email(to_email, name, verification_url, expire_minutes)` — Email verification
- `send_password_reset_email(to_email, name, reset_url, expire_minutes)` — Password reset

The service uses **Mailjet's HTTP API** (`https://api.mailjet.com/v3.1/send`) instead of SMTP.

The service is **disabled** when `MAILJET_API_KEY`, `MAILJET_SECRET_KEY`, or `MAIL_FROM_EMAIL` are not configured. In disabled mode, it logs a warning and returns without attempting to send.

## Email Templates

HTML templates are located in `app/templates/emails/`:

- `base.html` — Shared layout with HireSense AI branding
- `welcome.html` — Welcome email for new users
- `verification.html` — Email verification link
- `password_reset.html` — Password reset link

Templates use Jinja2 and extend `base.html` for consistent styling.

## API Endpoints

All email endpoints are in `app/api/v1/auth.py`:

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/v1/auth/register` | Creates user and sends verification email via background task |
| `GET` | `/api/v1/auth/verify-email?token={token}` | Verifies email using JWT token |
| `POST` | `/api/v1/auth/resend-verification` | Resends verification email |
| `POST` | `/api/v1/auth/forgot-password` | Requests password reset email |
| `POST` | `/api/v1/auth/reset-password` | Resets password using token |

### Verification Flow

1. User registers → `POST /auth/register`
2. System creates user with `is_verified=False`
3. System generates short-lived JWT verification token (`type: email_verification`)
4. Background task sends verification email
5. User clicks link → `GET /auth/verify-email?token={token}`
6. System validates token, marks user as verified

### Password Reset Flow

1. User requests reset → `POST /auth/forgot-password`
2. System generates short-lived JWT reset token (`type: password_reset`)
3. Background task sends reset email
4. User submits new password → `POST /auth/reset-password`
5. System validates token, updates password, invalidates all sessions

## Security Considerations

- **No plaintext tokens in database** — Verification and reset tokens are JWTs with expiration
- **Token expiration** — Verification and reset tokens expire after 30 minutes (configurable)
- **No password in emails** — Only reset links are sent, never actual passwords
- **User enumeration prevention** — `forgot-password` and `resend-verification` return generic messages regardless of whether the email exists
- **Session invalidation** — Password reset invalidates all existing refresh tokens
- **No SMTP credentials in code** — All credentials come from environment variables
- **Background tasks** — Email sending happens after the primary database operation, so registration/login don't wait for SMTP

## Schemas

`app/schemas/email.py`:

- `VerificationResendRequest` — Email for resend verification
- `VerificationResponse` — Generic verification message
- `ForgotPasswordRequest` — Email for password reset request
- `ResetPasswordRequest` — Token + new password
- `ResetPasswordResponse` — Success message

## Files Created

- `app/services/email_service.py` — Central email service
- `app/schemas/email.py` — Email-related Pydantic schemas
- `app/templates/emails/base.html` — Shared email template
- `app/templates/emails/welcome.html` — Welcome email template
- `app/templates/emails/verification.html` — Verification email template
- `app/templates/emails/password_reset.html` — Password reset email template
- `app/tests/test_email_service.py` — 14 tests

## Files Modified

- `app/core/config.py` — Added Mailjet email settings
- `.env` — Added Mailjet configuration placeholders
- `app/services/auth_service.py` — Added verification/password reset methods
- `app/api/v1/auth.py` — Added verification/resend/forgot-password/reset-password endpoints, registration now sends verification email via background task
- `requirements.txt` — Added `Jinja2==3.1.6`

## Testing

```bash
pytest app/tests/test_email_service.py -v
```

Tests cover:
- Email service enabled/disabled states
- Mailjet API sending success and failure
- Email verification flow
- Resend verification
- Password reset flow
- Session invalidation on password reset
- Registration creates unverified user
- Login still works after registration

## How to Test in Swagger UI

1. Start the application: `uvicorn app.main:app --reload`
2. Open `http://localhost:8000/docs`
3. Configure Mailjet in `.env`
4. Register a new user via `POST /api/v1/auth/register`
5. Check the console/logs for the verification email
6. Verify email via `GET /api/v1/auth/verify-email?token={token}`
7. Test password reset via `POST /api/v1/auth/forgot-password` and `POST /api/v1/auth/reset-password`

## Dependencies

- `httpx==0.28.1` — HTTP client for Mailjet API calls
- `Jinja2==3.1.6` — HTML template rendering
