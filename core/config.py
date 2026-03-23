from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional

class Settings(BaseSettings):
    DATABASE_URL: str = "sqlite:///./test.db" # Default fallback
    SUPABASE_URL: str = ""
    SUPABASE_ANON_KEY: str = ""
    SUPABASE_SERVICE_KEY: str = ""
    FIREBASE_SERVICE_ACCOUNT_JSON: str = "{}"
    GEMINI_API_KEY: Optional[str] = None
    EXA_API_KEY: Optional[str] = None
    HUGGINGFACE_API_KEY: Optional[str] = None
    FRONTEND_URL: str = "http://localhost:5173"
    UPLOAD_DIR: str = "uploads"
    
    model_config = SettingsConfigDict(
        env_file=".env", # Path relative to where main.py runs
        extra="ignore"
    )

settings = Settings()
