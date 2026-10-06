from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app import models
from app.auth import hash_pw, verify_pw, make_token
from app.db import get_db
from app.deps import get_current_user, optional_user
from app.schemas import RegisterIn, LoginIn, ProfileIn

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register")
def register(body: RegisterIn, db: Session = Depends(get_db)):
    if body.role not in ("student", "professor"):
        return {"error": "role must be student|professor (admin seeded separately)"}
    if db.query(models.User).filter_by(username=body.username).first():
        return {"error": "username taken"}
    u = models.User(username=body.username, password_hash=hash_pw(body.password), role=body.role)
    db.add(u)
    db.commit()
    db.refresh(u)
    db.add(models.Profile(user_id=u.id))
    db.commit()
    return {"ok": True, "id": u.id}


@router.post("/login")
def login(body: LoginIn, db: Session = Depends(get_db)):
    from fastapi.responses import JSONResponse
    u = db.query(models.User).filter_by(username=body.username).first()
    if not u or not verify_pw(body.password, u.password_hash):
        return {"error": "bad credentials"}
    tok = make_token(u.id, u.role)
    r = JSONResponse({"ok": True, "role": u.role})
    r.set_cookie("token", tok, httponly=True, samesite="lax")
    return r


@router.get("/me")
def me(user=Depends(optional_user)):
    if not user:
        return {"logged_in": False}
    return {"logged_in": True, "username": user.username, "role": user.role}


@router.post("/profile")
def save_profile(body: ProfileIn, db: Session = Depends(get_db), user=Depends(get_current_user)):
    p = db.query(models.Profile).filter_by(user_id=user.id).first()
    if not p:
        p = models.Profile(user_id=user.id)
        db.add(p)
    p.full_name = body.full_name
    if body.api_key:
        p.api_key = body.api_key
    p.api_provider = body.api_provider or "openai_compat"
    p.profile_complete = bool(p.full_name and p.api_key)
    db.commit()
    return {"ok": True, "profile_complete": p.profile_complete, "escalated": bool(p.profile_complete and p.api_key)}
