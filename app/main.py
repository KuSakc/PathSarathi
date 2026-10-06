from fastapi import FastAPI, Depends, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from app.config import settings
from app.db import Base, get_engine, get_db, init_session
from app import models
from app.deps import get_current_user, optional_user, can_upload
from app.routers import auth, subjects, library, syllabus, generate, admin
from app.seed import seed_all

app = FastAPI(title=f"{settings.SITE_NAME} E-Library")
app.include_router(auth.router)
app.include_router(subjects.router)
app.include_router(library.router)
app.include_router(syllabus.router)
app.include_router(generate.router)
app.include_router(admin.router)

try:
    app.mount("/static", StaticFiles(directory="static"), name="static")
except Exception:
    pass
templates = Jinja2Templates(directory="templates")

Base.metadata.create_all(bind=get_engine())

# Boot seed: subjects + demo accounts (idempotent)
try:
    _sdb = init_session()()
    seed_all(_sdb)
    _sdb.close()
except Exception as e:
    print("seed skipped:", e)

FACULTIES = [f.strip() for f in settings.FACULTIES.split(",") if f.strip()]
DESCRIPTIONS = {
    "BSc.CSIT": "CSIT is about coding and research. A study for great minds.",
    "BIT": "Business + IT applications.", "BBA": "Business administration.",
    "LAW": "Legal studies.", "BITM": "IT management.",
}


def brand(ctx: dict) -> dict:
    ctx.update({"site_name": settings.SITE_NAME, "site_tagline": settings.SITE_TAGLINE,
                "site_subtitle": settings.SITE_SUBTITLE})
    return ctx


def sem_label(sem: str) -> str:
    m = {"1": "First", "2": "Second", "3": "Third", "4": "Fourth",
         "5": "Fifth", "6": "Sixth", "7": "Seventh", "8": "Eighth"}
    return m.get(sem, sem)


@app.get("/", response_class=HTMLResponse)
def index(request: Request, db: Session = Depends(get_db)):
    subjects.seed_defaults(db)
    return templates.TemplateResponse(request, "index.html", brand(
        {"request": request, "faculties": FACULTIES, "descriptions": DESCRIPTIONS}))


@app.get("/f/{faculty}", response_class=HTMLResponse)
def faculty_page(faculty: str, request: Request):
    return templates.TemplateResponse(request, "semester.html", brand({"request": request, "faculty": faculty}))


@app.get("/f/{faculty}/sem/{sem}", response_class=HTMLResponse)
def semester_page(faculty: str, sem: str, request: Request, db: Session = Depends(get_db)):
    subjects.seed_defaults(db)
    if sem == "elective":  # legacy link: show faculty electives as subjects
        subs = db.query(models.Subject).filter_by(course=faculty, is_elective=True).all()
    else:
        try:
            n = int(sem)
        except ValueError:
            return HTMLResponse("unknown semester", status_code=404)
        subs = db.query(models.Subject).filter_by(course=faculty, semester=n).all()
        if not subs and faculty == "BSc.CSIT":  # v1 seed fallback for demo faculty
            subs = db.query(models.Subject).filter_by(semester=n).all()
    return templates.TemplateResponse(request, "subjects.html", brand(
        {"request": request, "faculty": faculty, "sem_label": sem_label(sem), "subjects": subs}))


KIND_GROUPS = [("Syllabus", ["syllabus", "microsyllabus"]), ("Notes", ["notes"]),
               ("Old Questions", ["paper"]), ("Old Question Solutions", ["solution"]),
               ("Books", ["book_raw"]), ("Additional Material", ["extra"]), ("Generated", ["generated"])]


