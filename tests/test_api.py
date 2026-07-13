"""Tests for the HTTP endpoint using FastAPI's TestClient.

Validation tests reach the endpoint WITHOUT calling OpenAI (rejected first),
so they're free. The happy-path and fallback tests MOCK the OpenAI call so
they're deterministic and cost nothing.
"""

import app.services.router_service as router_service
from app.main import app
from app.schemas.ticket import GptClassification
from fastapi.testclient import TestClient

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
        return GptClassification(category="Billing", priority="Low", reasoning="mock")

    monkeypatch.setattr(router_service, "classify_ticket", fake_classify)

    resp = client.post("/api/route-ticket", json={"text": "charged twice"})
    assert resp.status_code == 200
    body = resp.json()
    assert body["category"] == "Billing"
    assert body["priority"] == "High"            # overridden by business rule
    assert body["assigned_team"] == "Billing"    # derived from category
    assert body["processing_time_ms"] is not None


# --- Failure path: mock OpenAI to always fail -> fallback, never crash ----
def test_fallback_when_openai_fails(monkeypatch):
    def boom(text):
        raise RuntimeError("OpenAI down")

    monkeypatch.setattr(router_service, "classify_ticket", boom)

    resp = client.post("/api/route-ticket", json={"text": "help me"})
    assert resp.status_code == 200                       # did NOT crash
    assert resp.json()["assigned_team"] == "Customer Support"  # fallback result
