import os
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    DATABASE_URL: str = Field(default="sqlite:///./satypath.db", env="DATABASE_URL")
    UPLOAD_DIR: str = Field(default="./uploads", env="UPLOAD_DIR")
    OCR_ENABLED: bool = Field(default=False, env="OCR_ENABLED")
    TESSERACT_CMD: str = Field(default="tesseract", env="TESSERACT_CMD")
    model_config = SettingsConfigDict(env_file=".env")

settings = Settings()

# Ensure upload directory exists
os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
