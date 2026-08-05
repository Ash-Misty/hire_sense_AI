from pydantic import BaseModel
from pydantic import EmailStr
from pydantic import Field

from app.schemas.user import UserResponse


class UserRegisterRequest(BaseModel):

    full_name: str = Field(
        min_length=3,
        max_length=100,
        examples=["Charlin Ashini"],
    )

    email: EmailStr

    password: str = Field(
        min_length=8,
        max_length=128,
        examples=["Ashini@123"],
    )


class RegisterResponse(UserResponse):
    pass


class ChangePasswordRequest(BaseModel):

    current_password: str = Field(
        min_length=8,
        max_length=128,
        examples=["OldPassword@123"],
    )

    new_password: str = Field(
        min_length=8,
        max_length=128,
        examples=["NewPassword@123"],
    )


class RefreshTokenRequest(BaseModel):

    refresh_token: str
