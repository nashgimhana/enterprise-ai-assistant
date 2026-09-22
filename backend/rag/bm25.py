from collections import Counter
from math import log
import re

from backend.rag.documents import DocumentChunk, load_chunks
from backend.security.auth import allowed_access_levels


def tokenize(text: str) -> list[str]:
    return re.findall(r"[a-zA-Z0-9-]+", text.lower())


class BM25Index:
    def __init__(self, chunks: list[DocumentChunk]) -> None:
        self.chunks = chunks
        self.term_counts = [Counter(tokenize(self._chunk_text(chunk))) for chunk in chunks]
        self.doc_lengths = [sum(counter.values()) for counter in self.term_counts]
        self.average_length = sum(self.doc_lengths) / max(len(self.doc_lengths), 1)
        self.document_frequency: Counter[str] = Counter()
        for counter in self.term_counts:
            self.document_frequency.update(counter.keys())

    def search(self, query: str, role: str, limit: int = 6) -> list[DocumentChunk]:
        query_terms = tokenize(query)
        if not query_terms:
            return []

        allowed_levels = allowed_access_levels(role)
        scored: list[DocumentChunk] = []
        for index, chunk in enumerate(self.chunks):
            if chunk.access_level not in allowed_levels:
                continue

            score = self._score(query_terms, index)
            if score > 0:
                scored.append(self._with_score(chunk, score))

        return sorted(scored, key=lambda item: item.score, reverse=True)[:limit]

    def _score(self, query_terms: list[str], index: int) -> float:
        k1 = 1.5
        b = 0.75
        score = 0.0
        total_docs = len(self.chunks)
        doc_length = self.doc_lengths[index] or 1
        counts = self.term_counts[index]

        for term in query_terms:
            frequency = counts.get(term, 0)
            if frequency == 0:
                continue
            docs_with_term = self.document_frequency.get(term, 0)
            inverse_frequency = log(1 + (total_docs - docs_with_term + 0.5) / (docs_with_term + 0.5))
            denominator = frequency + k1 * (1 - b + b * doc_length / max(self.average_length, 1))
            score += inverse_frequency * ((frequency * (k1 + 1)) / denominator)

        return score

    @staticmethod
    def _chunk_text(chunk: DocumentChunk) -> str:
        return f"{chunk.document_id} {chunk.title} {chunk.department} {chunk.document_type} {chunk.content}"

    @staticmethod
    def _with_score(chunk: DocumentChunk, score: float) -> DocumentChunk:
        return DocumentChunk(
            chunk_id=chunk.chunk_id,
            document_id=chunk.document_id,
            title=chunk.title,
            department=chunk.department,
            document_type=chunk.document_type,
            access_level=chunk.access_level,
            source=chunk.source,
            content=chunk.content,
            score=score,
        )


_BM25_INDEX: BM25Index | None = None


def get_bm25_index() -> BM25Index:
    global _BM25_INDEX
    if _BM25_INDEX is None:
        _BM25_INDEX = BM25Index(load_chunks())
    return _BM25_INDEX


def bm25_search(query: str, role: str, limit: int = 6) -> list[DocumentChunk]:
    return get_bm25_index().search(query, role, limit)
