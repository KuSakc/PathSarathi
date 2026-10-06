# Tech Used — Garibi

| Package | Used for | Required? |
|---|---|---|
| fastapi, uvicorn | web API + server | yes |
| sqlalchemy, psycopg2-binary, alembic | Postgres ORM/migrate | yes (Postgres default) |
| pydantic, pydantic-settings | config/schemas | yes |
| python-jose, bcrypt | JWT + hash | yes |
| python-multipart, jinja2 | forms + HTMX templates | yes |
| chromadb | local vector DB (free) | yes, graceful fallback to JSON store if missing |
| sentence-transformers | local embeddings | yes, graceful fallback to hash embeddings if missing |
| pypdf, pymupdf | text extraction | yes |
| reportlab | PDF creation | yes |
| httpx | Ollama + OpenAI-compat calls | yes |
| ollama (server, not pip) | local Generator AI | external, optional (stub fallback) |
| postgres (server) | primary DB | external, required unless fallback enabled |
