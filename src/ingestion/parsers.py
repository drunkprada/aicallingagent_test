from pathlib import Path

import pdfplumber
from docx import Document


class ParserError(Exception):
    """Raised when a resume file cannot be parsed into text."""


def extract_text_from_pdf(path: Path) -> str:
    try:
        with pdfplumber.open(path) as pdf:
            pages = [page.extract_text() or "" for page in pdf.pages]
    except Exception as exc:  # pdfplumber raises varied underlying errors
        raise ParserError(f"Failed to read PDF {path.name}: {exc}") from exc

    text = "\n".join(pages).strip()
    if not text:
        raise ParserError(f"No extractable text found in {path.name}")
    return text


def extract_text_from_docx(path: Path) -> str:
    try:
        document = Document(path)
    except Exception as exc:
        raise ParserError(f"Failed to read DOCX {path.name}: {exc}") from exc

    text = "\n".join(p.text for p in document.paragraphs).strip()
    if not text:
        raise ParserError(f"No extractable text found in {path.name}")
    return text


def extract_text(path: Path) -> str:
    suffix = path.suffix.lower()
    if suffix == ".pdf":
        return extract_text_from_pdf(path)
    if suffix == ".docx":
        return extract_text_from_docx(path)
    raise ParserError(f"Unsupported file type: {suffix}")
