"""Tests for the HTTP endpoint using FastAPI's TestClient.

Validation tests reach the endpoint WITHOUT calling OpenAI (rejected first),
so they're free. The happy-path and fallback tests MOCK the OpenAI call so
they're deterministic and cost nothing.
"""

from fastapi.testclient import TestClient

import app.services.router_service as router_service
from app.main import app
from app.schemas.ticket import GptTicket

client = TestClient(app)


def test_health():
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}


# --- Input validation: these never reach OpenAI (422 first) ---------------
def test_empty_text_rejected():
    assert client.post("/api/route-ticket", json={"text": ""}).status_code == 422


def test_whitespace_text_rejected():
    assert client.post("/api/route-ticket", json={"text": "   "}).status_code == 422


def test_missing_field_rejected():
    assert client.post("/api/route-ticket", json={}).status_code == 422


def test_oversized_text_rejected():
    assert client.post("/api/route-ticket", json={"text": "a" * 6000}).status_code == 422


# --- Happy path: mock OpenAI so it's deterministic + free -----------------
def test_route_ticket_applies_business_rules(monkeypatch):
    # Pretend GPT said Billing/Low. Business rule must force priority to High.
    def fake_classify(text):
        return [
            GptTicket(text="charged twice", category="Billing", priority="Low", reasoning="mock")
        ]

    monkeypatch.setattr(router_service, "classify_tickets", fake_classify)

    resp = client.post("/api/route-ticket", json={"text": "charged twice"})
    assert resp.status_code == 200
    body = resp.json()
    # Response is a bare list of tickets — no wrapper, no metadata.
    assert isinstance(body, list)
    assert len(body) == 1
    first = body[0]
    assert first["category"] == "Billing"
    assert first["priority"] == "High"  # overridden by business rule
    assert first["assigned_team"] == "Billing"  # derived from category
    assert set(first.keys()) == {"text", "category", "priority", "assigned_team", "reasoning"}


# --- Multi-ticket: one message with two distinct tickets ------------------
def test_multiple_tickets_each_classified(monkeypatch):
    # A message that raises a billing problem AND a login problem.
    def fake_classify(text):
        return [
            GptTicket(
                text="charged twice", category="Billing", priority="Low", reasoning="billing"
            ),
            GptTicket(
                text="can't log in", category="Account", priority="Medium", reasoning="login"
            ),
        ]

    monkeypatch.setattr(router_service, "classify_tickets", fake_classify)

    resp = client.post("/api/route-ticket", json={"text": "charged twice; also can't log in"})
    assert resp.status_code == 200
    body = resp.json()
    assert len(body) == 2
    assert [t["category"] for t in body] == ["Billing", "Account"]
    # Business rules run per ticket: both categories force High priority.
    assert [t["priority"] for t in body] == ["High", "High"]
    assert [t["assigned_team"] for t in body] == ["Billing", "Account Management"]
    # Each ticket carries the text slice it came from.
    assert body[0]["text"] == "charged twice"


# --- Failure path: mock OpenAI to always fail -> fallback, never crash ----
def test_fallback_when_openai_fails(monkeypatch):
    def boom(text):
        raise RuntimeError("OpenAI down")

    monkeypatch.setattr(router_service, "classify_tickets", boom)

    resp = client.post("/api/route-ticket", json={"text": "help me"})
    assert resp.status_code == 200  # did NOT crash
    body = resp.json()
    assert len(body) == 1
    assert body[0]["assigned_team"] == "Customer Support"  # fallback result
