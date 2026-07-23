import os
from typing import Tuple, List
from app.config import ALLOWED_EXTENSIONS, MAX_FILE_SIZE_BYTES


def validate_file_extension(filename: str) -> Tuple[bool, str]:
    ext = os.path.splitext(filename)[1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        return False, f"Недопустимое расширение файла. Разрешены: {', '.join(ALLOWED_EXTENSIONS)}"
    return True, ""


def validate_file_size(file_size: int) -> Tuple[bool, str]:
    if file_size > MAX_FILE_SIZE_BYTES:
        return False, f"Размер файла превышает максимально допустимый ({MAX_FILE_SIZE_BYTES // (1024 * 1024)} MB)"
    return True, ""


def validate_uploaded_file(uploaded_file) -> Tuple[bool, str]:
    is_valid_ext, ext_msg = validate_file_extension(uploaded_file.name)
    if not is_valid_ext:
        return False, ext_msg

    uploaded_file.seek(0, 2)
    file_size = uploaded_file.tell()
    uploaded_file.seek(0)

    is_valid_size, size_msg = validate_file_size(file_size)
    if not is_valid_size:
        return False, size_msg

    return True, ""


def validate_archive_contents(filenames: List[str]) -> Tuple[bool, str]:
    for filename in filenames:
        ext = os.path.splitext(filename)[1].lower()
        if ext != ".pdf":
            return False, f"В архиве найден недопустимый файл: {filename}. Разрешены только PDF файлы."
    return True, ""


def get_file_extension(filename: str) -> str:
    return os.path.splitext(filename)[1].lower()
