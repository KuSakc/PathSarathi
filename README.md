# Garibi — Syllabus-aware E-Library

Web platform: E-library (35%) + AI generation (55%) + misc (10%).

V1 subjects: `microprocessor`, `discrete-structure` (Sem-2) + electives (same flow).

## Run (Postgres default)

1. `cp .env.example .env` (set `DATABASE_URL`, `SECRET_KEY`)
2. Start Postgres, create db `garibi`
3. `pip install -e .`
4. `uvicorn app.main:app --reload`
5. Open http://127.0.0.1:8000

If Postgres is down and `ALLOW_SQLITE_FALLBACK=true`, app boots on SQLite automatically (logged as warning).

## Roles

- Admin: absolute, sees chunks always, toggles `professor_chunk_access`.
- Professor: upload only to assigned subjects + read.
- Student: view-only; generate/private use only after profile complete + API key saved.

## AI agents (local-first)

- `Chunking AI` (`ai/chunking_agent.py`): extract -> semantic split -> Chroma (local free).
- `Generator AI` (`ai/generator_agent.py`): Ollama by default, stub fallback offline; external BYOK provider per-user for private User-mode generation.
- Prompts in `prompts/` are server-only, never sent to client.

See `MODULES.md` for module map, `TECH_USED.md` for deps, `CHANGELOG.md` for history.
