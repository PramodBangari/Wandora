from pydantic import BaseModel, Field


class UserCreate(BaseModel):
    username: str = Field(min_length=2, max_length=40)
    email: str = Field(min_length=5, max_length=255)
    password: str = Field(min_length=6, max_length=128)
    city: str = Field(default="Bengaluru", max_length=100)


class GoogleLoginRequest(BaseModel):
    credential: str = Field(min_length=20)


class LoginRequest(BaseModel):
    email: str = Field(min_length=5, max_length=255)
    password: str = Field(min_length=6, max_length=128)


class EmailCodeRequest(BaseModel):
    email: str = Field(min_length=5, max_length=255)
    code: str = Field(min_length=6, max_length=6, pattern=r"^\d{6}$")


class ResendVerificationRequest(BaseModel):
    email: str = Field(min_length=5, max_length=255)


class ForgotPasswordRequest(BaseModel):
    email: str = Field(min_length=5, max_length=255)


class ResetPasswordRequest(BaseModel):
    email: str = Field(min_length=5, max_length=255)
    code: str = Field(min_length=6, max_length=6, pattern=r"^\d{6}$")
    new_password: str = Field(min_length=6, max_length=128)


class UserUpdate(BaseModel):
    username: str = Field(min_length=2, max_length=40)
    bio: str = Field(default="", max_length=1000)
    interests: str = Field(default="", max_length=500)
    city: str = Field(default="Bengaluru", max_length=100)
    avatar_url: str = Field(default="", max_length=500)


class UserOut(BaseModel):
    id: int
    username: str
    email: str
    email_verified: bool
    bio: str
    interests: str
    city: str
    avatar_url: str

    class Config:
        from_attributes = True


class TokenOut(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserOut


class MessageOut(BaseModel):
    message: str
