import os
import zipfile
from typing import List, Tuple
from io import BytesIO

try:
    import rarfile
    RAR_AVAILABLE = True
except ImportError:
    RAR_AVAILABLE = False


def extract_archive(archive_path: str, extract_to: str) -> Tuple[bool, List[str], str]:
    extracted_files = []
    ext = os.path.splitext(archive_path)[1].lower()

    try:
        if ext == ".zip":
            with zipfile.ZipFile(archive_path, 'r') as zf:
                for member in zf.namelist():
                    if member.endswith('/'):
                        continue
                    zf.extract(member, extract_to)
                    extracted_files.append(os.path.join(extract_to, member))
            return True, extracted_files, ""

        elif ext == ".rar":
            if not RAR_AVAILABLE:
                return False, [], "RAR архивы не поддерживаются (библиотека rarfile не установлена)"
            with rarfile.RarFile(archive_path, 'r') as rf:
                for member in rf.namelist():
                    if member.endswith('/'):
                        continue
                    rf.extract(member, extract_to)
                    extracted_files.append(os.path.join(extract_to, member))
            return True, extracted_files, ""

        else:
            return False, [], f"Неподдерживаемый формат архива: {ext}"

    except Exception as e:
        return False, [], f"Ошибка при распаковке архива: {str(e)}"


def get_archive_filenames(archive_path: str) -> List[str]:
    filenames = []
    ext = os.path.splitext(archive_path)[1].lower()

    try:
        if ext == ".zip":
            with zipfile.ZipFile(archive_path, 'r') as zf:
                filenames = [m for m in zf.namelist() if not m.endswith('/')]
        elif ext == ".rar" and RAR_AVAILABLE:
            with rarfile.RarFile(archive_path, 'r') as rf:
                filenames = [m for m in rf.namelist() if not m.endswith('/')]
    except Exception:
        pass

    return filenames


def is_archive(filename: str) -> bool:
    ext = os.path.splitext(filename)[1].lower()
    return ext in [".zip", ".rar"]