NOTICES = [
    {"id": 1, "tag": "Result", "title": "BSc.CSIT 2nd Semester Result Published",
     "date": "2081-09-12", "body": "The 2nd semester board results are published. Check your symbol number on the results page and contact the exam section for retotaling within 15 days."},
    {"id": 2, "tag": "Routine", "title": "2nd Semester Board Exam Routine",
     "date": "2081-08-28", "body": "Board exams start 2nd week of Ashwin, 7 AM shift. Admit cards available at respective campuses from Bhadra 30."},
    {"id": 3, "tag": "Holiday", "title": "Campus Closed on Thursday",
     "date": "2081-08-20", "body": "All campuses remain closed this Thursday on account of a public holiday. Library stays open 10 AM – 2 PM."},
    {"id": 4, "tag": "Practical", "title": "Practical Exam Schedule: Microprocessor Lab",
     "date": "2081-08-15", "body": "Microprocessor practicals run in two shifts (A: roll 1–30, B: roll 31+). Bring lab file, admit card and college ID."},
]


DEMO_TEACHER = {  # slug -> sir name for ICT-style demo filenames (for show until real PDFs)
    "microprocessor": "karki", "discrete-structure": "subedi", "oop": "sharma",
    "mathematics-ii": "thapa", "statistics-i": "adhikari",
}
DEMO_PAPER_YEARS = [2076, 2075, 2074, 2073, 2072, 2071, 2070, 2069, 2068, 2067]


class Demo:
    def __init__(self, title, edition=""):
        self.id = None
        self.title = title
        self.edition = edition
        self.demo = True


@app.get("/subject/{slug}", response_class=HTMLResponse)
def subject_page(slug: str, request: Request, db: Session = Depends(get_db)):
    s = db.query(models.Subject).filter_by(slug=slug).first()
    if not s:
        return HTMLResponse("subject not found", status_code=404)
    res = db.query(models.Resource).filter_by(subject_id=s.id).all()
    gen = db.query(models.GeneratedDoc).filter_by(subject_id=s.id).all()
    by_kind: dict[str, list] = {}
    for r in res:
        by_kind.setdefault(r.kind, []).append(r)
    for g in gen:  # real custom generations carry -custom- in filename
        by_kind.setdefault("generated", []).append(
            type("O", (), {"id": g.id, "title": f"{s.slug}-custom-{g.topic[:30]} ({g.origin})",
                           "edition": "", "demo": False})())
    groups = {label: [x for k in kinds for x in by_kind.get(k, [])] for label, kinds in KIND_GROUPS}
    # Placeholder entries read like the real lists until actual files are uploaded
    sir = DEMO_TEACHER.get(s.slug, "sir")
    if not groups["Notes"]:
        groups["Notes"] = [Demo(f"{s.slug}-{sir}-sir-notes.pdf", "2081")]
    if not groups["Old Questions"]:
        groups["Old Questions"] = [Demo(f"{s.slug}-old-question-{y}.pdf", str(y)) for y in DEMO_PAPER_YEARS]
    if not groups["Old Question Solutions"]:
        groups["Old Question Solutions"] = [Demo(f"{s.slug}-model-question-solution.pdf", "2080")]
    if not groups["Syllabus"]:
        groups["Syllabus"] = [Demo(f"{s.slug}-syllabus-2079.pdf", "2079"),
                              Demo(f"{s.slug}-syllabus-2074.pdf", "2074"),
                              Demo(f"{s.slug}-microsyllabus-model.pdf", "2079")]
    if not groups["Additional Material"]:
        groups["Additional Material"] = [Demo(f"{s.slug}-formula-sheet.pdf", "2081"),
                                         Demo(f"{s.slug}-lab-manual.pdf", "2081")]
    if not groups["Generated"]:
        groups["Generated"] = [Demo(f"{s.slug}-for-all-notes.pdf", "2081")]
    others = db.query(models.Subject).filter(models.Subject.id != s.id).limit(8).all()
    me = optional_user(request, db)
    can_manage = bool(me and (me.role == "admin" or can_upload(me, s.id, db)))
    return templates.TemplateResponse(request, "subject_detail.html", brand(
        {"request": request, "subject": s, "groups": groups, "others": others,
         "logged_in": bool(me), "can_manage": can_manage}))


