from pydantic import BaseModel


class AgentStateFieldInfo(BaseModel):
    name: str
    type: str
    required_at_start: bool
    description: str


class AgentStateDescriptionResponse(BaseModel):
    state_name: str
    purpose: str
    fields: list[AgentStateFieldInfo]


class AgentStatePreviewRequest(BaseModel):
    user_query: str
    department: str = "general"
    access_level: str = "standard"


class AgentStatePreviewResponse(BaseModel):
    state: dict[str, object]
