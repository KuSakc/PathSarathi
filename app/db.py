import logging
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker
from app.config import settings

log = logging.getLogger("garibi.db")
Base = declarative_base()

_engine = None
_using_fallback = False


def get_engine():
    global _engine, _using_fallback
    if _engine is not None:
        return _engine
    try:
        _engine = create_engine(settings.DATABASE_URL, pool_pre_ping=True)
        with _engine.connect() as c:
            c.exec_driver_sql("SELECT 1")
        log.info("DB: connected Postgres")
    except Exception as e:
        if not settings.ALLOW_SQLITE_FALLBACK:
            raise
        log.warning(f"DB: Postgres unreachable ({e}); falling back to SQLite")
        _engine = create_engine(settings.SQLITE_URL, connect_args={"check_same_thread": False})
        _using_fallback = True
    return _engine


def is_fallback() -> bool:
    return _using_fallback


def get_sessionmaker():
    return sessionmaker(bind=get_engine(), autoflush=False, autocommit=False)


SessionLocal = None


def init_session():
    global SessionLocal
    if SessionLocal is None:
        SessionLocal = get_sessionmaker()
    return SessionLocal


def get_db():
    Session = init_session()
    db = Session()
    try:
        yield db
    finally:
        db.close()
