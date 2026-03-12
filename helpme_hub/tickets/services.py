from django.utils import timezone

from .models import Ticket
from accounts.utils import get_user_school_group
import json
import time
from pathlib import Path


def create_ticket_from_chat(*, user, school_group=None, chat=None, data=None):
    """
    Shared helper to create a Ticket from a chat context.

    Parameters are passed as keyword-only to keep call-sites explicit:
      - user:        request.user who is creating the ticket
      - school_group: organization; if None, derived from user
      - chat:        Chat instance this ticket is escalated from (optional)
      - data:        dict with optional keys:
                       - 'short_title'
                       - 'full_description'
                       - 'priority'
                       - 'category'
                       - 'extra_details'
    """
    if data is None:
        data = {}

    if school_group is None:
        school_group = get_user_school_group(user)

    # Title / description fallbacks depending on whether this came from
    # the escalate form or from a /ticket command.
    short_title = data.get("short_title")
    full_description = data.get("full_description")
    priority = data.get("priority") or "medium"

    if not short_title:
        category = data.get("category", "general")
        short_title = f"Support request ({category})"

    if not full_description:
        extra_details = data.get("extra_details", "").strip()
        base = "Ticket created from chat conversation."
        if extra_details:
            full_description = f"{base}\n\nDetails: {extra_details}"
        else:
            full_description = base

    # #region agent log
    try:
        log_entry = {
            "sessionId": "c93079",
            "runId": "chat-ticket",
            "hypothesisId": "H1",
            "location": "tickets/services.py:create_ticket_from_chat:before_create",
            "message": "About to create ticket from chat",
            "data": {
                "user_id": getattr(user, "id", None),
                "school_group_id": getattr(school_group, "id", None),
                "chat_id": getattr(chat, "id", None),
                "data_keys": sorted(list(data.keys())),
            },
            "timestamp": int(time.time() * 1000),
        }
        log_path = Path("/Users/islamelsayed/Documents/Help Me /.cursor/debug-c93079.log")
        with log_path.open("a") as f:
            f.write(json.dumps(log_entry) + "\n")
    except Exception:
        pass
    # #endregion agent log

    ticket = Ticket.objects.create(
        user=user,
        school_group=school_group,
        chat=chat,
        title=short_title,
        description=full_description,
        priority=priority,
        status="open",
        source="chat",
    )

    # Touch updated_at so any consumers relying on "recent" tickets behave
    # consistently even if created in quick succession.
    ticket.updated_at = timezone.now()
    ticket.save(update_fields=["updated_at"])

    # #region agent log
    try:
        log_entry = {
            "sessionId": "c93079",
            "runId": "chat-ticket",
            "hypothesisId": "H1",
            "location": "tickets/services.py:create_ticket_from_chat:after_create",
            "message": "Ticket created from chat",
            "data": {
                "ticket_id": getattr(ticket, "id", None),
                "user_id": getattr(user, "id", None),
                "school_group_id": getattr(school_group, "id", None),
                "chat_id": getattr(chat, "id", None),
                "priority": ticket.priority,
                "source": ticket.source,
            },
            "timestamp": int(time.time() * 1000),
        }
        log_path = Path("/Users/islamelsayed/Documents/Help Me /.cursor/debug-c93079.log")
        with log_path.open("a") as f:
            f.write(json.dumps(log_entry) + "\n")
    except Exception:
        pass
    # #endregion agent log

    return ticket

