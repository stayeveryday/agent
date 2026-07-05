from itertools import count
from typing import Literal

from langchain_core.tools import StructuredTool
from pydantic import BaseModel, Field


TicketPriority = Literal["low", "medium", "high"]
TicketCategory = Literal["email", "network", "hardware", "account", "other"]


_TICKETS: dict[str, dict[str, object]] = {
    "INC-1001": {
        "ticket_id": "INC-1001",
        "requester": "u10001",
        "status": "in_progress",
        "priority": "high",
        "category": "network",
        "summary": "VPN connection fails after password reset",
        "assigned_group": "network-ops",
    },
    "INC-1002": {
        "ticket_id": "INC-1002",
        "requester": "u10018",
        "status": "waiting_for_user",
        "priority": "medium",
        "category": "email",
        "summary": "Outlook client keeps asking for password",
        "assigned_group": "service-desk",
    },
    "REQ-2001": {
        "ticket_id": "REQ-2001",
        "requester": "u10025",
        "status": "resolved",
        "priority": "low",
        "category": "hardware",
        "summary": "Request for external monitor",
        "assigned_group": "it-asset",
    },
}
_TICKET_SEQ = count(start=3001)


class TicketStatusInput(BaseModel):
    ticket_id: str = Field(min_length=3, description="Ticket identifier such as INC-1001")


class TicketCreateInput(BaseModel):
    requester: str = Field(min_length=1, description="Employee id or requester account")
    summary: str = Field(min_length=5, description="Short summary of the issue")
    category: TicketCategory = Field(description="Ticket category")
    priority: TicketPriority = Field(description="Requested ticket priority")


def get_ticket_status(ticket_id: str) -> dict[str, object]:
    ticket = _TICKETS.get(ticket_id.upper())
    if not ticket:
        return {
            "found": False,
            "ticket_id": ticket_id,
            "message": "Ticket not found.",
        }
    return {
        "found": True,
        "ticket": ticket,
    }


def create_ticket(
    requester: str,
    summary: str,
    category: TicketCategory,
    priority: TicketPriority,
) -> dict[str, object]:
    ticket_id = f"INC-{next(_TICKET_SEQ)}"
    assigned_group = {
        "email": "service-desk",
        "network": "network-ops",
        "hardware": "it-asset",
        "account": "identity-support",
        "other": "service-desk",
    }[category]
    ticket = {
        "ticket_id": ticket_id,
        "requester": requester,
        "status": "new",
        "priority": priority,
        "category": category,
        "summary": summary,
        "assigned_group": assigned_group,
    }
    _TICKETS[ticket_id] = ticket
    return {
        "created": True,
        "ticket": ticket,
    }


def build_ticket_status_tool() -> StructuredTool:
    return StructuredTool.from_function(
        func=get_ticket_status,
        name="get_ticket_status",
        description="Look up the current status of an IT service ticket by ticket id.",
        args_schema=TicketStatusInput,
    )


def build_create_ticket_tool() -> StructuredTool:
    return StructuredTool.from_function(
        func=create_ticket,
        name="create_ticket",
        description="Create a new IT service ticket for a user issue.",
        args_schema=TicketCreateInput,
    )

