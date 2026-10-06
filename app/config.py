from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # --- Branding: SINGLE place to rename the site ---
    SITE_NAME: str = "Path Sarathi"
    SITE_TAGLINE: str = "For Students to study, with no Worry"
    SITE_SUBTITLE: str = "Everything for Students to Study"
    # Faculties shown on home (course key -> display). Subjects use `course` to map.
    FACULTIES: str = "BSc.CSIT,BIT,BBA,LAW,BITM"
    DATABASE_URL: str = "postgresql+psycopg2://garibi:garibi@localhost:5432/garibi"
    ALLOW_SQLITE_FALLBACK: bool = True
    SQLITE_URL: str = "sqlite:///./garibi_dev.db"
    SECRET_KEY: str = "change-me"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 720
    OLLAMA_BASE_URL: str = "http://localhost:11434"
    OLLAMA_MODEL: str = "llama3"
    EMBEDDING_MODEL: str = "sentence-transformers/all-MiniLM-L6-v2"
    CHROMA_DIR: str = "./chroma_db"
    DATA_DIR: str = "./data"
    PROMPTS_DIR: str = "./prompts"

    class Config:
        env_file = ".env"
        extra = "ignore"


settings = Settings()
