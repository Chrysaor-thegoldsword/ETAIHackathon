from __future__ import annotations

import io
import re
from typing import Any

from fastapi import UploadFile

from .financial_utils import parse_annual_amount

try:
    from pypdf import PdfReader
except Exception:  # pragma: no cover
    PdfReader = None


def _extract_pdf_text(content: bytes) -> str:
    if not PdfReader:
        return ""
    try:
        reader = PdfReader(io.BytesIO(content))
        pages = []
        for page in reader.pages[:3]:
            pages.append(page.extract_text() or "")
        return "\n".join(pages)
    except Exception:
        return ""


def _extract_amount_after(label: str, text: str) -> float:
    match = re.search(label + r".{0,40}?(\d[\d,\.]*)", text, re.IGNORECASE | re.DOTALL)
    return parse_annual_amount(match.group(1)) if match else 0.0


async def parse_document(file: UploadFile) -> dict[str, Any]:
    content = await file.read()
    text = _extract_pdf_text(content) if (file.filename or "").lower().endswith(".pdf") else ""
    lower_name = (file.filename or "document").lower()

    document_type = "financial document"
    if "itr" in lower_name:
        document_type = "ITR return"
    elif "form16" in lower_name or "form 16" in lower_name:
        document_type = "Form 16"
    elif "cas" in lower_name or "statement" in lower_name:
        document_type = "investment statement"

    extracted_income = _extract_amount_after(r"(gross total income|total income|income from salary)", text)
    extracted_tax_saving = _extract_amount_after(r"(80c|deduction under chapter vi-a|total deductions)", text)

    summary = f"Imported {document_type} from {file.filename or 'uploaded file'}."
    if text:
        summary += " Text extraction succeeded on the first few pages."
    else:
        summary += " Text extraction was limited, so the file is stored mainly as supporting evidence."

    payload: dict[str, Any] = {
        "uploaded_documents": [
            {
                "name": file.filename or "uploaded-file",
                "type": document_type,
                "summary": summary,
            }
        ],
        "document_summary": summary,
    }

    if extracted_income:
        payload["monthly_income"] = round(extracted_income / 12.0, 2)
    if extracted_tax_saving:
        payload["tax_saving_investments"] = round(extracted_tax_saving, 2)

    return payload
