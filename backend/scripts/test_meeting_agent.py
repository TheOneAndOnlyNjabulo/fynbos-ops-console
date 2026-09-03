"""
Manual test script for the Meeting Notes two-agent chain - run via CLI:
    cd backend
    .venv/Scripts/python.exe scripts/test_meeting_agent.py

Runs a sample transcript through run_meeting_notes() and prints the summary,
every extracted action item with its grounding verdict, and the final
(filtered) list. The transcript is deliberately written with a mix of clearly
grounded items, one item with a genuinely missing owner/due date, and one idea
that's floated but nobody commits to - the last one exists specifically to see
whether the Extraction Agent over-eagerly lists it as an action item, and
whether the Grounding Checker Agent then correctly catches and drops it. This
is checked for real, not assumed, before it's wired into the /meeting-notes
endpoint.
"""

import sys
from pathlib import Path

from dotenv import load_dotenv

sys.stdout.reconfigure(encoding="utf-8")

BACKEND_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BACKEND_DIR))
load_dotenv(BACKEND_DIR / ".env")

from app.meeting_agent import run_meeting_notes  # noqa: E402

TRANSCRIPT = """
Priya: Okay, let's get into it. First up - the returns dashboard. Sipho, can you pull together the Q3 returns
numbers by Friday so we can review them at next week's ops meeting?
Sipho: Sure, I'll have that ready by Friday.
Priya: Great. Next, the warehouse team flagged that the packaging supplier has been late twice this month.
Thabo, can you follow up with Karoo Packaging and get an explanation?
Thabo: Yeah, I'll email them today.
Priya: Thanks. Someone also mentioned we should maybe look into switching to a different packaging supplier
entirely at some point, but let's not commit to anything on that today, it's just something to keep in mind.
Priya: Last thing - the loyalty program tier thresholds. We need someone to double check the Silver and Gold
spend thresholds are still being applied correctly in the system, there's been a customer complaint. Nomvula,
would you mind taking a look?
Nomvula: Sure, I can check that.
Priya: No specific deadline on that one, just whenever you get a chance. Okay, I think that's everything for
today.
""".strip()


def main() -> None:
    run = run_meeting_notes(TRANSCRIPT)

    print(f"[Summary]\n{run.summary}\n")

    print(f"[All extracted action items ({run.total_count})]")
    for item, result in zip(run.all_action_items, run.grounding_results):
        status = "GROUNDED" if result.grounded else "NOT GROUNDED"
        print(f"  - [{status}] {item.task!r} (owner={item.owner!r}, due={item.due_date!r})")
        if result.grounded:
            print(f"      quote: {result.supporting_quote!r}")
        else:
            print(f"      reason: {result.reason!r}")

    print(f"\n[Final action items ({run.grounded_count}/{run.total_count} verified)]")
    for item in run.final_action_items:
        print(f"  - {item.task!r} (owner={item.owner!r}, due={item.due_date!r})")

    print(f"\n[Citations] {run.citations}")


if __name__ == "__main__":
    main()
