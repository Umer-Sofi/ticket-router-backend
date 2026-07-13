"""Orchestrator: turns raw ticket text into a final RouteResult.

Ties together the whole pipeline and guarantees the app NEVER crashes:
    classify (with retries) -> business rules -> RouteResult (+ metadata)
If every attempt fails, we return a safe fallback instead of raising.
"""

import logging

from app.core.config import settings
from app.schemas.ticket import RouteResult
from app.services.business_rules import apply_business_rules
from app.services.openai_client import classify_ticket, cost_usd

logger = logging.getLogger(__name__)

MAX_ATTEMPTS = 3


def _fallback(retries: int) -> RouteResult:
    """Safe result when OpenAI is unreachable after all retries.
    Priority = Medium (not Low, so urgent tickets aren't buried; not High, so a
    real outage doesn't flag everything as critical). Built fresh each call so
    we never mutate a shared instance.
    """
    return RouteResult(
        category="General",
        priority="Medium",
        assigned_team="Customer Support",
        reasoning="Automatic classification unavailable — routed for manual review.",
        retries=retries,
    )


def route_ticket(text: str) -> RouteResult:
    """Classify a ticket, retrying transient failures, never crashing."""
    for attempt in range(1, MAX_ATTEMPTS + 1):
        try:
            gpt, usage = classify_ticket(text)      # may raise (network / API)
            result = apply_business_rules(gpt)       # success: policy applied

            # Attach real metadata for the dashboard.
            result.model = settings.openai_model
            result.prompt_tokens = usage.prompt_tokens
            result.completion_tokens = usage.completion_tokens
            result.total_tokens = usage.total_tokens
            result.cost_usd = cost_usd(usage)
            result.retries = attempt - 1             # 0 if it worked first try
            return result
        except Exception as exc:
            logger.warning("classify attempt %d/%d failed: %s", attempt, MAX_ATTEMPTS, exc)

    logger.error("All %d classification attempts failed — returning fallback.", MAX_ATTEMPTS)
    return _fallback(retries=MAX_ATTEMPTS)
