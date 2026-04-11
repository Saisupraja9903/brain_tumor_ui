import os
import logging
import uuid
from datetime import datetime
from typing import Optional
from fastapi import FastAPI, File, UploadFile, HTTPException, status, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from ultralytics import YOLO
import aiofiles
import cv2
import numpy as np

# Register image formats with PIL/Pillow
try:
    from PIL import Image, JpegImagePlugin
    # Register JFIF as a JPEG format
    Image.register_open(JpegImagePlugin.JpegImageFile.format, JpegImagePlugin.JpegImageFile, lambda p: p)
    Image.register_extension('.jfif', JpegImagePlugin.JpegImageFile.format)
    Image.register_mime('image/jpeg', '.jfif')
except ImportError:
    # Pillow is a dependency, but handle case where it's not installed
    pass
except Exception as e:
    # Handle registration errors
    logging.warning(f"Could not fully register JFIF format: {e}")
from config import get_settings
from models import PredictionResponse, UploadResponse, ErrorResponse, HealthResponse
from utils import (
    ModelLoader,
    ImageProcessor,
    Predictor,
    validate_file_extension,
    get_file_size_mb,
    ensure_upload_dir_exists,
    ensure_logs_dir_exists,
)

# Configuration
settings = get_settings()

# Ensure directories exist
ensure_upload_dir_exists()
ensure_logs_dir_exists()

# Setup logging
logging.basicConfig(
    level=settings.log_level,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler(settings.log_file),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

yolo_path = settings.get_absolute_yolo_model_path()
fallback_yolo_path = os.path.join(settings.base_dir, "brain_classifier.pt")

if os.path.exists(yolo_path):
    brain_model = YOLO(yolo_path)
    logger.info(f"YOLO validation model loaded successfully from {yolo_path}")
elif os.path.exists(fallback_yolo_path):
    brain_model = YOLO(fallback_yolo_path)
    logger.info(f"YOLO validation model loaded successfully from fallback path: {fallback_yolo_path}")
else:
    logger.warning(f"YOLO model not found at {yolo_path} or {fallback_yolo_path}! "
                   "YOLO validation will be disabled. Will use PIL fallback validation only.")
    brain_model = None

# Initialize FastAPI app
app = FastAPI(
    title="Brain Tumor Detection API",
    description="API for detecting brain tumors from MRI scan images using deep learning",
    version="1.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.frontend_url, "http://localhost:3000", "http://localhost:3001"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Load model on startup
try:
    ModelLoader.load_model()
    model_loaded = ModelLoader.is_model_loaded()
    if model_loaded:
        logger.info("Model loaded successfully on startup")
    else:
        logger.warning("Model not loaded on startup, using dummy predictions")
except Exception as e:
    logger.error(f"Failed to load model on startup: {str(e)}")
    model_loaded = False


@app.on_event("startup")
async def startup_event():
    """Handle startup events."""
    logger.info("Application starting...")
    logger.info(f"Environment: {settings.env}")
    logger.info(f"Frontend URL: {settings.frontend_url}")
    logger.info(f"Model Path: {settings.get_absolute_model_path()}")


@app.on_event("shutdown")
async def shutdown_event():
    """Handle shutdown events."""
    logger.info("Application shutting down...")


# ============================================================================
# Health Check Endpoints
# ============================================================================

@app.get(
    "/health",
    response_model=HealthResponse,
    summary="Health Check",
    tags=["Health"]
)
async def health_check() -> HealthResponse:
    """
    Check API health and model status.
    
    Returns:
        HealthResponse: API health status and model availability
    """
    return HealthResponse(
        status="healthy",
        version="1.0.0",
        model_loaded=model_loaded,
        environment=settings.env
    )


# ============================================================================
# Image Upload Endpoints
# ============================================================================

@app.post(
    "/api/v1/upload",
    response_model=UploadResponse,
    summary="Upload MRI Image",
    tags=["Upload"],
    status_code=status.HTTP_201_CREATED
)
async def upload_image(file: UploadFile = File(...)) -> UploadResponse:
    """
    Upload an MRI scan image for analysis.
    
    Args:
        file: Image file (JPG, JPEG, PNG)
        
    Returns:
        UploadResponse: Upload status and image ID
        
    Raises:
        HTTPException: If file is invalid or upload fails
    """
    request_id = str(uuid.uuid4())
    
    try:
        # Validate file extension
        if not validate_file_extension(file.filename):
            logger.warning(f"[{request_id}] Invalid file extension: {file.filename}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid file type. Allowed types: {', '.join(settings.get_allowed_extensions())}"
            )
        
        # Generate unique image ID
        image_id = str(uuid.uuid4())
        
        file_ext = file.filename.rsplit('.', 1)[1].lower()
        stored_filename = f"{image_id}.{file_ext}"
        file_path = os.path.join(settings.upload_dir, stored_filename)
        
        # Save file
        async with aiofiles.open(file_path, 'wb') as f:
            contents = await file.read()
            await f.write(contents)
        
        # Validate saved file
        if not ImageProcessor.validate_image_file(file_path):
            os.remove(file_path)
            logger.warning(f"[{request_id}] Uploaded file is not a valid image")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="File is not a valid image"
            )
        
        # Get file size
        file_size = get_file_size_mb(file_path)
        if file_size > settings.max_file_size_mb:
            os.remove(file_path)
            logger.warning(f"[{request_id}] File size exceeds limit")
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail=f"File size exceeds {settings.max_file_size_mb}MB limit"
            )
        
        logger.info(f"[{request_id}] Image uploaded successfully: {stored_filename}")
        
        return UploadResponse(
            image_id=image_id,
            filename=file.filename,
            file_size=len(contents),
            upload_path=f"uploads/{stored_filename}"
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[{request_id}] Upload failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to upload image"
        )


