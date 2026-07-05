from pydantic import BaseModel, Field


class RagChunkPreviewItem(BaseModel):
    source: str
    department: str
    access_level: str
    length: int
    content: str


class RagPreviewResponse(BaseModel):
    document_count: int
    chunk_count: int
    chunk_size: int
    chunk_overlap: int
    chunks: list[RagChunkPreviewItem]


class RagPreviewRequest(BaseModel):
    chunk_size: int = Field(default=400, ge=100, le=2000)
    chunk_overlap: int = Field(default=80, ge=0, le=500)
    limit: int = Field(default=5, ge=1, le=20)


class RagIngestResponse(BaseModel):
    document_count: int
    chunk_count: int
    stored_count: int
    embedding_model_name: str
    embedding_device: str
    gpu_available: bool


class RagSearchRequest(BaseModel):
    query: str = Field(min_length=1)
    top_k: int = Field(default=4, ge=1, le=10)
    fetch_k: int = Field(default=8, ge=1, le=20)
    department: str | None = None
    access_level: str | None = None


class RagSearchResultItem(BaseModel):
    source: str
    department: str
    access_level: str
    length: int
    score: float
    content: str


class RagSearchResponse(BaseModel):
    query: str
    top_k: int
    fetch_k: int
    department: str | None = None
    access_level: str | None = None
    results: list[RagSearchResultItem]


class RagAnswerRequest(BaseModel):
    question: str = Field(min_length=1)
    top_k: int = Field(default=4, ge=1, le=10)
    fetch_k: int = Field(default=8, ge=1, le=20)
    department: str | None = None
    access_level: str | None = None


class RagAnswerResponse(BaseModel):
    question: str
    top_k: int
    fetch_k: int
    department: str | None = None
    access_level: str | None = None
    answer: str
    sources: list[str]
    results: list[RagSearchResultItem]
