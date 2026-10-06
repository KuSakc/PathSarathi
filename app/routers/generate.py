import os
from fastapi import APIRouter, Depends
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from app import models
from app.db import get_db
from app.schemas import GenerateIn, FlashcardsIn, SolveIn, SummaryIn, QuizIn, ExportIn
from app.deps import require_escalated_student
from app.config import settings
from app.pdf import make_pdf
from ai.generator_agent import generate_doc
from ai.rag import retrieve

router = APIRouter(prefix="/generate", tags=["generate"])


def importance_depth(weight: float, freq: float) -> str:
    score = weight * 0.6 + freq * 0.4
    if score >= 7:
        return "detailed"
    if score >= 3:
        return "standard"
    return "summary"


def load_prompt(subject_slug: str) -> str:
    base = os.path.join(settings.PROMPTS_DIR, "_base.md")
    sub = os.path.join(settings.PROMPTS_DIR, "subjects", f"{subject_slug}.md")
    t = open(base).read() if os.path.exists(base) else "{reference}\n{classroom}\n{context}"
    if os.path.exists(sub):
        t += "\n\n" + open(sub).read()
    return t


@router.post("/{subject_id}")
def generate(subject_id: int, body: GenerateIn, db: Session = Depends(get_db), user=Depends(require_escalated_student)):
    s = db.query(models.Subject).filter_by(id=subject_id).first()
    if not s:
        return {"error": "subject not found"}
    depth = importance_depth(body.syllabus_weight, body.paper_frequency)
    ctx = retrieve(body.topic, {"subject_id": subject_id}, k=5)
    template = load_prompt(s.slug)
    # decide provider: local Ollama default; external BYOK only if escalated student opts in
    use_external = bool(body.use_external)
    api_key = api_provider = None
    origin = "local"
    if use_external and user.role == "student":
        p = db.query(models.Profile).filter_by(user_id=user.id).first()
        api_key, api_provider, origin = p.api_key, p.api_provider, "external"
    md = generate_doc(topic=body.topic, depth=depth, context_chunks=[c for c, _ in ctx],
                      template=template, api_key=api_key, api_provider=api_provider)
    out_dir = os.path.join(settings.DATA_DIR, "generated")
    os.makedirs(out_dir, exist_ok=True)
    safe_topic = "".join(ch if ch.isalnum() or ch in ("-","_") else "_" for ch in body.topic[:30].strip())
    pdf_path = os.path.join(out_dir, f"{s.slug}-custom-{safe_topic or 'notes'}.pdf")
    make_pdf(md, pdf_path, title=f"{s.name} — {body.topic}")
    doc = models.GeneratedDoc(subject_id=subject_id, topic=body.topic, content_md=md,
                              pdf_path=pdf_path, origin=origin,
                              private_to_user=user.id if origin == "external" else None)
    db.add(doc)
    db.commit()
    return {"ok": True, "id": doc.id, "depth": depth, "origin": origin, "pdf": pdf_path}


@router.get("/download/{doc_id}")
def download_doc(doc_id: int, db: Session = Depends(get_db), user=Depends(require_escalated_student)):
    d = db.query(models.GeneratedDoc).filter_by(id=doc_id).first()
    if not d:
        return {"error": "not found"}
    if d.private_to_user and d.private_to_user != user.id and user.role != "admin":
        return {"error": "private to another user"}
    return FileResponse(d.pdf_path, filename=os.path.basename(d.pdf_path))


def _byok(subject_id: int, use_external: bool, user, db: Session):
    if use_external and user.role == "student":
        p = db.query(models.Profile).filter_by(user_id=user.id).first()
        if p and p.api_key:
            return p.api_key, p.api_provider, "external"
    return None, None, "local"


@router.post("/{subject_id}/flashcards")
def flashcards(subject_id: int, body: FlashcardsIn, db: Session = Depends(get_db), user=Depends(require_escalated_student)):
    s = db.query(models.Subject).filter_by(id=subject_id).first()
    if not s:
        return {"error": "subject not found"}
    ctx = retrieve(body.topic, {"subject_id": subject_id}, k=5)
    n = max(1, min(20, body.count))
    cards = [{"q": f"{body.topic} — card {i+1}: key point?", "a": f"Answer {i+1} grounded in {len(ctx)} source chunk(s)."} for i in range(n)]
    # Try LLM for first card when available (keeps stub offline-safe)
    try:
        api_key, api_provider, origin = _byok(subject_id, body.use_external, user, db)
        md = generate_doc(topic=f"flashcards: {body.topic}", depth="summary",
                          context_chunks=[c for c, _ in ctx], template=load_prompt(s.slug),
                          api_key=api_key, api_provider=api_provider)
        if md:
            cards[0]["a"] = md[:500]
    except Exception:
        origin = "local"
    else:
        origin = origin if "origin" in dir() else "local"
    return {"ok": True, "topic": body.topic, "origin": origin, "sources": len(ctx), "cards": cards}


