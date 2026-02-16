import React from 'react';
import { Link } from 'react-router-dom';
import './HomePage.css'; // Assuming you will create a CSS file for HomePage styles

const HomePage: React.FC = () => {
    return (
        <div className="home-page">
            <h1>Brain Tumor Detection System</h1>
            <p>
                Welcome to the Brain Tumor Detection System. This application allows you to upload MRI scans
                and receive predictions on the presence of tumors.
            </p>
            <Link to="/upload">
                <button className="upload-button">Upload MRI Scan</button>
            </Link>
        </div>
    );
};

export default HomePage;