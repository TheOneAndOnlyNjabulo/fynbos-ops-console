"""
Meeting Notes module: an Extraction Agent reads a meeting transcript and
produces a summary plus a list of action items. A Grounding Checker Agent
independently verifies EACH action item against the actual transcript text.

A third distinct checker shape in this app, and deliberately so - not because
variety is a goal in itself, but because each module's correction strategy has
to fit what's actually safe to do with the checker's finding:
  - Support Inbox: the Checker's finding can be legitimately fixed by having
    the same agent redraft (a wrong claim in a reply can just be rewritten
    correctly) - so it revises and re-verifies (see support_agent.py).
  - Document Extraction: the Checker's finding must NEVER be "fixed" by
    rewriting a number - so it only routes/flags, never corrects.
  - Meeting Notes (here): an ungrounded action item can't be "corrected" into
    a grounded one - if nobody actually said it, no rewrite makes it true. The
    only safe move is to drop it. So the check here is per-item, and the
    "correction" is a deterministic filter (keep only grounded items), not
    another LLM pass that could itself hallucinate a fix.
"""

import os
from dataclasses import dataclass, field

from langchain_core.prompts import ChatPromptTemplate
from langchain_google_genai import ChatGoogleGenerativeAI
from pydantic import BaseModel, Field

from app.retrieval import RetrievedChunk, retrieve

GENERATION_MODEL = "gemini-3.5-flash-lite"


class ActionItem(BaseModel):
    task: str
    owner: str = Field(default="", description="Empty string if no owner was stated")
    due_date: str = Field(default="", description="Empty string if no due date was stated")


class ExtractionOutput(BaseModel):
    summary: str = Field(description="A brief summary of what was discussed, 2-4 sentences")
    action_items: list[ActionItem]


class ItemGroundingResult(BaseModel):
    task: str = Field(description="Echo the exact task text this result refers to")
    grounded: bool
    supporting_quote: str = Field(default="", description="The transcript text that supports it, if grounded")
    reason: str = Field(default="", description="Why it's not grounded, if it isn't")


class GroundingCheckOutput(BaseModel):
    results: list[ItemGroundingResult] = Field(
        description="Exactly one result per action item given, in the same order"
    )


@dataclass
class MeetingNotesRun:
    summary: str
    all_action_items: list[ActionItem]
    grounding_results: list[ItemGroundingResult]
    final_action_items: list[ActionItem]
    citations: list[str] = field(default_factory=list)

    @property
    def grounded_count(self) -> int:
        return sum(1 for r in self.grounding_results if r.grounded)

    @property
    def total_count(self) -> int:
        return len(self.all_action_items)


EXTRACTION_SYSTEM_PROMPT = """You are the Extraction Agent for Fynbos Retail's meeting notes tool, a fictional \
South African online retailer. Read the meeting transcript and produce:

- summary: a brief 2-4 sentence summary of what was discussed.
- action_items: a list of specific, assignable tasks someone actually agreed to do. An action item is NOT a \
general topic that was discussed, a decision with no follow-up task, or an idea someone floated that nobody \
committed to. If an owner or due date wasn't explicitly stated for an item, leave that field as an empty string \
rather than guessing."""

_extraction_prompt = ChatPromptTemplate.from_messages(
    [
        ("system", EXTRACTION_SYSTEM_PROMPT),
        ("human", "Transcript:\n{transcript}"),
    ]
)

GROUNDING_SYSTEM_PROMPT = """You are the Grounding Checker Agent for Fynbos Retail's meeting notes tool. You \
independently verify each action item the Extraction Agent produced against the actual transcript text - you do \
not trust the Extraction Agent's judgment, only the transcript itself.

For each action item, determine whether it is genuinely grounded: traceable to something actually said in the \
transcript, not inferred, assumed, or extrapolated from context. If it is grounded, quote the specific transcript \
text that supports it. If it is not grounded, explain briefly why - for example, it was floated as an idea but \
nobody committed to it, or no such statement appears in the transcript at all.

Return exactly one result per action item given, in the same order they were given, echoing the exact task text \
in the "task" field so results can be matched back to items."""

