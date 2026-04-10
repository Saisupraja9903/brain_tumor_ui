import React from 'react';
import { useLocation, useHistory } from 'react-router-dom';

type ResultsState = {
    result: string;
    confidence: number;
};

const ResultsPage: React.FC = () => {
        const location = useLocation<ResultsState>();
        const history = useHistory();
        const { result, confidence } = location.state || { result: 'No Result', confidence: 0 };

    const handleUploadAnother = () => {
        history.push('/upload');
    };

        return (
                <div className="results-page">
                        <h1>Prediction Result</h1>
                        <div className={`result ${result === 'Tumor' ? 'tumor' : 'no-tumor'}`}>
                                <h2>{result}</h2>
                                <p>Confidence Score: {confidence.toFixed(2)}%</p>
                                {/* Show only the relevant probability bar */}
                                {result === 'Tumor' ? (
                                    <div className="probability-bar tumor-bar">
                                        <span>🔴 Tumor: {confidence.toFixed(2)}%</span>
                                        <div className="probability-bar-inner" style={{ width: `${confidence}%`, background: '#dc3545', height: '10px', borderRadius: '5px', marginTop: '4px' }} />
                                    </div>
                                ) : result === 'No Tumor' ? (
                                    <div className="probability-bar no-tumor-bar">
                                        <span>🟢 No Tumor: {confidence.toFixed(2)}%</span>
                                        <div className="probability-bar-inner" style={{ width: `${confidence}%`, background: '#28a745', height: '10px', borderRadius: '5px', marginTop: '4px' }} />
                                    </div>
                                ) : null}
                        </div>
                        <button onClick={handleUploadAnother}>Upload Another Image</button>
                </div>
        );
};

export default ResultsPage;