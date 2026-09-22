from itertools import islice
from typing import TypeVar

from backend.rag.documents import load_chunks
from backend.rag.embeddings import get_embedding_client
from backend.rag.pinecone_store import PineconeDocumentStore, ensure_pinecone_index


T = TypeVar("T")


def batched(items: list[T], size: int) -> list[list[T]]:
    batches: list[list[T]] = []
    iterator = iter(items)
    while batch := list(islice(iterator, size)):
        batches.append(batch)
    return batches


def ingest(batch_size: int = 32) -> int:
    chunks = load_chunks()
    if not chunks:
        return 0

    ensure_pinecone_index()
    embeddings = get_embedding_client()
    store = PineconeDocumentStore()
    total = 0

    for batch in batched(chunks, batch_size):
        vectors = embeddings.embed_texts([chunk.content for chunk in batch])
        total += store.upsert_chunks(batch, vectors)

    return total


if __name__ == "__main__":
    indexed = ingest()
    print(f"Indexed {indexed} document chunks into Pinecone.")
