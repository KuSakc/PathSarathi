"""RAG over Chroma (local free) with JSON fallback if chroma missing."""
import os, json
from app.config import settings
from ai.chunking_agent import embed_texts

_client = None
_mem: list[tuple[str, dict]] = []
META = os.path.join(settings.CHROMA_DIR, "fallback_store.json")


def _client_or_none():
    global _client
    if _client is not None:
        return _client
    try:
        import chromadb
        os.makedirs(settings.CHROMA_DIR, exist_ok=True)
        _client = chromadb.PersistentClient(path=settings.CHROMA_DIR)
        return _client
    except Exception:
        return None


def ingest_chunks(items: list[tuple[str, dict]]):
    c = _client_or_none()
    if c is None:
        _mem.extend(items)
        os.makedirs(settings.CHROMA_DIR, exist_ok=True)
        with open(META, "w") as f:
            json.dump([{"text": t, "meta": m} for t, m in _mem[-500:]], f)
        return len(items)
    col = c.get_or_create_collection("garibi")
    vecs = embed_texts([t for t, _ in items])
    base = col.count()
    col.add(ids=[f"c{base+i}" for i in range(len(items))],
            documents=[t for t, _ in items],
            metadatas=[m for _, m in items], embeddings=vecs)
    return len(items)


def retrieve(query: str, where: dict | None = None, k: int = 5):
    c = _client_or_none()
    if c is None:
        q = query.lower()
        scored = [(t, m) for t, m in _mem if any(w in t.lower() for w in q.split()[:6])]
        return [(t, m) for t, m in scored[:k]]
    col = c.get_or_create_collection("garibi")
    if col.count() == 0:
        return []
    vecs = embed_texts([query])
    res = col.query(query_embeddings=vecs, n_results=min(k, col.count()),
                    where=where or None)
    docs = (res.get("documents") or [[]])[0]
    metas = (res.get("metadatas") or [[]])[0]
    return list(zip(docs, metas))


def preview(subject_id: int, k: int = 5):
    c = _client_or_none()
    if c is None:
        return [t[:300] for t, m in _mem if m.get("subject_id") == subject_id][:k]
    col = c.get_or_create_collection("garibi")
    if col.count() == 0:
        return []
    res = col.get(where={"subject_id": subject_id}, limit=k)
    return [(d[:300]) for d in (res.get("documents") or [])]
