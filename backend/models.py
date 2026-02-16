from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
from datetime import datetime
import uuid


class PredictionResponse(BaseModel):
    """Response model for prediction results."""
    
    image_id: str = Field(..., description="Unique identifier for the uploaded image")
    prediction: str = Field(..., description="Prediction result (tumor/no_tumor)")
    confidence: float = Field(..., description="Confidence score (0-100)")
    probability: Dict[str, float] = Field(..., description="Probability for each class")
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    model_version: str = Field(default="1.0.0")
    
    class Config:
        json_schema_extra = {
            "example": {
                "image_id": "uuid-12345",
                "prediction": "tumor",
                "confidence": 95.5,
                "probability": {"tumor": 0.955, "no_tumor": 0.045},
                "timestamp": "2024-01-01T12:00:00",
                "model_version": "1.0.0"
            }
        }


class UploadResponse(BaseModel):
    """Response model for image upload."""
    
    image_id: str = Field(..., description="Unique identifier for the uploaded image")
    filename: str = Field(..., description="Original filename")
    file_size: int = Field(..., description="File size in bytes")
    upload_path: str = Field(..., description="Path where image was stored")
    message: str = Field(default="Image uploaded successfully")
    
    class Config:
        json_schema_extra = {
            "example": {
                "image_id": "uuid-12345",
                "filename": "brain_scan.jpg",
                "file_size": 102400,
                "upload_path": "uploads/uuid-12345.jpg",
                "message": "Image uploaded successfully"
            }
        }


class ErrorResponse(BaseModel):
    """Response model for errors."""
    
    error: str = Field(..., description="Error message")
    error_code: str = Field(default="UNKNOWN_ERROR")
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    request_id: Optional[str] = Field(default=None)
    details: Optional[Dict[str, Any]] = Field(default=None)
    
    class Config:
        json_schema_extra = {
            "example": {
                "error": "Invalid file type",
                "error_code": "INVALID_FILE_TYPE",
                "timestamp": "2024-01-01T12:00:00",
                "request_id": "uuid-12345",
                "details": {"allowed_types": ["jpg", "jpeg", "png"]}
            }
        }


class HealthResponse(BaseModel):
    """Response model for health check."""
    
    status: str = Field(default="healthy")
    version: str = Field(default="1.0.0")
    model_loaded: bool = Field(...)
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    environment: str = Field(...)
    
    class Config:
        json_schema_extra = {
            "example": {
                "status": "healthy",
                "version": "1.0.0",
                "model_loaded": True,
                "timestamp": "2024-01-01T12:00:00",
                "environment": "development"
            }
        }
