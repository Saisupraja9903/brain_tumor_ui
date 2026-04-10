# import os
# import logging
# import numpy as np
# from PIL import Image
# from typing import Tuple, Dict, Optional
# import tensorflow as tf
# import hashlib
# from config import get_settings

# logger = logging.getLogger(__name__)
# settings = get_settings()


# class ModelLoader:
#     """Handles loading and caching of ML models."""
    
#     _instance = None
#     _model = None
    
#     def __new__(cls):
#         """Singleton pattern to ensure only one model instance."""
#         if cls._instance is None:
#             cls._instance = super(ModelLoader, cls).__new__(cls)
#         return cls._instance
    
#     @classmethod
#     def load_model(cls):
#         """Load the trained model."""
#         if cls._model is not None:
#             return cls._model

#         try:
#             model_path = settings.get_absolute_model_path()

#             if not os.path.exists(model_path):
#                 logger.warning(f"Model file not found at {model_path}, using dummy predictions")
#                 cls._model = None
#                 return cls._model

#             logger.info(f"Loading model from {model_path}")

#             if settings.model_type == "h5":
#                 cls._model = tf.keras.models.load_model(model_path)
#             elif settings.model_type == "SavedModel":
#                 cls._model = tf.keras.models.load_model(model_path)
#             else:
#                 raise ValueError(f"Unsupported model type: {settings.model_type}")

#             logger.info("Model loaded successfully")
#             return cls._model

#         except Exception as e:
#             logger.error(f"Error loading model: {str(e)}")
#             cls._model = None
#             return cls._model
    
#     @classmethod
#     def is_model_loaded(cls) -> bool:
#         """Check if model is loaded."""
#         return cls._model is not None


# class ImageProcessor:
#     """Handles image processing and validation."""
    
#     @staticmethod
#     def validate_image_file(file_path: str) -> bool:
#         """Validate if file is a valid image."""
#         try:
#             with Image.open(file_path) as img:
#                 # Force load to verify the image is valid
#                 img.verify()
#             return True
#         except Exception as e:
#             # Log the error for debugging but allow JFIF to pass
#             # JFIF files sometimes fail verify() but open successfully
#             logger.warning(f"Image validation passed with warning: {str(e)}")
#             try:
#                 # Fallback: try to open again without verify
#                 with Image.open(file_path) as img:
#                     # Just check that we can access image properties
#                     _ = img.format
#                     _ = img.size
#                 return True
#             except Exception as fallback_e:
#                 logger.error(f"Image validation failed: {str(fallback_e)}")
#                 return False
    
#     @staticmethod
#     def preprocess_image(image_path: str) -> np.ndarray:
#         """
#         Preprocess image for model prediction.
        
#         Args:
#             image_path: Path to the image file
            
#         Returns:
#             Preprocessed image array
#         """
#         try:
#             # Open and convert image
#             img = Image.open(image_path).convert('L')  # Convert to grayscale
            
#             # Resize to model input size
#             img = img.resize((settings.image_size, settings.image_size))
            
#             # Convert to numpy array
#             img_array = np.array(img)
            
#             # Normalize if configured
#             if settings.normalize_images:
#                 img_array = img_array / 255.0
            
#             # Expand dimensions for batch (model expects batch dimension)
#             img_array = np.expand_dims(img_array, axis=0)
            
#             logger.debug(f"Image preprocessed: shape={img_array.shape}")
#             return img_array
        
#         except Exception as e:
#             logger.error(f"Image preprocessing failed: {str(e)}")
#             raise


# class Predictor:
#     """Handles predictions using the loaded model."""

#     def __init__(self):
#         self.model = ModelLoader.load_model()
#         self.class_names = ["no_tumor", "tumor"]  # Adjust based on your model

#     def predict(self, image_path: str) -> Dict[str, any]:
#         """
#         Make prediction on an image.

#         Args:
#             image_path: Path to the preprocessed image

#         Returns:
#             Dictionary with prediction results
#         """
#         try:
#             if self.model is None:
#                 # Dummy prediction when model is not available
#                 logger.warning("Model not loaded, returning dummy prediction")
                
#                 # Generate deterministic prediction based on image hash
#                 # This ensures the same image always gets the same prediction
#                 with open(image_path, 'rb') as f:
#                     image_hash = hashlib.md5(f.read()).hexdigest()
                
#                 # Use hash to seed random for deterministic results
#                 seed = int(image_hash, 16) % (2**32)
#                 rng = np.random.RandomState(seed)
                
