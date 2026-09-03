"""
Manual test script for the Support Inbox two-agent chain - run via CLI:
    cd backend
    .venv/Scripts/python.exe scripts/test_support_agent.py

Runs a handful of sample customer emails through run_support() and prints the
full audit trail (Draft Agent's first pass -> Policy Checker's verdict -> final
result) for each, including at least one email crafted to trip up the Draft
Agent's first pass (a price-match request outside the 7-day eligibility
window) - so the "agent checks agent" mechanic can be verified with a real,
not simulated, rejection before it's wired into the /support endpoint.
"""

import sys
from pathlib import Path

from dotenv import load_dotenv

sys.stdout.reconfigure(encoding="utf-8")

BACKEND_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BACKEND_DIR))
load_dotenv(BACKEND_DIR / ".env")

from app.support_agent import run_support  # noqa: E402

SAMPLE_EMAILS = [
    "Hi, I bought a pair of shoes 3 weeks ago and they just don't fit right. Can I return them for a refund?",
    "My blender arrived yesterday with a cracked lid. Can you help me sort this out?",
    "I found the exact same TV I bought from you two months ago selling for less on another site. Can you "
    "match the price and refund me the difference?",
    "Where is my order? It's been 10 days and I haven't received anything.",
]


def main() -> None:
    for email in SAMPLE_EMAILS:
        print(f"\n{'=' * 80}\nEMAIL: {email}")
        run = run_support(email)

        print(f"\n[Draft Agent]")
        print(f"  category={run.draft.category!r}")
        print(f"  reply: {run.draft.draft_reply}")

        print(f"\n[Policy Checker: {run.checker.verdict.upper()}]")
        print(f"  citation: {run.checker.citation}")
        if run.checker.verdict == "rejected":
            print(f"  critique: {run.checker.critique}")
            print(f"  corrected_category: {run.checker.corrected_category!r}")

        print(f"\n[Final result]")
        print(f"  category={run.final.category!r}")
        print(f"  reply: {run.final.draft_reply}")
        print(f"  citations used: {run.citations}")


if __name__ == "__main__":
    main()
