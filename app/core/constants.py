"""Fixed values used across the app: the categories a ticket can have,
and which team owns each category. Defined ONCE here so a typo can't
create a silent mismatch between the schema, the prompt, and the rules.
"""

# The single source of truth: each category maps to the team that owns it.
# In Phase 7 you'll look up a team by category in one line: CATEGORY_TO_TEAM[category]
CATEGORY_TO_TEAM: dict[str, str] = {
    "Billing": "Billing",
    "Security": "Security",
    "Account": "Account Management",
    "Technical": "Engineering",
    "Feature Request": "Product",
    "General": "Customer Support",
}

# Derived lists — so schemas/prompt can reuse them without re-typing the values.
CATEGORIES = list(CATEGORY_TO_TEAM.keys())
TEAMS = list(CATEGORY_TO_TEAM.values())
