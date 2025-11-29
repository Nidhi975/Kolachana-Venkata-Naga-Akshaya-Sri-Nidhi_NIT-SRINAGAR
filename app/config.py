"""
Configuration management for Medical Bill Extraction System
"""
from pydantic_settings import BaseSettings
from typing import Optional
import os


class Settings(BaseSettings):
    """Application settings with environment variable support"""
    
    # API Keys
    openai_api_key: Optional[str] = None
    anthropic_api_key: Optional[str] = None
    
    # Application Settings
    app_name: str = "BAJAJ HEALTH DATATHON"
    app_version: str = "1.0.0"
    debug_mode: bool = False
    
    # Processing Settings
    max_file_size_mb: int = 50
    max_pages: int = 100
    temp_dir: str = "temp"
    output_dir: str = "outputs"
    
    # OCR Settings
    tesseract_cmd: Optional[str] = None  # Auto-detect if None
    ocr_languages: str = "eng"
    ocr_confidence_threshold: float = 0.6
    
    # LLM Settings
    use_gpt4_vision: bool = True
    use_claude: bool = True
    llm_max_tokens: int = 2000
    llm_temperature: float = 0.1
    
    # Fraud Detection Settings
    benford_chi_square_threshold: float = 15.507
    font_outlier_threshold: float = 0.15
    tampering_sensitivity: float = 0.7
    
    # Validation Settings
    total_match_tolerance: float = 0.01  # 1% tolerance
    min_confidence_score: float = 0.7
    
    # API Settings
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    api_workers: int = 4
    max_concurrent_jobs: int = 10
    job_timeout_seconds: int = 300
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False


# Global settings instance
settings = Settings()

# Create necessary directories
os.makedirs(settings.temp_dir, exist_ok=True)
os.makedirs(settings.output_dir, exist_ok=True)
