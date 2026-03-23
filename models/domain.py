import uuid
from sqlalchemy import Column, String, Text, Boolean, Integer, ForeignKey, DateTime, Float
from sqlalchemy.dialects.postgresql import UUID, ARRAY, JSONB
from pgvector.sqlalchemy import Vector
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from database import Base

class User(Base):
    __tablename__ = "users"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    firebase_uid = Column(String, unique=True, index=True)
    name = Column(String)
    email = Column(String, unique=True, index=True)
    university = Column(String)
    department = Column(String)
    avatar_url = Column(String)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    papers = relationship("Paper", back_populates="user")
    submissions = relationship("Submission", back_populates="user")
    saved_journals = relationship("SavedJournal", back_populates="user")

class Paper(Base):
    __tablename__ = "papers"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    title = Column(String)
    abstract = Column(Text)
    domain = Column(String)
    keywords = Column(ARRAY(Text))
    file_url = Column(String)
    file_name = Column(String)
    plagiarism_score = Column(Integer)
    abstract_quality_score = Column(Integer)
    abstract_feedback = Column(Text)
    ai_keywords = Column(ARRAY(Text))
    status = Column(String)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    user = relationship("User", back_populates="papers")
    submissions = relationship("Submission", back_populates="paper")

class Journal(Base):
    __tablename__ = "journals"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String)
    publisher = Column(String)
    domain = Column(String)
    index_types = Column(ARRAY(Text))
    quartile = Column(String)
    speed = Column(String)
    avg_weeks = Column(Integer)
    is_free = Column(Boolean, default=True)
    cost_note = Column(String)
    submission_url = Column(String)
    topics = Column(ARRAY(Text))
    impact_factor = Column(String)
    embedding = Column(Vector(384))

class SavedJournal(Base):
    __tablename__ = "saved_journals"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    journal_id = Column(UUID(as_uuid=True), ForeignKey("journals.id"))
    saved_at = Column(DateTime(timezone=True), server_default=func.now())

    user = relationship("User", back_populates="saved_journals")
    journal = relationship("Journal")

class Submission(Base):
    __tablename__ = "submissions"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    paper_id = Column(UUID(as_uuid=True), ForeignKey("papers.id"))
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    journal_name = Column(String)
    journal_url = Column(String)
    submitted_at = Column(DateTime(timezone=True), server_default=func.now())
    current_status = Column(String)
    notes = Column(Text)
    reminder_date = Column(DateTime(timezone=True))

    user = relationship("User", back_populates="submissions")
    paper = relationship("Paper", back_populates="submissions")

class GeneratedTemplate(Base):
    __tablename__ = "generated_templates"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    paper_id = Column(UUID(as_uuid=True), ForeignKey("papers.id"))
    journal_name = Column(String)
    format_type = Column(String)
    latex_code = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class CoverLetter(Base):
    __tablename__ = "cover_letters"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    paper_id = Column(UUID(as_uuid=True), ForeignKey("papers.id"))
    journal_name = Column(String)
    content = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class PaperAnalysis(Base):
    __tablename__ = "paper_analyses"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    paper_id = Column(UUID(as_uuid=True), ForeignKey("papers.id"))
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    analysis_json = Column(JSONB)
    overall_score = Column(Integer)
    publication_readiness = Column(String)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