# ============================================================================
# Prediction Endpoints
# ============================================================================

@app.post(
    "/api/v1/predict",
    response_model=PredictionResponse,
    summary="Predict Brain Tumor",
    tags=["Prediction"]
)
async def predict_tumor(image_id: str) -> PredictionResponse:
    """
    Perform brain tumor prediction on an uploaded image.
    
    Args:
        image_id: ID of the uploaded image
        
    Returns:
        PredictionResponse: Prediction results with confidence
        
    Raises:
        HTTPException: If image not found or prediction fails
    """
    request_id = str(uuid.uuid4())
    
    try:
        # Find the image file
        image_path = None
        for file in os.listdir(settings.upload_dir):
            if file.startswith(image_id):
                image_path = os.path.join(settings.upload_dir, file)
                break
        
        if not image_path or not os.path.exists(image_path):
            logger.warning(f"[{request_id}] Image not found: {image_id}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Image with ID {image_id} not found"
            )
        
        # Make prediction
        logger.info(f"[{request_id}] Performing prediction on image {image_id}")
        predictor = Predictor()
        result = predictor.predict(image_path)
        
        logger.info(f"[{request_id}] Prediction completed: {result['prediction']} ({result['confidence']:.2f}%)")
        
        return PredictionResponse(
            image_id=image_id,
            prediction=result["prediction"],
            confidence=result["confidence"],
            probability=result["probability"]
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[{request_id}] Prediction failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to process prediction"
        )


