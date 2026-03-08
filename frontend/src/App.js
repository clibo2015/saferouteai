import React, { useState, useEffect } from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { AnimatePresence } from 'framer-motion';

// Components
import ErrorBoundary from './components/ErrorBoundary';
import OnboardingScreen from './components/OnboardingScreen';
import AuthScreen from './components/AuthScreen';
import Dashboard from './components/Dashboard';
import NavigationScreen from './components/NavigationScreen';
import HazardHUD from './components/HazardHUD';
import LoadingScreen from './components/LoadingScreen';

// Services
import { apiService } from './services/apiService';

// Styles
import './App.css';
import './components/ErrorBoundary.css';

function App() {
  const [isLoading, setIsLoading] = useState(true);
  const [isOnboarded, setIsOnboarded] = useState(false);
  const [isLoggedIn, setIsLoggedIn] = useState(false);
  const [user, setUser] = useState(null);
  const [backendStatus, setBackendStatus] = useState(null);

  useEffect(() => {
    initializeApp();
  }, []);

  const initializeApp = async () => {
    try {
      // Check if user has completed onboarding
      const onboardingStatus = localStorage.getItem('saferoute_onboarded');
      setIsOnboarded(onboardingStatus === 'true');

      // Check if user is logged in
      const authenticated = apiService.isAuthenticated();
      setIsLoggedIn(authenticated);

      if (authenticated) {
        const userData = await apiService.getCurrentUser();
        setUser(userData);
      }

      // Real connectivity check
      const status = await apiService.getStatus();
      setBackendStatus(status);
      setIsLoading(false);
    } catch (error) {
      console.error('Failed to initialize app:', error);
      setIsLoading(false);
    }
  };

  const handleOnboardingComplete = () => {
    localStorage.setItem('saferoute_onboarded', 'true');
    setIsOnboarded(true);
  };

  const handleLoginSuccess = (userData) => {
    setUser(userData);
    setIsLoggedIn(true);
  };

  const handleLogout = () => {
    apiService.logout();
    setIsLoggedIn(false);
    setUser(null);
  };

  if (isLoading) {
    return <LoadingScreen />;
  }

  return (
    <ErrorBoundary>
      <div className="App">
        <Router>
          <AnimatePresence mode="wait">
            <Routes>
              <Route
                path="/"
                element={
                  !isOnboarded ? (
                    <Navigate to="/onboarding" replace />
                  ) : isLoggedIn ? (
                    <Navigate to="/dashboard" replace />
                  ) : (
                    <Navigate to="/auth" replace />
                  )
                }
              />
              <Route
                path="/onboarding"
                element={
                  !isOnboarded ? (
                    <OnboardingScreen onComplete={handleOnboardingComplete} />
                  ) : (
                    <Navigate to="/auth" replace />
                  )
                }
              />
              <Route
                path="/auth"
                element={
                  !isLoggedIn ? (
                    <AuthScreen onLoginSuccess={handleLoginSuccess} />
                  ) : (
                    <Navigate to="/dashboard" replace />
                  )
                }
              />
              <Route
                path="/dashboard"
                element={
                  isLoggedIn ? (
                    <Dashboard backendStatus={backendStatus} user={user} onLogout={handleLogout} />
                  ) : (
                    <Navigate to="/auth" replace />
                  )
                }
              />
              <Route
                path="/navigation"
                element={
                  isLoggedIn ? (
                    <NavigationScreen />
                  ) : (
                    <Navigate to="/auth" replace />
                  )
                }
              />
              <Route
                path="/hazard-hud"
                element={
                  isLoggedIn ? (
                    <HazardHUD />
                  ) : (
                    <Navigate to="/auth" replace />
                  )
                }
              />
              <Route path="*" element={<Navigate to="/" replace />} />
            </Routes>
          </AnimatePresence>
        </Router>
      </div>
    </ErrorBoundary>
  );
}

export default App;