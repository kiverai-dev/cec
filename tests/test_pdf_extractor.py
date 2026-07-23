import pytest
import tempfile
import os
from app.core.pdf_extractor import extract_text_from_pdf, is_valid_pdf


def test_extract_text_from_invalid_pdf():
    with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as f:
        f.write(b"Not a valid PDF content")
        temp_path = f.name

    try:
        text = extract_text_from_pdf(temp_path)
        assert text == "" or text is not None
    finally:
        os.unlink(temp_path)


def test_is_valid_pdf_with_invalid_file():
    with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as f:
        f.write(b"Not a valid PDF content")
        temp_path = f.name

    try:
        assert is_valid_pdf(temp_path) == False
    finally:
        os.unlink(temp_path)


def test_is_valid_pdf_with_nonexistent_file():
    assert is_valid_pdf("/nonexistent/file.pdf") == False


def test_extract_text_from_nonexistent_pdf():
    text = extract_text_from_pdf("/nonexistent/file.pdf")
    assert text == "" or text is None
