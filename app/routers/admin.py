from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app import models
from app.db import get_db
from app.deps import require_admin

router = APIRouter(prefix="/admin", tags=["admin"])


@router.post("/chunk-access/{subject_id}")
def toggle_chunk(subject_id: int, allow: bool, db: Session = Depends(get_db), user=Depends(require_admin)):
    s = db.query(models.Subject).filter_by(id=subject_id).first()
    if not s:
        return {"error": "not found"}
    s.professor_chunk_access = allow
    db.commit()
    return {"ok": True, "professor_chunk_access": s.professor_chunk_access}


@router.post("/assign/{user_id}/{subject_id}")
def assign(user_id: int, subject_id: int, db: Session = Depends(get_db), user=Depends(require_admin)):
    if not db.query(models.ProfessorSubject).filter_by(user_id=user_id, subject_id=subject_id).first():
        db.add(models.ProfessorSubject(user_id=user_id, subject_id=subject_id))
        db.commit()
    return {"ok": True}


@router.get("/users")
def users(db: Session = Depends(get_db), user=Depends(require_admin)):
    return [{"id": u.id, "username": u.username, "role": u.role} for u in db.query(models.User).all()]
