from typing import Optional
import fitz


def extract_text_from_pdf(file_path: str) -> str:
    doc = fitz.open(file_path)
    text_parts = []
    for page in doc:
        text_parts.append(page.get_text())
    doc.close()
    return "\n".join(text_parts)


def extract_text_from_pdf_bytes(pdf_bytes: bytes) -> str:
    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    text_parts = []
    for page in doc:
        text_parts.append(page.get_text())
    doc.close()
    return "\n".join(text_parts)


def get_pdf_page_count(file_path: str) -> int:
    doc = fitz.open(file_path)
    count = doc.page_count
    doc.close()
    return count


def is_valid_pdf(file_path: str) -> bool:
    try:
        doc = fitz.open(file_path)
        doc.close()
        return True
    except Exception:
        return False
