from dataclasses import dataclass
from pathlib import Path
import re

from backend.config import CHUNK_OVERLAP, CHUNK_SIZE


DOCUMENTS_DIR = Path(__file__).resolve().parents[2] / "documents"


@dataclass(frozen=True)
class SourceDocument:
    document_id: str
    title: str
    department: str
    document_type: str
    access_level: str
    created_date: str
    source: str
    body: str


@dataclass(frozen=True)
class DocumentChunk:
    chunk_id: str
    document_id: str
    title: str
    department: str
    document_type: str
    access_level: str
    source: str
    content: str
    score: float = 0.0

    def metadata(self) -> dict[str, str]:
        return {
            "chunk_id": self.chunk_id,
            "document_id": self.document_id,
            "title": self.title,
            "department": self.department,
            "document_type": self.document_type,
            "access_level": self.access_level,
            "source": self.source,
        }


def read_metadata_and_body(path: Path) -> tuple[dict[str, str], str]:
    text = path.read_text(encoding="utf-8")
    if not text.startswith("---"):
        return {}, text

    parts = text.split("---", 2)
    if len(parts) < 3:
        return {}, text

    _, metadata_block, body = parts
    metadata: dict[str, str] = {}
    for line in metadata_block.strip().splitlines():
        if ":" in line:
            key, value = line.split(":", 1)
            metadata[key.strip()] = value.strip().strip('"')
    return metadata, body.strip()


def load_documents(root: Path = DOCUMENTS_DIR) -> list[SourceDocument]:
    documents: list[SourceDocument] = []
    for path in sorted(root.rglob("*.md")):
        metadata, body = read_metadata_and_body(path)
        relative_source = str(path.relative_to(root.parent)).replace("\\", "/")
        documents.append(
            SourceDocument(
                document_id=metadata.get("document_id", path.stem),
                title=metadata.get("title", path.stem.replace("-", " ").title()),
                department=metadata.get("department", "unknown"),
                document_type=metadata.get("document_type", "document"),
                access_level=metadata.get("access_level", "internal"),
                created_date=metadata.get("created_date", ""),
                source=relative_source,
                body=body,
            )
        )
    return documents


def chunk_text(text: str, chunk_size: int = CHUNK_SIZE, overlap: int = CHUNK_OVERLAP) -> list[str]:
    normalized = re.sub(r"\n{3,}", "\n\n", text.strip())
    if not normalized:
        return []
    if chunk_size <= 0:
        raise ValueError("chunk_size must be greater than zero")
    if overlap < 0:
        raise ValueError("overlap cannot be negative")
    if overlap >= chunk_size:
        overlap = chunk_size - 1
    if len(normalized) <= chunk_size:
        return [normalized]

    chunks: list[str] = []
    start = 0
    while start < len(normalized):
        end = min(start + chunk_size, len(normalized))
        if end < len(normalized):
            paragraph_break = normalized.rfind("\n\n", start, end)
            sentence_break = normalized.rfind(". ", start, end)
            split_at = max(paragraph_break, sentence_break)
            if split_at > start + 200:
                end = split_at + 1

        chunk = normalized[start:end].strip()
        if chunk:
            chunks.append(chunk)

        if end >= len(normalized):
            break
        next_start = max(0, end - overlap)
        if next_start <= start:
            next_start = min(len(normalized), start + 1)
        start = next_start

    return chunks


def load_chunks(root: Path = DOCUMENTS_DIR) -> list[DocumentChunk]:
    chunks: list[DocumentChunk] = []
    for document in load_documents(root):
        for index, content in enumerate(chunk_text(document.body), start=1):
            chunk_id = f"{document.document_id}-chunk-{index:03d}"
            chunks.append(
                DocumentChunk(
                    chunk_id=chunk_id,
                    document_id=document.document_id,
                    title=document.title,
                    department=document.department,
                    document_type=document.document_type,
                    access_level=document.access_level,
                    source=document.source,
                    content=content,
                )
            )
    return chunks
