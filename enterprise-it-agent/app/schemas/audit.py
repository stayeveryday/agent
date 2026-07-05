from pydantic import BaseModel, Field


class AuditListResponse(BaseModel):
    events: list[dict[str, object]]


class AuditEventResponse(BaseModel):
    event: dict[str, object]


class AuditListRequest(BaseModel):
    limit: int = Field(default=50, ge=1, le=200)
