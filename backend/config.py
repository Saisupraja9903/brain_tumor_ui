import os
from typing import Optional
from functools import lru_cache
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings and configuration."""
    
    # API Configuration
    api_host: str = os.getenv("API_HOST", "0.0.0.0")
    api_port: int = int(os.getenv("API_PORT", 5000))
    debug: bool = os.getenv("DEBUG", "False").lower() == "true"
    env: str = os.getenv("ENV", "development")
    
    # Frontend CORS
    frontend_url: str = os.getenv("FRONTEND_URL", "http://localhost:3000")
    
    # Model Configuration
    model_path: str = os.getenv("MODEL_PATH", "../models/cnn-parameters-improvement-23-0.91.model")
    model_type: str = os.getenv("MODEL_TYPE", "h5")
    
    # File Upload Configuration
    max_file_size_mb: int = int(os.getenv("MAX_FILE_SIZE_MB", 10))
    # store as a raw string to avoid pydantic attempting to json-decode
    # Allowed formats: jpg, jpeg, png, jfif (JPEG with different extension), gif, bmp, webp, tiff
    allowed_extensions: str = os.getenv("ALLOWED_EXTENSIONS", "jpg,jpeg,png,jfif,gif,bmp,webp,tiff,tif")
    
    # Image Processing
    image_size: int = int(os.getenv("IMAGE_SIZE", 150))
    normalize_images: bool = os.getenv("NORMALIZE_IMAGES", "True").lower() == "true"
    
    # Logging
    log_level: str = os.getenv("LOG_LEVEL", "INFO")
    log_file: str = os.getenv("LOG_FILE", "logs/app.log")
    
    # Paths
    base_dir: str = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    upload_dir: str = os.path.join(base_dir, "uploads")
    models_dir: str = os.path.join(base_dir, "models")
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

    def get_absolute_model_path(self) -> str:
        """Get absolute path to the model file."""
        if os.path.isabs(self.model_path):
            return self.model_path
        return os.path.join(self.base_dir, self.model_path)

    def get_allowed_extensions(self) -> list:
        """Return allowed extensions as a normalized list."""
        if not self.allowed_extensions:
            return []
        return [e.strip().lower() for e in str(self.allowed_extensions).split(",") if e.strip()]


@lru_cache
def get_settings() -> Settings:
    """Cached settings singleton."""
    return Settings()
