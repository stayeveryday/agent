from pydantic import BaseModel, Field


class EvalDatasetPreviewResponse(BaseModel):
    dataset_path: str
    case_count: int
    multi_step_count: int
    category_counts: dict[str, int]
    cases: list[dict[str, object]]


class EvalDatasetPreviewRequest(BaseModel):
    limit: int = Field(default=5, ge=1, le=50)


class EvalRunRequest(BaseModel):
    limit: int | None = Field(default=None, ge=1, le=50)
    category: str | None = None


class EvalRunResponse(BaseModel):
    total: int
    passed: int
    failed: int
    pass_rate: float
    category_summary: dict[str, dict[str, int]]
    results: list[dict[str, object]]
