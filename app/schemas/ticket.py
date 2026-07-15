"""Pydantic models = the data contract for this service.

- TicketRequest:  the shape of what comes IN (the request body).
- RouteResult:    one classified ticket; the endpoint returns a LIST of these
                  (one per distinct ticket found in the message).

Pydantic validates data against these models automatically. If incoming
data doesn't match, FastAPI rejects it with a 422 before our code runs.
"""

from typing import Optional

from pydantic import BaseModel, Field, field_validator

from app.core.constants import Category, Priority, Team

# Cap ticket length: protects against huge pastes (token cost + latency).
# The frontend textarea should use the same limit (kept in sync by hand).
MAX_TICKET_CHARS = 5000


class TicketRequest(BaseModel):
    """What the support operator sends us: the raw ticket text."""

    # min_length rejects "", max_length rejects huge pastes — both -> 422.
    text: str = Field(..., min_length=1, max_length=MAX_TICKET_CHARS)

    @field_validator("text")
    @classmethod
    def not_blank(cls, v: str) -> str:
        # min_length=1 lets "   " (whitespace) through; this rejects it.
        if not v.strip():
            raise ValueError("Ticket text cannot be empty or whitespace.")
        return v


class GptClassification(BaseModel):
    """The 3 fields that need GPT's judgment, for ONE ticket.
    `assigned_team` is NOT here — it's derived from category in our code.
    """

    category: Category
    priority: Priority
    reasoning: str


class GptTicket(GptClassification):
    """One ticket the model extracted from the message: a classification
    plus the slice of text it applies to. `text` lets the UI show WHICH
    part of the message produced each result.
    """

    text: str


class GptClassificationList(BaseModel):
    """The strict schema the OpenAI API is forced to match: a list of tickets.
    (Structured outputs need an object at the top level, so the list is wrapped
    in this `tickets` field rather than returned bare.)
    """

    tickets: list[GptTicket]


class RouteResult(BaseModel):
    """One classified ticket we send back, after applying business rules.
    Built from a GptTicket + the derived team + the final (possibly forced)
    priority. The endpoint returns a list of these — one per ticket found.
    """

    text: Optional[str] = None  # the ticket text this result was derived from
    category: Category
    priority: Priority
    assigned_team: Team
    reasoning: str
