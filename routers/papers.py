from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.orm import Session
from typing import List
from uuid import UUID
import os
import shutil

from core.config import settings
from core.deps import get_current_user
from database import get_db
from models.domain import User, Paper, PaperAnalysis, GeneratedTemplate, CoverLetter, Submission
from schemas.domain import PaperResponse, PaperCreate, PaperUpdate

router = APIRouter()

@router.get("/", response_model=List[PaperResponse])
def get_papers(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return db.query(Paper).filter(Paper.user_id == current_user.id).order_by(Paper.created_at.desc()).all()

@router.post("/", response_model=PaperResponse)
def create_paper(paper: PaperCreate, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    db_paper = Paper(**paper.dict(), user_id=current_user.id, status="draft")
    db.add(db_paper)
    db.commit()
    db.refresh(db_paper)
    return db_paper

@router.get("/{paper_id}", response_model=PaperResponse)
def get_paper(paper_id: UUID, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    paper = db.query(Paper).filter(Paper.id == paper_id, Paper.user_id == current_user.id).first()
    if not paper:
        raise HTTPException(status_code=404, detail="Paper not found")
    return paper

@router.put("/{paper_id}", response_model=PaperResponse)
def update_paper(paper_id: UUID, paper_update: PaperUpdate, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    paper = db.query(Paper).filter(Paper.id == paper_id, Paper.user_id == current_user.id).first()
    if not paper:
        raise HTTPException(status_code=404, detail="Paper not found")
        
    update_data = paper_update.dict(exclude_unset=True)
    for key, value in update_data.items():
        setattr(paper, key, value)
        
    db.commit()
    db.refresh(paper)
    return paper

@router.post("/{paper_id}/upload-pdf")
async def upload_pdf(
    paper_id: UUID, 
    file: UploadFile = File(...), 
    current_user: User = Depends(get_current_user), 
    db: Session = Depends(get_db)
):
    paper = db.query(Paper).filter(Paper.id == paper_id, Paper.user_id == current_user.id).first()
    if not paper:
        raise HTTPException(status_code=404, detail="Paper not found")
        
    file_path = os.path.join(settings.UPLOAD_DIR, f"{paper.id}_{file.filename}")
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
        
    paper.file_url = f"/uploads/{paper.id}_{file.filename}"
    paper.file_name = file.filename
    db.commit()
    
    return {"message": "File uploaded successfully", "file_url": paper.file_url}

@router.delete("/{paper_id}")
def delete_paper(paper_id: UUID, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    paper = db.query(Paper).filter(Paper.id == paper_id, Paper.user_id == current_user.id).first()
    if not paper:
        raise HTTPException(status_code=404, detail="Paper not found")
        
    # Delete related records to prevent FK constraints
    db.query(PaperAnalysis).filter(PaperAnalysis.paper_id == paper.id).delete()
    db.query(GeneratedTemplate).filter(GeneratedTemplate.paper_id == paper.id).delete()
    db.query(CoverLetter).filter(CoverLetter.paper_id == paper.id).delete()
    db.query(Submission).filter(Submission.paper_id == paper.id).delete()
    
    # Try deleting file from local storage
    if paper.file_url:
        file_path = os.path.join(settings.UPLOAD_DIR, paper.file_url.split('/')[-1])
        if os.path.exists(file_path):
            try:
                os.remove(file_path)
            except Exception:
                pass

    db.delete(paper)
    db.commit()
    return {"message": "Paper and associated records deleted successfully"}
