"""
Document Extraction module: an Extraction Agent reads an uploaded supplier
invoice (image or PDF) via Gemini's multimodal input and pulls structured
fields. A Validation Agent independently checks the result - but unlike the
Support Inbox module, this checker does not "correct" anything.

That's a deliberate design difference, not an oversight: a wrong support reply
can be legitimately rewritten by the same agent that drafted it. A wrong
invoice total cannot be "corrected" by an LLM guessing at a number that
reconciles - if the arithmetic on a real invoice genuinely doesn't add up,
silently rewriting it to balance would hide a real problem instead of
surfacing it. So this module's arithmetic check is deterministic Python, not
LLM judgment (models are not reliable calculators), and the Validation Agent's
job is to ROUTE the extraction (auto-approve / needs manager approval / needs
finance director approval / flagged for review) by applying Fynbos's actual
policy thresholds - read from retrieved policy text, not hardcoded in code -
not to rewrite the numbers.
"""

import base64
import os
from dataclasses import dataclass, field
from typing import Literal

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_google_genai import ChatGoogleGenerativeAI
from pydantic import BaseModel, Field

from app.retrieval import RetrievedChunk, retrieve

GENERATION_MODEL = "gemini-3.5-flash-lite"

ARITHMETIC_TOLERANCE = 0.02  # Rand - allows for float rounding, not a real tolerance policy


class LineItem(BaseModel):
    description: str
    quantity: float
    unit_price: float
    line_total: float


class ExtractionOutput(BaseModel):
    vendor_name: str
    invoice_number: str
    invoice_date: str = Field(description="As printed on the invoice, in whatever format it appears")
    po_number: str = Field(default="", description="Empty string if no PO number appears on the invoice")
    line_items: list[LineItem]
    subtotal: float
    vat_amount: float
    grand_total: float


class ValidationOutput(BaseModel):
    verdict: Literal["auto_approved", "needs_manager_approval", "needs_finance_director_approval", "flagged"]
    citation: str = Field(description="The exact 'Document Title §N' section this routing decision is grounded in")
    issues: list[str] = Field(default_factory=list, description="Specific problems found; empty if none")


@dataclass
class ArithmeticCheck:
    line_item_issues: list[str]
    line_items_reconcile: bool
    line_items_sum: float
    subtotal_plus_vat_reconciles: bool
    computed_total: float

    @property
    def has_discrepancy(self) -> bool:
        return bool(self.line_item_issues) or not (self.line_items_reconcile and self.subtotal_plus_vat_reconciles)

    def describe(self) -> str:
        lines = list(self.line_item_issues)
        if not self.line_items_reconcile:
            lines.append(
                f"Line items sum to R{self.line_items_sum:.2f} but the invoice states a subtotal that doesn't "
                f"match."
            )
        if not self.subtotal_plus_vat_reconciles:
            lines.append(
                f"Subtotal + VAT computes to R{self.computed_total:.2f} but the invoice states a different "
                f"grand total."
            )
        return " ".join(lines) if lines else "Arithmetic reconciles."


@dataclass
class ExtractionRun:
    extraction: ExtractionOutput
    arithmetic: ArithmeticCheck
    validation: ValidationOutput
    citations: list[str] = field(default_factory=list)


EXTRACTION_SYSTEM_PROMPT = """You are the Extraction Agent for Fynbos Retail's accounts payable team, a \
fictional South African online retailer. Read the supplier invoice image provided and extract exactly what is \
printed on it - vendor name, invoice number, invoice date, PO number (empty string if none appears), every line \
item (description, quantity, unit price, line total), the subtotal, the VAT amount, and the grand total.

Do not calculate or infer any number that isn't actually printed on the invoice - if a field is genuinely not \
present, use an empty string (or 0 for a missing numeric field), never a guess."""


CHECKER_SYSTEM_PROMPT = """You are the Validation Agent for Fynbos Retail's accounts payable team. You \
independently route an extracted invoice to the correct approval level based ONLY on Fynbos's actual policy \
documents provided as context below - you do not see the Extraction Agent's reasoning, only its output, a \
deterministic arithmetic check result, and the policy context.

Rules:
- If the arithmetic check reports a discrepancy, or the invoice is missing its PO number, verdict is "flagged" \
regardless of amount - list the specific issue(s). These conditions override the amount-based thresholds, per \
the Invoice Approval Thresholds & Escalation Policy.
- Otherwise, route by the grand total against the exact Rand thresholds stated in the policy context: \
"auto_approved", "needs_manager_approval", or "needs_finance_director_approval". Do not use thresholds from \
outside knowledge - use only the figures stated in the provided context.
- citation must be the exact "Document Title §N" section that supports the routing decision.
- issues should be empty if the invoice is clean; otherwise list each specific problem in one short sentence."""

