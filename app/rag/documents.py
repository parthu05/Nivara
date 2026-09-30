from __future__ import annotations

from pathlib import Path

from pypdf import PdfReader

from app.config import settings


def _chunk_text(text: str, size: int = 900, overlap: int = 150) -> list[str]:
    cleaned = " ".join(text.split())
    if not cleaned:
        return []
    chunks: list[str] = []
    start = 0
    while start < len(cleaned):
        end = min(start + size, len(cleaned))
        chunk = cleaned[start:end].strip()
        if chunk:
            chunks.append(chunk)
        if end == len(cleaned):
            break
        start = max(0, end - overlap)
    return chunks


def _read_pdf(path: Path) -> str:
    reader = PdfReader(str(path))
    pages = []
    for page in reader.pages:
        pages.append(page.extract_text() or "")
    return "\n".join(pages)


def load_knowledge_documents() -> list[dict[str, str]]:
    root = Path(settings.knowledge_base_path)
    documents: list[dict[str, str]] = []
    for path in root.rglob("*"):
        if not path.is_file():
            continue
        suffix = path.suffix.lower()
        if suffix not in {".md", ".txt", ".pdf"}:
            continue
        if suffix == ".pdf":
            text = _read_pdf(path)
        else:
            text = path.read_text(encoding="utf-8", errors="ignore")
        topic = path.parent.name
        for i, chunk in enumerate(_chunk_text(text)):
            documents.append(
                {
                    "id": f"{path.relative_to(root).as_posix()}::{i}",
                    "text": chunk,
                    "source": str(path.relative_to(root)),
                    "topic": topic,
                }
            )
    return documents
