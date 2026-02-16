export interface ImageUploadRequest {
    image: File;
}

export interface PredictionResponse {
    result: 'Tumor' | 'No Tumor';
    confidence: number;
}

export interface ErrorResponse {
    message: string;
}