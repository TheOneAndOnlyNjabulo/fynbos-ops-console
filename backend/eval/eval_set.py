"""
Evaluation set covering the three modules with a checker agent (Support Inbox,
Document Extraction, Meeting Notes) - the Knowledge Assistant chatbot isn't
included here since its dual-guardrail behavior was already directly verified
with a dedicated test set in step 7 (bare-keyword queries, out-of-domain
control), not because it's untested.

Each case's expected value was decided by reading the actual docs/ text (or,
for extraction, by reading the actual synthetic invoice generated in
scripts/generate_test_invoices.py), not recalled from memory - a failure here
means the pipeline is wrong, not the eval data.
"""

from dataclasses import dataclass


@dataclass
class SupportEvalCase:
    email_text: str
    expected_category: str


SUPPORT_EVAL_SET: list[SupportEvalCase] = [
    SupportEvalCase("I want to return these shoes, they just don't fit right.", "Returns & Refunds"),
    SupportEvalCase("My blender arrived with a cracked lid, can you help?", "Damaged/Defective Item"),
    SupportEvalCase(
        "I found this exact TV cheaper on another site, can you match the price?", "Price Match"
    ),
    SupportEvalCase("My card was charged twice for the same order, please help.", "Payment & Billing"),
    SupportEvalCase("How many loyalty points do I have and when do they expire?", "Loyalty & Rewards"),
    SupportEvalCase("I have a question about how your gift cards work.", "Gift Cards & Vouchers"),
    SupportEvalCase("The TV I bought three months ago just stopped turning on.", "Warranty"),
    SupportEvalCase("Can I cancel my order? I haven't received a dispatch email yet.", "Cancellation"),
]


@dataclass
class ExtractionEvalCase:
    fixture_filename: str
    expected_vendor_substring: str
    expected_po_present: bool
    expected_verdict: str


# Ground truth taken directly from scripts/generate_test_invoices.py's known inputs -
# same fixtures used in scripts/test_extraction_agent.py, reused here rather than
# duplicated with different values.
EXTRACTION_EVAL_SET: list[ExtractionEvalCase] = [
    ExtractionEvalCase("clean_small.png", "Karoo Packaging", True, "auto_approved"),
    ExtractionEvalCase("clean_large.png", "Highveld Electronics", True, "needs_finance_director_approval"),
    ExtractionEvalCase("missing_po.png", "Cape Coastal", False, "flagged"),
    ExtractionEvalCase("bad_arithmetic.png", "Durban Freight", True, "flagged"),
]


@dataclass
class MeetingEvalCase:
    transcript: str
    expected_item_substrings: list[str]  # each must appear in some final (grounded) action item's task text
    max_final_items: int  # upper bound - catches over-extraction (e.g. the floated idea slipping through)


MEETING_EVAL_SET: list[MeetingEvalCase] = [
    MeetingEvalCase(
        transcript=(
            "Priya: Sipho, can you pull together the Q3 returns numbers by Friday? "
            "Sipho: Sure, I'll have that ready by Friday. "
            "Priya: Great. Someone also mentioned we should maybe look into switching packaging suppliers "
            "at some point, but let's not commit to anything on that today."
        ),
        expected_item_substrings=["Q3"],
        max_final_items=1,
    ),
    MeetingEvalCase(
        transcript=(
            "Lindiwe: The checkout conversion rate has been dipping. "
            "Marco: It might be worth revisiting guest checkout at some point, just an idea though. "
            "Lindiwe: Separately, Zanele, can you confirm whether the gift card display bug is a caching issue? "
            "Zanele: Yes, I'll confirm that by tomorrow."
        ),
        expected_item_substrings=["gift card"],
        max_final_items=1,
    ),
    MeetingEvalCase(
        transcript=(
            "Thabo: The packaging supplier has been late twice this month. "
            "Nomvula: I'll follow up with them today and get an explanation. "
            "Thabo: Thanks. Also, can someone double check the Silver and Gold loyalty thresholds are still "
            "correct in the system? There's been a complaint. "
            "Priya: I can take that, no specific deadline though."
        ),
        expected_item_substrings=["supplier", "loyalty"],
        max_final_items=2,
    ),
]
