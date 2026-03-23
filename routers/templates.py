from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import Response
from sqlalchemy.orm import Session
from typing import List
from uuid import UUID
import urllib.parse

from core.deps import get_current_user
from database import get_db
from models.domain import User, GeneratedTemplate
from schemas.domain import GeneratedTemplateResponse

router = APIRouter()

@router.get("/", response_model=List[GeneratedTemplateResponse])
def get_templates(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return db.query(GeneratedTemplate).filter(GeneratedTemplate.user_id == current_user.id).order_by(GeneratedTemplate.created_at.desc()).all()

@router.get("/{template_id}", response_model=GeneratedTemplateResponse)
def get_template(template_id: UUID, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    template = db.query(GeneratedTemplate).filter(GeneratedTemplate.id == template_id, GeneratedTemplate.user_id == current_user.id).first()
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")
    return template

@router.get("/{template_id}/download")
def download_template(template_id: UUID, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    template = db.query(GeneratedTemplate).filter(GeneratedTemplate.id == template_id, GeneratedTemplate.user_id == current_user.id).first()
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")
        
    return Response(content=template.latex_code, media_type="application/x-tex", headers={"Content-Disposition": f"attachment; filename=template_{template.id}.tex"})

@router.get("/{template_id}/overleaf")
def overleaf_url(template_id: UUID, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    template = db.query(GeneratedTemplate).filter(GeneratedTemplate.id == template_id, GeneratedTemplate.user_id == current_user.id).first()
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")
        
    encoded_snip = urllib.parse.quote(template.latex_code)
    url = f"https://www.overleaf.com/docs?snip_uri=data:application/x-tex,{encoded_snip}"
    return {"url": url}

@router.delete("/{template_id}")
def delete_template(template_id: UUID, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    template = db.query(GeneratedTemplate).filter(GeneratedTemplate.id == template_id, GeneratedTemplate.user_id == current_user.id).first()
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")
        
    db.delete(template)
    db.commit()
    return {"message": "Template deleted successfully"}
