import re

from pydantic import BaseModel, ConfigDict, Field, field_validator


USERNAME_PATTERN = re.compile(r"^[a-z0-9_]{3,30}$")


class UserBase(BaseModel):
    name: str = Field(..., min_length=2, max_length=120)
    email: str = Field(..., max_length=255)
    college: str | None = Field(default=None, max_length=255)
    branch: str | None = Field(default=None, max_length=120)
    year: int | None = Field(default=None, ge=1, le=6)
    skills: list[str] = Field(default_factory=list)

    @field_validator("name", "college", "branch")
    @classmethod
    def strip_optional_text(cls, value: str | None) -> str | None:
        if value is None:
            return value
        stripped = value.strip()
        return stripped or None

    @field_validator("email")
    @classmethod
    def validate_email(cls, value: str) -> str:
        normalized = value.strip().lower()
        if "@" not in normalized or "." not in normalized.rsplit("@", 1)[-1]:
            raise ValueError("Invalid email address")
        return normalized

    @field_validator("skills")
    @classmethod
    def normalize_skills(cls, value: list[str]) -> list[str]:
        skills = []
        seen = set()
        for skill in value:
            normalized = skill.strip()
            key = normalized.lower()
            if normalized and key not in seen:
                skills.append(normalized)
                seen.add(key)
        return skills


class UserCreate(UserBase):
    username: str = Field(..., min_length=3, max_length=30)
    password: str = Field(..., min_length=8, max_length=128)

    @field_validator("username")
    @classmethod
    def validate_username(cls, value: str) -> str:
        normalized = value.strip().lower()
        if not USERNAME_PATTERN.fullmatch(normalized):
            raise ValueError("Username must be 3-30 lowercase letters, numbers, or underscores")
        return normalized


class UserUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=2, max_length=120)
    college: str | None = Field(default=None, max_length=255)
    branch: str | None = Field(default=None, max_length=120)
    year: int | None = Field(default=None, ge=1, le=6)
    skills: list[str] | None = None

    @field_validator("name", "college", "branch")
    @classmethod
    def strip_optional_text(cls, value: str | None) -> str | None:
        if value is None:
            return value
        stripped = value.strip()
        return stripped or None

    @field_validator("skills")
    @classmethod
    def normalize_skills(cls, value: list[str] | None) -> list[str] | None:
        if value is None:
            return value
        skills = []
        seen = set()
        for skill in value:
            normalized = skill.strip()
            key = normalized.lower()
            if normalized and key not in seen:
                skills.append(normalized)
                seen.add(key)
        return skills


class UserResponse(UserBase):
    id: int
    username: str | None = None
    is_admin: bool
    auth_provider: str
    profile_image_url: str | None = None

    model_config = ConfigDict(from_attributes=True)


UserRead = UserResponse


class UserPublicResponse(BaseModel):
    id: int
    name: str
    username: str | None = None
    college: str | None = None
    branch: str | None = None
    year: int | None = None
    skills: list[str] = Field(default_factory=list)
    profile_image_url: str | None = None

    model_config = ConfigDict(from_attributes=True)


class UserLogin(BaseModel):
    email: str = Field(..., max_length=255)
    password: str = Field(..., min_length=8, max_length=128)

    @field_validator("email")
    @classmethod
    def validate_email(cls, value: str) -> str:
        normalized = value.strip().lower()
        if "@" not in normalized or "." not in normalized.rsplit("@", 1)[-1]:
            raise ValueError("Invalid email address")
        return normalized


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class TokenWithUser(Token):
    user: UserRead
