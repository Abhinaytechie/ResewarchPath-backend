from fastapi import APIRouter
from . import auth, journals, papers, ai, templates, submissions, analysis

api_router = APIRouter()
api_router.include_router(auth.router, prefix="/auth", tags=["Auth"])
api_router.include_router(journals.router, prefix="/journals", tags=["Journals"])
api_router.include_router(papers.router, prefix="/papers", tags=["Papers"])
api_router.include_router(ai.router, prefix="/ai", tags=["AI"])
api_router.include_router(templates.router, prefix="/templates", tags=["Templates"])
api_router.include_router(submissions.router, prefix="/submissions", tags=["Submissions"])
api_router.include_router(analysis.router, prefix="/analysis", tags=["Analysis"])
