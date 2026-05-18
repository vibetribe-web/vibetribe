from pydantic import BaseModel, Field, field_validator

from app.schemas.request import JoinRequestRead
from app.schemas.team import TeamRead
from app.schemas.user import UserRead


class AdminStatusUpdate(BaseModel):
    is_admin: bool


class AdminBootstrapResponse(BaseModel):
    user: UserRead
    message: str


class AdminDashboard(BaseModel):
    users_count: int
    teams_count: int
    requests_count: int
    pending_requests_count: int


class AdminDataExport(BaseModel):
    users: list[UserRead]
    teams: list[TeamRead]
    requests: list[JoinRequestRead]


class AdminBootstrapCreate(BaseModel):
    email: str = Field(..., max_length=255)
    admin_setup_key: str = Field(..., min_length=1, max_length=255)

    @field_validator("email")
    @classmethod
    def validate_email(cls, value: str) -> str:
        normalized = value.strip().lower()
        if "@" not in normalized or "." not in normalized.rsplit("@", 1)[-1]:
            raise ValueError("Invalid email address")
        return normalized
