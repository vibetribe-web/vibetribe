from pydantic import BaseModel, ConfigDict, Field

from app.models.request import RequestStatus


class JoinRequestCreate(BaseModel):
    team_id: int = Field(..., gt=0)
    message: str | None = Field(default=None, max_length=1000)


class JoinRequestUpdate(BaseModel):
    status: RequestStatus
    reply_message: str | None = Field(default=None, max_length=1000)


JoinRequestRespond = JoinRequestUpdate


class RequestTeamSummary(BaseModel):
    id: int
    name: str

    model_config = ConfigDict(from_attributes=True)


class RequestUserSummary(BaseModel):
    id: int
    username: str | None = None
    full_name: str | None = Field(default=None, validation_alias="name")

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)


class JoinRequestResponse(BaseModel):
    id: int
    from_user_id: int
    team_id: int
    message: str | None
    status: RequestStatus
    reply_message: str | None
    team: RequestTeamSummary | None = None
    from_user: RequestUserSummary | None = None

    model_config = ConfigDict(from_attributes=True)


JoinRequestRead = JoinRequestResponse
