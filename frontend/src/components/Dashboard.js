import React, { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { useNavigate } from 'react-router-dom';
import { CircularProgressbar, buildStyles } from 'react-circular-progressbar';
import 'react-circular-progressbar/dist/styles.css';

// Components
import NavigationBar from './common/NavigationBar';

// Services
import { apiService } from '../services/apiService';

// Styles
import './Dashboard.css';

const Dashboard = ({ backendStatus, user, onLogout }) => {
  const navigate = useNavigate();
  const [dashboardData, setDashboardData] = useState(null);
  const [isLoading, setIsLoading] = useState(true);
  const [safetyScore, setSafetyScore] = useState(0);

  useEffect(() => {
    loadDashboardData();
  }, []);

  useEffect(() => {
    // Animate safety score
    if (dashboardData) {
      const timer = setTimeout(() => {
        animateSafetyScore(dashboardData.safetyScore);
      }, 500);
      return () => clearTimeout(timer);
    }
  }, [dashboardData]);

  const loadDashboardData = async () => {
    try {
      setIsLoading(true);

      // Get real data from backend
      const [apiStatus, mapConfig, markers, journeysData] = await Promise.all([
        apiService.getStatus(),
        apiService.getMapConfig(),
        apiService.getMapMarkers(),
        apiService.getUserJourneys(5).catch(() => ({ success: true, journeys: [] }))
      ]);

      // Calculate stats based on real data
      const totalMarkers = markers.total_markers || 0;
      const highRiskMarkers = markers.markers?.filter(m => m.severity > 0.7).length || 0;

      // Calculate safety score (default 100 if no markers/high risk)
      const calculatedSafetyScore = totalMarkers > 0
        ? Math.max(50, 100 - (highRiskMarkers / totalMarkers * 100))
        : 100;

      // Calculate total kilometers from journeys
      const journeys = journeysData.journeys || [];
      const totalKm = journeys.reduce((acc, curr) => acc + (curr.distance_km || 0), 0);

      const data = {
        safetyScore: Math.round(calculatedSafetyScore),
        totalKilometers: Math.round(totalKm),
        activeAlerts: highRiskMarkers,
        recentJourneys: journeys.map(j => ({
          id: j.id,
          name: j.name && j.name !== "Unknown Destination" ? `Drive to ${j.name}` : `Route ${j.id.substring(0, 8)}`,
          date: new Date(j.created_at).toLocaleDateString(),
          distance: `${j.distance_km?.toFixed(1) || 0} km`,
          duration: `${j.duration_minutes || 0}m`,
        })),
        backendStatus: {
          isOnline: true,
          mapKitEnabled: mapConfig.success,
          crimeDataPoints: totalMarkers,
          version: apiStatus.version || '3.0.0'
        }
      };

      setDashboardData(data);
    } catch (error) {
      console.error('Failed to load dashboard data:', error);
      // Use empty state when backend is unavailable - NO mock data
      setDashboardData({
        safetyScore: 0,
        totalKilometers: 0,
        activeAlerts: 0,
        recentJourneys: [],
        backendStatus: {
          isOnline: false,
          mapKitEnabled: false,
          crimeDataPoints: 0,
          version: 'Offline',
          error: error.message
        }
      });
    } finally {
      setIsLoading(false);
    }
  };

  const animateSafetyScore = (targetScore) => {
    let currentScore = 0;
    const increment = targetScore / 50; // Animate over 50 steps

    const timer = setInterval(() => {
      currentScore += increment;
      if (currentScore >= targetScore) {
        currentScore = targetScore;
        clearInterval(timer);
      }
      setSafetyScore(Math.round(currentScore));
    }, 30);
  };

  const handleJourneyClick = (journey) => {
    // Navigate to navigation screen with journey details
    navigate('/navigation', { state: { journey } });
  };

  const handleStartNewRoute = () => {
    navigate('/navigation');
  };

  const handleLogout = () => {
    if (onLogout) onLogout();
    navigate('/auth');
  };

  if (isLoading) {
    return <DashboardSkeleton />;
  }

  return (
    <motion.div
      className="dashboard"
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: -20 }}
      transition={{ duration: 0.6 }}
    >

      <div className="dashboard-content">
        {/* Header */}
        <motion.div
          className="dashboard-header"
          initial={{ opacity: 0, y: -20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.2, duration: 0.6 }}
        >
          <div className="header-user">
            <div className="user-avatar">
              {user?.name?.charAt(0) || 'C'}
            </div>
            <div className="user-info">
              <div className="welcome-text">Welcome,</div>
              <div className="user-name">{user?.name || 'Commander'}</div>
            </div>
          </div>
          <button className="logout-btn" onClick={handleLogout} title="Logout">
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4"></path>
              <polyline points="16 17 21 12 16 7"></polyline>
              <line x1="21" y1="12" x2="9" y2="12"></line>
            </svg>
          </button>
        </motion.div>

        {/* Stats Cards */}
        <motion.div
          className="stats-grid"
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.3, duration: 0.6 }}
          role="region"
          aria-label="Safety statistics"
        >
          <StatsCard
            title="Safety Score"
            value={`${safetyScore}%`}
            className="stats-safety"
            delay={0.4}
            ariaLabel={`Current safety score is ${safetyScore} percent`}
          />
          <StatsCard
            title="Total Safe Kilometers"
            value={dashboardData.totalKilometers > 0 ? `${dashboardData.totalKilometers}km` : '0km'}
            subtitle={dashboardData.totalKilometers === 0 ? "Ready to drive!" : ""}
            className="stats-distance"
            delay={0.5}
            ariaLabel={`Total safe kilometers traveled: ${dashboardData.totalKilometers}`}
          />
          <StatsCard
            title="Active Alerts"
            value={dashboardData.activeAlerts}
            subtitle={dashboardData.activeAlerts === 0 ? "All clear in area" : "High severe risk zones"}
            className="stats-alerts"
            delay={0.6}
            ariaLabel={`Active alerts: ${dashboardData.activeAlerts === 0 ? 'No alerts' : dashboardData.activeAlerts}`}
          />
        </motion.div>

        {/* Safety Score Circle */}
        <motion.div
          className="safety-score-section"
          initial={{ opacity: 0, scale: 0.8 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ delay: 0.7, duration: 0.8 }}
        >
          <div className="safety-score-container">
            <div className="safety-score-circle">
              <CircularProgressbar
                value={safetyScore}
                text={`${safetyScore}%`}
                styles={buildStyles({
                  pathColor: safetyScore >= 90 ? '#00ff88' : safetyScore >= 70 ? '#ffa502' : '#ff3838',
                  textColor: '#ffffff',
                  trailColor: 'rgba(255, 255, 255, 0.1)',
                  backgroundColor: 'transparent',
                  textSize: '24px',
                  pathTransitionDuration: 2,
                })}
                strokeWidth={8}
              />

              {/* Animated particles around circle */}
              <div className="score-particles">
                {[...Array(8)].map((_, i) => (
                  <motion.div
                    key={i}
                    className="score-particle"
                    animate={{
                      rotate: [0, 360],
                      scale: [1, 1.2, 1],
                      opacity: [0.3, 1, 0.3]
                    }}
                    transition={{
                      duration: 4,
                      repeat: Infinity,
                      delay: i * 0.5,
                      ease: "easeInOut"
                    }}
                    style={{
                      position: 'absolute',
                      left: `${50 + 45 * Math.cos((i * 45) * Math.PI / 180)}%`,
                      top: `${50 + 45 * Math.sin((i * 45) * Math.PI / 180)}%`,
                    }}
                  />
                ))}
              </div>
            </div>
          </div>
        </motion.div>

        {/* Recent Journeys */}
        <motion.div
          className="recent-journeys-section"
          initial={{ opacity: 0, y: 30 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.9, duration: 0.6 }}
        >
          <div className="section-header">
            <h3 className="section-title">Recent Safe Journeys</h3>
            <button className="section-action">•••</button>
          </div>

          <div className="journeys-list">
            {dashboardData.recentJourneys.length > 0 ? (
              dashboardData.recentJourneys.map((journey, index) => (
                <JourneyCard
                  key={journey.id}
                  journey={journey}
                  onClick={() => handleJourneyClick(journey)}
                  delay={1 + index * 0.1}
                />
              ))
            ) : (
              <motion.div
                className="empty-journeys"
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                transition={{ delay: 1 }}
              >
                <div className="empty-icon">🗺️</div>
                <div className="empty-text">No trips yet</div>
                <div className="empty-subtext">Tap the plus button below to start your first safe journey</div>
              </motion.div>
            )}
          </div>
        </motion.div>

        {/* Map + routing stack */}
        <motion.div
          className="powered-by-section"
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 1.5, duration: 0.6 }}
        >
          <span>Powered by</span>
          <div className="powered-by-logo">
            🌍 <strong>OPENSTREETMAP + OSRM</strong>
          </div>
          {dashboardData?.backendStatus && (
            <div className="backend-status">
              <span className={`status-dot ${dashboardData.backendStatus.isOnline ? 'online' : 'offline'}`}></span>
              <span className="status-text">
                {dashboardData.backendStatus.isOnline ? 'Live Data' : 'Offline Mode'}
              </span>
              {dashboardData.backendStatus.isOnline && (
                <span className="data-info">
                  {dashboardData.backendStatus.crimeDataPoints} crime hotspots
                </span>
              )}
            </div>
          )}
        </motion.div>
      </div>

      {/* Floating Action Button */}
      <motion.button
        className="fab start-route-fab"
        onClick={handleStartNewRoute}
        initial={{ scale: 0, rotate: -180 }}
        animate={{ scale: 1, rotate: 0 }}
        transition={{ delay: 1.2, type: "spring", stiffness: 200 }}
        whileHover={{ scale: 1.1 }}
        whileTap={{ scale: 0.9 }}
      >
        <svg width="24" height="24" viewBox="0 0 24 24" fill="none">
          <path
            d="M12 2L22 8.5V15.5C22 19.5 12 22 12 22S2 19.5 2 15.5V8.5L12 2Z"
            fill="currentColor"
          />
          <path
            d="M8 12L10 14L16 8"
            stroke="white"
            strokeWidth="2"
            strokeLinecap="round"
            strokeLinejoin="round"
          />
        </svg>
      </motion.button>

      <NavigationBar currentPage="dashboard" />
    </motion.div>
  );
};

