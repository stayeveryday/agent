from pydantic import BaseModel, Field


class TraceListResponse(BaseModel):
    traces: list[dict[str, object]]


class TraceResponse(BaseModel):
    trace: dict[str, object]


class TraceListRequest(BaseModel):
    limit: int = Field(default=20, ge=1, le=100)
