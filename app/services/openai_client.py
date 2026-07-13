"""Talks to OpenAI. Its ONLY job: send prompt + ticket, get a structured
GptClassification back (plus token usage). No business rules, no HTTP.
"""

from openai import OpenAI
from openai.types import CompletionUsage

from app.core.config import settings
from app.schemas.ticket import GptClassification
from app.services.prompt import SYSTEM_PROMPT

# One client, created once, reused for every call. Reads the key from config.
# timeout: don't let a slow/hung call freeze the app.
# max_retries=0: WE own the retry logic in router_service, so disable the
# SDK's built-in retries to avoid them stacking (3 of ours x 2 of theirs).
client = OpenAI(api_key=settings.openai_api_key, timeout=20.0, max_retries=0)

# gpt-4o-mini pricing (USD per 1M tokens). Update if the model or prices change.
_PRICE_PER_1M_INPUT = 0.15
_PRICE_PER_1M_OUTPUT = 0.60


def cost_usd(usage: CompletionUsage) -> float:
    """Estimate the dollar cost of one call from its token usage."""
    prompt = (usage.prompt_tokens or 0) / 1_000_000 * _PRICE_PER_1M_INPUT
    completion = (usage.completion_tokens or 0) / 1_000_000 * _PRICE_PER_1M_OUTPUT
    return round(prompt + completion, 6)


def classify_ticket(text: str) -> tuple[GptClassification, CompletionUsage]:
    """Ask GPT to classify one ticket.
    Returns (classification, usage) so the caller can report tokens/cost.
    """
    completion = client.chat.completions.parse(
        model=settings.openai_model,
        temperature=0,  # deterministic: same ticket -> same classification
        messages=[
            # System = our instructions (trusted). User = the ticket (untrusted data).
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": text},
        ],
        # Strict schema: the API is forced to return exactly this shape.
        response_format=GptClassification,
    )
    return completion.choices[0].message.parsed, completion.usage
