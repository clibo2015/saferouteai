import React, { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import './OnboardingScreen.css';

const OnboardingScreen = ({ onComplete }) => {
  const [isAnimating, setIsAnimating] = useState(true);

  useEffect(() => {
    // Start the main animation after component mounts
    const timer = setTimeout(() => {
      setIsAnimating(false);
    }, 3000);

    return () => clearTimeout(timer);
  }, []);

  const handleGetStarted = () => {
    onComplete();
  };

  return (
    <motion.div
      className="onboarding-screen"
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0, scale: 0.95 }}
      transition={{ duration: 0.8 }}
    >
      {/* Background Effects */}
      <div className="onboarding-background">
        <div className="bg-grid"></div>
        <div className="bg-glow bg-glow-1"></div>
        <div className="bg-glow bg-glow-2"></div>
        <div className="bg-particles">
          {[...Array(20)].map((_, i) => (
            <div key={i} className="particle" style={{
              left: `${Math.random() * 100}%`,
              top: `${Math.random() * 100}%`,
              animationDelay: `${Math.random() * 5}s`,
              animationDuration: `${3 + Math.random() * 4}s`
            }} />
          ))}
        </div>
      </div>

      {/* Main Content */}
      <div className="onboarding-content">
        {/* Logo and Title */}
        <motion.div
          className="onboarding-header"
          initial={{ y: -50, opacity: 0 }}
          animate={{ y: 0, opacity: 1 }}
          transition={{ delay: 0.3, duration: 0.8 }}
        >
          <div className="logo-container">
            <motion.div
              className="logo-shield"
              animate={{
                rotateY: isAnimating ? [0, 360] : 0,
                scale: isAnimating ? [1, 1.1, 1] : 1
              }}
              transition={{
                duration: 2,
                repeat: isAnimating ? Infinity : 0,
                ease: "easeInOut"
              }}
            >
              <svg width="120" height="120" viewBox="0 0 120 120" fill="none">
                {/* Outer Shield */}
                <path
                  d="M60 10L100 30V50C100 80 60 110 60 110S20 80 20 50V30L60 10Z"
                  fill="url(#shieldGradient)"
                  stroke="rgba(228, 30, 38, 0.8)"
                  strokeWidth="2"
                />
                {/* Inner Shield */}
                <path
                  d="M60 25L85 35V50C85 70 60 90 60 90S35 70 35 50V35L60 25Z"
                  fill="rgba(255, 255, 255, 0.1)"
                  stroke="rgba(255, 255, 255, 0.3)"
                  strokeWidth="1"
                />
                {/* Center Emblem */}
                <circle cx="60" cy="55" r="15" fill="rgba(255, 255, 255, 0.2)" />
                <path
                  d="M55 55L58 58L65 51"
                  stroke="#ffffff"
                  strokeWidth="3"
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  fill="none"
                />

                <defs>
                  <linearGradient id="shieldGradient" x1="0%" y1="0%" x2="100%" y2="100%">
                    <stop offset="0%" stopColor="#E41E26" />
                    <stop offset="50%" stopColor="#ff4757" />
                    <stop offset="100%" stopColor="#E41E26" />
                  </linearGradient>
                </defs>
              </svg>
            </motion.div>
          </div>

          <motion.h1
            className="onboarding-title"
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.6, duration: 0.8 }}
          >
            SafeRoute<span className="gradient-text">AI</span>
          </motion.h1>
        </motion.div>

        {/* Main Message */}
        <motion.div
          className="onboarding-message"
          initial={{ opacity: 0, y: 30 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.9, duration: 0.8 }}
        >
          <h2 className="message-title">
            Welcome to the Future<br />
            of Secure Logistics
          </h2>
          <p className="message-subtitle">
            AI-powered route optimization with real-time hazard detection
            and crime prevention for South African logistics
          </p>
        </motion.div>

        {/* 3D Vehicle with Shield */}
        <motion.div
          className="vehicle-showcase"
          initial={{ opacity: 0, scale: 0.8 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ delay: 1.2, duration: 1 }}
        >
          <div className="vehicle-container">
            {/* Holographic Platform */}
            <motion.div
              className="holo-platform"
              animate={{
                rotateY: [0, 360],
                scale: [1, 1.05, 1]
              }}
              transition={{
                duration: 8,
                repeat: Infinity,
                ease: "linear"
              }}
            >
              <div className="platform-ring platform-ring-1"></div>
              <div className="platform-ring platform-ring-2"></div>
              <div className="platform-ring platform-ring-3"></div>
            </motion.div>

            {/* Vehicle */}
            <motion.div
              className="vehicle"
              animate={{
                y: [0, -10, 0],
                rotateY: [0, 5, 0, -5, 0]
              }}
              transition={{
                duration: 4,
                repeat: Infinity,
                ease: "easeInOut"
              }}
            >
              <svg width="80" height="80" viewBox="0 0 24 24" fill="none">
                <path d="M1 14h15v-9h-10l-5 5v4z" fill="url(#vanGradient)" opacity="0.8" />
                <path d="M16 14h5l2-3v-3h-7v6z" fill="url(#vanGradient)" />
                <circle cx="6" cy="18" r="2" fill="#E41E26" />
                <circle cx="18" cy="18" r="2" fill="#E41E26" />
                <defs>
                  <linearGradient id="vanGradient" x1="0%" y1="0%" x2="100%" y2="100%">
                    <stop offset="0%" stopColor="#E41E26" />
                    <stop offset="100%" stopColor="#ff4757" />
                  </linearGradient>
                </defs>
              </svg>
            </motion.div>

            {/* Protective Shield */}
            <motion.div
              className="protection-shield"
              animate={{
                scale: [1, 1.2, 1],
                opacity: [0.3, 0.6, 0.3]
              }}
              transition={{
                duration: 3,
                repeat: Infinity,
                ease: "easeInOut"
              }}
            >
              <div className="shield-layer shield-layer-1"></div>
              <div className="shield-layer shield-layer-2"></div>
              <div className="shield-layer shield-layer-3"></div>
            </motion.div>

            {/* Energy Particles */}
            <div className="energy-particles">
              {[...Array(12)].map((_, i) => (
                <motion.div
                  key={i}
                  className="energy-particle"
                  animate={{
                    scale: [0, 1, 0],
                    opacity: [0, 1, 0],
                    rotate: [0, 360]
                  }}
                  transition={{
                    duration: 2,
                    repeat: Infinity,
                    delay: i * 0.2,
                    ease: "easeInOut"
                  }}
                  style={{
                    position: 'absolute',
                    left: `${50 + 30 * Math.cos((i * 30) * Math.PI / 180)}%`,
                    top: `${50 + 30 * Math.sin((i * 30) * Math.PI / 180)}%`,
                  }}
                />
              ))}
            </div>
          </div>
        </motion.div>

        {/* Features List */}
        <motion.div
          className="features-list"
          initial={{ opacity: 0, y: 40 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 1.5, duration: 0.8 }}
        >
          <FeatureItem
            icon="🛡️"
            text="Real-time Crime Prevention"
            delay={1.6}
          />
          <FeatureItem
            icon="🧠"
            text="AI-Powered Route Optimization"
            delay={1.8}
          />
          <FeatureItem
            icon="📱"
            text="Edge AI Hazard Detection"
            delay={2.0}
          />
          <FeatureItem
            icon="☁️"
            text="Huawei Cloud Integration"
            delay={2.2}
          />
        </motion.div>

        {/* Get Started Button */}
        <motion.div
          className="onboarding-action"
          initial={{ opacity: 0, y: 50 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 2.4, duration: 0.8 }}
        >
          <motion.button
            className="get-started-btn"
            onClick={handleGetStarted}
            whileHover={{
              scale: 1.05,
              boxShadow: "0 20px 40px rgba(228, 30, 38, 0.4)"
            }}
            whileTap={{ scale: 0.95 }}
            transition={{ type: "spring", stiffness: 300 }}
          >
            <span className="btn-text">Get Started</span>
            <motion.div
              className="btn-arrow"
              animate={{ x: [0, 5, 0] }}
              transition={{ duration: 2, repeat: Infinity }}
            >
              →
            </motion.div>
          </motion.button>
        </motion.div>

        {/* Powered by Huawei */}
        <motion.div
          className="powered-by-footer"
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 2.8, duration: 0.8 }}
        >
          <span>Powered by</span>
          <div className="huawei-brand">
            🔴 <strong>HUAWEI CLOUD</strong>
          </div>
        </motion.div>
      </div>
    </motion.div>
  );
};

const FeatureItem = ({ icon, text, delay }) => {
  return (
    <motion.div
      className="feature-item"
      initial={{ opacity: 0, x: -30 }}
      animate={{ opacity: 1, x: 0 }}
      transition={{ delay, duration: 0.6 }}
    >
      <span className="feature-icon">{icon}</span>
      <span className="feature-text">{text}</span>
    </motion.div>
  );
};

export default OnboardingScreen;