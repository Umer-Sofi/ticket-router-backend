"""Manual end-to-end eval: run 20 sample tickets through the REAL pipeline
(OpenAI + business rules) and report category accuracy.

This is NOT a pytest test — it costs money and GPT isn't 100% deterministic.
Run it by hand to sanity-check classification quality:
    python -m scripts.eval_tickets
"""

from app.services.router_service import route_ticket

# (ticket text, expected category) — expectations are the human's judgment.
SAMPLES = [
    ("I was charged twice for my subscription this month", "Billing"),
    ("My invoice shows the wrong amount", "Billing"),
    ("I want a refund for last month's payment", "Billing"),
    ("Someone logged into my account from another country", "Security"),
    ("I think my account has been hacked", "Security"),
    ("I received a suspicious phishing email pretending to be you", "Security"),
    ("I can't log in, it says my password is wrong", "Account"),
    ("I'm locked out of my account after too many attempts", "Account"),
    ("How do I reset my password?", "Account"),
    ("The app crashes every time I click export", "Technical"),
    ("The dashboard shows a blank screen after login", "Technical"),
    ("Uploading a file gives me a 500 error", "Technical"),
    ("Please add a dark mode to the dashboard", "Feature Request"),
    ("It would be great to have CSV export", "Feature Request"),
    ("Can you support single sign-on (SSO)?", "Feature Request"),
    ("How do I change my email address?", "General"),
    ("What are your business hours?", "General"),
    ("Where can I find the user guide?", "General"),
    ("La aplicacion se cierra cuando intento exportar datos", "Technical"),
    ("THIS IS RIDICULOUS!! You charged me THREE times!!!", "Billing"),
]


def main():
    passed = 0
    print(f"{'#':>2}  {'EXPECTED':16} {'GOT':16} {'PRIORITY':8} {'TEAM':18} OK")
    print("-" * 78)
    for i, (text, expected) in enumerate(SAMPLES, 1):
        r = route_ticket(text)
        ok = r.category == expected
        passed += ok
        print(f"{i:>2}  {expected:16} {r.category:16} {r.priority:8} {r.assigned_team:18} {'✅' if ok else '❌'}")
    print("-" * 78)
    print(f"Category accuracy: {passed}/{len(SAMPLES)} = {passed / len(SAMPLES) * 100:.0f}%")


if __name__ == "__main__":
    main()
