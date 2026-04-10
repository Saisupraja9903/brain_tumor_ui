import React, { useState, useRef } from 'react';
import { analyzeImage, ApiError, PredictionResponse } from '../services/api';
import './UploadPage.css';

interface AnalysisResult extends PredictionResponse {
  duration?: number;
  stage?: string;
}

interface MedicalGuidance {
  status: string;
  warning?: string;
  points: string[];
  hospital: string;
  className: string;
}

const getGuidance = (prediction: string, stage?: string): MedicalGuidance => {
  if (prediction !== 'tumor') {
    return {
      status: "No Tumor Detected (AI Based Screening)",
      points: [
        "No immediate abnormality detected.",
        "Maintain regular health monitoring.",
        "If symptoms like persistent headaches, vision changes, or dizziness occur, consult a physician."
      ],
      hospital: "Routine hospital consultation is sufficient unless symptoms develop.",
      className: "safe-guide"
    };
  }

  switch (stage) {
    case 'Stage I':
      return {
        status: "Stage I (Preliminary AI Detection) - Low Grade",
        points: [
          "Low-grade or slowly developing tumor characteristics detected.",
          "Consult a Neurologist or Neuro-oncologist for clinical validation.",
          "Prepare for a follow-up MRI with contrast or further diagnostic testing."
        ],
        hospital: "Visit a specialized Neurology department for further screening.",
        className: "tumor-guide stage-1"
      };
    case 'Stage II':
      return {
        status: "Stage II (Preliminary AI Detection) - Mid Grade",
        points: [
          "Mid-grade tumor characteristics detected, suggesting possible progression.",
          "Prompt consultation with a Neurosurgeon or Oncologist is advised.",
          "Treatment planning including possible biopsy or surgical options may be discussed."
        ],
        hospital: "Seek an appointment at a multi-specialty hospital with Neurology/Oncology.",
        className: "tumor-guide stage-2"
      };
    case 'Stage III':
      return {
        status: "Stage III (Preliminary AI Detection) - High Grade",
        warning: "⚠️ High probability of an aggressive tumor detected. Urgent medical consultation is recommended.",
        points: [
          "High-grade, potentially aggressive tumor characteristics detected.",
          "Urgent consultation with a Neuro-oncology team is strongly recommended.",
          "Immediate comprehensive diagnostic testing and treatment planning are necessary."
        ],
        hospital: "Visit a comprehensive cancer center or specialized neuro-care hospital promptly.",
        className: "tumor-guide stage-3"
      };
    case 'Stage IV':
      return {
        status: "Stage IV (Preliminary AI Detection) - Severe",
        warning: "⚠️ CRITICAL: Highly aggressive tumor characteristics detected. Immediate medical intervention is strongly recommended.",
        points: [
          "Severe, rapidly progressing tumor characteristics detected.",
          "Immediate emergency medical attention and specialist intervention are required.",
          "Consult a Neurosurgeon and Oncology specialist without delay.",
          "Rapid intervention is critical for managing symptoms and comprehensive treatment."
        ],
        hospital: "Seek immediate medical care at an emergency department or specialized cancer center.",
        className: "tumor-guide stage-4"
      };
    case 'Early / Indeterminate':
    default:
      return {
        status: "Early / Indeterminate Stage (Preliminary AI Detection)",
        points: [
          "Possible early-stage abnormality or indeterminate characteristics detected.",
          "Consult a Neurologist for a comprehensive clinical evaluation.",
          "A follow-up MRI or CT scan may be recommended to clarify the findings."
        ],
        hospital: "Schedule a non-emergency appointment with a Neurologist.",
        className: "tumor-guide stage-indeterminate"
      };
  }
};

