from datetime import datetime

from langchain_core.tools import BaseTool, tool


@tool
def current_time() -> str:
    """Return the current local time for time-related requests."""
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


@tool
def create_helpdesk_ticket(issue: str, priority: str = "normal") -> str:
    """Create a fake helpdesk ticket for issues like VPN, laptop, or mailbox access."""
    ticket_id = f"HD-{abs(hash((issue, priority))) % 100000:05d}"
    return f"已创建服务台工单 {ticket_id}，优先级 {priority}，问题：{issue}"


def build_default_tools() -> list[BaseTool]:
    return [current_time, create_helpdesk_ticket]

