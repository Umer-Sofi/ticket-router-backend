"""Orchestrator: turns raw ticket text into a final RouteResult.

Ties together the whole pipeline and guarantees the app NEVER crashes:
    classify (with retries) -> business rules -> RouteResult
If every attempt fails, we return a safe fallback instead of raising.
"""

import logging

from app.schemas.ticket import RouteResult
from app.services.openai_client import classify_ticket
from app.services.business_rules import apply_business_rules

logger = logging.getLogger(__name__)

MAX_ATTEMPTS = 3

# Fallback when OpenAI is unreachable after all retries.
# Design choice: priority = Medium (not Low, so urgent tickets aren't buried;
# not High, so a real outage doesn't flag everything as critical) and route to
# Customer Support for a human to triage manually. The reasoning makes the
# degraded state obvious to whoever reads it.
FALLBACK_RESULT = RouteResult(
    category="General",
    priority="Medium",
    assigned_team="Customer Support",
    reasoning="Automatic classification unavailable — routed for manual review.",
)


def route_ticket(text: str) -> RouteResult:
    """Classify a ticket, retrying transient failures, never crashing."""
    for attempt in range(1, MAX_ATTEMPTS + 1):
        try:
            gpt = classify_ticket(text)          # may raise (network / API / timeout)
            return apply_business_rules(gpt)     # success: policy applied, done
        except Exception as exc:
            logger.warning("classify attempt %d/%d failed: %s", attempt, MAX_ATTEMPTS, exc)

    # Every attempt failed. Log loudly (so an outage is visible) and degrade gracefully.
    logger.error("All %d classification attempts failed — returning fallback.", MAX_ATTEMPTS)
    return FALLBACK_RESULT
