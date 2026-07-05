from typing import Any

from langchain_core.tools import StructuredTool
from pydantic import BaseModel, Field, model_validator


_ASSETS: list[dict[str, Any]] = [
    {
        "asset_tag": "LT-2024-001",
        "hostname": "SZ-LAPTOP-001",
        "employee_id": "u10001",
        "owner_name": "Alice",
        "department": "finance",
        "device_type": "laptop",
        "status": "in_use",
    },
    {
        "asset_tag": "LT-2024-018",
        "hostname": "SZ-LAPTOP-018",
        "employee_id": "u10018",
        "owner_name": "Bob",
        "department": "sales",
        "device_type": "laptop",
        "status": "in_use",
    },
    {
        "asset_tag": "DT-2023-105",
        "hostname": "SH-DESKTOP-105",
        "employee_id": "u10025",
        "owner_name": "Carol",
        "department": "hr",
        "device_type": "desktop",
        "status": "spare",
    },
]


class AssetLookupInput(BaseModel):
    employee_id: str | None = Field(default=None, description="Employee id")
    asset_tag: str | None = Field(default=None, description="Asset tag")
    hostname: str | None = Field(default=None, description="Device hostname")

    @model_validator(mode="after")
    def validate_at_least_one_field(self) -> "AssetLookupInput":
        if self.employee_id or self.asset_tag or self.hostname:
            return self
        raise ValueError("At least one of employee_id, asset_tag, or hostname is required.")


def lookup_asset(
    employee_id: str | None = None,
    asset_tag: str | None = None,
    hostname: str | None = None,
) -> dict[str, object]:
    matches = []
    for asset in _ASSETS:
        if employee_id and asset["employee_id"] != employee_id:
            continue
        if asset_tag and asset["asset_tag"] != asset_tag:
            continue
        if hostname and asset["hostname"] != hostname:
            continue
        matches.append(asset)

    return {
        "match_count": len(matches),
        "results": matches,
    }


def build_asset_lookup_tool() -> StructuredTool:
    return StructuredTool.from_function(
        func=lookup_asset,
        name="lookup_asset",
        description="Look up enterprise asset records by employee id, asset tag, or hostname.",
        args_schema=AssetLookupInput,
    )

