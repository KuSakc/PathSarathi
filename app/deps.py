from fastapi import Depends, HTTPException, Request
from sqlalchemy.orm import Session
from app.auth import parse_token
from app.db import get_db
from app import models


def get_current_user(request: Request, db: Session = Depends(get_db)):
    token = request.cookies.get("token") or (request.headers.get("Authorization", "").replace("Bearer ", "") or None)
    if not token:
        raise HTTPException(401, "login required")
    try:
        data = parse_token(token)
    except Exception:
        raise HTTPException(401, "invalid token")
    user = db.query(models.User).filter_by(id=int(data["sub"])).first()
    if not user:
        raise HTTPException(401, "user not found")
    return user


def optional_user(request: Request, db: Session = Depends(get_db)):
    """Anonymous-safe: returns User or None (public pages, view-only)."""
    try:
        token = request.cookies.get("token") or (request.headers.get("Authorization", "").replace("Bearer ", "") or None)
        if not token:
            return None
        data = parse_token(token)
        return db.query(models.User).filter_by(id=int(data["sub"])).first()
    except Exception:
        return None


def require_admin(user=Depends(get_current_user)):
    if user.role != "admin":
        raise HTTPException(403, "admin only")
    return user


def require_professor_or_admin(user=Depends(get_current_user)):
    if user.role not in ("admin", "professor"):
        raise HTTPException(403, "professor/admin only")
    return user


def can_upload(user, subject_id: int, db: Session) -> bool:
    if user.role == "admin":
        return True
    if user.role != "professor":
        return False
    return db.query(models.ProfessorSubject).filter_by(user_id=user.id, subject_id=subject_id).first() is not None


def require_escalated_student(user=Depends(get_current_user), db: Session = Depends(get_db)):
    """Students need profile_complete + api_key OR professor/admin to generate."""
    if user.role in ("admin", "professor"):
        return user
    prof = db.query(models.Profile).filter_by(user_id=user.id).first()
    if not prof or not prof.profile_complete or not prof.api_key:
        raise HTTPException(403, "complete profile + save API key to generate")
    return user


def can_view_chunks(user, subject: models.Subject) -> bool:
    if user.role == "admin":
        return True
    if user.role == "professor":
        return bool(subject.professor_chunk_access)
    return False
