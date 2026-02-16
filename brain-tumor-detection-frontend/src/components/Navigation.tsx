import React from 'react';
import { Link } from 'react-router-dom';

const Navigation: React.FC = () => {
    return (
        <nav>
            <ul>
                <li>
                    <Link to="/">Home</Link>
                </li>
                <li>
                    <Link to="/upload">Upload MRI Scan</Link>
                </li>
                <li>
                    <Link to="/results">Results</Link>
                </li>
            </ul>
        </nav>
    );
};

export default Navigation;