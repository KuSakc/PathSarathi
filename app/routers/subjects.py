from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app import models
from app.db import get_db
from app.deps import require_admin

router = APIRouter(prefix="/subjects", tags=["subjects"])


def seed_defaults(db: Session):
    # Full Sem-2 list (all subjects show on click). Upserts so old rows heal.
    defaults = [
        ("oop", "Object Oriented Programming", 2, "BSc.CSIT", False),
        ("mathematics-ii", "Mathematics II", 2, "BSc.CSIT", False),
        ("statistics-i", "Statistics I", 2, "BSc.CSIT", False),
        ("discrete-structure", "Discrete Structure", 2, "BSc.CSIT", False),
        ("microprocessor", "Microprocessor", 2, "BSc.CSIT", False),
    ]
    for slug, name, sem, course, elec in defaults:
        row = db.query(models.Subject).filter_by(slug=slug).first()
        if not row:
            db.add(models.Subject(slug=slug, name=name, semester=sem, course=course, is_elective=elec))
        else:
            row.name, row.semester, row.course, row.is_elective = name, sem, course, elec
    db.commit()


@router.get("/")
def list_subjects(db: Session = Depends(get_db)):
    seed_defaults(db)
    out = []
    for s in db.query(models.Subject).all():
        out.append({"id": s.id, "slug": s.slug, "name": s.name, "semester": s.semester,
                    "course": s.course, "is_elective": s.is_elective})
    return out


@router.post("/")
def add_subject(slug: str, name: str, semester: int | None = None, course: str = "CSIT",
                is_elective: bool = False, db: Session = Depends(get_db),
                user=Depends(require_admin)):
    if db.query(models.Subject).filter_by(slug=slug).first():
        return {"error": "slug exists"}
    s = models.Subject(slug=slug, name=name, semester=semester, course=course, is_elective=is_elective)
    db.add(s)
    db.commit()
    return {"ok": True, "id": s.id}
