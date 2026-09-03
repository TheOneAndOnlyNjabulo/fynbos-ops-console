from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# Loads backend/.env for local dev. In production env vars are injected directly,
# and this file won't exist - load_dotenv() silently no-ops rather than erroring.
load_dotenv(Path(__file__).resolve().parent.parent / ".env")

from app.rag_chain import answer_question  # noqa: E402
from app.support_agent import run_support  # noqa: E402

app = FastAPI(title="Fynbos Ops Console API")

app.add_middleware(
    CORSMiddleware,
    allow_origin_regex=r"http://localhost:\d+",
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type"],
)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


class SupportRequest(BaseModel):
    email_text: str


class SupportDraftResponse(BaseModel):
    category: str
    draft_reply: str


class CheckerVerdictResponse(BaseModel):
    verdict: str
    citation: str
    critique: str
    corrected_category: str


class SupportResponse(BaseModel):
    draft: SupportDraftResponse
    checker: CheckerVerdictResponse
    final: SupportDraftResponse
    citations: list[str]


@app.post("/support")
def support(body: SupportRequest) -> SupportResponse:
    if not body.email_text.strip():
        raise HTTPException(status_code=422, detail="email_text must not be empty")

    try:
        run = run_support(body.email_text)
    except Exception:
        raise HTTPException(status_code=502, detail="Failed to process this email. Please try again.")

    return SupportResponse(
        draft=SupportDraftResponse(**run.draft.__dict__),
        checker=CheckerVerdictResponse(**run.checker.__dict__),
        final=SupportDraftResponse(**run.final.__dict__),
        citations=run.citations,
    )


class ChatRequest(BaseModel):
    question: str


class SourceResponse(BaseModel):
    document: str
    section: str


class ChatResponse(BaseModel):
    answer: str
    sources: list[SourceResponse]


@app.post("/chat")
def chat(body: ChatRequest) -> ChatResponse:
    if not body.question.strip():
        raise HTTPException(status_code=422, detail="question must not be empty")

    try:
        result = answer_question(body.question)
    except Exception:
        raise HTTPException(status_code=502, detail="Failed to generate an answer. Please try again.")

    return ChatResponse(
        answer=result.answer,
        sources=[SourceResponse(document=s.document, section=s.section) for s in result.sources],
    )
