from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from uuid import UUID
import json

from core.deps import get_current_user
from database import get_db
from models.domain import User, Paper, CoverLetter, GeneratedTemplate, Journal
from services.ai_service import call_gemini

router = APIRouter()

@router.post("/analyze-paper")
async def analyze_paper(paper_id: UUID = Query(...), current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    paper = db.query(Paper).filter(Paper.id == paper_id, Paper.user_id == current_user.id).first()
    if not paper:
        raise HTTPException(status_code=404, detail="Paper not found")
        
    system_prompt = "You are an expert academic journal editor. Return ONLY valid JSON."
    prompt = f"Analyze this research abstract for a paper in the domain of {paper.domain}: {paper.abstract}. Return valid JSON: {{ abstract_quality_score: number 1-10, clarity_score: number 1-10, novelty_score: number 1-10, structure_score: number 1-10, completeness_score: number 1-10, abstract_feedback: string, extracted_keywords: array of 6 strings, improvement_suggestions: array of 3 strings, journal_recommendations: array of 5 objects each with journal_name, reason, match_score 1-10 }}"
    
    response_text = await call_gemini(prompt, system_prompt)
    try:
        clean_json = response_text.replace("```json", "").replace("```", "").strip()
        data = json.loads(clean_json)
        
        paper.abstract_quality_score = data.get("abstract_quality_score")
        paper.abstract_feedback = data.get("abstract_feedback")
        paper.ai_keywords = data.get("extracted_keywords", [])
        db.commit()
        return data
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to parse AI response: {str(e)}")

@router.post("/generate-cover-letter")
async def generate_cover_letter(paper_id: UUID = Query(...), journal_name: str = Query(...), journal_scope: str = Query(""), current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    paper = db.query(Paper).filter(Paper.id == paper_id, Paper.user_id == current_user.id).first()
    if not paper:
        raise HTTPException(status_code=404, detail="Paper not found")
        
    prompt = f"Write a 250-300 word professional cover letter for submitting a paper titled '{paper.title}' to the journal '{journal_name}'. The abstract is: '{paper.abstract}'. Keep it professional and compelling."
    content = await call_gemini(prompt)
    
    cl = CoverLetter(user_id=current_user.id, paper_id=paper.id, journal_name=journal_name, content=content)
    db.add(cl)
    db.commit()
    db.refresh(cl)
    return {"content": content, "id": cl.id}

@router.post("/generate-template")
async def generate_template(paper_id: UUID = Query(...), journal_name: str = Query(...), format_type: str = Query(...), current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    paper = db.query(Paper).filter(Paper.id == paper_id, Paper.user_id == current_user.id).first()
    if not paper:
        raise HTTPException(status_code=404, detail="Paper not found")
        
    prompt = f"Generate a COMPLETE, standalone, and strictly compilable LaTeX template for a {format_type} format journal paper. Title: {paper.title}. Authors: {current_user.name}, Department of {current_user.department or 'CS'}, {current_user.university or 'University'}, India. Email: {current_user.email}. Abstract: {paper.abstract}. Keywords: {', '.join(paper.keywords or [])}. You MUST include \\documentclass, all necessary \\usepackage imports, \\begin{{document}}, the title/author block (e.g. \\maketitle), an abstract environment, 5 populated sections (Introduction, Related Work, Methodology, Results and Discussion, Conclusion), and a mock bibliography/references section that actually renders successfully without external files. Use \\begin{{thebibliography}}. The code MUST compile immediately if pasted into a blank Overleaf document without any errors. Return ONLY the raw LaTeX code, no markdown formatting."
    
    latex_code = await call_gemini(prompt)
    if latex_code.startswith("```"):
        latex_code = "\n".join(latex_code.split("\n")[1:])
        if latex_code.endswith("```"):
            latex_code = latex_code[:-3]
    latex_code = latex_code.strip()
    if latex_code.startswith("```latex"):
        latex_code = latex_code[8:].strip()
        if latex_code.endswith("```"):
            latex_code = latex_code[:-3].strip()
            
    template = GeneratedTemplate(user_id=current_user.id, paper_id=paper.id, journal_name=journal_name, format_type=format_type, latex_code=latex_code)
    db.add(template)
    db.commit()
    db.refresh(template)
    return {"latex_code": latex_code, "id": template.id}

@router.post("/check-journal-fit")
async def check_journal_fit(paper_id: UUID = Query(...), journal_id: UUID = Query(...), current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    paper = db.query(Paper).filter(Paper.id == paper_id, Paper.user_id == current_user.id).first()
    journal = db.query(Journal).filter(Journal.id == journal_id).first()
    if not paper or not journal:
        raise HTTPException(status_code=404, detail="Not found")
        
    prompt = f"Analyze the fit between this paper and this journal. Paper Title: {paper.title}. Abstract: {paper.abstract}. Journal Name: {journal.name}. Journal Domain: {journal.domain}. Topics: {', '.join(journal.topics)}. Return ONLY valid JSON: {{ fit_score: number 1-100, explanation: string }}"
    system_prompt = "You are an expert academic evaluator. Return ONLY valid JSON."
    
    response_text = await call_gemini(prompt, system_prompt)
    try:
        clean_json = response_text.replace("```json", "").replace("```", "").strip()
        data = json.loads(clean_json)
        return data
    except Exception as e:
        raise HTTPException(status_code=500, detail="Failed to parse AI response")

@router.post("/improve-abstract")
async def improve_abstract(paper_id: UUID = Query(...), current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    paper = db.query(Paper).filter(Paper.id == paper_id, Paper.user_id == current_user.id).first()
    if not paper:
        raise HTTPException(status_code=404, detail="Paper not found")
        
    prompt = f"Improve this abstract to make it more impactful, concise, and academically sound: {paper.abstract}. Return ONLY the improved text."
    improved = await call_gemini(prompt)
    return {"improved_abstract": improved}