@app.get("/search", response_class=HTMLResponse)
def search(q: str = "", request: Request = None, db: Session = Depends(get_db)):
    subjects.seed_defaults(db)
    ql = (q or "").lower()
    subs = db.query(models.Subject).all()
    if ql:
        subs = [s for s in subs if ql in s.name.lower() or ql in s.slug.lower() or ql in (s.course or "").lower()]
    res = []
    if ql:
        for r in db.query(models.Resource).all():
            if ql in (r.title or "").lower() or ql in (r.kind or "").lower():
                res.append(r)
    res = res[:30]
    return templates.TemplateResponse(request, "search.html", brand(
        {"request": request, "q": q, "subjects": subs[:30], "resources": res}))


@app.get("/notices", response_class=HTMLResponse)
def notices(request: Request):
    return templates.TemplateResponse(request, "notices.html", brand(
        {"request": request, "notices": NOTICES}))


@app.get("/notices/{nid}", response_class=HTMLResponse)
def notice_detail(nid: int, request: Request):
    n = next((x for x in NOTICES if x["id"] == nid), None)
    if not n:
        return HTMLResponse("notice not found", status_code=404)
    return templates.TemplateResponse(request, "notice_detail.html", brand(
        {"request": request, "notice": n, "notices": NOTICES}))


@app.get("/generation", response_class=HTMLResponse)
def generation(request: Request, subject: str = "", db: Session = Depends(get_db)):
    me = optional_user(request, db)
    if not me:
        return RedirectResponse("/login?next=/generation", status_code=307)
    subjects.seed_defaults(db)
    subs = db.query(models.Subject).all()
    return templates.TemplateResponse(request, "generation.html", brand(
        {"request": request, "subjects": subs, "active_slug": subject}))


@app.get("/studio", include_in_schema=False)
def studio_redirect():
    return RedirectResponse("/generation", status_code=307)


@app.get("/login", response_class=HTMLResponse)
def login_page(request: Request):
    return templates.TemplateResponse(request, "login.html", brand({"request": request, "admin_mode": False}))


@app.get("/register", response_class=HTMLResponse)
def register_page(request: Request):
    return templates.TemplateResponse(request, "register.html", brand({"request": request}))


@app.get("/profile", response_class=HTMLResponse)
def profile_page(request: Request):
    return templates.TemplateResponse(request, "profile.html", brand({"request": request}))


@app.get("/admin/login", response_class=HTMLResponse)
def admin_login(request: Request):
    return templates.TemplateResponse(request, "login.html", brand({"request": request, "admin_mode": True}))


@app.get("/admin", response_class=HTMLResponse)
def admin_page(request: Request, user=Depends(get_current_user)):
    if user.role != "admin":
        return HTMLResponse("admin only — use /admin/login", status_code=403)
    return templates.TemplateResponse(request, "admin.html", brand({"request": request}))


@app.get("/manage/{slug}", response_class=HTMLResponse)
def manage_page(slug: str, request: Request, db: Session = Depends(get_db), user=Depends(get_current_user)):
    s = db.query(models.Subject).filter_by(slug=slug).first()
    if not s:
        return HTMLResponse("subject not found", status_code=404)
    if not (user.role == "admin" or can_upload(user, s.id, db)):
        return HTMLResponse("professor assigned to this subject only", status_code=403)
    res = db.query(models.Resource).filter_by(subject_id=s.id).all()
    return templates.TemplateResponse(request, "manage.html", brand(
        {"request": request, "subject": s,
         "resources": [{"id": r.id, "title": r.title, "kind": r.kind, "edition": r.edition} for r in res]}))


@app.get("/favicon.ico", include_in_schema=False)
def favicon():
    from fastapi.responses import Response
    return Response(status_code=204)


@app.get("/health")
def health():
    from app.db import is_fallback
    return {"ok": True, "db_fallback_sqlite": is_fallback()}
