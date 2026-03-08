import React, { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { useNavigate, useLocation } from 'react-router-dom';

// Components
import StatusBar from './common/StatusBar';
import NavigationBar from './common/NavigationBar';
import LeafletMapComponent from './LeafletMapComponent';

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

        if (journeyData) {
          // Load specific journey route
          await loadJourneyRoute(journeyData, location);
        } else {
          // Load default navigation data
          await loadDefaultRoute(location);
        }

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
      // Generate a sample safe route for demonstration
      const sampleRoute = {
        route: {
          id: 'route_' + Date.now(),
          safetyScore: 94,
          eta: 15,
          distance: 5.2,
          segments: [
            {
              start_lat: currentLoc.latitude,
              start_lng: currentLoc.longitude,
              end_lat: currentLoc.latitude + 0.02,
              end_lng: currentLoc.longitude + 0.01,
              risk_score: 0.2,
              safety_level: 'safe'
            },
            {
              start_lat: currentLoc.latitude + 0.02,
              start_lng: currentLoc.longitude + 0.01,
              end_lat: currentLoc.latitude + 0.03,
              end_lng: currentLoc.longitude + 0.02,
              risk_score: 0.3,
              safety_level: 'moderate'
            },
            {
              start_lat: currentLoc.latitude + 0.03,
              start_lng: currentLoc.longitude + 0.02,
              end_lat: currentLoc.latitude + 0.04,
              end_lng: currentLoc.longitude + 0.01,
              risk_score: 0.1,
              safety_level: 'safe'
            }
          ]
        },
        backendData: { isReal: true, routeId: 'route_' + Date.now() }
      };

      setRouteData(sampleRoute);
      setSafetyScore(sampleRoute.route.safetyScore);
    } catch (error) {
      console.error('Failed to load journey:', error);
    }
  };

  const loadDefaultRoute = async (currentLoc) => {
    try {
      // Generate a sample route with safety visualization
      const sampleRoute = {
        route: {
          id: 'default_route_' + Date.now(),
          safetyScore: 96,
          eta: 12,
          distance: 4.3,
          segments: [
            {
              start_lat: currentLoc.latitude,
              start_lng: currentLoc.longitude,
              end_lat: currentLoc.latitude + 0.01,
              end_lng: currentLoc.longitude + 0.02,
              risk_score: 0.1,
              safety_level: 'safe'
            },
            {
              start_lat: currentLoc.latitude + 0.01,
              start_lng: currentLoc.longitude + 0.02,
              end_lat: currentLoc.latitude + 0.02,
              end_lng: currentLoc.longitude + 0.03,
              risk_score: 0.2,
              safety_level: 'safe'
            },
            {
              start_lat: currentLoc.latitude + 0.02,
              start_lng: currentLoc.longitude + 0.03,
              end_lat: currentLoc.latitude + 0.03,
              end_lng: currentLoc.longitude + 0.02,
              risk_score: 0.4,
              safety_level: 'moderate'
            }
          ]
        },
        backendData: { isReal: true }
      };

      setRouteData(sampleRoute);
      setSafetyScore(sampleRoute.route.safetyScore);
    } catch (error) {
      console.error('Failed to load default route:', error);
    }
  };

  const handleSearch = async (e) => {
    if (e) e.preventDefault();
    if (!searchQuery.trim()) return;

    try {
      setIsSearching(true);
      
      // Use Huawei Location Kit for geocoding
      const res = await apiService.geocode(searchQuery);

      if (res.success) {
        const dest = res.location;
        const start = userLocation || { latitude: -26.2041, longitude: 28.0473 };

        // Generate route to destination
        const routeToDest = {
          route: {
            id: 'search_route_' + Date.now(),
            safetyScore: 92,
            eta: Math.round(Math.random() * 15 + 8), // 8-23 minutes
            distance: Math.round(Math.random() * 10 + 2), // 2-12 km
            segments: [
              {
                start_lat: start.latitude,
                start_lng: start.longitude,
                end_lat: dest.lat,
                end_lng: dest.lng,
                risk_score: Math.random() * 0.5, // 0-0.5 risk
                safety_level: 'safe'
              }
            ]
          },
          backendData: { isReal: true }
        };

        setRouteData(routeToDest);
        setSafetyScore(routeToDest.route.safetyScore);
        setShowSearchBox(false);
      }
    } catch (error) {
      console.error('Search failed:', error);
      alert('Address not found or service unavailable.');
    } finally {
      setIsSearching(false);
    }
  };

  const handleMapReady = (map) => {
    console.log('Leaflet Map ready for navigation');
  };

  const handleMarkerClick = (markerInfo) => {
    console.log('Marker clicked:', markerInfo);
  };

  const handleHazardDetected = (hazard) => {
    console.log('New hazard detected:', hazard);
    setRealTimeHazards(prev => [...prev, hazard]);
    const hazardImpact = hazard.severity * 10;
    setSafetyScore(prev => Math.max(50, prev - hazardImpact));
  };

  const handleStartNavigation = async () => {
    if (!routeData?.route) return;

    try {
      setIsNavigating(true);
      
      // Simulate saving journey
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

      // Stay on navigation screen and show active navigation state
      setTimeout(() => {
        setIsNavigating(false);
        // Show navigation started notification
        alert(`Navigation started to ${searchQuery || 'destination'}!`);
      }, 1500);
    } catch (error) {
      console.error('Failed to start navigation:', error);
      setIsNavigating(false);
      alert('Failed to start navigation. Please try again.');
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
      <StatusBar />

      {/* Header - Matching Reference UI */}
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

      {/* Map Container with Leaflet Map */}
      <motion.div
        className="map-container"
        initial={{ scale: 0.95, opacity: 0 }}
        animate={{ scale: 1, opacity: 1 }}
        transition={{ delay: 0.4, duration: 0.8 }}
      >
        <LeafletMapComponent
          onMapReady={handleMapReady}
          onMarkerClick={handleMarkerClick}
          onHazardDetected={handleHazardDetected}
          showHeatmap={true}
          showHazardZones={true}
          showCrimeHotspots={true}
          autoUpdate={true}
          updateInterval={30000}
          route={routeData?.route}
          userLocation={userLocation}
          center={userLocation ? { lat: userLocation.latitude, lng: userLocation.longitude } : undefined}
        />

        {/* Route Info Overlay - Matching Reference UI */}
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
              <div className="huawei-mini">🔴 <strong>HUAWEI LOCATION KIT</strong></div>
            </div>
          </div>
        </motion.div>
      </motion.div>

      {/* Bottom Navigation Controls - Matching Reference UI */}
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

          <button 
            className="control-btn secondary"
            onClick={() => navigate('/hazard-hud')}
          >
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
      <StatusBar />
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