const StatsCard = ({ title, value, subtitle, className, delay, ariaLabel }) => {
  return (
    <motion.div
      className={`stats-card ${className}`}
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay, duration: 0.6 }}
      whileHover={{ y: -2, transition: { duration: 0.2 } }}
      role="button"
      tabIndex={0}
      aria-label={ariaLabel || `${title}: ${value}`}
      onKeyDown={(e) => {
        if (e.key === 'Enter' || e.key === ' ') {
          // Handle keyboard interaction
          e.preventDefault();
        }
      }}
    >
      <div className="stats-title">{title}</div>
      <div className="stats-value">{value}</div>
      {subtitle && <div className="stats-subtitle">{subtitle}</div>}
    </motion.div>
  );
};

const JourneyCard = ({ journey, onClick, delay }) => {
  return (
    <motion.div
      className="journey-card"
      initial={{ opacity: 0, x: -20 }}
      animate={{ opacity: 1, x: 0 }}
      transition={{ delay, duration: 0.6 }}
      onClick={onClick}
      whileHover={{ x: 5, transition: { duration: 0.2 } }}
      whileTap={{ scale: 0.98 }}
    >
      <div className="journey-thumbnail">
        <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
          <polygon points="1 6 1 22 8 18 16 22 23 18 23 2 16 6 8 2 1 6"></polygon>
          <line x1="8" y1="2" x2="8" y2="18"></line>
          <line x1="16" y1="6" x2="16" y2="22"></line>
        </svg>
      </div>
      <div className="journey-info">
        <div className="journey-name">{journey.name}</div>
        <div className="journey-details">
          {journey.date}, {journey.distance}, {journey.duration}
        </div>
      </div>
      <div className="journey-arrow">
        <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
          <path
            d="M6 4L10 8L6 12"
            stroke="currentColor"
            strokeWidth="2"
            strokeLinecap="round"
            strokeLinejoin="round"
          />
        </svg>
      </div>
    </motion.div>
  );
};

const DashboardSkeleton = () => {
  return (
    <div className="dashboard">
      <div className="dashboard-content">
        <div className="dashboard-header">
          <div className="skeleton" style={{ width: '150px', height: '32px' }}></div>
          <div className="skeleton" style={{ width: '80px', height: '20px' }}></div>
        </div>

        <div className="stats-grid">
          {[...Array(3)].map((_, i) => (
            <div key={i} className="stats-card">
              <div className="skeleton" style={{ width: '100%', height: '60px' }}></div>
            </div>
          ))}
        </div>

        <div className="safety-score-section">
          <div className="skeleton" style={{ width: '200px', height: '200px', borderRadius: '50%' }}></div>
        </div>

        <div className="recent-journeys-section">
          <div className="skeleton" style={{ width: '200px', height: '24px', marginBottom: '16px' }}></div>
          {[...Array(4)].map((_, i) => (
            <div key={i} className="skeleton" style={{ width: '100%', height: '60px', marginBottom: '8px' }}></div>
          ))}
        </div>
      </div>
    </div>
  );
};

export default Dashboard;