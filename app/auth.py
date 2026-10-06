import bcrypt
from jose import jwt
import datetime
from app.config import settings


def hash_pw(p: str) -> str:
    pw = p.encode()[:72]
    return bcrypt.hashpw(pw, bcrypt.gensalt()).decode()


def verify_pw(p: str, h: str) -> bool:
    try:
        return bcrypt.checkpw(p.encode()[:72], h.encode())
    except Exception:
        return False


def make_token(user_id: int, role: str) -> str:
    exp = datetime.datetime.utcnow() + datetime.timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    return jwt.encode({"sub": str(user_id), "role": role, "exp": exp}, settings.SECRET_KEY, algorithm="HS256")


def parse_token(t: str) -> dict:
    return jwt.decode(t, settings.SECRET_KEY, algorithms=["HS256"])
