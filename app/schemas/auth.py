"""Validated authentication inputs and safe user outputs."""
from datetime import datetime
from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator

class SignupInput(BaseModel):
    email: EmailStr
    display_name: str = Field(min_length=2, max_length=80)
    password: str = Field(min_length=12, max_length=128)
    @field_validator("email")
    @classmethod
    def normalize_email(cls, value: EmailStr) -> str:
        return str(value).strip().lower()
    @field_validator("display_name")
    @classmethod
    def normalize_name(cls, value: str) -> str:
        value = value.strip()
        if len(value) < 2:
            raise ValueError("Display name must contain at least 2 non-space characters")
        return value

class LoginInput(BaseModel):
    email: EmailStr
    password: str = Field(min_length=1, max_length=128)
    @field_validator("email")
    @classmethod
    def normalize_email(cls, value: EmailStr) -> str:
        return str(value).strip().lower()

class ProfileUpdate(BaseModel):
    display_name: str = Field(min_length=2, max_length=80)
    @field_validator("display_name")
    @classmethod
    def normalize_name(cls, value: str) -> str:
        value = value.strip()
        if len(value) < 2:
            raise ValueError("Display name must contain at least 2 non-space characters")
        return value

class UserRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    email: EmailStr
    display_name: str
    is_active: bool
    created_at: datetime
    updated_at: datetime