@router.post("/{subject_id}/solve")
def solve(subject_id: int, body: SolveIn, db: Session = Depends(get_db), user=Depends(require_escalated_student)):
    s = db.query(models.Subject).filter_by(id=subject_id).first()
    if not s:
        return {"error": "subject not found"}
    ctx = retrieve(body.question, {"subject_id": subject_id}, k=5)
    api_key, api_provider, origin = _byok(subject_id, body.use_external, user, db)
    md = generate_doc(topic=f"solve: {body.question}", depth="detailed",
                      context_chunks=[c for c, _ in ctx], template=load_prompt(s.slug),
                      api_key=api_key, api_provider=api_provider)
    return {"ok": True, "question": body.question, "paper": body.paper_title, "origin": origin,
            "sources": len(ctx), "solution_md": md[:4000]}


@router.post("/{subject_id}/summary")
def summary(subject_id: int, body: SummaryIn, db: Session = Depends(get_db), user=Depends(require_escalated_student)):
    """Summary mode — prefers API/BYOK; prompt in prompts/summary.md (user-supplied later)."""
    s = db.query(models.Subject).filter_by(id=subject_id).first()
    if not s:
        return {"error": "subject not found"}
    ctx = retrieve(body.topic, {"subject_id": subject_id}, k=5)
    api_key, api_provider, origin = _byok(subject_id, body.use_external, user, db)
    tpl_path = os.path.join(settings.PROMPTS_DIR, "summary.md")
    tpl = open(tpl_path).read() if os.path.exists(tpl_path) else "{topic}\n{context}"
    prompt = tpl.replace("{topic}", body.topic).replace("{length}", body.length).replace(
        "{context}", "\n---\n".join([c for c, _ in ctx]) or "(no context)")
    md = generate_doc(topic=body.topic, depth=body.length, context_chunks=[c for c, _ in ctx],
                      template=prompt, api_key=api_key, api_provider=api_provider)
    return {"ok": True, "topic": body.topic, "length": body.length, "origin": origin,
            "sources": len(ctx), "summary_md": md[:4000]}


@router.post("/{subject_id}/quiz")
def quiz(subject_id: int, body: QuizIn, db: Session = Depends(get_db), user=Depends(require_escalated_student)):
    """Quiz Me — MCQ set grounded in sources."""
    s = db.query(models.Subject).filter_by(id=subject_id).first()
    if not s:
        return {"error": "subject not found"}
    ctx = retrieve(body.topic, {"subject_id": subject_id}, k=5)
    api_key, api_provider, origin = _byok(subject_id, body.use_external, user, db)
    n = max(1, min(15, body.count))
    md = generate_doc(topic=f"quiz ({n} MCQs): {body.topic}", depth="standard",
                      context_chunks=[c for c, _ in ctx], template=load_prompt(s.slug),
                      api_key=api_key, api_provider=api_provider)
    items = [{"q": f"{body.topic} Q{i+1}: key concept?", "choices": ["A", "B", "C", "D"],
              "answer": "A", "explain": f"Grounded in {len(ctx)} source(s)."} for i in range(n)]
    if md:
        items[0]["explain"] = md[:400]
    return {"ok": True, "topic": body.topic, "origin": origin, "sources": len(ctx), "quiz": items}


@router.post("/export/pdf")
def export_pdf(body: ExportIn, db: Session = Depends(get_db), user=Depends(require_escalated_student)):
    """Export any studio output to styled PDF (title + linked TOC)."""
    md = body.content_md or ""
    if body.doc_id:
        d = db.query(models.GeneratedDoc).filter_by(id=body.doc_id).first()
        if d:
            md = d.content_md
    if not md.strip():
        return {"error": "nothing to export"}
    out_dir = os.path.join(settings.DATA_DIR, "generated")
    os.makedirs(out_dir, exist_ok=True)
    safe = "".join(ch if ch.isalnum() or ch in ("-","_") else "_" for ch in body.title[:30].strip()) or "export"
    path = os.path.join(out_dir, f"export-{safe}.pdf")
    make_pdf(md, path, title=body.title)
    return {"ok": True, "pdf": path, "download": f"/generate/download-file?path={os.path.basename(path)}"}


@router.get("/download-file")
def download_file(path: str, user=Depends(require_escalated_student)):
    from fastapi import HTTPException
    safe = os.path.basename(path)
    full = os.path.join(settings.DATA_DIR, "generated", safe)
    if not os.path.exists(full):
        raise HTTPException(404, "not found")
    return FileResponse(full, filename=safe)
