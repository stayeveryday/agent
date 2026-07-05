from app.tools.registry import get_tool_by_name


def run_tool(tool_name: str, arguments: dict[str, object]) -> dict[str, object]:
    tool = get_tool_by_name(tool_name)
    if tool is None:
        raise ValueError(f"Unknown tool: {tool_name}")

    result = tool.invoke(arguments)
    return {
        "tool_name": tool_name,
        "arguments": arguments,
        "result": result,
    }

