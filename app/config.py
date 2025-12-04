"""
Application configuration
"""
from pydantic_settings import BaseSettings
from pathlib import Path


class Settings(BaseSettings):
    """Application settings"""

    # FastAPI
    FASTAPI_HOST: str = "0.0.0.0"
    FASTAPI_PORT: int = 8000
    DEBUG: bool = True

    # Neo4j (Future)
    NEO4J_URI: str = "bolt://localhost:7687"
    NEO4J_USER: str = "neo4j"
    NEO4J_PASSWORD: str = "password"

    # Liases Foras API (Future)
    LIASES_FORAS_API_KEY: str = ""
    LF_DATA_VERSION: str = "Q3_FY25"

    # Claude AI (Future)
    CLAUDE_API_KEY: str = ""

    # Gemini AI for LLM-based QA
    GEMINI_API_KEY: str = "AIzaSyAG33P0W7MaScsX7VJxBy-dPJiiIbZ_XhM"

    # Google APIs for Context Panel
    GOOGLE_MAPS_API_KEY: str = ""
    GOOGLE_SEARCH_API_KEY: str = ""
    GOOGLE_SEARCH_CX: str = ""
    OPENWEATHER_API_KEY: str = ""

    # Government of India Data APIs
    GOV_IN_API_KEY: str = ""
    GOV_IN_API_BASE_URL: str = "https://api.data.gov.in"

    # NewsData.io API for location-based news
    NEWSDATA_API_KEY: str = ""
    NEWSDATA_API_BASE_URL: str = "https://newsdata.io/api/1"

    # Data Sources
    DATA_PATH: str = "./data"
    MOCK_DATA_ENABLED: bool = True

    # Vector Database
    CHROMA_DB_PATH: str = "data/chroma_db"

    # Project root
    PROJECT_ROOT: Path = Path(__file__).parent.parent

    class Config:
        env_file = ".env"
        case_sensitive = True


# Global settings instance
settings = Settings()
