import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { useNavigate } from 'react-router-dom';
import { apiService } from '../services/apiService';
import './AuthScreen.css';

const AuthScreen = ({ onLoginSuccess }) => {
    const navigate = useNavigate();
    const [isLogin, setIsLogin] = useState(true);
    const [isLoading, setIsLoading] = useState(false);
    const [error, setError] = useState('');
    const [formData, setFormData] = useState({
        email: '',
        password: '',
        name: ''
    });

    const handleChange = (e) => {
        setFormData({ ...formData, [e.target.name]: e.target.value });
        setError('');
    };

    const handleSubmit = async (e) => {
        e.preventDefault();
        setIsLoading(true);
        setError('');

        try {
            let response;
            if (isLogin) {
                response = await apiService.login(formData.email, formData.password);
            } else {
                response = await apiService.register(formData.email, formData.name, formData.password);
            }

            if (response && response.access_token) {
                onLoginSuccess(response.user);
                navigate('/dashboard');
            } else {
                setError('Authentication failed. Please check your credentials.');
            }
        } catch (err) {
            console.error('Auth error:', err);
            setError(err.message || 'An error occurred during authentication.');
        } finally {
            setIsLoading(false);
        }
    };

    return (
        <div className="auth-screen">
            <div className="auth-background">
                <div className="bg-grid"></div>
                <div className="bg-glow"></div>
            </div>

            <motion.div
                className="auth-container"
                initial={{ opacity: 0, y: 30 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.6 }}
            >
                <div className="auth-header">
                    <div className="auth-logo">
                        <svg width="40" height="40" viewBox="0 0 32 32" fill="none">
                            <path
                                d="M16 2L26 8V14C26 22 16 30 16 30S6 22 6 14V8L16 2Z"
                                fill="url(#authShieldGradient)"
                            />
                            <defs>
                                <linearGradient id="authShieldGradient" x1="0%" y1="0%" x2="100%" y2="100%">
                                    <stop offset="0%" stopColor="#E41E26" />
                                    <stop offset="100%" stopColor="#ff4757" />
                                </linearGradient>
                            </defs>
                        </svg>
                    </div>
                    <h1>SafeRoute<span className="gradient-text">AI</span></h1>
                    <p>{isLogin ? 'Welcome back, Commander' : 'Initialize security clearance'}</p>
                </div>

                <div className="auth-tabs">
                    <button
                        className={`auth-tab ${isLogin ? 'active' : ''}`}
                        onClick={() => setIsLogin(true)}
                    >
                        Login
                    </button>
                    <button
                        className={`auth-tab ${!isLogin ? 'active' : ''}`}
                        onClick={() => setIsLogin(false)}
                    >
                        Register
                    </button>
                    <motion.div
                        className="tab-indicator"
                        animate={{ x: isLogin ? 0 : '100%' }}
                        transition={{ type: "spring", stiffness: 300, damping: 30 }}
                    />
                </div>

                <form className="auth-form" onSubmit={handleSubmit}>
                    <AnimatePresence mode="wait">
                        {!isLogin && (
                            <motion.div
                                className="form-group"
                                initial={{ opacity: 0, height: 0 }}
                                animate={{ opacity: 1, height: 'auto' }}
                                exit={{ opacity: 0, height: 0 }}
                                transition={{ duration: 0.3 }}
                            >
                                <label>Full Name</label>
                                <input
                                    type="text"
                                    name="name"
                                    placeholder="John Doe"
                                    value={formData.name}
                                    onChange={handleChange}
                                    required={!isLogin}
                                />
                            </motion.div>
                        )}
                    </AnimatePresence>

                    <div className="form-group">
                        <label>Email Address</label>
                        <input
                            type="email"
                            name="email"
                            placeholder="commander@saferoute.ai"
                            value={formData.email}
                            onChange={handleChange}
                            required
                        />
                    </div>

                    <div className="form-group">
                        <label>Secure Password</label>
                        <input
                            type="password"
                            name="password"
                            placeholder="••••••••"
                            value={formData.password}
                            onChange={handleChange}
                            required
                        />
                    </div>

                    {error && (
                        <motion.div
                            className="auth-error"
                            initial={{ opacity: 0, x: -10 }}
                            animate={{ opacity: 1, x: 0 }}
                        >
                            ⚠️ {error}
                        </motion.div>
                    )}

                    <button
                        type="submit"
                        className={`auth-submit-btn ${isLoading ? 'loading' : ''}`}
                        disabled={isLoading}
                    >
                        {isLoading ? (
                            <div className="spinner"></div>
                        ) : (
                            isLogin ? 'Access Dashboard' : 'Create Clearance'
                        )}
                    </button>
                </form>

                <div className="auth-footer">
                    <p>
                        {isLogin
                            ? "Don't have clearance yet?"
                            : "Already registered?"}
                        <span onClick={() => setIsLogin(!isLogin)}>
                            {isLogin ? ' Request here' : ' Login here'}
                        </span>
                    </p>
                </div>
            </motion.div>

            <div className="auth-security-info">
                <div className="security-badge">
                    <span className="badge-icon">🔒</span>
                    End-to-end encrypted
                </div>
                <div className="security-badge">
                    <span className="badge-icon">🛡️</span>
                    Neon Database Secure
                </div>
            </div>
        </div>
    );
};

export default AuthScreen;
