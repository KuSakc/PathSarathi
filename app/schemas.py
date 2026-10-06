from pydantic import BaseModel
from typing import Optional, List


class RegisterIn(BaseModel):
    username: str
    password: str
    role: str = "student"


class LoginIn(BaseModel):
    username: str
    password: str


class ProfileIn(BaseModel):
    full_name: str = ""
    api_key: str = ""
    api_provider: str = "openai_compat"


class TopicIn(BaseModel):
    topic: str
    hours: float = 0
    marks: float = 0


class SyllabusIn(BaseModel):
    edition: str
    topics: List[TopicIn]


class GenerateIn(BaseModel):
    topic: str
    syllabus_weight: float = 1.0
    paper_frequency: float = 0.0
    use_external: bool = False


class FlashcardsIn(BaseModel):
    topic: str
    count: int = 6
    use_external: bool = False


class SolveIn(BaseModel):
    question: str
    paper_title: str = ""
    use_external: bool = False


class SummaryIn(BaseModel):
    topic: str
    length: str = "standard"  # brief|standard|detailed
    use_external: bool = True  # summary prefers API/BYOK


class QuizIn(BaseModel):
    topic: str
    count: int = 5
    use_external: bool = False


class ExportIn(BaseModel):
    title: str = "Study Notes"
    content_md: str = ""
    doc_id: int | None = None
