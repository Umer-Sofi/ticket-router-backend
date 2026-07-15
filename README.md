# Smart Ticket Router — Backend

AI-powered support-ticket triage. A **FastAPI** service that reads a support
message, splits it into one or more **distinct tickets**, and classifies each
into a **category**, **priority**, and **assigned team** — using **GPT-4o-mini**
for understanding and **deterministic business rules** for policy.

> Frontend (Next.js) lives in a separate repo: **ticket-router-frontend**.

---

## What it does

A support operator submits raw ticket text. One message may contain several
distinct tickets, so the service returns a **JSON array** of classified tickets
— one entry per distinct issue found:

```json
[
  {
    "text": "I was charged twice this month.",
    "category": "Billing",
    "priority": "High",
    "assigned_team": "Billing",
    "reasoning": "The user was charged twice, indicating a payment failure."
  },
  {
    "text": "I also can't log in.",
    "category": "Account",
    "priority": "High",
    "assigned_team": "Account Management",
    "reasoning": "The user cannot access their account."
  }
]
```

The AI *splits* the message and *suggests* a classification for each ticket;
the app's own rules *decide* the final priority and team — so a payment failure
is always **High**, no matter what the model says.

---

## Architecture

```
Browser → Next.js frontend → REST API → FastAPI backend
        → GPT-4o-mini (classify) → business rules (override) → JSON response
```

| Layer | Responsibility |
|-------|----------------|
| `routers/` | HTTP only — request/response, validation |
| `services/openai_client.py` | Calls GPT with a strict JSON schema (temperature 0) |
| `services/business_rules.py` | Deterministic priority override + team assignment |
| `services/router_service.py` | Orchestration: classify → retry → fallback |
| `schemas/` | Pydantic models = the data contract |
| `core/` | Config (API key) + constants (categories, teams, rules) |

**Why a separate backend?** The OpenAI key stays server-side (never in the browser),
and business rules + validation run where users can't tamper with them.

---

## Tech stack

Python · FastAPI · Pydantic · OpenAI SDK · Uvicorn · pytest

---

## Setup

**Requirements:** Python 3.9+

```bash
# 1. create + activate a virtual environment
python3 -m venv venv
source venv/bin/activate

# 2. install dependencies
pip install -r requirements.txt

# 3. add your OpenAI key (see Environment variables below)
echo "OPENAI_API_KEY=sk-your-key" > .env

# 4. run the server
uvicorn app.main:app --reload --port 8000
```

Open **http://localhost:8000/docs** for interactive API docs.

---

## Environment variables

Create a `.env` file in this folder (it is git-ignored — never commit it):

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `OPENAI_API_KEY` | ✅ | — | Your OpenAI secret key. App won't start without it. |
| `OPENAI_MODEL` | ❌ | `gpt-4o-mini` | Model used for classification. |

---

## API

### `GET /health`
Liveness check. Returns `{"status": "ok"}`.

### `POST /api/route-ticket`
Classify a ticket.

**Request:**
```json
{ "text": "I was charged twice for my subscription" }
```

**Response:** a JSON **array** of ticket objects — each
`{ text, category, priority, assigned_team, reasoning }` (see example at top).
A single-issue message returns one ticket; a message with several distinct
issues returns one entry per ticket.

**Validation:** empty, whitespace-only, or text over 5000 chars → `422`.

---

## Categories, teams & business rules

| Category | Team | Forced priority |
|----------|------|-----------------|
| Billing | Billing | High |
| Security | Security | High |
| Account | Account Management | High |
| Technical | Engineering | (defers to GPT) |
| Feature Request | Product | Low |
| General | Customer Support | Low |

---

## Folder structure

```
app/
  main.py            FastAPI entrypoint, /health, CORS
  core/              config.py (settings) + constants.py (categories/teams/rules)
  schemas/           ticket.py — Pydantic models (the contract)
  routers/           tickets.py — POST /api/route-ticket
  services/          openai_client · business_rules · router_service
tests/               pytest suite (unit + mocked API)
scripts/             eval_tickets.py — 20-ticket manual eval
```

---

## Testing

```bash
pytest                            # unit + API tests (free, OpenAI mocked)
python -m scripts.eval_tickets    # 20-ticket end-to-end eval (uses real OpenAI)
```

---

## Reliability

- **Strict JSON schema** — the model cannot return malformed output.
- **Retry** — 3 attempts on transient API failures.
- **Fallback** — if all attempts fail, returns a safe result instead of crashing.

---

## Future work

- Persist ticket history (database)
- Token-usage & cost tracking
- Analytics dashboard
- Confidence scoring
