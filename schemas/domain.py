from pydantic import BaseModel, EmailStr
from typing import List, Optional, Any, Literal
from datetime import datetime
from uuid import UUID

class UserBase(BaseModel):
    name: str
    email: EmailStr
    university: Optional[str] = None
    department: Optional[str] = None
    avatar_url: Optional[str] = None

class UserResponse(UserBase):
    id: UUID
    firebase_uid: str
    created_at: datetime
    class Config:
        from_attributes = True

class PaperBase(BaseModel):
    title: str
    abstract: str
    domain: str
    keywords: Optional[List[str]] = []

class PaperCreate(PaperBase):
    pass

class PaperUpdate(BaseModel):
    title: Optional[str] = None
    abstract: Optional[str] = None
    domain: Optional[str] = None
    keywords: Optional[List[str]] = None
    file_url: Optional[str] = None
    file_name: Optional[str] = None

class PaperResponse(PaperBase):
    id: UUID
    user_id: UUID
    file_url: Optional[str] = None
    file_name: Optional[str] = None
    plagiarism_score: Optional[int] = None
    abstract_quality_score: Optional[int] = None
    abstract_feedback: Optional[str] = None
    ai_keywords: Optional[List[str]] = []
    status: Optional[str] = None
    created_at: datetime
    class Config:
        from_attributes = True

class JournalResponse(BaseModel):
    id: UUID
    name: str
    publisher: str
    domain: str
    index_types: Optional[List[str]] = []
    quartile: str
    speed: str
    avg_weeks: int
    is_free: bool
    cost_note: Optional[str] = None
    submission_url: Optional[str] = None
    topics: Optional[List[str]] = []
    impact_factor: Optional[Any] = None
    class Config:
        from_attributes = True


class JournalSearchItem(JournalResponse):
    source: Literal["rag", "exa"] = "rag"
    snippet: Optional[str] = None


class JournalSearchBundle(BaseModel):
    rag: List[JournalSearchItem]
    exa: List[JournalSearchItem]
    exa_key_configured: bool = False


class SavedJournalResponse(BaseModel):
    id: UUID
    user_id: UUID
    journal_id: UUID
    journal: JournalResponse
    saved_at: datetime
    class Config:
        from_attributes = True

class SubmissionBase(BaseModel):
    paper_id: UUID
    journal_name: str
    journal_url: Optional[str] = None
    notes: Optional[str] = None
    reminder_date: Optional[datetime] = None

class SubmissionCreate(SubmissionBase):
    pass

class SubmissionUpdate(BaseModel):
    current_status: Optional[str] = None
    notes: Optional[str] = None

class SubmissionResponse(SubmissionBase):
    id: UUID
    user_id: UUID
    current_status: Optional[str] = None
    submitted_at: datetime
    class Config:
        from_attributes = True

class GeneratedTemplateResponse(BaseModel):
    id: UUID
    user_id: UUID
    paper_id: UUID
    journal_name: str
    format_type: str
    latex_code: str
    created_at: datetime
    class Config:
        from_attributes = True

class CoverLetterResponse(BaseModel):
    id: UUID
    user_id: UUID
    paper_id: UUID
    journal_name: str
    content: str
    created_at: datetime
    class Config:
        from_attributes = True