@app.post(
    "/api/v1/analyze",
    response_model=PredictionResponse,
    summary="Upload and Analyze Image",
    tags=["Prediction"]
)
async def analyze_image(file: UploadFile = File(...)) -> PredictionResponse:
    """
    Combined endpoint: Upload image and immediately get prediction.
    
    Args:
        file: Image file (JPG, JPEG, PNG)
        
    Returns:
        PredictionResponse: Prediction results
        
    Raises:
        HTTPException: If file is invalid or analysis fails
    """
    request_id = str(uuid.uuid4())
    
    try:
        # Validate and save file
        if not validate_file_extension(file.filename):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid file type. Allowed types: {', '.join(settings.get_allowed_extensions())}"
            )
        
        image_id = str(uuid.uuid4())
        file_ext = file.filename.rsplit('.', 1)[1].lower()
        stored_filename = f"{image_id}.{file_ext}"
        file_path = os.path.join(settings.upload_dir, stored_filename)
        
        contents = await file.read()
        
        # Validate file size
        file_size_mb = len(contents) / (1024 * 1024)
        if file_size_mb > settings.max_file_size_mb:
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail=f"File size exceeds {settings.max_file_size_mb}MB limit"
            )
        
        # Save file
        async with aiofiles.open(file_path, 'wb') as f:
            await f.write(contents)

        logger.info(f"[{request_id}] Analyzing image: {stored_filename}")

        # 1. Face Detection (Reject immediately if human face)
        face_detected = False
        try:
            # Safely load OpenCV haarcascade (checks system library then local path)
            cascade_path = cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
            face_cascade = cv2.CascadeClassifier(cascade_path)
            if face_cascade.empty():
                face_cascade = cv2.CascadeClassifier('haarcascade_frontalface_default.xml')
                
            img_cv = cv2.imread(file_path, cv2.IMREAD_GRAYSCALE)
            if img_cv is not None and not face_cascade.empty():
                faces = face_cascade.detectMultiScale(img_cv, scaleFactor=1.1, minNeighbors=5, minSize=(30, 30))
                if len(faces) > 0:
                    face_detected = True
        except Exception as e:
            logger.warning(f"[{request_id}] Face detection error: {str(e)}")

        logger.debug(f"[{request_id}] Face detected: {face_detected}")

        if face_detected:
            if os.path.exists(file_path):
                os.remove(file_path)
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Please upload MRI scan, not a brain image"
            )

        # 2. YOLO validation (label + confidence)
        is_brain_yolo = False
        if brain_model is not None:
            try:
                results = brain_model(file_path)
                label_index = int(results[0].probs.top1)
                label = results[0].names[label_index]
                confidence = float(results[0].probs.top1conf)
                
                logger.debug(f"[{request_id}] YOLO Predicted Label: {label}")
                logger.debug(f"[{request_id}] YOLO Confidence Score: {confidence:.4f}")

                # Fast rejection for explicitly bad non-MRI labels
                if any(bad in label.lower() for bad in ["person", "face", "object", "unknown"]):
                    if os.path.exists(file_path):
                        os.remove(file_path)
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="Only brain MRI images are allowed"
                    )
                
                # Accept if confidently classified as brain
                if label == "brain" and confidence >= 0.75:
                    is_brain_yolo = True
                    
            except HTTPException:
                raise
            except Exception as e:
                logger.error(f"[{request_id}] YOLO validation error: {str(e)}")
        else:
            logger.info(f"[{request_id}] YOLO model unavailable, skipping YOLO validation.")

        # 3. MRI grayscale structure validation (PIL + numpy)
        is_mri_structure = False
        try:
            with Image.open(file_path) as img:
                img_gray = img.convert('L')
                width, height = img.size
                aspect_ratio = width / height
                
                arr = np.array(img_gray)
                std_dev = np.std(arr)
                
            logger.debug(f"[{request_id}] MRI Structure Check - Std Dev: {std_dev:.2f}, Aspect Ratio: {aspect_ratio:.2f}")
            
            if (5 <= std_dev <= 80) and (0.5 <= aspect_ratio <= 1.5):
                is_mri_structure = True
        except Exception as e:
            logger.error(f"[{request_id}] MRI structure validation error: {str(e)}")

        logger.debug(f"[{request_id}] Validation Results -> YOLO: {is_brain_yolo}, MRI Structure: {is_mri_structure}")

        # 4. Hybrid Validation Logic
        if not (is_brain_yolo or is_mri_structure):
            if os.path.exists(file_path):
                os.remove(file_path)
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid MRI scan. Please upload a proper brain MRI image."
            )

        # 5. Then tumor prediction
        predictor = Predictor()
        result = predictor.predict(file_path)
        
        logger.info(f"[{request_id}] Analysis completed: {result['prediction']} ({result['confidence']:.2f}%)")
        
        return PredictionResponse(
            image_id=image_id,
            prediction=result["prediction"],
            confidence=result["confidence"],
            probability=result["probability"]
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[{request_id}] Analysis failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to analyze image"
        )


# ============================================================================
# Root Endpoint
# ============================================================================

@app.get(
    "/",
    summary="API Information",
    tags=["Info"]
)
async def root():
    """Get API information and documentation links."""
    return {
        "message": "Brain Tumor Detection API",
        "version": "1.0.0",
        "status": "running",
        "docs": "/api/docs",
        "endpoints": {
            "health": "/health",
            "upload": "/api/v1/upload",
            "predict": "/api/v1/predict",
            "analyze": "/api/v1/analyze"
        }
    }


# ============================================================================
# Exception Handlers
# ============================================================================

@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    """Custom HTTP exception handler."""
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": exc.detail,
            "status_code": exc.status_code,
            "timestamp": datetime.utcnow().isoformat()
        }
    )


@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    """Custom general exception handler."""
    logger.error(f"Unhandled exception: {str(exc)}")
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": "Internal server error",
            "status_code": 500,
            "timestamp": datetime.utcnow().isoformat()
        }
    )