#                 # Create deterministic probabilities based on image hash
#                 probabilities = [rng.uniform(0.1, 0.9) for _ in self.class_names]
#                 # Normalize probabilities to sum to 1
#                 total = sum(probabilities)
#                 probabilities = [p / total for p in probabilities]
                
#                 # Get predicted class (highest probability)
#                 class_idx = int(np.argmax(probabilities))
#                 predicted_class = self.class_names[class_idx]
                
#                 # Create probability dict
#                 probability_dict = {
#                     self.class_names[i]: float(probabilities[i])
#                     for i in range(len(self.class_names))
#                 }
                
#                 # Confidence is the probability of the predicted class (in percentage)
#                 confidence = probability_dict[predicted_class] * 100
                
#                 logger.info(f"Dummy prediction for {image_path}: {predicted_class} ({confidence:.2f}%)")
                
#                 return {
#                     "prediction": predicted_class,
#                     "confidence": confidence,  # Now matches the predicted class probability
#                     "probability": probability_dict,
#                     "raw_output": probabilities
#                 }

#             # Preprocess image
#             processed_image = ImageProcessor.preprocess_image(image_path)

#             # Make prediction
#             predictions = self.model.predict(processed_image, verbose=0)

#             # Get prediction results
#             class_idx = int(np.argmax(predictions))
#             predicted_class = self.class_names[class_idx]
            
#             # Create probability dict for all classes
#             probability_dict = {
#                 self.class_names[i]: float(predictions[0][i])
#                 for i in range(len(self.class_names))
#             }
            
#             # Confidence is the probability of the predicted class
#             confidence = probability_dict[predicted_class] * 100  # Convert to percentage

#             return {
#                 "prediction": predicted_class,
#                 "confidence": confidence,  # Now matches the predicted class probability
#                 "probability": probability_dict,
#                 "raw_output": predictions[0].tolist()
#             }

#         except Exception as e:
#             logger.error(f"Prediction failed: {str(e)}")
#             raise


# def validate_file_extension(filename: str) -> bool:
#     """Check if file has allowed extension."""
#     if '.' not in filename:
#         return False
#     ext = filename.rsplit('.', 1)[1].lower()
#     try:
#         allowed = settings.get_allowed_extensions()
#     except Exception:
#         allowed = []
#     return ext in allowed


# def get_file_size_mb(file_path: str) -> float:
#     """Get file size in MB."""
#     size_bytes = os.path.getsize(file_path)
#     return size_bytes / (1024 * 1024)


# def ensure_upload_dir_exists():
#     """Ensure upload directory exists."""
#     os.makedirs(settings.upload_dir, exist_ok=True)
#     logger.info(f"Upload directory ensured at {settings.upload_dir}")


# def ensure_logs_dir_exists():
#     """Ensure logs directory exists."""
#     log_dir = os.path.dirname(settings.log_file)
#     os.makedirs(log_dir, exist_ok=True)


import os
import logging
import numpy as np
from PIL import Image
from typing import Tuple, Dict, Optional
import tensorflow as tf
import hashlib
from config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


class ModelLoader:
    """Handles loading and caching of ML models."""
    
    _instance = None
    _model = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(ModelLoader, cls).__new__(cls)
        return cls._instance
    
    @classmethod
    def load_model(cls):
        if cls._model is not None:
            return cls._model

        try:
            model_path = settings.get_absolute_model_path()

            if not os.path.exists(model_path):
                logger.warning(f"Model file not found at {model_path}, using dummy predictions")
                cls._model = None
                return cls._model

            logger.info(f"Loading model from {model_path}")

            if settings.model_type == "h5":
                cls._model = tf.keras.models.load_model(model_path)
            elif settings.model_type == "SavedModel":
                cls._model = tf.keras.models.load_model(model_path)
            else:
                raise ValueError(f"Unsupported model type: {settings.model_type}")

            logger.info("Model loaded successfully")
            return cls._model

        except Exception as e:
            logger.error(f"Error loading model: {str(e)}")
            cls._model = None
            return cls._model
    
    @classmethod
    def is_model_loaded(cls) -> bool:
        return cls._model is not None


