from pathlib import Path


DEMO_DOC_PATH = Path(__file__).resolve().parents[2] / "docs" / "demo_scenarios.md"


def get_demo_scenarios_doc() -> dict[str, str]:
    return {
        "path": str(DEMO_DOC_PATH),
        "content": DEMO_DOC_PATH.read_text(encoding="utf-8"),
    }
