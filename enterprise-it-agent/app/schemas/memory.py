from pydantic import BaseModel


class SessionMemoryResponse(BaseModel):
    session: dict[str, object]


class SessionMemoryClearResponse(BaseModel):
    session_id: str
    cleared: bool
