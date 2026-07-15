"""Deterministic routing: GPT suggests, this layer decides.

Takes GPT's classification and applies company policy that must NOT depend
on the model's judgment — the forced priorities and the team assignment.
This is pure, testable logic with no OpenAI or HTTP involved.
"""

from app.core.constants import CATEGORY_TO_TEAM, PRIORITY_OVERRIDES
from app.schemas.ticket import GptClassification, RouteResult


def apply_business_rules(gpt: GptClassification) -> RouteResult:
    # Team is a pure lookup from category — zero judgment, always consistent.
    assigned_team = CATEGORY_TO_TEAM[gpt.category]

    # If the category has a hard rule, use it; otherwise keep GPT's suggestion.
    # .get(key, fallback) does exactly this: fallback = GPT's own priority.
    final_priority = PRIORITY_OVERRIDES.get(gpt.category, gpt.priority)

    # `text` only exists on a GptTicket (multi-ticket input); tolerate a plain
    # GptClassification (used by unit tests) by defaulting to None.
    return RouteResult(
        text=getattr(gpt, "text", None),
        category=gpt.category,
        priority=final_priority,
        assigned_team=assigned_team,
        reasoning=gpt.reasoning,
    )
