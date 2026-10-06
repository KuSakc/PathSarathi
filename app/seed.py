"""Boot seed: subjects + demo accounts (dev only — change passwords before hosting)."""
from app import models
from app.auth import hash_pw
from app.routers import subjects as subjects_router

# (username, password, role)
SEED_USERS = [
    ("User", "Pass", "student"),
    ("Professor", "Password", "professor"),
    ("Admin", "admin", "admin"),
]


def seed_all(db):
    subjects_router.seed_defaults(db)
    for username, password, role in SEED_USERS:
        u = db.query(models.User).filter_by(username=username).first()
        if not u:
            u = models.User(username=username, password_hash=hash_pw(password), role=role)
            db.add(u)
            db.commit()
            db.refresh(u)
        if not db.query(models.Profile).filter_by(user_id=u.id).first():
            db.add(models.Profile(user_id=u.id))
            db.commit()
    # Professor teaches all subjects (so Manage + upload work everywhere)
    prof = db.query(models.User).filter_by(username="Professor").first()
    if prof:
        for s in db.query(models.Subject).all():
            if not db.query(models.ProfessorSubject).filter_by(user_id=prof.id, subject_id=s.id).first():
                db.add(models.ProfessorSubject(user_id=prof.id, subject_id=s.id))
        db.commit()