_llm: ChatGoogleGenerativeAI | None = None
_checker_llm: ChatGoogleGenerativeAI | None = None


def _get_extraction_llm() -> ChatGoogleGenerativeAI:
    global _llm
    if _llm is None:
        api_key = os.environ.get("GEMINI_API_KEY")
        if not api_key:
            raise RuntimeError("GEMINI_API_KEY is not set")
        _llm = ChatGoogleGenerativeAI(model=GENERATION_MODEL, google_api_key=api_key)
    return _llm


def _get_checker_llm() -> ChatGoogleGenerativeAI:
    global _checker_llm
    if _checker_llm is None:
        api_key = os.environ.get("GEMINI_API_KEY")
        if not api_key:
            raise RuntimeError("GEMINI_API_KEY is not set")
        _checker_llm = ChatGoogleGenerativeAI(model=GENERATION_MODEL, google_api_key=api_key)
    return _checker_llm


def _check_arithmetic(extraction: ExtractionOutput) -> ArithmeticCheck:
    line_item_issues = []
    for li in extraction.line_items:
        expected_total = li.quantity * li.unit_price
        if abs(expected_total - li.line_total) > ARITHMETIC_TOLERANCE:
            line_item_issues.append(
                f"'{li.description}': {li.quantity} x R{li.unit_price:.2f} = R{expected_total:.2f}, "
                f"but the line states R{li.line_total:.2f}."
            )

    line_items_sum = sum(li.line_total for li in extraction.line_items)
    computed_total = extraction.subtotal + extraction.vat_amount
    return ArithmeticCheck(
        line_item_issues=line_item_issues,
        line_items_reconcile=abs(line_items_sum - extraction.subtotal) <= ARITHMETIC_TOLERANCE,
        line_items_sum=line_items_sum,
        subtotal_plus_vat_reconciles=abs(computed_total - extraction.grand_total) <= ARITHMETIC_TOLERANCE,
        computed_total=computed_total,
    )


def _format_context(chunks: list[RetrievedChunk]) -> str:
    return "\n\n".join(f"[{c.source_document} §{c.section}]\n{c.text}" for c in chunks)


def _dedupe_citations(chunks: list[RetrievedChunk]) -> list[str]:
    seen: set[tuple[str, str]] = set()
    citations: list[str] = []
    for c in chunks:
        key = (c.source_document, c.section)
        if key not in seen:
            seen.add(key)
            citations.append(f"{c.source_document} §{c.section}")
    return citations


def run_extraction(image_bytes: bytes, mime_type: str, top_k: int = 7) -> ExtractionRun:
    llm = _get_extraction_llm()
    b64 = base64.b64encode(image_bytes).decode("ascii")
    messages = [
        SystemMessage(content=EXTRACTION_SYSTEM_PROMPT),
        HumanMessage(
            content=[
                {"type": "text", "text": "Extract this invoice's fields."},
                {"type": "image_url", "image_url": f"data:{mime_type};base64,{b64}"},
            ]
        ),
    ]
    extraction: ExtractionOutput = llm.with_structured_output(ExtractionOutput).invoke(messages)

    arithmetic = _check_arithmetic(extraction)

    query = (
        f"Invoice from {extraction.vendor_name}, PO number: {extraction.po_number or 'MISSING'}, "
        f"grand total R{extraction.grand_total:.2f}. Arithmetic check: {arithmetic.describe()}"
    )
    chunks = retrieve(query, top_k=top_k)
    context = _format_context(chunks)
    citations = _dedupe_citations(chunks)

    checker_llm = _get_checker_llm()
    validation_prompt = [
        SystemMessage(content=CHECKER_SYSTEM_PROMPT),
        HumanMessage(
            content=(
                f"Extracted invoice:\n"
                f"- Vendor: {extraction.vendor_name}\n"
                f"- PO number: {extraction.po_number or '(none)'}\n"
                f"- Grand total: R{extraction.grand_total:.2f}\n"
                f"- Line items: {len(extraction.line_items)}\n\n"
                f"Arithmetic check: {arithmetic.describe()}\n\n"
                f"Policy context:\n{context}"
            )
        ),
    ]
    validation: ValidationOutput = checker_llm.with_structured_output(ValidationOutput).invoke(validation_prompt)

    return ExtractionRun(extraction=extraction, arithmetic=arithmetic, validation=validation, citations=citations)
