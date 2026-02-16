import axios, { AxiosError } from 'axios';

// Types
export interface UploadResponse {
  image_id: string;
  filename: string;
  file_size: number;
  upload_path: string;
  message: string;
}

export interface PredictionResponse {
  image_id: string;
  prediction: string;
  confidence: number;
  probability: {
    [key: string]: number;
  };
  timestamp: string;
  model_version: string;
}

export interface HealthResponse {
  status: string;
  version: string;
  model_loaded: boolean;
  timestamp: string;
  environment: string;
}

export interface ApiError {
  error: string;
  status_code: number;
  timestamp: string;
  request_id?: string;
  details?: Record<string, any>;
}

// API Configuration
const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:5000';
const API_TIMEOUT = 60000; // 60 seconds

// Create axios instance with default config
const apiClient = axios.create({
  baseURL: API_URL,
  timeout: API_TIMEOUT,
});

// Add response interceptor for error handling
apiClient.interceptors.response.use(
  (response) => response,
  (error: AxiosError) => {
    const apiError: ApiError = {
      error: 'An error occurred',
      status_code: error.response?.status || 500,
      timestamp: new Date().toISOString(),
    };

    if (error.response?.data && typeof error.response.data === 'object') {
      const data = error.response.data as any;
      apiError.error = data.error || data.detail || apiError.error;
      apiError.details = data.details;
    } else if (error.message) {
      apiError.error = error.message;
    }

    return Promise.reject(apiError);
  }
);

// Health Check
export const checkHealth = async (): Promise<HealthResponse> => {
  try {
    const response = await apiClient.get<HealthResponse>('/health');
    return response.data;
  } catch (error) {
    throw formatError(error, 'Failed to check API health');
  }
};

// Upload Image
export const uploadImage = async (file: File): Promise<UploadResponse> => {
  try {
    // Validate file before upload
    if (!file) {
      throw new Error('No file selected');
    }

    if (file.size > 10 * 1024 * 1024) {
      throw new Error('File size exceeds 10MB limit');
    }

    const allowedExtensions = ['jpg', 'jpeg', 'png', 'jfif', 'gif', 'bmp', 'webp', 'tiff', 'tif'];
    const fileExtension = file.name.split('.').pop()?.toLowerCase();
    if (!fileExtension || !allowedExtensions.includes(fileExtension)) {
      throw new Error(`Invalid file type. Allowed: ${allowedExtensions.join(', ')}`);
    }

    // Create FormData
    const formData = new FormData();
    formData.append('file', file);

    // Upload
    const response = await apiClient.post<UploadResponse>(
      '/api/v1/upload',
      formData
    );

    return response.data;
  } catch (error) {
    throw formatError(error, 'Failed to upload image');
  }
};

// Get Prediction
export const getPrediction = async (imageId: string): Promise<PredictionResponse> => {
  try {
    if (!imageId) {
      throw new Error('Image ID is required');
    }

    const response = await apiClient.post<PredictionResponse>(
      '/api/v1/predict',
      {},
      {
        params: { image_id: imageId },
      }
    );

    return response.data;
  } catch (error) {
    throw formatError(error, 'Failed to get prediction');
  }
};

// Analyze Image (Combined Upload + Predict)
export const analyzeImage = async (file: File): Promise<PredictionResponse> => {
  try {
    // Validate file before upload
    if (!file) {
      throw new Error('No file selected');
    }

    if (file.size > 10 * 1024 * 1024) {
      throw new Error('File size exceeds 10MB limit');
    }

    const allowedExtensions = ['jpg', 'jpeg', 'png', 'jfif', 'gif', 'bmp', 'webp', 'tiff', 'tif'];
    const fileExtension = file.name.split('.').pop()?.toLowerCase();
    if (!fileExtension || !allowedExtensions.includes(fileExtension)) {
      throw new Error(`Invalid file type. Allowed: ${allowedExtensions.join(', ')}`);
    }

    // Create FormData
    const formData = new FormData();
    formData.append('file', file);

    // Analyze (upload + predict in one call)
    const response = await apiClient.post<PredictionResponse>(
      '/api/v1/analyze',
      formData
    );

    return response.data;
  } catch (error) {
    throw formatError(error, 'Failed to analyze image');
  }
};

// Helper function to format errors
const formatError = (error: any, fallbackMessage: string): ApiError => {
  if (error && typeof error === 'object' && 'error' in error) {
    return error as ApiError;
  }

  return {
    error: error?.message || fallbackMessage,
    status_code: error?.status_code || 500,
    timestamp: new Date().toISOString(),
  };
};

// Export API client for direct use if needed
export default apiClient;