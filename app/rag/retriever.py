from __future__ import annotations

from functools import lru_cache

import chromadb
from chromadb.api.types import Documents, EmbeddingFunction, Embeddings

from app.config import settings
from app.llm.provider import llm
from app.rag.documents import load_knowledge_documents


class ProviderEmbeddingFunction(EmbeddingFunction):
    def __call__(self, input: Documents) -> Embeddings:
        if not input:
            return []
        return llm.embed(list(input))


@lru_cache(maxsize=1)
def _collection():
    client = chromadb.PersistentClient(path=settings.chroma_path)
    return client.get_or_create_collection(
        name="nivara_knowledge",
        embedding_function=ProviderEmbeddingFunction(),
        metadata={"hnsw:space": "cosine"},
    )


def ingest_knowledge_base(force: bool = False) -> int:
    collection = _collection()
    docs = load_knowledge_documents()
    if not docs:
        return 0
    existing_ids = set(collection.get(include=[]).get("ids") or [])
    if force and existing_ids:
        collection.delete(ids=list(existing_ids))
        existing_ids.clear()
    docs_to_upsert = [doc for doc in docs if doc["id"] not in existing_ids]
    batch = 16
    for i in range(0, len(docs_to_upsert), batch):
        part = docs_to_upsert[i : i + batch]
        collection.upsert(
            ids=[d["id"] for d in part],
            documents=[d["text"] for d in part],
            metadatas=[{"source": d["source"], "topic": d["topic"]} for d in part],
        )
    return collection.count()


def retrieve(query: str, k: int = 4) -> list[dict[str, str]]:
    collection = _collection()
    if collection.count() == 0:
        return []
    result = collection.query(query_texts=[query], n_results=min(k, collection.count()))
    docs = result.get("documents") or [[]]
    metas = result.get("metadatas") or [[]]
    hits: list[dict[str, str]] = []
    for text, meta in zip(docs[0], metas[0]):
        hits.append(
            {
                "text": text,
                "source": str((meta or {}).get("source", "")),
                "topic": str((meta or {}).get("topic", "")),
            }
        )
    return hits


def format_context(query: str, k: int = 4) -> str:
    hits = retrieve(query, k=k)
    if not hits:
        return ""
    blocks = []
    for hit in hits:
        blocks.append(f"[{hit['topic']} / {hit['source']}]\n{hit['text']}")
    return "\n\n".join(blocks)
