"""Chunking AI (local agent): extract -> split -> embed-texts."""
import os

SPLIT = 800


def extract_text(path: str) -> str:
    if path.lower().endswith(".pdf"):
        try:
            from pypdf import PdfReader
            r = PdfReader(path)
            return "\n".join([(p.extract_text() or "") for p in r.pages])
        except Exception:
            pass
        try:
            import fitz  # pymupdf
            d = fitz.open(path)
            return "\n".join([p.get_text() for p in d])
        except Exception as e:
            return f"[extract-failed: {e}]"
    try:
        with open(path, errors="ignore") as f:
            return f.read()[:200000]
    except Exception as e:
        return f"[extract-failed: {e}]"


def chunk_text(text: str, size: int = SPLIT):
    text = (text or "").strip()
    if not text:
        return []
    # paragraph-aware semantic-ish split
    paras, chunks, cur = text.split("\n"), [], ""
    for p in paras:
        if len(cur) + len(p) + 1 > size and cur:
            chunks.append(cur.strip())
            cur = p
        else:
            cur = (cur + "\n" + p).strip()
    if cur.strip():
        chunks.append(cur.strip())
    return chunks


_embed_model = None


def embed_texts(texts):
    """Local free embeddings; falls back to hash vectors if sentence-transformers missing."""
    global _embed_model
    try:
        from sentence_transformers import SentenceTransformer
        from app.config import settings
        if _embed_model is None:
            _embed_model = SentenceTransformer(settings.EMBEDDING_MODEL)
        return _embed_model.encode(texts).tolist()
    except Exception:
        import hashlib
        vecs = []
        for t in texts:
            h = hashlib.sha256(t.encode()).digest()
            vecs.append([b / 255.0 for b in h[:16]])
        return vecs
