"""Unit tests for the deterministic routing layer.
No OpenAI, no network — pure logic, so these are fast and always reliable.
"""

import pytest

from app.schemas.ticket import GptClassification
from app.services.business_rules import apply_business_rules


def _gpt(category, priority="Medium"):
    return GptClassification(category=category, priority=priority, reasoning="test")


@pytest.mark.parametrize(
    "category, expected_priority",
    [
        ("Billing", "High"),
        ("Security", "High"),
        ("Account", "High"),
        ("Feature Request", "Low"),
        ("General", "Low"),
    ],
)
def test_priority_override_forces_business_rule(category, expected_priority):
    # Even if GPT suggested Medium, the rule must override it.
    result = apply_business_rules(_gpt(category, priority="Medium"))
    assert result.priority == expected_priority


def test_technical_keeps_gpt_priority():
    # Technical has NO rule -> GPT's suggestion is kept.
    assert apply_business_rules(_gpt("Technical", priority="Low")).priority == "Low"
    assert apply_business_rules(_gpt("Technical", priority="High")).priority == "High"


def test_override_ignores_wrong_gpt_priority_both_directions():
    # GPT over-rates a feature request -> forced back down to Low.
    assert apply_business_rules(_gpt("Feature Request", priority="High")).priority == "Low"
    # GPT under-rates a payment issue -> forced up to High.
    assert apply_business_rules(_gpt("Billing", priority="Low")).priority == "High"


def test_team_is_derived_from_category():
    assert apply_business_rules(_gpt("Billing")).assigned_team == "Billing"
    assert apply_business_rules(_gpt("Technical")).assigned_team == "Engineering"
    assert apply_business_rules(_gpt("General")).assigned_team == "Customer Support"


def test_reasoning_and_category_pass_through():
    gpt = GptClassification(category="Security", priority="Low", reasoning="hacked")
    result = apply_business_rules(gpt)
    assert result.category == "Security"
    assert result.reasoning == "hacked"
