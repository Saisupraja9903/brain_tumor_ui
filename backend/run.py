#!/usr/bin/env python3
"""
Entry point for the Brain Tumor Detection API server.
"""

import uvicorn
import os
import sys
from config import get_settings

if __name__ == "__main__":
    settings = get_settings()
    
    print(f"Starting Brain Tumor Detection API")
    print(f"Environment: {settings.env}")
    print(f"API Host: {settings.api_host}:{settings.api_port}")
    print(f"Frontend URL: {settings.frontend_url}")
    print(f"Model Path: {settings.get_absolute_model_path()}")
    print(f"Debug Mode: {settings.debug}")
    print("\nAPI Documentation available at:")
    print(f"  Swagger UI: http://{settings.api_host}:{settings.api_port}/api/docs")
    print(f"  ReDoc: http://{settings.api_host}:{settings.api_port}/api/redoc")
    print("\n" + "="*60)
    
    uvicorn.run(
        "main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=settings.debug,
        log_level=settings.log_level.lower()
    )
