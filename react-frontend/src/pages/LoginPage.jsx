import React, { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';

function LoginPage() {
    const [email, setEmail] = useState('');
    const [password, setPassword] = useState('');
    const [error, setError] = useState('');
    const navigate = useNavigate();

    const handleSubmit = async (e) => {
        e.preventDefault();
        setError('');

        
        const formData = new URLSearchParams();
        formData.append('username', email);
        formData.append('password', password);

        try {
            
            const response = await fetch('http:
                method: 'POST',
                headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
                body: formData,
            });

            if (response.ok) {
                const data = await response.json();
                localStorage.setItem('stockbot_token', data.access_token);
                navigate('/'); 
            } else {
                const errorData = await response.json();
                setError(errorData.detail || 'Invalid email or password.');
            }
        } catch (err) {
            setError('An error occurred. Please try again.');
        }
    };

    return (
        <div className="auth-container">
            <div className="auth-form-container">
                <h1>Login to Your Stock Bot</h1>
                <form id="login-form" onSubmit={handleSubmit}>
                    {error && <div className="flash error">{error}</div>}
                    <div className="form-group">
                        <label htmlFor="email">Email</label>
                        {}
                        <input
                            type="email"
                            name="username"
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
                    <button type="submit" className="auth-btn">Log In</button>
                </form>
                <p className="auth-switch">Don't have an account? <Link to="/signup">Sign Up</Link></p>
            </div>
        </div>
    );
}

export default LoginPage;