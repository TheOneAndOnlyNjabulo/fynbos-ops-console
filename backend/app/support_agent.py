"""
Support Inbox module: a Draft Agent classifies an incoming customer email and
drafts a reply; a Policy Checker Agent independently retrieves relevant policy
context and checks the draft's category AND its specific factual claims
(timelines, eligibility, amounts) against that context before it's accepted.
On rejection, the Draft Agent gets exactly one revision pass.

Named support_agent.py (not agents.py) since this is the first of four modules
in this app - later modules get their own files rather than one growing
agents.py, so each module's agent logic stays independently readable.
"""

import os
from dataclasses import dataclass
from typing import Literal

from langchain_core.prompts import ChatPromptTemplate
from langchain_google_genai import ChatGoogleGenerativeAI
from pydantic import BaseModel, Field

from app.retrieval import RetrievedChunk, retrieve

GENERATION_MODEL = "gemini-3.5-flash-lite"

CATEGORIES = [
    "Order Status",
    "Returns & Refunds",
    "Damaged/Defective Item",
    "Shipping & Delivery",
    "Cancellation",
    "Price Match",
    "Payment & Billing",
    "Warranty",
    "Loyalty & Rewards",
    "Gift Cards & Vouchers",
    "Complaint",
    "General Question",
]


class DraftOutput(BaseModel):
    category: str = Field(description=f"Exactly one of: {', '.join(CATEGORIES)}")
    draft_reply: str = Field(description="A complete reply to send the customer")


class CheckerOutput(BaseModel):
    verdict: Literal["approved", "rejected"]
    citation: str = Field(description="The exact 'Document Title §N' section this verdict is grounded in")
    critique: str = Field(description="Empty string if approved; explanation of the error if rejected")
    corrected_category: str = Field(default="", description="Only set if rejected and the category was wrong")


@dataclass
class SupportDraft:
    category: str
    draft_reply: str


@dataclass
class CheckerVerdict:
    verdict: str
    citation: str
    critique: str
    corrected_category: str


@dataclass
class SupportRun:
    email_text: str
    draft: SupportDraft
    checker: CheckerVerdict
    final: SupportDraft
    citations: list[str]


DRAFT_SYSTEM_PROMPT = f"""You are the Draft Agent for Fynbos Retail's customer support inbox, a fictional South \
African online retailer. Read the customer's email and produce:

- category: exactly one of {", ".join(CATEGORIES)}
- draft_reply: a complete reply following these rules:
  - Acknowledge the specific issue raised.
  - Give a clear next step or resolution, including any concrete timeline or eligibility rule that applies (use \
your best knowledge of typical retail policy - your specific factual claims will be checked against Fynbos's \
actual policy documents before this reply is sent, so state a specific claim rather than being vague).
  - Warm, plain-language tone. Do not over-apologise or admit fault before the facts are confirmed.
  - Do not promise a delivery date that hasn't been confirmed, and do not state a refund has already been \
processed unless the customer says it has.

If the email describes more than one issue, classify by the primary issue being raised."""

_draft_prompt = ChatPromptTemplate.from_messages(
    [
        ("system", DRAFT_SYSTEM_PROMPT),
        ("human", "Customer email:\n{email_text}"),
    ]
)

_revision_prompt = ChatPromptTemplate.from_messages(
    [
        ("system", DRAFT_SYSTEM_PROMPT),
        (
            "human",
            "Customer email:\n{email_text}\n\n"
            "Your first draft was classified as category={category}. Fynbos's Policy Checker rejected it, "
            "citing {citation}:\n{critique}\n\n"
            "Produce a corrected classification and reply.",
        ),
    ]
)

