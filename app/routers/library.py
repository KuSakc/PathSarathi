import os
from fastapi import APIRouter, Depends, UploadFile, File, Form
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from app import models
from app.db import get_db
from app.config import settings
from app.deps import get_current_user, can_upload, can_view_chunks
from ai.chunking_agent import extract_text, chunk_text
from ai.rag import ingest_chunks

router = APIRouter(prefix="/library", tags=["library"])


@router.post("/upload")
async def upload(subject_id: int = Form(...), kind: str = Form("notes"), title: str = Form(...),
                 edition: str = Form(""), file: UploadFile = File(...),
                 db: Session = Depends(get_db), user=Depends(get_current_user)):
    if not can_upload(user, subject_id, db):
        return {"error": "professor not assigned to this subject (or student upload forbidden)"}
    raw_dir = os.path.join(settings.DATA_DIR, "raw")
    os.makedirs(raw_dir, exist_ok=True)
    dest = os.path.join(raw_dir, f"{subject_id}_{file.filename}")
    with open(dest, "wb") as f:
        f.write(await file.read())
    r = models.Resource(subject_id=subject_id, kind=kind, title=title, filepath=dest, edition=edition, uploaded_by=user.id)
    db.add(r)
    db.commit()
    # chunk + ingest (Chunking AI, local)
    try:
        text = extract_text(dest)
        chunks = chunk_text(text)
        ingest_chunks([(c, {"subject_id": subject_id, "resource": title}) for c in chunks])
        n = len(chunks)
    except Exception as e:
        n = 0
        print("ingest failed:", e)
    return {"ok": True, "id": r.id, "chunks": n}


@router.get("/")
def list_resources(subject_id: int | None = None, db: Session = Depends(get_db)):
    q = db.query(models.Resource)
    if subject_id:
        q = q.filter_by(subject_id=subject_id)
    return [{"id": r.id, "subject_id": r.subject_id, "kind": r.kind, "title": r.title, "edition": r.edition} for r in q.all()]


@router.get("/download/{rid}")
def download(rid: int, db: Session = Depends(get_db), user=Depends(get_current_user)):
    r = db.query(models.Resource).filter_by(id=rid).first()
    if not r:
        return {"error": "not found"}
    return FileResponse(r.filepath, filename=os.path.basename(r.filepath))


@router.patch("/{rid}")
def edit_resource(rid: int, title: str | None = None, edition: str | None = None, kind: str | None = None,
                  db: Session = Depends(get_db), user=Depends(get_current_user)):
    r = db.query(models.Resource).filter_by(id=rid).first()
    if not r:
        return {"error": "not found"}
    if not can_upload(user, r.subject_id, db):
        return {"error": "not allowed for this subject"}
    if title is not None:
        r.title = title
    if edition is not None:
        r.edition = edition
    if kind is not None:
        r.kind = kind
    db.commit()
    return {"ok": True}


@router.delete("/{rid}")
def delete_resource(rid: int, db: Session = Depends(get_db), user=Depends(get_current_user)):
    r = db.query(models.Resource).filter_by(id=rid).first()
    if not r:
        return {"error": "not found"}
    if not can_upload(user, r.subject_id, db):
        return {"error": "not allowed for this subject"}
    try:
        if r.filepath and os.path.exists(r.filepath):
            os.remove(r.filepath)
    except Exception:
        pass
    db.delete(r)
    db.commit()
    return {"ok": True}


@router.get("/chunks/{subject_id}")
def chunk_preview(subject_id: int, db: Session = Depends(get_db), user=Depends(get_current_user)):
    s = db.query(models.Subject).filter_by(id=subject_id).first()
    if not s:
        return {"error": "subject not found"}
    if not can_view_chunks(user, s):
        return {"error": "chunk access disabled (admin toggle)"}
    from ai.rag import preview
    return {"chunks": preview(subject_id)}
