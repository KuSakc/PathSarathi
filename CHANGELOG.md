# Changelog — Garibi

All notable changes, newest first. Format: `[date] module: change`.

## [2026-10-04] v0.1.0 scaffold
- `project`: init pyproject, .env.example (Postgres default + SQLite fallback), .gitignore, README
- `app/config,db,models,auth,deps`: Postgres-first engine with SQLite fallback, User/Profile/Subject/ProfessorSubject/Resource/SyllabusEdition/GeneratedDoc, JWT cookie auth, role gates
- `app/routers`: auth, subjects, library, syllabus, generate, admin (chunk-visibility toggle)
- `ai/`: chunking_agent (extract+split+embed), generator_agent (Ollama + stub), rag (Chroma + fallback), providers (base, openai_compat, local_stub, ollama)
- `prompts/`: _base + microprocessor + discrete-structure flexible templates
- `templates/static`: base/index/library/subject_detail/login/profile/admin HTMX UI
- `app/pdf`: reportlab generation
- `docs`: MODULES.md, TECH_USED.md, CHANGELOG.md tracking started
- `tests`: import smoke test

## [2026-10-04] fix auth + verified e2e
- `app/auth.py`: replaced passlib with direct bcrypt (fixed 72-byte crash)
- `app/routers/auth.py,subjects.py`: direct deps imports (removed __import__ hacks)
- `pyproject.toml,TECH_USED.md`: passlib -> bcrypt
- verified: health SQLite-fallback, seed 2 core, prof/student register+login, syllabus save+gap, escalation, generate detailed + PDF, admin assign + chunk-toggle + elective same-flow

## [2026-10-04] fix index + favicon
- `app/main.py:29`: router attr -> `seed_defaults(db)` direct call
- `app/main.py:31`: Starlette 1.7 TemplateResponse new signature `TemplateResponse(request, name, ctx)`
- `app/main.py`: added `GET /favicon.ico` 204 to silence 404
- verified: `/` 200, `/favicon.ico` 204, `/health` ok

## [2026-10-06] frontend v1 (wireframes + refs)
- `app/config.py`: SITE_NAME/SITE_TAGLINE/SITE_SUBTITLE/FACULTIES — single-place rename
- `static/theme.css`: NEW proper theme variables (dark default + light toggle, orange accent)
- `static/style.css`: layout-only rewrite (topbar/hero/grid/card/resgroup/cols/fast)
- `templates/base.html`: brand left/tagline center/Login right, crumb block, theme toggle, fast-selection
- `templates/`: index=faculty grid, semester.html, subjects.html (Hamro cards), subject_detail.html (ICT groups: Syllabus/Notes/Old Q/Solutions/Books/Generated + inline Generate + Other Subjects), studio.html (dedicated generate), login.html (unified student/prof + separate admin_mode), register.html (fixed role id bug), profile.html (BYOK), admin.html (dashboard)
- `app/main.py`: UI routes /f/{fac}, /f/{fac}/sem/{sem}, /subject/{slug} grouped resources, /studio, /login, /register, /profile, /admin/login, /admin (gated)
- verified: 13 pages 200 (/favicon 204), brand present, unified login text, admin gate 401→200, pytest 1 passed

