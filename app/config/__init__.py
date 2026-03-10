"""
Configuration module for Liases Foras application
"""

from .defaults import defaults, DefaultConfig

# Create a settings instance for backward compatibility
class Settings:
    """Settings wrapper for backward compatibility"""
    def __init__(self):
        self.DEBUG = True
        self.EMBEDDING_MODEL = "sentence-transformers/all-MiniLM-L6-v2"
        self.CHROMA_COLLECTION_NAME = "liases_foras_docs"
        self.CHROMA_PERSIST_DIR = "./data/chroma_db"
        self.DATA_PATH = "./data"
        self.GOOGLE_MAPS_API_KEY = None
        self.GOOGLE_SEARCH_API_KEY = None
        self.GOOGLE_SEARCH_CX = None
        self.OPENWEATHER_API_KEY = None
        # Add other settings as needed

settings = Settings()

# City Data Configuration (location-agnostic data mapping)
CITY_DATA_CONFIG = {
    "Pune": {
        "data_file": "extracted/v4_clean_nested_structure.json",
        "format": "v4_nested",
        "regions": ["Chakan", "Baner", "Hinjewadi"],
        "default_region": "Chakan"
    },
    "Kolkata": {
        "data_file": "extracted/kolkata/kolkata_v4_enriched.json",  # Enriched: unitMixBreakdown + priceRangeDistribution (960KB)
        "format": "v4_nested_enriched",
        "regions": ["New Town", "Rajarhat", "E-M Bypass", "Salt Lake", "Park Street"],
        "default_region": "New Town"
    }
}

__all__ = ["defaults", "DefaultConfig", "settings", "CITY_DATA_CONFIG"]