import React from 'react';
import { Link } from 'react-router-dom';
import './Header.css'; // Assuming you have a CSS file for styling

const Header: React.FC = () => {
    return (
        <header className="header">
            <h1 className="header-title">Brain Tumor Detection System</h1>
            <nav className="header-nav">
                <ul>
                    <li>
                        <Link to="/">Home</Link>
                    </li>
                    <li>
                        <Link to="/upload">Upload MRI Scan</Link>
                    </li>
                    {/* <li>
                        <Link to="/results">Results</Link>
                    </li> */}
                </ul>
            </nav>
        </header>
    );
};

export default Header;