from pydantic import BaseModel, Field


class ToolInfo(BaseModel):
    name: str
    description: str


class ToolListResponse(BaseModel):
    tools: list[ToolInfo]


class ToolRunRequest(BaseModel):
    tool_name: str = Field(min_length=1)
    arguments: dict[str, object] = Field(default_factory=dict)


class ToolRunResponse(BaseModel):
    tool_name: str
    arguments: dict[str, object]
    result: dict[str, object]
