from pydantic import BaseModel
from pydantic import EmailStr


class VerificationResendRequest(BaseModel):
    email: EmailStr


class VerificationResponse(BaseModel):
    message: str


class ForgotPasswordRequest(BaseModel):
    email: EmailStr


class ResetPasswordRequest(BaseModel):
    token: str
    new_password: str


class ResetPasswordResponse(BaseModel):
    message: str
