from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator

# ponytail: simple shape check instead of the email-validator package; we never send email.
EMAIL_PATTERN = r"^[^@\s]{1,64}@[^@\s]+\.[^@\s]{2,}$"


class _Email(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    email: str = Field(..., max_length=254, pattern=EMAIL_PATTERN)

    @field_validator("email")
    @classmethod
    def _lower(cls, v: str) -> str:
        return v.lower()


class RegisterRequest(_Email):
    name: str = Field(..., min_length=2, max_length=80)
    password: str = Field(..., min_length=8, max_length=128)


class LoginRequest(_Email):
    password: str = Field(..., min_length=1, max_length=128)


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    email: str
    created_at: datetime


class ContactRequest(_Email):
    name: str = Field(..., min_length=2, max_length=80)
    message: str = Field(..., min_length=10, max_length=2000)


class NewsletterRequest(_Email):
    pass
