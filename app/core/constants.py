"""Domain vocabulary and deterministic routing policy.

Single source of truth for the categories, teams, and priorities — and the
rules that map between them. The schemas import the TYPES from here, so the
vocabulary is defined exactly once and cannot drift between layers.
"""

from typing import Literal

# --- Domain types: the only place these values are declared -----------------
Priority = Literal["High", "Medium", "Low"]
Category = Literal["Billing", "Security", "Account", "Technical", "Feature Request", "General"]
Team = Literal[
    "Billing",
    "Security",
    "Account Management",
    "Engineering",
    "Product",
    "Customer Support",
]

# Each category maps to the team that owns it. Typed by the domain types above,
# so a mistyped key or value is a static type error — the mapping cannot drift
# from the Category/Team definitions.
CATEGORY_TO_TEAM: dict[Category, Team] = {
    "Billing": "Billing",
    "Security": "Security",
    "Account": "Account Management",
    "Technical": "Engineering",
    "Feature Request": "Product",
    "General": "Customer Support",
}

# Derived list so other layers can reuse the values without re-typing them.
CATEGORIES: list[Category] = list(CATEGORY_TO_TEAM.keys())

# Deterministic priority policy (the business rules). These OVERRIDE whatever
# priority GPT suggested. "Technical" is intentionally omitted: it has no hard
# rule, so we defer to GPT's suggested priority.
PRIORITY_OVERRIDES: dict[Category, Priority] = {
    "Billing": "High",  # payment failures, charges
    "Security": "High",  # compromised accounts, breaches
    "Account": "High",  # lockouts, cannot log in
    "Feature Request": "Low",  # nice-to-haves
    "General": "Low",  # how-to questions
}

# Safe routing used when classification is unavailable (all retries failed).
FALLBACK_CATEGORY: Category = "General"
FALLBACK_PRIORITY: Priority = "Medium"
