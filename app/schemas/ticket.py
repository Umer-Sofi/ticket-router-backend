"""Pydantic models = the data contract for this service.

- TicketRequest: the shape of what comes IN (the request body).
- RouteResult:   the shape of what goes OUT (the response).

Pydantic validates data against these models automatically. If incoming
data doesn't match, FastAPI rejects it with a 422 before our code runs.
"""

from pydantic import BaseModel, Field, field_validator
from typing import Literal, Optional

# Cap ticket length: protects against huge pastes (token cost + latency).
# The frontend textarea should use the same limit (kept in sync by hand).
MAX_TICKET_CHARS = 5000

# --- Allowed values, expressed as TYPES ------------------------------------
# Literal means "the value must be exactly one of these strings, nothing else."
# Why not `str`? A plain str would accept "Hgih" or "urgent" — garbage the
# frontend can't handle. Literal makes an invalid value impossible: Pydantic
# rejects anything outside the list. Compile-time-style safety, like a Java enum.
# NOTE: these strings must match constants.py EXACTLY (spelling + capitalisation).
Priority = Literal["High", "Medium", "Low"]
Category = Literal["Billing", "Security", "Account", "Technical", "Feature Request", "General"]
Team = Literal["Billing", "Security", "Account Management", "Engineering", "Product", "Customer Support"]


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
    """What GPT is allowed to return: the 3 fields that need judgment.
    `assigned_team` is NOT here — it's derived from category in our code.
    This is also the strict schema the OpenAI API is forced to match.
    """
    category: Category
    priority: Priority
    reasoning: str


class RouteResult(BaseModel):
    """What we send back after classifying + applying business rules.
    Built from GptClassification + the derived team + final priority.
    """
    category: Category
    priority: Priority
    assigned_team: Team
    reasoning: str
    # Set by the endpoint (metadata, not part of the routing decision).
    # Optional so the business-rules layer doesn't have to know about timing.
    processing_time_ms: Optional[float] = None
