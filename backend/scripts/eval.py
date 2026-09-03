"""
Evaluation harness: runs every case in eval/eval_set.py through the real
Support, Extraction, and Meeting Notes pipelines, scores each module
separately, and writes a markdown report to eval/eval_results.md (linked from
the README, step 14).

Run manually via CLI:
    cd backend
    .venv/Scripts/python.exe scripts/eval.py

Three modules, three different metrics, on purpose - each module's checker
does a different job (see meeting_agent.py's docstring), so "accuracy" means
something different in each:
  - Support: does the FINAL category (after any Checker-driven revision)
    match the expected category?
  - Extraction: does the extracted vendor match, is PO presence correctly
    detected, and does the Validation Agent's routing decision match the
    expected approval level?
  - Meeting Notes: do all expected action items survive into the final
    (grounded) list, and does the final list stay at or under the expected
    upper bound (catching over-extraction that the Checker should have caught
    but didn't)?
"""

import sys
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

from dotenv import load_dotenv

sys.stdout.reconfigure(encoding="utf-8")

BACKEND_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BACKEND_DIR))
load_dotenv(BACKEND_DIR / ".env")

from app.extraction_agent import run_extraction  # noqa: E402
from app.meeting_agent import run_meeting_notes  # noqa: E402
from app.support_agent import run_support  # noqa: E402
from eval.eval_set import (  # noqa: E402
    EXTRACTION_EVAL_SET,
    MEETING_EVAL_SET,
    SUPPORT_EVAL_SET,
    ExtractionEvalCase,
    MeetingEvalCase,
    SupportEvalCase,
)

RESULTS_PATH = BACKEND_DIR / "eval" / "eval_results.md"
FIXTURES_DIR = BACKEND_DIR / "scripts" / "fixtures"


@dataclass
class SupportResult:
    case: SupportEvalCase
    final_category: str
    auditor_verdict: str

    @property
    def passed(self) -> bool:
        return self.final_category == self.case.expected_category


@dataclass
class ExtractionResult:
    case: ExtractionEvalCase
    vendor: str
    po_present: bool
    verdict: str

    @property
    def vendor_ok(self) -> bool:
        return self.case.expected_vendor_substring.lower() in self.vendor.lower()

    @property
    def po_ok(self) -> bool:
        return self.po_present == self.case.expected_po_present

    @property
    def verdict_ok(self) -> bool:
        return self.verdict == self.case.expected_verdict

    @property
    def passed(self) -> bool:
        return self.vendor_ok and self.po_ok and self.verdict_ok


@dataclass
class MeetingResult:
    case: MeetingEvalCase
    final_tasks: list[str]

    @property
    def all_expected_present(self) -> bool:
        joined = " ".join(t.lower() for t in self.final_tasks)
        return all(s.lower() in joined for s in self.case.expected_item_substrings)

    @property
    def within_bound(self) -> bool:
        return len(self.final_tasks) <= self.case.max_final_items

    @property
    def passed(self) -> bool:
        return self.all_expected_present and self.within_bound


def run_support_eval() -> list[SupportResult]:
    results = []
    for case in SUPPORT_EVAL_SET:
        run = run_support(case.email_text)
        results.append(SupportResult(case, run.final.category, run.checker.verdict))
    return results


def run_extraction_eval() -> list[ExtractionResult]:
    results = []
    for case in EXTRACTION_EVAL_SET:
        image_bytes = (FIXTURES_DIR / case.fixture_filename).read_bytes()
        run = run_extraction(image_bytes, mime_type="image/png")
        results.append(
            ExtractionResult(
                case, run.extraction.vendor_name, bool(run.extraction.po_number), run.validation.verdict
            )
        )
    return results


def run_meeting_eval() -> list[MeetingResult]:
    results = []
    for case in MEETING_EVAL_SET:
        run = run_meeting_notes(case.transcript)
        results.append(MeetingResult(case, [item.task for item in run.final_action_items]))
    return results


def format_report(
    support: list[SupportResult], extraction: list[ExtractionResult], meeting: list[MeetingResult]
) -> str:
    lines = [
        "# Evaluation Results",
        "",
        f"Generated: {datetime.now(timezone.utc).isoformat(timespec='seconds')}",
        "",
        "## Summary",
        "",
    ]

    s_passed = sum(1 for r in support if r.passed)
    lines.append(f"- **Support Inbox**: {s_passed}/{len(support)} correctly classified (final category)")
    e_passed = sum(1 for r in extraction if r.passed)
    lines.append(f"- **Document Extraction**: {e_passed}/{len(extraction)} fully correct (vendor + PO + routing)")
    m_passed = sum(1 for r in meeting if r.passed)
    lines.append(f"- **Meeting Notes**: {m_passed}/{len(meeting)} correct (expected items kept, no over-extraction)")

    lines += ["", "## Support Inbox", "", "| # | Email | Expected | Final | Auditor | Passed |", "|---|---|---|---|---|---|"]
    for i, r in enumerate(support, start=1):
        email_short = r.case.email_text if len(r.case.email_text) <= 50 else r.case.email_text[:47] + "..."
        final_cell = r.final_category if r.passed else f"**{r.final_category}**"
        lines.append(
            f"| {i} | {email_short} | {r.case.expected_category} | {final_cell} | {r.auditor_verdict} | "
            f"{'yes' if r.passed else '**no**'} |"
        )

    lines += [
        "",
        "## Document Extraction",
        "",
        "| # | Fixture | Vendor OK | PO OK | Verdict | Expected | Passed |",
        "|---|---|---|---|---|---|---|",
    ]
    for i, r in enumerate(extraction, start=1):
        lines.append(
            f"| {i} | {r.case.fixture_filename} | {'yes' if r.vendor_ok else '**no**'} | "
            f"{'yes' if r.po_ok else '**no**'} | {r.verdict} | {r.case.expected_verdict} | "
            f"{'yes' if r.passed else '**no**'} |"
        )

    lines += [
        "",
        "## Meeting Notes",
        "",
        "| # | Expected items present | Item count ≤ bound | Final tasks | Passed |",
        "|---|---|---|---|---|",
    ]
    for i, r in enumerate(meeting, start=1):
        tasks_preview = "; ".join(r.final_tasks) if r.final_tasks else "(none)"
        lines.append(
            f"| {i} | {'yes' if r.all_expected_present else '**no**'} | "
            f"{'yes' if r.within_bound else '**no**'} ({len(r.final_tasks)}/{r.case.max_final_items}) | "
            f"{tasks_preview} | {'yes' if r.passed else '**no**'} |"
        )

    return "\n".join(lines) + "\n"


def main() -> None:
    start = time.perf_counter()

    print(f"Running {len(SUPPORT_EVAL_SET)} Support Inbox cases...")
    support = run_support_eval()
    print(f"Running {len(EXTRACTION_EVAL_SET)} Document Extraction cases...")
    extraction = run_extraction_eval()
    print(f"Running {len(MEETING_EVAL_SET)} Meeting Notes cases...")
    meeting = run_meeting_eval()

    elapsed = time.perf_counter() - start
    report = format_report(support, extraction, meeting)
    RESULTS_PATH.write_text(report, encoding="utf-8")

    total = len(support) + len(extraction) + len(meeting)
    passed = sum(r.passed for r in support) + sum(r.passed for r in extraction) + sum(r.passed for r in meeting)
    print(f"\nDone in {elapsed:.0f}s. Report written to {RESULTS_PATH}")
    print(f"Cases passed: {passed}/{total}")


if __name__ == "__main__":
    main()
