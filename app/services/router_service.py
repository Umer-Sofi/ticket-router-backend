"""Orchestrator: turns a raw message into a final RouteResponse.

A message may hold several tickets, so the pipeline is:
    classify message -> [business rules per ticket] -> RouteResponse (+ metadata)
Retries wrap the whole thing, and it guarantees the app NEVER crashes: if
every attempt fails, we return a safe single-ticket fallback instead of raising.
"""

import logging

from app.core.constants import (
    CATEGORY_TO_TEAM,
    FALLBACK_CATEGORY,
    FALLBACK_PRIORITY,
)
from app.schemas.ticket import RouteResult
from app.services.business_rules import apply_business_rules
from app.services.openai_client import classify_tickets

logger = logging.getLogger(__name__)

MAX_ATTEMPTS = 3


def _fallback() -> list[RouteResult]:
    """Safe result when OpenAI is unreachable after all retries.
    One catch-all ticket for the whole message. Priority = Medium (not Low, so
    urgent tickets aren't buried; not High, so a real outage doesn't flag
    everything as critical). Built fresh each call so we never mutate a shared
    instance. All values come from constants.
    """
    fallback_ticket = RouteResult(
        category=FALLBACK_CATEGORY,
        priority=FALLBACK_PRIORITY,
        assigned_team=CATEGORY_TO_TEAM[FALLBACK_CATEGORY],
        reasoning="Automatic classification unavailable — routed for manual review.",
    )
    return [fallback_ticket]


def route_message(text: str) -> list[RouteResult]:
    """Classify every ticket in a message, retrying transient failures, never
    crashing. One OpenAI call handles the whole message; business rules are
    then applied to each extracted ticket independently. Returns a list of
    tickets (one per distinct issue found).
    """
    for attempt in range(1, MAX_ATTEMPTS + 1):
        try:
            gpt_tickets = classify_tickets(text)  # may raise (network / API)

            # An empty list means we couldn't identify a ticket — treat it as a
            # failure so we retry and ultimately fall back, never return zero.
            if not gpt_tickets:
                raise ValueError("model returned no tickets")

            # Apply the SAME deterministic policy to each ticket.
            return [apply_business_rules(t) for t in gpt_tickets]
        except Exception as exc:
            logger.warning("classify attempt %d/%d failed: %s", attempt, MAX_ATTEMPTS, exc)

    logger.error("All %d classification attempts failed — returning fallback.", MAX_ATTEMPTS)
    return _fallback()
