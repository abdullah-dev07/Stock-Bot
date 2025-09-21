import React, { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';

function SignupPage() {
    const [email, setEmail] = useState('');
    const [password, setPassword] = useState('');
    const [error, setError] = useState('');
    const [success, setSuccess] = useState('');
    const navigate = useNavigate();

    const handleSubmit = async (e) => {
        e.preventDefault();
        setError('');
        setSuccess('');

        
        const formData = new FormData();
        formData.append('email', email);
        formData.append('password', password);

        try {
            const response = await fetch('http:
                method: 'POST',
                body: formData, 
            });

            const responseData = await response.json();

            if (response.ok) {
                setSuccess('Signup successful! Redirecting to login...');
                setTimeout(() => {
                    navigate('/login');
                }, 2000); 
            } else {
                setError(responseData.detail || 'An error occurred during signup.');
            }
        } catch (err) {
            setError('A network error occurred. Please try again.');
        }
    };

    return (
        <div className="auth-container">
            <div className="auth-form-container">
                <h1>Create an Account</h1>
                <form id="signup-form" onSubmit={handleSubmit}>
                    {error && <div className="flash error">{error}</div>}
                    {success && <div className="flash success">{success}</div>}
                    <div className="form-group">
                        <label htmlFor="email">Email</label>
                        <input
                            type="email"
                            name="email"
                            value={email}
                            onChange={(e) => setEmail(e.target.value)}
                            required
                        />
                    </div>
                    <div className="form-group">
                        <label htmlFor="password">Password</label>
                        <input
                            type="password"
                            name="password"
                            value={password}
                            onChange={(e) => setPassword(e.target.value)}
                            required
                        />
                    </div>
                    <button type="submit" className="auth-btn">Sign Up</button>
                </form>
                <p className="auth-switch">Already have an account? <Link to="/login">Log In</Link></p>
            </div>
        </div>
    );
}

export default SignupPage;