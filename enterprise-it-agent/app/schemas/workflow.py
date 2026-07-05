from pydantic import BaseModel, Field


class GraphNodeInfo(BaseModel):
    name: str
    description: str


class GraphDescriptionResponse(BaseModel):
    graph_name: str
    purpose: str
    nodes: list[GraphNodeInfo]
    edges: list[str]


class GraphRunRequest(BaseModel):
    user_query: str = Field(min_length=1)
    session_id: str | None = None
    department: str = "general"
    access_level: str = "standard"
    approved: bool = False


class GraphRunResponse(BaseModel):
    state: dict[str, object]


class GraphApprovalRequest(BaseModel):
    reason: str = ""


class GraphApprovalResponse(BaseModel):
    checkpoint_id: str
    state: dict[str, object]
