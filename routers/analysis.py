from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional
from uuid import UUID
import os
import fitz
import docx
import json

from core.config import settings
from core.deps import get_current_user
from database import get_db
from models.domain import User, Paper, PaperAnalysis
from services.ai_service import call_gemini

router = APIRouter()

class AnalysisRequest(BaseModel):
    paper_id: Optional[UUID] = None
    raw_text: Optional[str] = None

ANALYSIS_PROMPT = """
You are a senior academic journal editor and peer reviewer with 20 years of experience reviewing papers for Scopus Q1 journals like Elsevier, Springer, and IEEE.

Analyse the following research paper text against these 10 publication criteria. Be specific, honest, and constructive. Write feedback as if you are directly advising the student author.

Return ONLY valid JSON in this exact structure — no text outside the JSON:

{
  "overall_score": <number 0-100>,
  "publication_readiness": "<Ready to Submit | Needs Minor Revision | Needs Major Revision | Not Ready>",
  "checks": [
    {
      "id": "novelty",
      "title": "Novelty & Originality",
      "score": <0-10>,
      "verdict": "<Strong | Acceptable | Weak | Critical Issue>",
      "summary": "<one sentence verdict>",
      "feedback": "<3-5 specific sentences explaining what is novel, what is missing, what to strengthen>",
      "how_to_fix": "<concrete actionable steps to improve this specific aspect>"
    },
    {
      "id": "abstract_quality",
      "title": "Abstract Quality",
      "score": <0-10>,
      "verdict": "<Strong | Acceptable | Weak | Critical Issue>",
      "summary": "<one sentence verdict>",
      "feedback": "<3-5 specific sentences>",
      "how_to_fix": "<concrete actionable steps>"
    },
    {
      "id": "literature_review",
      "title": "Literature Review Depth",
      "score": <0-10>,
      "verdict": "<Strong | Acceptable | Weak | Critical Issue>",
      "summary": "<one sentence verdict>",
      "feedback": "<3-5 specific sentences>",
      "how_to_fix": "<concrete actionable steps>"
    },
    {
      "id": "methodology",
      "title": "Methodology Clarity & Reproducibility",
      "score": <0-10>,
      "verdict": "<Strong | Acceptable | Weak | Critical Issue>",
      "summary": "<one sentence verdict>",
      "feedback": "<3-5 specific sentences>",
      "how_to_fix": "<concrete actionable steps>"
    },
    {
      "id": "results_analysis",
      "title": "Results & Comparative Analysis",
      "score": <0-10>,
      "verdict": "<Strong | Acceptable | Weak | Critical Issue>",
      "summary": "<one sentence verdict>",
      "feedback": "<3-5 specific sentences>",
      "how_to_fix": "<concrete actionable steps>"
    },
    {
      "id": "language_clarity",
      "title": "Language & Writing Quality",
      "score": <0-10>,
      "verdict": "<Strong | Acceptable | Weak | Critical Issue>",
      "summary": "<one sentence verdict>",
      "feedback": "<3-5 specific sentences>",
      "how_to_fix": "<concrete actionable steps>"
    },
    {
      "id": "structure_formatting",
      "title": "Structure & Formatting",
      "score": <0-10>,
      "verdict": "<Strong | Acceptable | Weak | Critical Issue>",
      "summary": "<one sentence verdict>",
      "feedback": "<3-5 specific sentences>",
      "how_to_fix": "<concrete actionable steps>"
    },
    {
      "id": "ethical_compliance",
      "title": "Ethical & Academic Integrity",
      "score": <0-10>,
      "verdict": "<Strong | Acceptable | Weak | Critical Issue>",
      "summary": "<one sentence verdict>",
      "feedback": "<3-5 specific sentences>",
      "how_to_fix": "<concrete actionable steps>"
    },
    {
      "id": "references_quality",
      "title": "References Quality & Recency",
      "score": <0-10>,
      "verdict": "<Strong | Acceptable | Weak | Critical Issue>",
      "summary": "<one sentence verdict>",
      "feedback": "<3-5 specific sentences>",
      "how_to_fix": "<concrete actionable steps>"
    },
    {
      "id": "conclusion_impact",
      "title": "Conclusion & Research Impact",
      "score": <0-10>,
      "verdict": "<Strong | Acceptable | Weak | Critical Issue>",
      "summary": "<one sentence verdict>",
      "feedback": "<3-5 specific sentences>",
      "how_to_fix": "<concrete actionable steps>"
    }
  ],
  "top_3_strengths": ["strength 1", "strength 2", "strength 3"],
  "top_3_critical_fixes": ["fix 1", "fix 2", "fix 3"],
  "estimated_desk_rejection_risk": "<Low | Medium | High | Very High>",
  "suggested_target_quartile": "<Q1 | Q2 | Q3>",
  "one_line_summary": "<one honest sentence about the paper's publication readiness>"
}

The 10 checks to evaluate must use exactly these ids as listed above.

Paper text to analyse:
{paper_text}
"""

