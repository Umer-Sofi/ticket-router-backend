"""Guards against the domain vocabulary drifting between layers.

The prompt spells out each category (with a description GPT needs), so those
strings can't be auto-derived. These tests make sure they stay in sync with
the single source of truth in constants.py.
"""

from app.core.constants import CATEGORIES, CATEGORY_TO_TEAM, PRIORITY_OVERRIDES
from app.services.prompt import SYSTEM_PROMPT


def test_prompt_mentions_every_category():
    for category in CATEGORIES:
        assert category in SYSTEM_PROMPT, f"'{category}' missing from the system prompt"


def test_priority_overrides_use_valid_categories():
    for category in PRIORITY_OVERRIDES:
        assert category in CATEGORY_TO_TEAM, f"'{category}' is not a known category"
