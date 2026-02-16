import React, { useState, useRef } from 'react';
import { analyzeImage, ApiError, PredictionResponse } from '../services/api';
import './UploadPage.css';

interface AnalysisResult extends PredictionResponse {
  duration?: number;
}

const UploadPage: React.FC = () => {
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [previewUrl, setPreviewUrl] = useState<string | null>(null);
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<AnalysisResult | null>(null);
  const [uploadProgress, setUploadProgress] = useState<number>(0);
  const [analysisStep, setAnalysisStep] = useState<'idle' | 'uploading' | 'analyzing'>('idle');
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleFileChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0] || null;

    if (!file) return;

    // Validate size
    if (file.size > 10 * 1024 * 1024) {
      setError('File size exceeds 10MB limit');
      return;
    }

    // Validate extension
    const allowedExtensions = ['jpg', 'jpeg', 'png', 'jfif', 'gif', 'bmp', 'webp', 'tiff', 'tif'];
    const fileExtension = file.name.split('.').pop()?.toLowerCase();
    if (!fileExtension || !allowedExtensions.includes(fileExtension)) {
      setError('Invalid file type. Please upload JPG, JPEG, PNG, JFIF, GIF, BMP, WebP, or TIFF.');
      return;
    }

    // Validate image by attempting to load it
    const img = new Image();
    img.onload = () => {
      setSelectedFile(file);
      setPreviewUrl(URL.createObjectURL(file));
      setError(null);
      setResult(null);
    };
    img.onerror = () => {
      setError('Invalid image file. Please upload a valid image.');
    };
    img.src = URL.createObjectURL(file);
  };

  const handleAnalyzeImage = async () => {
    if (!selectedFile) {
      setError('Please select an MRI image to analyze.');
      return;
    }

    setLoading(true);
    setError(null);
    setResult(null);
    const startTime = Date.now();

    try {
      setAnalysisStep('uploading');
      
      // Use combined analyze endpoint for better UX
      const response = await analyzeImage(selectedFile);
      
      const duration = (Date.now() - startTime) / 1000;
      setAnalysisStep('analyzing');
      
      setResult({
        ...response,
        duration,
      });
      
      setAnalysisStep('idle');
    } catch (err) {
      const apiError = err as ApiError;
      setError(apiError.error || 'Failed to analyze the image. Please try again.');
      setAnalysisStep('idle');
    } finally {
      setLoading(false);
    }
  };

  const handleUploadClick = () => {
    fileInputRef.current?.click();
  };

  const handleRemoveFile = () => {
    setSelectedFile(null);
    setPreviewUrl(null);
    setError(null);
    setResult(null);
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
  };

  const getRiskLevel = (confidence: number): 'Low' | 'Medium' | 'High' => {
    if (confidence >= 80) return 'High';
    if (confidence >= 60) return 'Medium';
    return 'Low';
  };

  const getConfidenceColor = (confidence: number): string => {
    if (confidence >= 80) return '#dc3545'; // Red for high confidence tumor
    if (confidence >= 60) return '#ffc107'; // Yellow for medium
    return '#28a745'; // Green for low
  };

  return (
    <div className="upload-page">
      <div className="upload-container">
        <h1>Brain MRI Analysis</h1>
        <p className="subtitle">Upload an MRI scan image for instant brain tumor detection</p>

        {/* Upload Section */}
        <div className="upload-section">
          <div className="file-input-wrapper">
            <input
              ref={fileInputRef}
              type="file"
              accept=".jpg,.jpeg,.png,.jfif,.gif,.bmp,.webp,.tiff,.tif"
              onChange={handleFileChange}
              style={{ display: 'none' }}
            />
            
            {!selectedFile ? (
              <div
                className="upload-area"
                onClick={handleUploadClick}
                onDragOver={(e) => {
                  e.preventDefault();
                  e.currentTarget.classList.add('drag-over');
                }}
                onDragLeave={(e) => {
                  e.currentTarget.classList.remove('drag-over');
                }}
                onDrop={(e) => {
                  e.preventDefault();
                  e.currentTarget.classList.remove('drag-over');
                  const files = e.dataTransfer.files;
                  if (files[0]) {
                    const event = {
                      target: { files },
                    } as any;
                    handleFileChange(event);
                  }
                }}
              >
                <div className="upload-icon">📁</div>
                <h3>Drop your MRI image here</h3>
                <p>or click to browse</p>
                <p className="file-hint">Supported formats: JPG, JPEG, PNG, JFIF (Max 10MB)</p>
              </div>
            ) : (
              <div className="file-selected">
                <div className="file-info">
                  <p className="file-name">📄 {selectedFile.name}</p>
                  <p className="file-size">
                    {(selectedFile.size / 1024 / 1024).toFixed(2)} MB
                  </p>
                </div>
                <button
                  type="button"
                  className="btn-remove"
                  onClick={handleRemoveFile}
                  disabled={loading}
                >
                  Remove
                </button>
              </div>
            )}
          </div>

          {/* Preview */}
          {previewUrl && (
            <div className="preview-section">
              <h3>Preview</h3>
              <img src={previewUrl} alt="MRI Preview" className="preview-image" />
            </div>
          )}
        </div>

        {/* Error Display */}
        {error && (
          <div className="alert alert-error">
            <span className="alert-icon">⚠️</span>
            <span className="alert-message">{error}</span>
          </div>
        )}

        {/* Loading State */}
        {loading && (
          <div className="loading-section">
            <div className="spinner"></div>
            <p>
              {analysisStep === 'uploading' && 'Uploading image...'}
              {analysisStep === 'analyzing' && 'Analyzing image with AI model...'}
            </p>
          </div>
        )}

        {/* Analyze Button */}
        {selectedFile && !loading && !result && (
          <button
            className="btn-analyze"
            onClick={handleAnalyzeImage}
            disabled={!selectedFile || loading}
          >
            🔍 Analyze Image
          </button>
        )}

        {/* Results Display */}
        {result && !loading && (
          <div className="results-section">
            <div className="results-header">
              <h2>Analysis Results</h2>
              <p className="result-timestamp">
                Completed in {result.duration?.toFixed(2)}s
              </p>
            </div>

            <div className="result-cards">
              {/* Prediction Card */}
              <div className="result-card prediction-card">
                <h3>Prediction</h3>
                <div className="prediction-result">
                  <p className={`prediction-text ${result.prediction}`}>
                    {result.prediction === 'tumor'
                      ? '🔴 Tumor Detected'
                      : '🟢 No Tumor Found'}
                  </p>
                </div>
              </div>

              {/* Confidence Card */}
              <div className="result-card confidence-card">
                <h3>Confidence Score</h3>
                <div className="confidence-display">
                  <div className="confidence-circle">
                    <svg viewBox="0 0 100 100">
                      <circle cx="50" cy="50" r="45" className="circle-bg" />
                      <circle
                        cx="50"
                        cy="50"
                        r="45"
                        className="circle-progress"
                        style={{
                          strokeDasharray: `${2 * Math.PI * 45 * (result.confidence / 100)} ${2 * Math.PI * 45}`,
                          stroke: getConfidenceColor(result.confidence),
                        }}
                      />
                    </svg>
                    <div className="confidence-value">
                      {result.confidence.toFixed(1)}%
                    </div>
                  </div>
                  <p className="risk-level">
                    Risk Level: <strong>{getRiskLevel(result.confidence)}</strong>
                  </p>
                </div>
              </div>
            </div>

            {/* Probability Details */}
            <div className="result-details">
              <h3>Detailed Probabilities</h3>
              <div className="probability-list">
                {Object.entries(result.probability).map(([label, prob]) => (
                  <div key={label} className="probability-item">
                    <div className="probability-label">
                      <span className="label-name">
                        {label === 'tumor' ? '🔴' : '🟢'} {label.charAt(0).toUpperCase() + label.slice(1)}
                      </span>
                      <span className="probability-value">
                        {(prob * 100).toFixed(2)}%
                      </span>
                    </div>
                    <div className="probability-bar">
                      <div
                        className="probability-fill"
                        style={{
                          width: `${prob * 100}%`,
                          backgroundColor: label === 'tumor' ? '#dc3545' : '#28a745',
                        }}
                      ></div>
                    </div>
                  </div>
                ))}
              </div>
            </div>

            {/* Model Info */}
            <div className="model-info">
              <p>Model Version: {result.model_version}</p>
              <p>Analysis Date: {new Date(result.timestamp).toLocaleString()}</p>
            </div>

            {/* Action Buttons */}
            <div className="action-buttons">
              <button className="btn-new-analysis" onClick={handleRemoveFile}>
                🔄 Analyze Another Image
              </button>
            </div>
          </div>
        )}

        {/* Empty State */}
        {!selectedFile && !loading && !result && (
          <div className="empty-state">
            <p>Select an image to get started with brain tumor detection</p>
          </div>
        )}
      </div>
    </div>
  );
};

export default UploadPage;