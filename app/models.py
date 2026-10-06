import datetime
from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String, Text
from app.db import Base


class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True)
    username = Column(String(64), unique=True, nullable=False)
    password_hash = Column(String(256), nullable=False)
    role = Column(String(16), nullable=False, default="student")  # admin|professor|student
    created_at = Column(DateTime, default=datetime.datetime.utcnow)


class Profile(Base):
    __tablename__ = "profiles"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True, nullable=False)
    full_name = Column(String(128), default="")
    api_key = Column(String(512), default="")  # user BYOK, never returned
    api_provider = Column(String(64), default="openai_compat")
    profile_complete = Column(Boolean, default=False)


class Subject(Base):
    __tablename__ = "subjects"
    id = Column(Integer, primary_key=True)
    slug = Column(String(64), unique=True, nullable=False)  # microprocessor, discrete-structure
    name = Column(String(128), nullable=False)
    semester = Column(Integer, nullable=True)  # null for electives without fixed sem
    course = Column(String(64), default="CSIT")
    is_elective = Column(Boolean, default=False)
    professor_chunk_access = Column(Boolean, default=False)  # admin toggle


class ProfessorSubject(Base):
    __tablename__ = "professor_subjects"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    subject_id = Column(Integer, ForeignKey("subjects.id"), nullable=False)


class Resource(Base):
    __tablename__ = "resources"
    id = Column(Integer, primary_key=True)
    subject_id = Column(Integer, ForeignKey("subjects.id"), nullable=False)
    kind = Column(String(32), nullable=False)  # notes|book_raw|paper|generated|syllabus
    title = Column(String(256), nullable=False)
    filepath = Column(String(512), nullable=False)
    edition = Column(String(64), default="")
    uploaded_by = Column(Integer, ForeignKey("users.id"))
    created_at = Column(DateTime, default=datetime.datetime.utcnow)


class SyllabusEdition(Base):
    __tablename__ = "syllabus_editions"
    id = Column(Integer, primary_key=True)
    subject_id = Column(Integer, ForeignKey("subjects.id"), nullable=False)
    edition = Column(String(64), nullable=False)  # e.g. 2024-rev
    topics_json = Column(Text, default="[]")  # [{"topic":..,"hours":..,"marks":..}]
    filepath = Column(String(512), default="")


class GeneratedDoc(Base):
    __tablename__ = "generated_docs"
    id = Column(Integer, primary_key=True)
    subject_id = Column(Integer, ForeignKey("subjects.id"), nullable=False)
    topic = Column(String(256), nullable=False)
    content_md = Column(Text, default="")
    pdf_path = Column(String(512), default="")
    origin = Column(String(16), default="local")  # local|external
    private_to_user = Column(Integer, nullable=True)  # user_id if BYOK-private
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
