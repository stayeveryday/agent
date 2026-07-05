from pydantic import BaseModel


class DemoScenariosResponse(BaseModel):
    path: str
    content: str


class DemoAcceptanceRequest(BaseModel):
    include_slow: bool = False
    write_report: bool = True


class DemoAcceptanceResponse(BaseModel):
    generated_at: str
    total: int
    passed: int
    failed: int
    pass_rate: float
    checks: list[dict[str, object]]
    report_path: str
