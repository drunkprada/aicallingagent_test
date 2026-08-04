import hashlib
import shutil
from pathlib import Path
from typing import Iterator

from src.config import FAILED_DIR, INCOMING_RESUMES_DIR, PROCESSED_DIR, SUPPORTED_RESUME_EXTENSIONS


def hash_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            digest.update(chunk)
    return digest.hexdigest()


def scan_incoming() -> Iterator[Path]:
    if not INCOMING_RESUMES_DIR.exists():
        return
    for path in sorted(INCOMING_RESUMES_DIR.iterdir()):
        if path.is_file() and path.suffix.lower() in SUPPORTED_RESUME_EXTENSIONS:
            yield path


def move_to_processed(path: Path) -> None:
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    destination = PROCESSED_DIR / path.name
    destination = _unique_destination(destination)
    shutil.move(str(path), str(destination))


def move_to_failed(path: Path) -> None:
    FAILED_DIR.mkdir(parents=True, exist_ok=True)
    destination = FAILED_DIR / path.name
    destination = _unique_destination(destination)
    shutil.move(str(path), str(destination))


def _unique_destination(destination: Path) -> Path:
    if not destination.exists():
        return destination
    stem, suffix = destination.stem, destination.suffix
    counter = 1
    while True:
        candidate = destination.with_name(f"{stem}_{counter}{suffix}")
        if not candidate.exists():
            return candidate
        counter += 1
