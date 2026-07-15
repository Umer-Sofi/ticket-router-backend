"""Talks to OpenAI. Its ONLY job: send prompt + message, get back the
structured list of tickets found in it. No business rules, no HTTP.
"""

from openai import OpenAI

from app.core.config import settings
from app.schemas.ticket import GptClassificationList, GptTicket
from app.services.prompt import SYSTEM_PROMPT

# One client, created once, reused for every call. Reads the key from config.
# timeout: don't let a slow/hung call freeze the app.
# max_retries=0: WE own the retry logic in router_service, so disable the
# SDK's built-in retries to avoid them stacking (3 of ours x 2 of theirs).
client = OpenAI(api_key=settings.openai_api_key, timeout=20.0, max_retries=0)


def classify_tickets(text: str) -> list[GptTicket]:
    """Ask GPT to split a message into distinct tickets and classify each.
    One API call classifies the whole message.
    """
    completion = client.chat.completions.parse(
        model=settings.openai_model,
        temperature=0,  # deterministic: same message -> same classification
        messages=[
            # System = our instructions (trusted). User = the message (untrusted data).
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": text},
        ],
        # Strict schema: the API is forced to return exactly this shape.
        response_format=GptClassificationList,
    )
    return completion.choices[0].message.parsed.tickets

