from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import SystemMessage, HumanMessage
from core.config import settings
import logging

logger = logging.getLogger(__name__)

# Initialize model
llm = ChatGoogleGenerativeAI(
    model="gemini-2.5-flash",
    google_api_key=settings.GEMINI_API_KEY,
    temperature=0.3
) if settings.GEMINI_API_KEY else None

async def call_gemini(prompt: str, system_prompt: str = "") -> str:
    if not llm:
        logger.warning("No Gemini API key found. Returning mock response.")
        if "quality_score" in prompt or "analyze" in prompt.lower():
            return '{"abstract_quality_score": 8, "clarity_score": 7, "novelty_score": 9, "structure_score": 8, "completeness_score": 7, "abstract_feedback": "Good but could be clearer.", "extracted_keywords": ["AI", "Research"], "improvement_suggestions": ["Add method details"], "journal_recommendations": [{"journal_name": "Demo", "reason": "Good match", "match_score": 9}] }'
        elif "fit" in prompt.lower():
            return '{"fit_score": 85, "explanation": "Good fit because of overlapping domain."}'
        else:
            return "This is a mock AI response since GEMINI_API_KEY is not set."
            
    try:
        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=prompt)
        ]
        response = await llm.ainvoke(messages)
        return response.content
    except Exception as e:
        logger.error(f"Error calling Gemini via LangChain: {e}")
        raise e
