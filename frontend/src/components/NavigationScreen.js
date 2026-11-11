import React, { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { useNavigate, useLocation } from 'react-router-dom';

// Components
import NavigationBar from './common/NavigationBar';
import SafeRouteMapComponent from './SafeRouteMapComponent';

// Services
import { apiService } from '../services/apiService';

// Styles
import './NavigationScreen.css';

const NavigationScreen = () => {
  const navigate = useNavigate();
  const location = useLocation();

  const [routeData, setRouteData] = useState(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isNavigating, setIsNavigating] = useState(false);
  const [realTimeHazards, setRealTimeHazards] = useState([]);
  const [safetyScore, setSafetyScore] = useState(98);
  const [searchQuery, setSearchQuery] = useState('');
  const [isSearching, setIsSearching] = useState(false);
  const [userLocation, setUserLocation] = useState(null);
  const [showSearchBox, setShowSearchBox] = useState(false);

  useEffect(() => {
    const initializeNavigation = async () => {
      try {
        setIsLoading(true);

        // Get current location
        const location = await apiService.getCurrentLocation();
        setUserLocation(location);

        // Check if we have a specific journey from dashboard
        const journeyData = location.state?.journey;

        // Check if there's an ongoing navigation session in localStorage
        const isNavActive = localStorage.getItem('sr_nav_active') === 'true';

        if (journeyData) {
          // Load specific journey route
          await loadJourneyRoute(journeyData, location);
        } else if (isNavActive) {
          // Restore active session
          const savedRoute = JSON.parse(localStorage.getItem('sr_nav_info') || 'null');
          if (savedRoute) {
            setRouteData({ route: savedRoute, backendData: { isReal: true } });
            setSafetyScore(savedRoute.safetyScore);
            setIsNavigating(true);
          }
        }
        // No default route loading anymore. The user must explicitly search.

      } catch (error) {
        console.error('Failed to initialize navigation:', error);
        setRouteData({
          error: true,
          errorMessage: error.message || 'Failed to load route data',
          route: null,
          backendData: { isReal: false, error: error.message }
        });
      } finally {
        setIsLoading(false);
      }
    };

    initializeNavigation();
  }, [location.state]);

  const loadJourneyRoute = async (journey, currentLoc) => {
    try {
      const routeRequest = {
        start_point: { lat: currentLoc.latitude, lng: currentLoc.longitude },
        end_point: { lat: currentLoc.latitude + 0.02, lng: currentLoc.longitude + 0.02 },
        departure_time: new Date().toISOString(),
        safety_preferences: { avoid_high_crime: true, priority: "safety" }
      };

      const optimizedRoute = await apiService.optimizeRoute(routeRequest);

      if (optimizedRoute.success) {
        const navigationData = {
          route: {
            id: optimizedRoute.route_data.route_id,
            safetyScore: Math.round(optimizedRoute.route_data.overall_safety_score * 100),
            eta: Math.round(optimizedRoute.route_data.total_time_minutes),
            distance: optimizedRoute.route_data.total_distance_km,
            segments: optimizedRoute.route_data.segments
          },
          backendData: { isReal: true, routeId: optimizedRoute.route_data.route_id }
        };

        setRouteData(navigationData);
        setSafetyScore(navigationData.route.safetyScore);
      }
    } catch (error) {
      console.error('Failed to load journey:', error);
    }
  };

  const loadDefaultRoute = async (currentLoc) => {
    try {
      const routeRequest = {
        start_point: { lat: currentLoc.latitude, lng: currentLoc.longitude },
        end_point: { lat: currentLoc.latitude + 0.05, lng: currentLoc.longitude + 0.03 },
        departure_time: new Date().toISOString(),
        safety_preferences: { avoid_high_crime: true, priority: "safety" }
      };

      const optimizedRoute = await apiService.optimizeRoute(routeRequest);

      if (optimizedRoute.success) {
        setRouteData({
          route: {
            id: optimizedRoute.route_data.route_id,
            safetyScore: Math.round(optimizedRoute.route_data.overall_safety_score * 100),
            eta: Math.round(optimizedRoute.route_data.total_time_minutes),
            distance: optimizedRoute.route_data.total_distance_km,
            segments: optimizedRoute.route_data.segments
          },
          backendData: { isReal: true }
        });
        setSafetyScore(Math.round(optimizedRoute.route_data.overall_safety_score * 100));
      }
    } catch (error) {
      console.error('Failed to load default route:', error);
    }
  };

  const handleSearch = async (e) => {
    if (e) e.preventDefault();
    if (!searchQuery.trim()) return;

    try {
      setIsSearching(true);
      const res = await apiService.geocode(searchQuery);

      if (res.success) {
        const dest = res.location;
        const start = userLocation || { latitude: -26.2041, longitude: 28.0473 };

        const optimizedRoute = await apiService.optimizeRoute({
          start_point: { lat: start.latitude, lng: start.longitude },
          end_point: { lat: dest.lat, lng: dest.lng },
          departure_time: new Date().toISOString(),
          safety_preferences: { priority: "safety", avoid_high_crime: true }
        });

        if (optimizedRoute.success) {
          setRouteData({
            route: {
              id: optimizedRoute.route_data.route_id,
              safetyScore: Math.round(optimizedRoute.route_data.overall_safety_score * 100),
              eta: Math.round(optimizedRoute.route_data.total_time_minutes),
              distance: optimizedRoute.route_data.total_distance_km,
              segments: optimizedRoute.route_data.segments
            },
            backendData: { isReal: true }
          });
          setSafetyScore(Math.round(optimizedRoute.route_data.overall_safety_score * 100));
          setShowSearchBox(false);
        }
      }
    } catch (error) {
      console.error('Search failed:', error);
      alert('Address not found or service unavailable.');
    } finally {
      setIsSearching(false);
    }
  };

  const handleMapReady = (map) => {
    // Map instance ready for navigation
    console.log('SafeRoute Map ready for navigation');
  };

  const handleMarkerClick = (markerInfo) => {
    console.log('Marker clicked:', markerInfo);
    // Handle marker interactions (show details, navigate around hazard, etc.)
  };

  const handleHazardDetected = (hazard) => {
    console.log('New hazard detected:', hazard);
    setRealTimeHazards(prev => [...prev, hazard]);

    // Update safety score based on hazards
    const hazardImpact = hazard.severity * 10;
    setSafetyScore(prev => Math.max(50, prev - hazardImpact));

    // Notify user of new hazard
    if (hazard.severity > 0.7) {
      alert(`High severity ${hazard.type} detected ahead! Consider alternate route.`);
    }
  };

  const handleStartNavigation = async () => {
    if (!routeData?.route) return;

    try {
      setIsNavigating(true);
      // Persist journey to backend
      const lastSeg = routeData.route.segments[routeData.route.segments.length - 1];
      const journeyToSave = {
        start_lat: userLocation?.latitude || -26.2041,
        start_lng: userLocation?.longitude || 28.0473,
        end_lat: lastSeg.end_lat,
        end_lng: lastSeg.end_lng,
        distance_km: routeData.route.distance,
        duration_minutes: routeData.route.eta,
        safety_score: routeData.route.safetyScore / 100,
        route_data: {
          id: routeData.route.id,
          segments: routeData.route.segments,
          query: searchQuery
        }
      };

      await apiService.saveJourney(journeyToSave);
      console.log('✅ Journey persisted to backend');

      // Save to localStorage for AR HUD and resuming
      localStorage.setItem('sr_nav_active', 'true');
      localStorage.setItem('sr_nav_steps', JSON.stringify(routeData.route.segments || []));
      localStorage.setItem('sr_nav_step_idx', '0');
      localStorage.setItem('sr_nav_info', JSON.stringify(routeData.route));

      // Navigate to HUD after a brief delay
      setTimeout(() => {
        navigate('/hazard-hud');
      }, 1500);
    } catch (error) {
      console.error('Failed to start navigation:', error);
      setIsNavigating(false);
    }
  };

  const handleBackToDashboard = () => {
    navigate('/dashboard');
  };

  if (isLoading) {
    return <NavigationSkeleton />;
  }

  return (
    <motion.div
      className="navigation-screen"
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
      transition={{ duration: 0.6 }}
    >

      {/* Header */}
      <motion.div
        className="navigation-header"
        initial={{ y: -20, opacity: 0 }}
        animate={{ y: 0, opacity: 1 }}
        transition={{ delay: 0.2, duration: 0.6 }}
      >
        <div className="header-content">
          <div className="header-logo">
            <div className="logo-shield">
              <svg width="32" height="32" viewBox="0 0 32 32" fill="none">
                <path
                  d="M16 2L26 8V14C26 22 16 30 16 30S6 22 6 14V8L16 2Z"
                  fill="url(#navShieldGradient)"
                />
                <defs>
                  <linearGradient id="navShieldGradient" x1="0%" y1="0%" x2="100%" y2="100%">
                    <stop offset="0%" stopColor="#E41E26" />
                    <stop offset="100%" stopColor="#ff4757" />
                  </linearGradient>
                </defs>
              </svg>
            </div>
            <span className="logo-text">SafeRoute AI</span>
          </div>

          <div className="header-actions">
            {showSearchBox ? (
              <form onSubmit={handleSearch} className="search-form">
                <input
                  type="text"
                  placeholder="Enter destination..."
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  autoFocus
                />
                <button type="submit" disabled={isSearching}>
                  {isSearching ? '...' : <SearchIcon />}
                </button>
                <button type="button" onClick={() => setShowSearchBox(false)}>×</button>
              </form>
            ) : (
              <>
                <button
                  className="header-btn"
                  onClick={() => setShowSearchBox(true)}
                  title="Search Destination"
                >
                  <SearchIcon />
                </button>
                <button
                  className="header-btn"
                  onClick={() => navigate('/dashboard')}
                  title="Dashboard"
                >
                  <SettingsIcon />
                </button>
              </>
            )}
          </div>
        </div>
      </motion.div>

      {/* Map Container — Custom SafeRoute Leaflet Map */}
      <motion.div
        className="map-container"
        initial={{ scale: 0.95, opacity: 0 }}
        animate={{ scale: 1, opacity: 1 }}
        transition={{ delay: 0.4, duration: 0.8 }}
      >
        <SafeRouteMapComponent
          onMapReady={handleMapReady}
          onMarkerClick={handleMarkerClick}
          onHazardDetected={handleHazardDetected}
          route={routeData?.route}
          userLocation={userLocation}
          isActiveNavigation={isNavigating}
          onRouteCalculated={(routeData) => {
            if (routeData?.overall_safety_score) {
              setSafetyScore(Math.round(routeData.overall_safety_score * 100));
            }
          }}
        />

        {/* Route Info Overlay */}
        {routeData?.route && (
          <motion.div
            className="route-info-overlay"
            initial={{ y: 50, opacity: 0 }}
            animate={{ y: 0, opacity: 1 }}
            transition={{ delay: 0.8, duration: 0.6 }}
          >
            <div className="route-info-content">
              <div className="route-stats">
                <div className="route-stat">
                  <div className="stat-icon">🛡️</div>
                  <div className="stat-info">
                    <span className="stat-label">Safety Score:</span>
                    <span className={`stat-value ${safetyScore > 90 ? 'excellent' : safetyScore > 70 ? 'good' : 'warning'}`}>
                      {safetyScore}%
                    </span>
                  </div>
                </div>

                <div className="route-stat">
                  <div className="stat-icon">⏱️</div>
                  <div className="stat-info">
                    <span className="stat-label">ETA:</span>
                    <span className="stat-value eta">{routeData?.route.eta || 12} min</span>
                  </div>
                </div>

                <div className="route-stat">
                  <div className="stat-icon">🚨</div>
                  <div className="stat-info">
                    <span className="stat-label">Live Hazards:</span>
                    <span className={`stat-value ${realTimeHazards.length > 0 ? 'warning' : 'good'}`}>
                      {realTimeHazards.length}
                    </span>
                  </div>
                </div>
              </div>

              <div className="powered-by-mini">
                <span>Powered by</span>
                <div className="powered-by-mini-brand">🛡️ <strong>SAFEROUTE MAP</strong></div>
              </div>
            </div>
          </motion.div>
        )}
      </motion.div>

      {/* Bottom Navigation Controls */}
      <motion.div
        className="navigation-controls"
        initial={{ y: 100, opacity: 0 }}
        animate={{ y: 0, opacity: 1 }}
        transition={{ delay: 1, duration: 0.6 }}
      >
        <div className="controls-content">
          <button
            className="control-btn secondary"
            onClick={handleBackToDashboard}
          >
            <HomeIcon />
          </button>

          {routeData?.route && (
            <motion.button
              className={`start-navigation-btn ${isNavigating ? 'navigating' : ''}`}
              onClick={handleStartNavigation}
              disabled={isNavigating}
              whileHover={{ scale: 1.05 }}
              whileTap={{ scale: 0.95 }}
            >
              {isNavigating ? (
                <>
                  <div className="loading-spinner"></div>
                  <span>Starting...</span>
                </>
              ) : (
                <>
                  <NavigateIcon />
                  <span>Start Navigation</span>
                </>
              )}
            </motion.button>
          )}

          <button className="control-btn secondary">
            <AlertIcon />
          </button>
        </div>
      </motion.div>

      <NavigationBar currentPage="navigation" />
    </motion.div>
  );
};

// Icon Components
const SearchIcon = () => (
  <svg width="20" height="20" viewBox="0 0 20 20" fill="none">
    <circle cx="9" cy="9" r="7" stroke="currentColor" strokeWidth="2" />
    <path d="M21 21L16.65 16.65" stroke="currentColor" strokeWidth="2" strokeLinecap="round" />
  </svg>
);

const SettingsIcon = () => (
  <svg width="20" height="20" viewBox="0 0 20 20" fill="none">
    <circle cx="10" cy="10" r="3" stroke="currentColor" strokeWidth="2" />
    <path d="M10 1V4M10 16V19M4.22 4.22L6.34 6.34M13.66 13.66L15.78 15.78M1 10H4M16 10H19M4.22 15.78L6.34 13.66M13.66 6.34L15.78 4.22" stroke="currentColor" strokeWidth="2" strokeLinecap="round" />
  </svg>
);

const HomeIcon = () => (
  <svg width="20" height="20" viewBox="0 0 20 20" fill="none">
    <path d="M3 9L12 2L21 9V20C21 20.5304 20.7893 21.0391 20.4142 21.4142C20.0391 21.7893 19.5304 22 19 22H5C4.46957 22 3.96086 21.7893 3.58579 21.4142C3.21071 21.0391 3 20.5304 3 20V9Z" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
  </svg>
);

const NavigateIcon = () => (
  <svg width="20" height="20" viewBox="0 0 20 20" fill="none">
    <polygon points="3,11 22,2 13,21 11,13 3,11" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
  </svg>
);

const AlertIcon = () => (
  <svg width="20" height="20" viewBox="0 0 20 20" fill="none">
    <path d="M10.29 3.86L1.82 18C1.64466 18.3024 1.55611 18.6453 1.56331 18.9945C1.57051 19.3437 1.67319 19.6831 1.86 19.9784C2.04681 20.2737 2.31259 20.5141 2.62618 20.6747C2.93977 20.8352 3.28907 20.9099 3.64 20.89H20.36C20.7109 20.9099 21.0602 20.8352 21.3738 20.6747C21.6874 20.5141 21.9532 20.2737 22.14 19.9784C22.3268 19.6831 22.4295 19.3437 22.4367 18.9945C22.4439 18.6453 22.3553 18.3024 22.18 18L13.71 3.86C13.5317 3.56611 13.2807 3.32312 12.9812 3.15448C12.6817 2.98585 12.3438 2.89725 12 2.89725C11.6562 2.89725 11.3183 2.98585 11.0188 3.15448C10.7193 3.32312 10.4683 3.56611 10.29 3.86V3.86Z" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
    <path d="M12 9V13" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
    <path d="M12 17H12.01" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
  </svg>
);

const NavigationSkeleton = () => {
  return (
    <div className="navigation-screen">
      <div className="navigation-header">
        <div className="skeleton" style={{ width: '200px', height: '32px' }}></div>
      </div>
      <div className="map-container">
        <div className="skeleton" style={{ width: '100%', height: '100%' }}></div>
      </div>
      <div className="navigation-controls">
        <div className="skeleton" style={{ width: '100%', height: '60px' }}></div>
      </div>
    </div>
  );
};

export default NavigationScreen;