import os
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    PROJECT_NAME: str = "Forma3D API"
    VERSION: str = "0.1.0"
    API_V1_STR: str = "/api/v1"
    LOG_LEVEL: str = "INFO"
    
    # Storage paths
    BASE_DIR: str = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    UPLOAD_DIR: str = os.path.join(BASE_DIR, "storage", "uploads")
    OUTPUT_DIR: str = os.path.join(BASE_DIR, "storage", "outputs")

    # Rate limiting (in-memory defaults suitable for single-instance deployments)
    RATE_LIMIT_UPLOAD_MAX_REQUESTS: int = 30
    RATE_LIMIT_UPLOAD_WINDOW_SECONDS: int = 60

    # Docs/metadata
    DOCS_URL: str = "/docs"
    REDOC_URL: str = "/redoc"
    OPENAPI_URL: str = "/openapi.json"

    class Config:
        case_sensitive = True

settings = Settings()

# Ensure directories exist
os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
os.makedirs(settings.OUTPUT_DIR, exist_ok=True)
