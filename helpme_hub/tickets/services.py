from django.utils import timezone

from .models import Ticket
from accounts.utils import get_user_school_group


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

    return ticket

