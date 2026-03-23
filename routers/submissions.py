from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from uuid import UUID

from core.deps import get_current_user
from database import get_db
from models.domain import User, Submission
from schemas.domain import SubmissionResponse, SubmissionCreate, SubmissionUpdate

router = APIRouter()

@router.get("/", response_model=List[SubmissionResponse])
def get_submissions(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return db.query(Submission).filter(Submission.user_id == current_user.id).order_by(Submission.submitted_at.desc()).all()

@router.post("/", response_model=SubmissionResponse)
def create_submission(submission: SubmissionCreate, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    db_item = Submission(**submission.dict(), user_id=current_user.id, current_status="submitted")
    db.add(db_item)
    db.commit()
    db.refresh(db_item)
    return db_item

@router.patch("/{submission_id}", response_model=SubmissionResponse)
def patch_submission(submission_id: UUID, sub_update: SubmissionUpdate, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    sub = db.query(Submission).filter(Submission.id == submission_id, Submission.user_id == current_user.id).first()
    if not sub:
        raise HTTPException(status_code=404, detail="Submission not found")
    
    update_data = sub_update.dict(exclude_unset=True)
    for key, value in update_data.items():
        setattr(sub, key, value)
        
    db.commit()
    db.refresh(sub)
    return sub
