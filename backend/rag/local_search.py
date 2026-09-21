from dataclasses import dataclass
from pathlib import Path
import re

from backend.security.auth import allowed_access_levels


DOCUMENTS_DIR = Path(__file__).resolve().parents[2] / "documents"


@dataclass
class DocumentChunk:
    document_id: str
    title: str
    source: str
    access_level: str
    content: str
    score: float


def _read_metadata_and_body(path: Path) -> tuple[dict[str, str], str]:
    text = path.read_text(encoding="utf-8")
    if not text.startswith("---"):
        return {}, text

    _, metadata_block, body = text.split("---", 2)
    metadata: dict[str, str] = {}
    for line in metadata_block.strip().splitlines():
        if ":" in line:
            key, value = line.split(":", 1)
            metadata[key.strip()] = value.strip().strip('"')
    return metadata, body.strip()


def _tokenize(text: str) -> set[str]:
    return set(re.findall(r"[a-zA-Z0-9-]+", text.lower()))


def search_documents(query: str, role: str, limit: int = 4) -> list[DocumentChunk]:
    query_terms = _tokenize(query)
    if not query_terms:
        return []

    allowed_levels = allowed_access_levels(role)
    results: list[DocumentChunk] = []

    for path in DOCUMENTS_DIR.rglob("*.md"):
        metadata, body = _read_metadata_and_body(path)
        access_level = metadata.get("access_level", "internal")
        if access_level not in allowed_levels:
            continue

        haystack = f"{metadata.get('document_id', '')} {metadata.get('title', '')} {body}"
        haystack_terms = _tokenize(haystack)
        overlap = query_terms.intersection(haystack_terms)
        phrase_bonus = 2 if query.lower() in haystack.lower() else 0
        score = len(overlap) + phrase_bonus
        if score <= 0:
            continue

        excerpt = body[:900].strip()
        results.append(
            DocumentChunk(
                document_id=metadata.get("document_id", path.stem),
                title=metadata.get("title", path.stem.replace("-", " ").title()),
                source=str(path.relative_to(DOCUMENTS_DIR.parent)),
                access_level=access_level,
                content=excerpt,
                score=float(score),
            )
        )

    return sorted(results, key=lambda item: item.score, reverse=True)[:limit]