def extract_text_from_file(file_path: str) -> str:
    ext = file_path.lower().split('.')[-1]
    text = ""
    try:
        if ext == 'pdf':
            with fitz.open(file_path) as pdf_doc:
                for page in pdf_doc:
                    text += page.get_text("text") + "\n"
        elif ext == 'docx':
            doc = docx.Document(file_path)
            for para in doc.paragraphs:
                text += para.text + "\n"
        elif ext == 'txt':
            with open(file_path, "r", encoding="utf-8") as f:
                text = f.read()
        return text
    except Exception as e:
        raise ValueError(f"Failed to extract text from {ext} file: {str(e)}")

@router.post("/analyse")
async def analyse_paper(
    request: AnalysisRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    paper_text = ""
    paper = None

    if request.paper_id:
        paper = db.query(Paper).filter(Paper.id == request.paper_id, Paper.user_id == current_user.id).first()
        if not paper:
            raise HTTPException(status_code=404, detail="Paper not found")
        if not paper.file_name:
            if not request.raw_text:
                raise HTTPException(status_code=400, detail="Paper has no file attached and no raw_text provided")
            paper_text = request.raw_text
        else:
            file_path = os.path.join(settings.UPLOAD_DIR, f"{paper.id}_{paper.file_name}")
            if not os.path.exists(file_path):
                raise HTTPException(status_code=404, detail="Paper file not found on server")
            try:
                paper_text = extract_text_from_file(file_path)
            except ValueError as e:
                raise HTTPException(status_code=400, detail=str(e))
    elif request.raw_text:
        paper_text = request.raw_text
    else:
        raise HTTPException(status_code=400, detail="Must provide either paper_id or raw_text")
        
    if not paper_text.strip():
        raise HTTPException(status_code=400, detail="Extracted document text is empty")
        
    prompt = ANALYSIS_PROMPT.replace("{paper_text}", paper_text[:80000]) # roughly limit to avoid huge context limits if needed
    
    try:
        response_text = await call_gemini(prompt)
        # Parse JSON
        start_idx = response_text.find('{')
        end_idx = response_text.rfind('}')
        if start_idx != -1 and end_idx != -1:
            json_str = response_text[start_idx:end_idx+1]
        else:
            json_str = response_text
            
        analysis_data = json.loads(json_str)
        
        # Save to DB
        new_analysis = PaperAnalysis(
            paper_id=request.paper_id if request.paper_id else None,
            user_id=current_user.id,
            analysis_json=analysis_data,
            overall_score=analysis_data.get("overall_score", 0),
            publication_readiness=analysis_data.get("publication_readiness", "Not Ready")
        )
        db.add(new_analysis)
        db.commit()
        db.refresh(new_analysis)
        
        return {
            "id": new_analysis.id,
            "analysis": analysis_data
        }
    except json.JSONDecodeError as e:
        raise HTTPException(status_code=500, detail=f"Failed to parse AI response as JSON: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")

@router.get("/{paper_id}")
async def get_analysis(
    paper_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    analysis = db.query(PaperAnalysis).filter(
        PaperAnalysis.paper_id == paper_id,
        PaperAnalysis.user_id == current_user.id
    ).order_by(PaperAnalysis.created_at.desc()).first()
    
    if not analysis:
        raise HTTPException(status_code=404, detail="Analysis not found for this paper")
        
    return {
        "id": analysis.id,
        "analysis": analysis.analysis_json,
        "created_at": analysis.created_at
    }
