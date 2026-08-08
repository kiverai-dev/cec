from typing import Optional
import io
import logging
import fitz
import pytesseract
from PIL import Image

from app.config import OCR_LANG

logger = logging.getLogger(__name__)

OCR_DPI = 300
OCR_CONFIG = f"--dpi {OCR_DPI}"


def extract_text_from_image(image_path: str, lang: Optional[str] = None) -> str:
    """Распознаёт текст на изображении (скриншот, скан). При ошибке возвращает ""."""
    try:
        with Image.open(image_path) as image:
            return pytesseract.image_to_string(image, lang=lang or OCR_LANG, config=OCR_CONFIG)
    except Exception as e:
        logger.error(f"Не удалось распознать текст на изображении {image_path}: {e}")
        return ""


def extract_text_from_image_bytes(image_bytes: bytes, lang: Optional[str] = None) -> str:
    try:
        with Image.open(io.BytesIO(image_bytes)) as image:
            return pytesseract.image_to_string(image, lang=lang or OCR_LANG, config=OCR_CONFIG)
    except Exception as e:
        logger.error(f"Не удалось распознать текст на изображении из байтов: {e}")
        return ""


def ocr_pdf(file_path: str, lang: Optional[str] = None) -> str:
    """OCR-фолбэк для PDF без текстового слоя: рендер страниц в растр 300 DPI → распознавание."""
    try:
        doc = fitz.open(file_path)
    except Exception as e:
        logger.error(f"Не удалось открыть PDF для OCR {file_path}: {e}")
        return ""

    text_parts = []
    try:
        for page in doc:
            pixmap = page.get_pixmap(dpi=OCR_DPI, alpha=False)
            image = Image.frombytes("RGB", (pixmap.width, pixmap.height), pixmap.samples)
            text_parts.append(pytesseract.image_to_string(image, lang=lang or OCR_LANG, config=OCR_CONFIG))
    except Exception as e:
        logger.error(f"Ошибка OCR PDF {file_path}: {e}")
        doc.close()
        return ""

    doc.close()
    return "\n".join(text_parts)
