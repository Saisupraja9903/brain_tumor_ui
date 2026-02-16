# Brain Tumor Detection Backend

A professional, production-ready FastAPI backend for brain tumor detection using deep learning.

## Features

- **FastAPI Framework**: Modern, fast, and easy-to-use Python web framework
- **ML Model Integration**: TensorFlow/Keras model loading and inference
- **Image Processing**: Automatic image validation and preprocessing
- **RESTful API**: Clean API design with multiple endpoints
- **CORS Support**: Configured for frontend integration
- **Error Handling**: Comprehensive error handling with detailed logging
- **Request Validation**: Pydantic models for request/response validation
- **Async Operations**: Async file handling for better performance
- **Request Tracking**: Unique request IDs for debugging
- **Interactive Documentation**: Auto-generated API documentation
- **Health Checks**: Model and service health monitoring

## Project Structure

```
backend/
├── main.py              # FastAPI application
├── config.py            # Configuration management
├── models.py            # Request/response schemas
├── utils.py             # Utility functions for ML
├── run.py               # Entry point to run the server
├── requirements.txt     # Python dependencies
├── .env.example         # Environment variables template
├── .gitignore          # Git ignore rules
├── README.md           # This file
├── logs/               # Application logs (created at runtime)
└── uploads/            # Uploaded images (created at runtime)
```

## Installation

### Prerequisites

- Python 3.8+
- pip or conda

### Setup

1. **Create and activate virtual environment:**

```bash
# Windows
python -m venv venv
venv\Scripts\activate

# macOS/Linux
python3 -m venv venv
source venv/bin/activate
```

2. **Install dependencies:**

```bash
pip install -r requirements.txt
```

3. **Configure environment:**

```bash
# Copy the example env file
cp .env.example .env

# Edit .env with your settings
# Make sure MODEL_PATH points to your trained model
```

4. **Create necessary directories:**

```bash
mkdir logs
mkdir uploads
```

## Configuration

Edit `.env` file to customize:

```env
# API Configuration
API_HOST=0.0.0.0
API_PORT=5000
DEBUG=False

# Frontend CORS
FRONTEND_URL=http://localhost:3000

# Model Configuration
MODEL_PATH=../models/cnn-parameters-improvement-23-0.91.model
MODEL_TYPE=h5

# File Upload
MAX_FILE_SIZE_MB=10
ALLOWED_EXTENSIONS=jpg,jpeg,png

# Image Processing
IMAGE_SIZE=150
NORMALIZE_IMAGES=True

# Logging
LOG_LEVEL=INFO
LOG_FILE=logs/app.log

# Environment
ENV=development
```

## Running the Server

### Development Mode

```bash
python run.py
```

The server will start at `http://localhost:5000`

### Production Mode

```bash
# Set DEBUG=False in .env
# Use a production ASGI server like Gunicorn and Uvicorn:

pip install gunicorn

gunicorn -w 4 -k uvicorn.workers.UvicornWorker main:app --bind 0.0.0.0:5000
```

## API Endpoints

### Health Check

```http
GET /health
```

Returns API and model health status.

### Upload Image

```http
POST /api/v1/upload
Content-Type: multipart/form-data

file: <image_file>
```

Uploads an MRI scan image.

**Response:**
```json
{
    "image_id": "uuid-12345",
    "filename": "brain_scan.jpg",
    "file_size": 102400,
    "upload_path": "uploads/uuid-12345.jpg",
    "message": "Image uploaded successfully"
}
```

### Predict Brain Tumor

```http
POST /api/v1/predict?image_id=uuid-12345
```

Performs brain tumor prediction on an uploaded image.

**Response:**
```json
{
    "image_id": "uuid-12345",
    "prediction": "tumor",
    "confidence": 95.5,
    "probability": {
        "tumor": 0.955,
        "no_tumor": 0.045
    },
    "timestamp": "2024-01-01T12:00:00",
    "model_version": "1.0.0"
}
```

### Analyze Image (Combined)

```http
POST /api/v1/analyze
Content-Type: multipart/form-data

file: <image_file>
```

Uploads and analyzes image in one request.

**Response:** Same as predict endpoint

## API Documentation

Once the server is running, visit:

- **Swagger UI**: http://localhost:5000/api/docs
- **ReDoc**: http://localhost:5000/api/redoc

## Logging

Logs are written to `logs/app.log` and console. Configure log level in `.env`:

- `DEBUG`: Detailed diagnostic information
- `INFO`: General information
- `WARNING`: Warning messages
- `ERROR`: Error messages

## Error Handling

The API returns structured error responses:

```json
{
    "error": "Invalid file type",
    "status_code": 400,
    "timestamp": "2024-01-01T12:00:00"
}
```

Common error codes:
- `400`: Bad request (invalid file, wrong format)
- `404`: Not found (image not found)
- `413`: File too large
- `500`: Internal server error
- `503`: Service unavailable (model not loaded)

## Integration with Frontend

The frontend should:

1. Upload image to `/api/v1/upload`
2. Get the `image_id` from response
3. Call `/api/v1/predict?image_id=<id>` to get results

Or use the combined endpoint:

1. Call `/api/v1/analyze` with image file
2. Get prediction results immediately

## Performance Optimization

- Model is loaded once on startup (singleton pattern)
- Images are preprocessed efficiently with PIL
- Async file operations for non-blocking I/O
- CORS headers cached for faster requests

## Troubleshooting

### Model Not Loading

```
Check if:
- MODEL_PATH in .env is correct
- Model file exists at the specified path
- TensorFlow is installed: pip install tensorflow
```

### Image Upload Fails

```
Check if:
- uploads/ directory exists and is writable
- MAX_FILE_SIZE_MB is appropriate
- ALLOWED_EXTENSIONS includes the file type
```

### CORS Issues

```
Update FRONTEND_URL in .env to match your frontend URL
```

## Development

### Add Custom Endpoints

Edit `main.py` to add new routes:

```python
@app.post("/api/v1/custom")
async def custom_endpoint():
    return {"message": "Custom endpoint"}
```

### Modify Image Processing

Edit `ImageProcessor` in `utils.py` to change preprocessing:

```python
@staticmethod
def preprocess_image(image_path: str) -> np.ndarray:
    # Your custom preprocessing logic
    pass
```

## Security Considerations

- Validate all file uploads (type, size)
- Set `DEBUG=False` in production
- Use environment variables for sensitive config
- Implement rate limiting for production
- Add authentication if needed

## Dependencies

See `requirements.txt` for complete list:

- fastapi: Web framework
- uvicorn: ASGI server
- tensorflow: Machine learning
- pillow: Image processing
- opencv: Computer vision
- pydantic: Data validation
- python-dotenv: Environment management

## License

MIT

## Support

For issues, check logs in `logs/app.log` or contact the development team.
