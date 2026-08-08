from app.utils.validators import is_image_file, validate_archive_contents
from app.core.ocr import extract_text_from_image, ocr_pdf


def test_is_image_file():
    assert is_image_file("scan.JPG") is True
    assert is_image_file("photo.png") is True
    assert is_image_file("doc.tiff") is True
    assert is_image_file("doc.pdf") is False
    assert is_image_file("archive.zip") is False


def test_validate_archive_contents_mixed_allowed():
    ok, _ = validate_archive_contents(["a.pdf", "b.png", "folder/c.jpg"])
    assert ok is True


def test_validate_archive_contents_rejects_other():
    ok, msg = validate_archive_contents(["a.pdf", "evil.exe"])
    assert ok is False
    assert "evil.exe" in msg


def test_extract_text_from_image_invalid_file(tmp_path):
    bad = tmp_path / "bad.png"
    bad.write_bytes(b"not an image")
    assert extract_text_from_image(str(bad)) == ""


def test_extract_text_from_image_nonexistent():
    assert extract_text_from_image("/nonexistent/file.png") == ""


def test_ocr_pdf_invalid_file(tmp_path):
    bad = tmp_path / "bad.pdf"
    bad.write_bytes(b"not a pdf")
    assert ocr_pdf(str(bad)) == ""
