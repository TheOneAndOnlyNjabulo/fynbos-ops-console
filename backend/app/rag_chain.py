"""
Knowledge Assistant chain: retrieval -> citation-aware prompt template -> Gemini
generation. Bundles two guardrails from the start (both learned the hard way on
Marula, not discovered here from scratch):

1. A calibrated similarity threshold that skips the LLM entirely when nothing
   retrieved is relevant enough - cheap, and an independent backstop against
   generating from irrelevant context.
2. An explicit system-prompt rule that a bare topic/keyword query ("returns
   policy", "price match") is a valid request to summarize, not a reason to
   refuse - Marula's chatbot shipped without this and had to be patched after
   real bare-keyword queries were incorrectly rejected in production, even
   though they scored well above the threshold and were reaching the model.
"""

import os
from dataclasses import dataclass

from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_google_genai import ChatGoogleGenerativeAI

from app.retrieval import RetrievedChunk, retrieve

GENERATION_MODEL = "gemini-3.5-flash-lite"

# Calibrated against this corpus specifically - do not assume a threshold from
# Baobab (0.62) or Marula (0.65) transfers; different documents produce different
# score distributions. Here: out-of-domain questions topped out at 0.624,
# in-domain questions (including short keyword-style ones) scored 0.717+. 0.67
# sits in that gap.
CONFIDENCE_THRESHOLD = 0.67

NOT_FOUND_ANSWER = (
    "I couldn't find anything in Fynbos Retail's policy documents that answers this "
    "question. Try rephrasing, or ask about returns, shipping, damaged items, price "
    "matching, payments, warranties, loyalty points, gift cards, supplier invoicing, "
    "or general FAQs."
)

# Sentinel the model must emit verbatim (and only this) when the retrieved context
# doesn't answer the question. The similarity threshold above catches queries where
# nothing relevant was retrieved at all; it does NOT catch queries using in-domain
# vocabulary that retrieve plausible-looking chunks but don't actually answer the
# question.
INSUFFICIENT_CONTEXT_SENTINEL = "INSUFFICIENT_CONTEXT"

SYSTEM_PROMPT = f"""You are the Fynbos Retail Assistant, a support chatbot for Fynbos Retail, a fictional South \
African online retailer, used internally by staff to answer policy questions. Answer the user's question using \
ONLY the context below, drawn from Fynbos's internal policy documents.

Rules:
- Base your answer strictly on the provided context. Do not use outside knowledge, and do not assume anything \
the context does not state.
- The question may use different wording than the context. If the context clearly covers the situation asked \
about, even via a specific example rather than the exact phrase used in the question, answer from it - do not \
withhold an answer just because the wording doesn't match verbatim.
- The input may be a bare topic or keyword rather than a full question (e.g. "returns policy", "price match", \
"invoice requirements") - treat that as a request to summarize the relevant policy from the context, the same \
as if the user had asked "tell me about" that topic, rather than treating it as too vague to answer. Only use \
the insufficient-context response below when the context itself doesn't cover the topic, not because the input \
wasn't phrased as a question.
- When you state a specific fact (a timeframe, threshold, or requirement), name the document it comes from, \
e.g. "(See the Returns & Refunds Policy document.)"
- If the context does not contain enough information to answer the question, respond with EXACTLY this and \
nothing else: {INSUFFICIENT_CONTEXT_SENTINEL}
- Do not guess or fabricate an answer.
- Be concise and direct."""

_prompt = ChatPromptTemplate.from_messages(
    [
        ("system", SYSTEM_PROMPT),
        ("human", "Context:\n{context}\n\nQuestion: {question}"),
    ]
)

_llm: ChatGoogleGenerativeAI | None = None
_chain = None


@dataclass
class Source:
    document: str
    section: str


@dataclass
class RagResult:
    answer: str
    sources: list[Source]
    chunk_ids: list[str]


def _format_context(chunks: list[RetrievedChunk]) -> str:
    return "\n\n".join(f"[Document: {c.source_document}, Section {c.section}]\n{c.text}" for c in chunks)


def _dedupe_sources(chunks: list[RetrievedChunk]) -> list[Source]:
    seen: set[tuple[str, str]] = set()
    sources: list[Source] = []
    for c in chunks:
        key = (c.source_document, c.section)
        if key not in seen:
            seen.add(key)
            sources.append(Source(document=c.source_document, section=c.section))
    return sources


def _get_chain():
    global _llm, _chain
    if _chain is None:
        api_key = os.environ.get("GEMINI_API_KEY")
        if not api_key:
            raise RuntimeError("GEMINI_API_KEY is not set")
        _llm = ChatGoogleGenerativeAI(model=GENERATION_MODEL, google_api_key=api_key)
        _chain = _prompt | _llm | StrOutputParser()
    return _chain


def answer_question(question: str, top_k: int = 7) -> RagResult:
    chunks = retrieve(question, top_k=top_k)

    if not chunks or chunks[0].score < CONFIDENCE_THRESHOLD:
        # Skip the LLM entirely - nothing retrieved is relevant enough to answer
        # from, and no sources are returned since none were actually usable.
        return RagResult(answer=NOT_FOUND_ANSWER, sources=[], chunk_ids=[])

    chain = _get_chain()
    answer = chain.invoke({"context": _format_context(chunks), "question": question})

    if answer.strip() == INSUFFICIENT_CONTEXT_SENTINEL:
        # Threshold gate passed (retrieval scored high enough), but the model itself
        # couldn't answer from what was retrieved - don't attach citations to a non-answer.
        return RagResult(answer=NOT_FOUND_ANSWER, sources=[], chunk_ids=[])

    return RagResult(
        answer=answer,
        sources=_dedupe_sources(chunks),
        chunk_ids=[c.id for c in chunks],
    )