CHECKER_SYSTEM_PROMPT = """You are the Policy Checker Agent for Fynbos Retail's customer support inbox. You \
independently check the Draft Agent's category assignment AND the specific factual claims in its drafted reply \
(timelines, eligibility windows, amounts, thresholds) against the policy context below - you do not see or trust \
the Draft Agent's reasoning, only its output and the original email.

Rules:
- Base your check strictly on the provided context. Do not use outside knowledge of retail norms that isn't \
stated in the context.
- If the category is right AND every specific factual claim in the draft reply matches the context, verdict is \
"approved" - citation should be the section that best supports the reply, critique should be an empty string, \
and leave corrected_category empty.
- If the category is wrong, or the reply makes a specific claim (a number, timeframe, or eligibility rule) that \
contradicts the context, verdict is "rejected" - citation must be the exact "Document Title §N" section that \
shows the error, and critique must explain what's wrong in one or two sentences. Set corrected_category only if \
the category itself was wrong.
- Never reject on a technicality the context doesn't actually support - if the context is genuinely silent on a \
claim, approve."""

_checker_prompt = ChatPromptTemplate.from_messages(
    [
        ("system", CHECKER_SYSTEM_PROMPT),
        (
            "human",
            "Customer email:\n{email_text}\n\nDraft Agent assigned category={category} and drafted this reply:\n"
            "{draft_reply}\n\nPolicy context:\n{context}",
        ),
    ]
)

_draft_llm: ChatGoogleGenerativeAI | None = None
_draft_chain = None
_revision_chain = None
_checker_chain = None


def _get_draft_chain():
    global _draft_llm, _draft_chain
    if _draft_chain is None:
        api_key = os.environ.get("GEMINI_API_KEY")
        if not api_key:
            raise RuntimeError("GEMINI_API_KEY is not set")
        _draft_llm = ChatGoogleGenerativeAI(model=GENERATION_MODEL, google_api_key=api_key)
        _draft_chain = _draft_prompt | _draft_llm.with_structured_output(DraftOutput)
    return _draft_chain


def _get_revision_chain():
    global _revision_chain
    if _revision_chain is None:
        _get_draft_chain()  # ensures _draft_llm is initialized
        _revision_chain = _revision_prompt | _draft_llm.with_structured_output(DraftOutput)
    return _revision_chain


def _get_checker_chain():
    global _checker_chain
    if _checker_chain is None:
        api_key = os.environ.get("GEMINI_API_KEY")
        if not api_key:
            raise RuntimeError("GEMINI_API_KEY is not set")
        llm = ChatGoogleGenerativeAI(model=GENERATION_MODEL, google_api_key=api_key)
        _checker_chain = _checker_prompt | llm.with_structured_output(CheckerOutput)
    return _checker_chain


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


def run_support(email_text: str, top_k: int = 7) -> SupportRun:
    draft_chain = _get_draft_chain()
    draft_out: DraftOutput = draft_chain.invoke({"email_text": email_text})
    draft = SupportDraft(category=draft_out.category, draft_reply=draft_out.draft_reply)

    # The Checker's retrieval query includes the drafted reply itself, not just the raw
    # email - this surfaces the specific policy sections that would confirm or contradict
    # the SPECIFIC claims the reply makes, not just generic sections about the topic.
    query = f"{email_text}\n\nCategory: {draft.category}\nDraft reply: {draft.draft_reply}"
    chunks = retrieve(query, top_k=top_k)
    context = _format_context(chunks)
    citations = _dedupe_citations(chunks)

    checker_chain = _get_checker_chain()
    verdict_out: CheckerOutput = checker_chain.invoke(
        {
            "email_text": email_text,
            "category": draft.category,
            "draft_reply": draft.draft_reply,
            "context": context,
        }
    )
    checker = CheckerVerdict(
        verdict=verdict_out.verdict,
        citation=verdict_out.citation,
        critique=verdict_out.critique,
        corrected_category=verdict_out.corrected_category,
    )

    if verdict_out.verdict == "approved":
        return SupportRun(email_text, draft, checker, draft, citations)

    revision_chain = _get_revision_chain()
    revised_out: DraftOutput = revision_chain.invoke(
        {
            "email_text": email_text,
            "category": draft.category,
            "citation": verdict_out.citation,
            "critique": verdict_out.critique,
        }
    )
    final = SupportDraft(category=revised_out.category, draft_reply=revised_out.draft_reply)
    return SupportRun(email_text, draft, checker, final, citations)
