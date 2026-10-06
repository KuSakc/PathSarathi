# Modules — Garibi

| Module | Path | Responsibility | Status |
|---|---|---|---|
| config | `app/config.py` | env, Postgres default + SQLite fallback, Ollama/Chroma dirs | done |
| db | `app/db.py` | engine/session init, fallback logic, Base | done |
| models | `app/models.py` | User, Profile, Subject(elective), ProfessorSubject, Resource, SyllabusEdition, GeneratedDoc | done |
| auth | `app/auth.py` | hash, JWT, cookie | done |
| deps | `app/deps.py` | current_user, require_admin, require_professor, require_escalated_student | done |
| routers/auth | `app/routers/auth.py` | register/login/profile/key | done |
| routers/subjects | `app/routers/subjects.py` | list incl. electives | done |
| routers/library | `app/routers/library.py` | upload (professor gated), list/download | done |
| routers/syllabus | `app/routers/syllabus.py` | versioned syllabus upload/list | done |
| routers/generate | `app/routers/generate.py` | gap->score->RAG->generate->PDF | done |
| routers/admin | `app/routers/admin.py` | chunk-access toggle, user list | done |
| pdf | `app/pdf.py` | reportlab doc creation | done |
| chunking_agent | `ai/chunking_agent.py` | PDF/image extract, split, embed | done |
| generator_agent | `ai/generator_agent.py` | Ollama primary, stub fallback, BYOK external | done |
| rag | `ai/rag.py` | Chroma retrieve + fallback store | done |
| providers | `ai/providers/` | base, ollama, openai_compat, local_stub | done |
| prompts | `prompts/` | _base + 2 subject templates, fallback | done |
| ui | `templates/`, `static/` | HTMX server-rendered: ICT header/search/hero/cards/sidebar, faculty/sem/subject/search/generation/login/register/profile/admin, theme.css vars | done v2 |
| pages | `app/main.py` | UI routes + brand() context + KIND_GROUPS + elective-as-subject + /search + /generation (/studio redirect) | done v2 |
| gen-modes | `app/routers/generate.py` | base generate (-custom- names) + flashcards + solve + summary(BYOK) + quiz + export-pdf/download-file | done v2 |
| pdf | `app/pdf.py` | styled export: title + linked TOC + headings + footers | done v2 |
| demo-content | `app/main.py` | sir-notes/10 papers/syllabus 2079+2074/for-all/additional placeholders (no demo markings) | done v2 |
| notices | `app/main.py` + `templates/notices*.html` | Notice nav + 4 fake notices + detail | done v1 |
| accounts | `app/seed.py` | User/Pass, Professor/Password (all subjects), Admin/admin; anon view-only, gen gated | done v1 |
| manage | `templates/manage.html` + `PATCH/DELETE /library` | professor curriculum editor + notes/extra file manager | done v1 |
| auth-ux | `templates/base.html,login.html` + `GET /auth/me` | header API-key link, 3s login toast w/ close, classic login, 401/403 redirects | done v1 |

## Change log pointer
See `CHANGELOG.md` for dated entries. Update both files on every change.