const UploadPage: React.FC = () => {
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [previewUrl, setPreviewUrl] = useState<string | null>(null);
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  
  const [result, setResult] = useState<AnalysisResult | null>(null);
  const [showBrainOnlyPopup, setShowBrainOnlyPopup] = useState(false);
  const [showBWOnlyPopup, setShowBWOnlyPopup] = useState(false);
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

    // Heuristic: Check filename for 'brain' keyword (case-insensitive)
    // const lowerName = file.name.toLowerCase();
    // if (!lowerName.includes('brain')) {
    //   setShowBrainOnlyPopup(true);
    //   setSelectedFile(null);
    //   setPreviewUrl(null);
    //   setError('Only brain images are allowed.');
    //   return;
    // }

    // ✅ ACCEPT IMAGE DIRECTLY
    setSelectedFile(file);
    setPreviewUrl(URL.createObjectURL(file));
    setError(null);
    setResult(null);
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

      // Compute stage only when tumor is predicted (client-side estimate)
      const stage = response.prediction === 'tumor' ? getCancerStage(response.confidence) : undefined;

      setResult({
        ...response,
        duration,
        stage,
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

  // Derive a simple cancer stage from confidence when a tumor is detected.
  // This is a client-side heuristic for display only and NOT a medical diagnosis.
  const getCancerStage = (confidence: number): string => {
    if (confidence >= 85) return 'Stage IV';
    if (confidence >= 70) return 'Stage III';
    if (confidence >= 50) return 'Stage II';
    if (confidence >= 30) return 'Stage I';
    return 'Early / Indeterminate';
  };

  return (
    <div className="upload-page">
      {showBrainOnlyPopup && (
        <div className="popup-overlay">
          <div className="popup-content">
            <h3>Upload Correct Brain Image</h3>
            <p>
              Only brain MRI images are allowed. Please upload a valid brain image.
            </p>
            <button onClick={() => setShowBrainOnlyPopup(false)} className="btn-close-popup">
              OK
            </button>
          </div>
        </div>
      )}
      {/* Popup for brain MRI only */}
      {/* No brain filename popup needed anymore */}
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

              {/* Stage Card (only when tumor detected) */}
              {result.prediction === 'tumor' && (
                <div className="result-card stage-card">
                  <h3>Estimated Cancer Stage</h3>
                  <div className="stage-result">
                    <p className="stage-text">{result.stage || getCancerStage(result.confidence)}</p>
                    <p className="stage-note">This stage is an illustrative estimate based on confidence and is not a medical diagnosis.</p>
                  </div>
                </div>
              )}

              {/* Confidence Card */}
              {result.prediction === 'tumor' && (
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
              )}
            </div>

            {/* Probability Details - Show only the relevant bar */}
            <div className="result-details">
              <h3>Detailed Probabilities</h3>
              <div className="probability-list">
                {result.prediction === 'tumor' && result.probability.tumor !== undefined && (
                  <div className="probability-item">
                    <div className="probability-label">
                      <span className="label-name">🔴 Tumor</span>
                      <span className="probability-value">{(result.probability.tumor * 100).toFixed(2)}%</span>
                    </div>
                    <div className="probability-bar">
                      <div
                        className="probability-fill"
                        style={{
                          width: `${result.probability.tumor * 100}%`,
                          backgroundColor: '#dc3545',
                        }}
                      ></div>
                    </div>
                  </div>
                )}
                {result.prediction !== 'tumor' && result.probability['no tumor'] !== undefined && (
                  <div className="probability-item">
                    <div className="probability-label">
                      <span className="label-name">🟢 No Tumor</span>
                      <span className="probability-value">{(result.probability['no tumor'] * 100).toFixed(2)}%</span>
                    </div>
                    <div className="probability-bar">
                      <div
                        className="probability-fill"
                        style={{
                          width: `${result.probability['no tumor'] * 100}%`,
                          backgroundColor: '#28a745',
                        }}
                      ></div>
                    </div>
                  </div>
                )}
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
            {/* ================= Medical Guidance Section ================= */}
{(() => {
  const currentStage = result.stage || (result.prediction === 'tumor' ? getCancerStage(result.confidence) : undefined);
  const guidance = getGuidance(result.prediction, currentStage);
  
  return (
    <div className="medical-guidance-section">
      {/* Emergency Warning */}
      {guidance.warning && (
        <div className="emergency-warning">
          {guidance.warning}
        </div>
      )}

      <h3>Preliminary Medical Guidance</h3>

      <div className={`guidance-box ${guidance.className}`}>
        <p><strong>Status:</strong> {guidance.status}</p>
        <ul>
          {guidance.points.map((point, index) => (
            <li key={index}>{point}</li>
          ))}
        </ul>
        <p className="hospital-recommendation">
          {guidance.hospital}
        </p>
      </div>

      {/* Legal Disclaimer */}
      <div className="legal-disclaimer">
        ⚖️ This AI system provides preliminary screening only and is NOT a confirmed medical diagnosis.
        Please consult a certified medical professional for clinical evaluation.
      </div>
    </div>
  );
})()}


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