from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    question: str = Field(min_length=1, description="User question")
    style: str = Field(default="default", description="Prompt style")


class ChatResponse(BaseModel):
    answer: str


class ModelChatResponse(BaseModel):
    answer: str


class PromptPreviewResponse(BaseModel):
    messages: list[dict[str, str]]


class ChainDebugResponse(BaseModel):
    prompt_messages: list[dict[str, str]]
    model_response_type: str
    model_response_content: str
    parsed_output: str
