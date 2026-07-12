"""Talks to OpenAI. Its ONLY job: send prompt + ticket, get a structured
GptClassification back. No business rules, no HTTP — those live elsewhere.
"""

from openai import OpenAI

from app.core.config import settings
from app.services.prompt import SYSTEM_PROMPT
from app.schemas.ticket import GptClassification

# One client, created once, reused for every call. Reads the key from config.
client = OpenAI(api_key=settings.openai_api_key)


def classify_ticket(text: str) -> GptClassification:
    """Ask GPT to classify one ticket and return the parsed result."""
    completion = client.chat.completions.parse(
        model=settings.openai_model,
        temperature=0,  # deterministic: same ticket -> same classification
        messages=[
            # System = our instructions (trusted). User = the ticket (untrusted data).
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": text},
        ],
        # Strict schema: the API is forced to return exactly this shape,
        # and the SDK parses the reply straight into a GptClassification.
        response_format=GptClassification,
    )
    return completion.choices[0].message.parsed
