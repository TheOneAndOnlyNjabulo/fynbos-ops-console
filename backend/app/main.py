from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# Loads backend/.env for local dev. In production env vars are injected directly,
# and this file won't exist - load_dotenv() silently no-ops rather than erroring.
load_dotenv(Path(__file__).resolve().parent.parent / ".env")

from app.db import log_agent_run  # noqa: E402
from app.extraction_agent import run_extraction  # noqa: E402
from app.rag_chain import answer_question  # noqa: E402
from app.support_agent import run_support  # noqa: E402

ALLOWED_UPLOAD_TYPES = {"image/png", "image/jpeg", "image/webp"}
MAX_UPLOAD_BYTES = 10 * 1024 * 1024  # 10MB - generous for a single-page invoice scan

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
        log_agent_run(
            module="support",
            input_payload={"email_text": body.email_text},
            draft=None,
            verdict=None,
            critique=None,
            final=None,
            citations=[],
        )
        raise HTTPException(status_code=502, detail="Failed to process this email. Please try again.")

    log_agent_run(
        module="support",
        input_payload={"email_text": run.email_text},
        draft={"category": run.draft.category, "draft_reply": run.draft.draft_reply},
        verdict=run.checker.verdict,
        critique=run.checker.critique,
        final={"category": run.final.category, "draft_reply": run.final.draft_reply},
        citations=run.citations,
    )

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
        log_agent_run(
            module="chat",
            input_payload={"question": body.question},
            draft=None,
            verdict=None,
            critique=None,
            final=None,
            citations=[],
        )
        raise HTTPException(status_code=502, detail="Failed to generate an answer. Please try again.")

    citations = [f"{s.document} §{s.section}" for s in result.sources]
    log_agent_run(
        module="chat",
        input_payload={"question": body.question},
        draft=None,
        verdict=None,
        critique=None,
        final={"answer": result.answer},
        citations=citations,
    )

    return ChatResponse(
        answer=result.answer,
        sources=[SourceResponse(document=s.document, section=s.section) for s in result.sources],
    )


class LineItemResponse(BaseModel):
    description: str
    quantity: float
    unit_price: float
    line_total: float


class ExtractionResponse(BaseModel):
    vendor_name: str
    invoice_number: str
    invoice_date: str
    po_number: str
    line_items: list[LineItemResponse]
    subtotal: float
    vat_amount: float
    grand_total: float


class ArithmeticResponse(BaseModel):
    has_discrepancy: bool
    description: str


class ValidationResponse(BaseModel):
    verdict: str
    citation: str
    issues: list[str]


class ExtractResponse(BaseModel):
    extraction: ExtractionResponse
    arithmetic: ArithmeticResponse
    validation: ValidationResponse
    citations: list[str]


@app.post("/extract")
async def extract(file: UploadFile = File(...)) -> ExtractResponse:
    if file.content_type not in ALLOWED_UPLOAD_TYPES:
        raise HTTPException(
            status_code=422,
            detail=f"Unsupported file type '{file.content_type}'. Upload a PNG, JPEG, or WEBP image.",
        )

    image_bytes = await file.read()
    if len(image_bytes) > MAX_UPLOAD_BYTES:
        raise HTTPException(status_code=422, detail="File is too large (max 10MB).")
    if not image_bytes:
        raise HTTPException(status_code=422, detail="Uploaded file is empty.")

    try:
        run = run_extraction(image_bytes, mime_type=file.content_type)
    except Exception:
        log_agent_run(
            module="extraction",
            input_payload={"filename": file.filename},
            draft=None,
            verdict=None,
            critique=None,
            final=None,
            citations=[],
        )
        raise HTTPException(status_code=502, detail="Failed to process this invoice. Please try again.")

    extraction_payload = {
        "vendor_name": run.extraction.vendor_name,
        "invoice_number": run.extraction.invoice_number,
        "invoice_date": run.extraction.invoice_date,
        "po_number": run.extraction.po_number,
        "line_items": [li.model_dump() for li in run.extraction.line_items],
        "subtotal": run.extraction.subtotal,
        "vat_amount": run.extraction.vat_amount,
        "grand_total": run.extraction.grand_total,
    }
    log_agent_run(
        module="extraction",
        input_payload={"filename": file.filename},
        draft=extraction_payload,
        verdict=run.validation.verdict,
        critique="; ".join(run.validation.issues) if run.validation.issues else None,
        final=extraction_payload,
        citations=run.citations,
    )

    return ExtractResponse(
        extraction=ExtractionResponse(**extraction_payload),
        arithmetic=ArithmeticResponse(
            has_discrepancy=run.arithmetic.has_discrepancy,
            description=run.arithmetic.describe(),
        ),
        validation=ValidationResponse(
            verdict=run.validation.verdict,
            citation=run.validation.citation,
            issues=run.validation.issues,
        ),
        citations=run.citations,
    )
