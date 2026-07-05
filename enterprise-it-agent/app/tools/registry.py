from functools import lru_cache

from langchain_core.tools import BaseTool

from app.tools.asset_tools import build_asset_lookup_tool
from app.tools.ticket_tools import build_create_ticket_tool, build_ticket_status_tool


@lru_cache(maxsize=1)
def get_business_tools() -> tuple[BaseTool, ...]:
    return (
        build_ticket_status_tool(),
        build_create_ticket_tool(),
        build_asset_lookup_tool(),
    )


def list_tool_summaries() -> list[dict[str, str]]:
    return [
        {
            "name": tool.name,
            "description": tool.description or "",
        }
        for tool in get_business_tools()
    ]


def get_tool_by_name(name: str) -> BaseTool | None:
    for tool in get_business_tools():
        if tool.name == name:
            return tool
    return None

