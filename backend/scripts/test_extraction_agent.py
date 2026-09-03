"""
Manual test script for the Document Extraction two-agent chain - run via CLI:
    cd backend
    .venv/Scripts/python.exe scripts/generate_test_invoices.py   # if fixtures/ is empty
    .venv/Scripts/python.exe scripts/test_extraction_agent.py

Runs all four synthetic test invoices through run_extraction() and prints the
extracted fields, the deterministic arithmetic check, and the Validation
Agent's routing decision - covering a clean small invoice (expect
auto_approved), a clean large invoice (expect needs_finance_director_approval),
a missing-PO invoice, and a bad-arithmetic invoice (both expect flagged),
so the routing logic can be verified against real, non-simulated outcomes
before this is wired into the /extract endpoint.
"""

import sys
from pathlib import Path

from dotenv import load_dotenv

sys.stdout.reconfigure(encoding="utf-8")

BACKEND_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BACKEND_DIR))
load_dotenv(BACKEND_DIR / ".env")

from app.extraction_agent import run_extraction  # noqa: E402

FIXTURES_DIR = BACKEND_DIR / "scripts" / "fixtures"

TEST_CASES = [
    ("clean_small.png", "auto_approved"),
    ("clean_large.png", "needs_finance_director_approval"),
    ("missing_po.png", "flagged"),
    ("bad_arithmetic.png", "flagged"),
]


def main() -> None:
    for filename, expected in TEST_CASES:
        path = FIXTURES_DIR / filename
        image_bytes = path.read_bytes()

        print(f"\n{'=' * 80}\nINVOICE: {filename} (expected: {expected})")
        run = run_extraction(image_bytes, mime_type="image/png")

        print(f"\n[Extraction Agent]")
        print(f"  vendor={run.extraction.vendor_name!r}")
        print(f"  invoice_number={run.extraction.invoice_number!r}")
        print(f"  po_number={run.extraction.po_number!r}")
        print(f"  line_items={len(run.extraction.line_items)}")
        print(f"  subtotal={run.extraction.subtotal} vat={run.extraction.vat_amount} "
              f"grand_total={run.extraction.grand_total}")

        print(f"\n[Arithmetic check]")
        print(f"  {run.arithmetic.describe()}")

        print(f"\n[Validation Agent: {run.validation.verdict}]")
        print(f"  citation: {run.validation.citation}")
        if run.validation.issues:
            print(f"  issues: {run.validation.issues}")

        status = "OK" if run.validation.verdict == expected else "CHECK (mismatch vs expected)"
        print(f"\n  [{status}]")


if __name__ == "__main__":
    main()