## [2026-10-06] ICT style + electives-as-subjects + Generation System
- `static/theme.css`: ICT light default (bg #eef2f7, orange/red hero), dark via data-theme=dark
- `static/style.css`: ICT header/nav/search, orange gradient hero w/ pattern, white cards+shadow, resgroup `📘 |` titles, red pdf icons, gen3 3-pane, removed `.fast`, added `.topbtn`
- `templates/base.html`: consistent header (logo C-mark + Home/Generation/About/Contact + search + theme + Login), footer, removed Fast Selection everywhere
- `templates/semester.html`: removed Electives tile — First–Eighth only
- `templates/subjects.html`, `subject_detail.html`, `search.html`: elective suffix `Name - Elective`; ICT groups + Other Subjects/Other Semesters sidebar; subject page links Generation System (not studio)
- `templates/generation.html`: NEW NotebookLM 3-pane (Sources | Ask/Create | Studio: Flashcards + Solve only, rest disabled)
- `templates/studio.html`: DELETED; `/studio` 307 → `/generation`
- `app/main.py`: `/search?q=`, `/generation?subject=`, legacy `/sem/elective` kept unlinked, brand() on all pages
- `app/routers/generate.py`: + `POST /generate/{id}/flashcards` + `POST /generate/{id}/solve` (RAG-grounded, stub-safe); `app/schemas.py`: FlashcardsIn/SolveIn
- verified: 12 pages 200 + /studio 307, no Fast Selection, no elective tile, ICT header ok, flashcards+solve+generate 200, pytest 1 passed

## [2026-10-06] blue theme + full Sem-2 + demo content + Studio Summary/Quiz/Export + styled PDF
- `static/theme.css`: warm orange/red -> sky blue (hero #38bdf8->#2563eb, accent/btn #0284c7) light+dark
- `app/routers/subjects.py`: seed all 5 Sem-2 (OOP, Math II, Stats I, DS, MP) with upsert heal + BSc.CSIT course
- `app/main.py`: demo for-show content per subject (sir-notes.pdf, 10 papers 2076-2067, syllabus-2079/2074, microsyllabus, {slug}-for-all-notes.pdf); real customs shown as {slug}-custom-{topic}
- `app/routers/generate.py`: generated PDFs renamed {slug}-custom-{topic}.pdf; + POST summary (prompts/summary.md placeholder, BYOK-first) + POST quiz (MCQs) + POST /export/pdf + GET /download-file
- `app/schemas.py`: SummaryIn/QuizIn/ExportIn; `prompts/summary.md`: placeholder until user prompt
- `app/pdf.py`: styled export — title page, TOC w/ page numbers, H1/H2/H3 styles, bullets, footers (fixed reportlab addOutline compat)
- `templates/generation.html`: Studio = Flashcards + Solve + Summary(API) + Quiz Me + Export-to-PDF below; lastMD carried to export
- `templates/subject_detail.html`: demo badge rendering (no dead download links)
- verified: Sem-2 5 cards, demo names present, blue vars, summary/quiz/generate/export/download 200, custom naming, pytest 1 passed

## [2026-10-06] rename + notices + legit lists + accounts + professor manage
- `app/config.py,.env.example,app/main.py`: BidhyaBhandar -> Path Sarathi (single spot + app title)
- `app/main.py`: KIND_GROUPS + Additional Material (extra); legit placeholder editions (no demo wording); NOTICES seed (Result/Routine/Close/Practical) + /notices + /notices/{id}; /generation 307->/login when anonymous; /manage/{slug} (professor-assigned/admin only); boot seed_all
- `app/seed.py`: NEW User/Pass student, Professor/Password professor (all Sem-2 assigned), Admin/admin
- `app/deps.py`: + optional_user (anonymous-safe)
- `app/routers/library.py`: + PATCH /{rid} edit + DELETE /{rid} (professor-gated)
- `templates/base.html`: Notice in nav; `notices.html` + `notice_detail.html`: NEW; `subject_detail.html`: demo badge removed (plain list), + Manage button (prof/admin) + login-gated Generate box; `manage.html`: NEW curriculum editor (editions/topics/gap) + file manager (upload notes/extra, edit, delete)
- verified: brand, anon-gen 307, notices 200, no demo badge, Additional Material present, 3 logins ok, manage 200 prof / 403 student, syllabus save+gap ok, pytest 1 passed

## [2026-10-06] header API key + login toast + classic login
- `templates/base.html`: 🔑 API Key header link (/profile, no force); flying login toast (3s auto-hide + ✕, no redirect) via /auth/me
- `app/routers/auth.py`: + GET /auth/me {logged_in, username, role}; fixed mangled profile decorator
- `templates/login.html`: standalone classic serif card (no ICT theme), ?next= support; admin login same classic
- `templates/generation.html`: credentials same-origin on all calls; 401->/login, 403->/profile (API key) redirects; `manage.html`: credentials on mutating calls
- verified: /auth/me anon+user, header key, toast markup, classic login (no theme css), 403 non-escalated gen, pytest 1 passed
