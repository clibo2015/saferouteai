import React from 'react';
import { motion } from 'framer-motion';
import './LoadingScreen.css';

const LoadingScreen = () => {
  return (
    <motion.div 
      className="loading-screen"
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
      transition={{ duration: 0.5 }}
    >
      <div className="loading-content">
        {/* SafeRouteAI Logo */}
        <motion.div 
          className="loading-logo"
          initial={{ scale: 0.8, opacity: 0 }}
          animate={{ scale: 1, opacity: 1 }}
          transition={{ delay: 0.2, duration: 0.8 }}
        >
          <div className="logo-shield">
            <svg width="80" height="80" viewBox="0 0 80 80" fill="none">
              <path
                d="M40 5L70 20V35C70 55 40 75 40 75S10 55 10 35V20L40 5Z"
                fill="url(#shieldGradient)"
                stroke="rgba(228, 30, 38, 0.5)"
                strokeWidth="2"
              />
              <path
                d="M40 15L60 25V35C60 50 40 65 40 65S20 50 20 35V25L40 15Z"
                fill="rgba(255, 255, 255, 0.1)"
              />
              <defs>
                <linearGradient id="shieldGradient" x1="0%" y1="0%" x2="100%" y2="100%">
                  <stop offset="0%" stopColor="#E41E26" />
                  <stop offset="100%" stopColor="#ff4757" />
                </linearGradient>
              </defs>
            </svg>
          </div>
          <h1 className="loading-title">SafeRoute<span className="gradient-text">AI</span></h1>
        </motion.div>

        {/* Loading Animation */}
        <motion.div 
          className="loading-animation"
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.5, duration: 0.6 }}
        >
          <div className="loading-spinner">
            <div className="spinner-ring"></div>
            <div className="spinner-ring"></div>
            <div className="spinner-ring"></div>
          </div>
          <p className="loading-text">Initializing AI Systems...</p>
        </motion.div>

        {/* Loading Steps */}
        <motion.div 
          className="loading-steps"
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 1, duration: 0.8 }}
        >
          <LoadingStep text="Connecting to SafeRouteAI services" delay={0} />
          <LoadingStep text="Loading AI Models" delay={0.5} />
          <LoadingStep text="Initializing Safety Systems" delay={1} />
          <LoadingStep text="Ready for Secure Logistics" delay={1.5} />
        </motion.div>

        {/* Map + routing stack */}
        <motion.div 
          className="powered-by"
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 1.8, duration: 0.6 }}
        >
          <span>Powered by</span>
          <div className="powered-by-logo">
            🌍 <strong>OPENSTREETMAP + OSRM</strong>
          </div>
        </motion.div>
      </div>

      {/* Background Animation */}
      <div className="loading-background">
        <div className="bg-particle"></div>
        <div className="bg-particle"></div>
        <div className="bg-particle"></div>
        <div className="bg-particle"></div>
        <div className="bg-particle"></div>
      </div>
    </motion.div>
  );
};

const LoadingStep = ({ text, delay }) => {
  return (
    <motion.div 
      className="loading-step"
      initial={{ opacity: 0, x: -20 }}
      animate={{ opacity: 1, x: 0 }}
      transition={{ delay, duration: 0.6 }}
    >
      <motion.div 
        className="step-indicator"
        initial={{ scale: 0 }}
        animate={{ scale: 1 }}
        transition={{ delay: delay + 0.3, duration: 0.4 }}
      >
        <motion.div 
          className="step-dot"
          animate={{ 
            backgroundColor: ['rgba(228, 30, 38, 0.3)', '#E41E26', 'rgba(228, 30, 38, 0.3)']
          }}
          transition={{ 
            duration: 2, 
            repeat: Infinity, 
            delay 
          }}
        />
      </motion.div>
      <span className="step-text">{text}</span>
    </motion.div>
  );
};

export default LoadingScreen;