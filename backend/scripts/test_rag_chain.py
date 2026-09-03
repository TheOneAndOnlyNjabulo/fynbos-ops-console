"""
Manual test script for the Knowledge Assistant chain - run via CLI:
    cd backend
    .venv/Scripts/python.exe scripts/test_rag_chain.py

Includes full-sentence questions, bare-keyword queries (the exact shape that
broke Marula's chatbot in production - included here from the start rather
than found later), and a deliberately out-of-scope question, to confirm both
guardrails behave correctly before this is wired into the Chat UI.
"""

import sys
from pathlib import Path

from dotenv import load_dotenv

sys.stdout.reconfigure(encoding="utf-8")

BACKEND_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BACKEND_DIR))
load_dotenv(BACKEND_DIR / ".env")

from app.rag_chain import answer_question  # noqa: E402

SAMPLE_QUESTIONS = [
    "How long do I have to return something I don't want anymore?",
    "returns policy",
    "price match",
    "invoice requirements",
    "What's a good recipe for chocolate cake?",  # deliberately out of scope
]


def main() -> None:
    for question in SAMPLE_QUESTIONS:
        print(f"\n=== {question}")
        result = answer_question(question)
        print(result.answer)
        print("\nSources:")
        for s in result.sources:
            print(f"  - {s.document} §{s.section}")


if __name__ == "__main__":
    main()