_grounding_prompt = ChatPromptTemplate.from_messages(
    [
        ("system", GROUNDING_SYSTEM_PROMPT),
        (
            "human",
            "Transcript:\n{transcript}\n\nAction items to verify:\n{items}",
        ),
    ]
)

_extraction_llm: ChatGoogleGenerativeAI | None = None
_extraction_chain = None
_grounding_chain = None


def _get_extraction_chain():
    global _extraction_llm, _extraction_chain
    if _extraction_chain is None:
        api_key = os.environ.get("GEMINI_API_KEY")
        if not api_key:
            raise RuntimeError("GEMINI_API_KEY is not set")
        _extraction_llm = ChatGoogleGenerativeAI(model=GENERATION_MODEL, google_api_key=api_key)
        _extraction_chain = _extraction_prompt | _extraction_llm.with_structured_output(ExtractionOutput)
    return _extraction_chain


def _get_grounding_chain():
    global _grounding_chain
    if _grounding_chain is None:
        api_key = os.environ.get("GEMINI_API_KEY")
        if not api_key:
            raise RuntimeError("GEMINI_API_KEY is not set")
        llm = ChatGoogleGenerativeAI(model=GENERATION_MODEL, google_api_key=api_key)
        _grounding_chain = _grounding_prompt | llm.with_structured_output(GroundingCheckOutput)
    return _grounding_chain


def _align_results(items: list[ActionItem], results: list[ItemGroundingResult]) -> list[ItemGroundingResult]:
    """Pad or truncate the checker's results to exactly one per item.

    The model is asked for exactly one result per action item, but structured
    output isn't guaranteed to honor that count. A naive zip() would silently
    drop any item past the shorter list - in this module specifically, that
    means an item skips the grounding check entirely and disappears without
    ever being flagged as ungrounded, which defeats the module's whole
    purpose. Any unmatched item is instead treated as not grounded, with an
    explicit reason, so it's visibly rejected rather than silently missing.
    """
    aligned = list(results[: len(items)])
    for item in items[len(aligned) :]:
        aligned.append(
            ItemGroundingResult(
                task=item.task,
                grounded=False,
                reason="Grounding Checker did not return a result for this item; treated as not grounded rather than silently dropped.",
            )
        )
    return aligned


def _format_items(items: list[ActionItem]) -> str:
    lines = []
    for i, item in enumerate(items, start=1):
        owner = item.owner or "(no owner stated)"
        due = item.due_date or "(no due date stated)"
        lines.append(f"{i}. {item.task} - owner: {owner}, due: {due}")
    return "\n".join(lines)


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


def run_meeting_notes(transcript: str, top_k: int = 3) -> MeetingNotesRun:
    extraction_chain = _get_extraction_chain()
    extraction: ExtractionOutput = extraction_chain.invoke({"transcript": transcript})

    # Retrieval here grounds the *standard itself* (Meeting Notes & Action Item Standards),
    # not the action items - included as citations so the audit trail shows which policy
    # defines what "grounded" means for this module, same transparency habit as the other
    # two modules even though the actual per-item check is against the transcript, not
    # Pinecone content.
    chunks = retrieve("what counts as a grounded action item in meeting notes", top_k=top_k)
    citations = _dedupe_citations(chunks)

    if not extraction.action_items:
        return MeetingNotesRun(
            summary=extraction.summary,
            all_action_items=[],
            grounding_results=[],
            final_action_items=[],
            citations=citations,
        )

    grounding_chain = _get_grounding_chain()
    grounding_out: GroundingCheckOutput = grounding_chain.invoke(
        {"transcript": transcript, "items": _format_items(extraction.action_items)}
    )

    # Match results back to items by position, not by re-parsing the echoed task text -
    # the model was asked to preserve order, and position is a more robust join than
    # string-matching a paraphrase-prone "task" echo.
    results = _align_results(extraction.action_items, grounding_out.results)
    final_items = [item for item, result in zip(extraction.action_items, results) if result.grounded]

    return MeetingNotesRun(
        summary=extraction.summary,
        all_action_items=extraction.action_items,
        grounding_results=results,
        final_action_items=final_items,
        citations=citations,
    )
