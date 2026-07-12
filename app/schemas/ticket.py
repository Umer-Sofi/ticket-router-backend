"""Pydantic models = the data contract for this service.

- TicketRequest: the shape of what comes IN (the request body).
- RouteResult:   the shape of what goes OUT (the response).

Pydantic validates data against these models automatically. If incoming
data doesn't match, FastAPI rejects it with a 422 before our code runs.
"""

from pydantic import BaseModel
from typing import Literal

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
    text: str


class RouteResult(BaseModel):
    """What we send back after classifying + applying business rules."""
    category: Category
    priority: Priority
    assigned_team: Team
    reasoning: str