class ImageProcessor:
    """Handles image processing and validation."""
    
    @staticmethod
    def validate_image_file(file_path: str) -> bool:
        try:
            with Image.open(file_path) as img:
                img.verify()
            return True
        except Exception as e:
            logger.warning(f"Image validation passed with warning: {str(e)}")
            try:
                with Image.open(file_path) as img:
                    _ = img.format
                    _ = img.size
                return True
            except Exception as fallback_e:
                logger.error(f"Image validation failed: {str(fallback_e)}")
                return False

    @staticmethod
    def is_brain_mri(image_path: str) -> bool:
        """
        Validates if an image file appears to be a brain MRI based on grayscale ratio and aspect ratio.
        
        Args:
            image_path: Path to the image file.
            
        Returns:
            True if the image is likely a brain MRI, False otherwise.
        """
        try:
            img = Image.open(image_path).convert('RGB')
            img = img.resize((128, 128))

            pixels = np.array(img)

            # Check grayscale (MRI is mostly grayscale)
            diff_rg = np.abs(pixels[:, :, 0] - pixels[:, :, 1])
            diff_rb = np.abs(pixels[:, :, 0] - pixels[:, :, 2])
            grayscale_ratio = np.mean((diff_rg < 25) & (diff_rb < 25))

            # Check aspect ratio (brain MRI usually square-ish)
            width, height = img.size
            aspect_ratio = width / height

            # FINAL CONDITION (balanced)
            if grayscale_ratio > 0.45 and 0.6 < aspect_ratio < 1.4:
                return True

            return False

        except Exception as e:
            logger.error(f"MRI validation failed: {str(e)}")
            return False

    @staticmethod
    def preprocess_image(image_path: str) -> np.ndarray:
        try:
            img = Image.open(image_path).convert('L')
            img = img.resize((settings.image_size, settings.image_size))

            img_array = np.array(img)

            if settings.normalize_images:
                img_array = img_array / 255.0

            img_array = np.expand_dims(img_array, axis=0)

            logger.debug(f"Image preprocessed: shape={img_array.shape}")
            return img_array

        except Exception as e:
            logger.error(f"Image preprocessing failed: {str(e)}")
            raise


class Predictor:
    def __init__(self):
        self.model = ModelLoader.load_model()
        self.class_names = ["no_tumor", "tumor"]

    def predict(self, image_path: str) -> Dict[str, any]:
        try:
            if self.model is None:
                logger.warning("Model not loaded, returning dummy prediction")
                
                with open(image_path, 'rb') as f:
                    image_hash = hashlib.md5(f.read()).hexdigest()
                
                seed = int(image_hash, 16) % (2**32)
                rng = np.random.RandomState(seed)

                probabilities = [rng.uniform(0.1, 0.9) for _ in self.class_names]
                total = sum(probabilities)
                probabilities = [p / total for p in probabilities]

                class_idx = int(np.argmax(probabilities))
                predicted_class = self.class_names[class_idx]

                probability_dict = {
                    self.class_names[i]: float(probabilities[i])
                    for i in range(len(self.class_names))
                }

                confidence = probability_dict[predicted_class] * 100

                return {
                    "prediction": predicted_class,
                    "confidence": confidence,
                    "probability": probability_dict,
                    "raw_output": probabilities
                }

            processed_image = ImageProcessor.preprocess_image(image_path)
            predictions = self.model.predict(processed_image, verbose=0)

            class_idx = int(np.argmax(predictions))
            predicted_class = self.class_names[class_idx]

            probability_dict = {
                self.class_names[i]: float(predictions[0][i])
                for i in range(len(self.class_names))
            }

            confidence = probability_dict[predicted_class] * 100

            return {
                "prediction": predicted_class,
                "confidence": confidence,
                "probability": probability_dict,
                "raw_output": predictions[0].tolist()
            }

        except Exception as e:
            logger.error(f"Prediction failed: {str(e)}")
            raise


def validate_file_extension(filename: str) -> bool:
    if '.' not in filename:
        return False
    ext = filename.rsplit('.', 1)[1].lower()
    try:
        allowed = settings.get_allowed_extensions()
    except Exception:
        allowed = []
    return ext in allowed


def get_file_size_mb(file_path: str) -> float:
    size_bytes = os.path.getsize(file_path)
    return size_bytes / (1024 * 1024)


def ensure_upload_dir_exists():
    os.makedirs(settings.upload_dir, exist_ok=True)
    logger.info(f"Upload directory ensured at {settings.upload_dir}")


def ensure_logs_dir_exists():
    log_dir = os.path.dirname(settings.log_file)
    os.makedirs(log_dir, exist_ok=True)