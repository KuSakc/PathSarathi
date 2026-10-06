import json
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app import models
from app.db import get_db
from app.schemas import SyllabusIn
from app.deps import require_professor_or_admin

router = APIRouter(prefix="/syllabus", tags=["syllabus"])


@router.post("/{subject_id}")
def save_syllabus(subject_id: int, body: SyllabusIn, db: Session = Depends(get_db), user=Depends(require_professor_or_admin)):
    row = db.query(models.SyllabusEdition).filter_by(subject_id=subject_id, edition=body.edition).first()
    payload = json.dumps([t.model_dump() for t in body.topics])
    if row:
        row.topics_json = payload
    else:
        row = models.SyllabusEdition(subject_id=subject_id, edition=body.edition, topics_json=payload)
        db.add(row)
    db.commit()
    return {"ok": True}


@router.get("/{subject_id}")
def list_editions(subject_id: int, db: Session = Depends(get_db)):
    rows = db.query(models.SyllabusEdition).filter_by(subject_id=subject_id).all()
    return [{"edition": r.edition, "topics": json.loads(r.topics_json or "[]")} for r in rows]


@router.get("/{subject_id}/gap")
def gap(subject_id: int, old: str, new: str, db: Session = Depends(get_db)):
    """Compare old vs new edition topics -> covered/changed/missing (gap analysis)."""
    def load(ed):
        r = db.query(models.SyllabusEdition).filter_by(subject_id=subject_id, edition=ed).first()
        return json.loads(r.topics_json) if r else []
    o = {t["topic"].lower(): t for t in load(old)}
    n = {t["topic"].lower(): t for t in load(new)}
    out = []
    for k, t in n.items():
        if k not in o:
            out.append({"topic": t["topic"], "status": "missing", "action": "generate"})
        elif o[k] != t:
            out.append({"topic": t["topic"], "status": "changed", "action": "regenerate"})
        else:
            out.append({"topic": t["topic"], "status": "covered", "action": "reuse"})
    return out
