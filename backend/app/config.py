"""Application configuration"""
from pydantic_settings import BaseSettings
from typing import List

class Settings(BaseSettings):
    # Database
    database_url: str
    
    # Supabase
    supabase_url: str
    supabase_service_key: str
    
    # Authentication
    secret_key: str
    admin_email: str
    admin_password: str
    access_token_expire_minutes: int = 1440  # 24 hours
    
    # CORS
    cors_origins: List[str] = ["http://localhost:3000", "https://your-app.vercel.app"]
    
    # Storage
    storage_bucket: str = "pharma-publications"
    
    class Config:
        env_file = ".env"

settings = Settings()
