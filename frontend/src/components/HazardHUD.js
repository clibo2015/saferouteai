import React, { useState, useEffect, useRef } from 'react';
import { motion } from 'framer-motion';
import { useNavigate } from 'react-router-dom';

// Components

// Services
import { apiService } from '../services/apiService';

// Styles
import './HazardHUD.css';

const HazardHUD = () => {
  const navigate = useNavigate();
  const videoRef = useRef(null);

  const [hazardData, setHazardData] = useState(null);
  const [isDetecting] = useState(true);
  const [voiceReporting, setVoiceReporting] = useState(false);

  // AR Navigation State
  const [navActive, setNavActive] = useState(false);
  const [navSteps, setNavSteps] = useState([]);
  const [stepIdx, setStepIdx] = useState(0);
  const [navInfo, setNavInfo] = useState(null);

  useEffect(() => {
    // Check for active navigation session
    const active = localStorage.getItem('sr_nav_active') === 'true';
    if (active) {
      setNavActive(true);
      try {
        setNavSteps(JSON.parse(localStorage.getItem('sr_nav_steps') || '[]'));
        setStepIdx(parseInt(localStorage.getItem('sr_nav_step_idx') || '0'));
        setNavInfo(JSON.parse(localStorage.getItem('sr_nav_info') || 'null'));
      } catch (e) {
        console.error('Failed to load AR nav state', e);
      }
    }

    const initializeCamera = async () => {
      try {
        if (navigator.mediaDevices && navigator.mediaDevices.getUserMedia) {
          const stream = await navigator.mediaDevices.getUserMedia({
            video: { facingMode: 'environment', width: 640, height: 480 }
          });
          if (videoRef.current) {
            videoRef.current.srcObject = stream;
            videoRef.current.play().catch(e => {
              if (e.name !== 'AbortError') console.error('Video play failed:', e);
            });
          }
        } else {
          // If no camera, we still show the HUD but with a dark placeholder
          console.warn('Camera access not supported');
        }
      } catch (error) {
        console.error('Camera initialization failed:', error);
      }
    };

    const fetchRealHazardData = async () => {
      try {
        // Get current location for context
        const location = await apiService.getCurrentLocation();

        // Fetch real hazard zones from backend
        const hazardZones = await apiService.getHazardZones({
          north: location.latitude + 0.05,
          south: location.latitude - 0.05,
          east: location.longitude + 0.05,
          west: location.longitude - 0.05
        });

        // Transform backend data to HUD format
        const hazardData = {
          hazards: (hazardZones.hazard_zones || []).map(zone => ({
            id: zone.id || Date.now(),
            type: zone.type || zone.hazard_type || 'hazard',
            confidence: (zone.confidence || zone.severity || 0.5) * 100,
            position: { x: 320, y: 400 },
            bbox: { x: 280, y: 380, width: 80, height: 60 }
          })),
          gpsCoordinates: {
            latitude: location.latitude,
            longitude: location.longitude
          },
          cameraInfo: {
            id: 'EDGE-AI-PROD-01',
            distance: 'Ready',
            direction: 'FORWARD'
          }
        };

        setHazardData(hazardData);
      } catch (error) {
        console.error('Failed to fetch real hazard data:', error);
        setHazardData({
          hazards: [],
          gpsCoordinates: { latitude: -26.2041, longitude: 28.0473 },
          cameraInfo: { id: 'EDGE-AI-OFFLINE', distance: 'N/A', direction: 'FORWARD' }
        });
      }
    };

    const startRealTimeDetection = () => {
      // Poll for hazard updates every 5 seconds
      const interval = setInterval(async () => {
        try {
          const location = await apiService.getCurrentLocation();
          const hazardZones = await apiService.getHazardZones({
            north: location.latitude + 0.01,
            south: location.latitude - 0.01,
            east: location.longitude + 0.01,
            west: location.longitude - 0.01
          });

          if (hazardZones.hazard_zones?.length > 0) {
            const latestHazard = hazardZones.hazard_zones[0];
            setHazardData(prev => ({
              ...prev,
              hazards: [{
                id: Date.now(),
                type: latestHazard.type || latestHazard.hazard_type || 'hazard',
                confidence: (latestHazard.confidence || latestHazard.severity || 0.7) * 100,
                position: { x: 280 + Math.random() * 80, y: 350 + Math.random() * 50 },
                bbox: { x: 280, y: 380, width: 80, height: 60 }
              }]
            }));

            // Clear temporary detection after 3 seconds to keep UI clean
            setTimeout(() => {
              setHazardData(prev => ({ ...prev, hazards: [] }));
            }, 3000);
          }
        } catch (error) {
          // Continue
        }
      }, 5000);

      return () => clearInterval(interval);
    };

    const initializeHazardDetection = async () => {
      await initializeCamera();
      await fetchRealHazardData();
      const stopDetection = startRealTimeDetection();
      return stopDetection;
    };

    const detectorCleanup = initializeHazardDetection();
    return () => {
      detectorCleanup.then(cleanupFn => cleanupFn && cleanupFn());
      cleanup();
    };
  }, []);

  const cleanup = () => {
    if (videoRef.current && videoRef.current.srcObject) {
      const tracks = videoRef.current.srcObject.getTracks();
      tracks.forEach(track => track.stop());
    }
  };

  const handleVoiceReport = () => {
    setVoiceReporting(true);

    // Simulate voice reporting
    setTimeout(() => {
      setVoiceReporting(false);
    }, 3000);
  };


  const handleSwitchToMap = () => {
    navigate('/navigation');
  };

  const getManeuverInfo = (step) => {
    if (!step) return { icon: '🏁', label: 'Arrived' };
    const type = step.maneuver?.type || '';
    const modifier = step.maneuver?.modifier || '';
    if (type === 'depart') return { icon: '🚗', label: 'Head' };
    if (type === 'arrive') return { icon: '🏁', label: 'Arrive' };
    if (modifier.includes('right')) return { icon: '↗️', label: 'Turn Right' };
    if (modifier.includes('left')) return { icon: '↖️', label: 'Turn Left' };
    if (modifier.includes('straight')) return { icon: '⬆️', label: 'Go Straight' };
    return { icon: '➡️', label: 'Turn' };
  };

  const currentStep = navSteps[stepIdx];
  const maneuver = getManeuverInfo(currentStep);

  const handleEmergencyAlert = () => {
    // In a real app, this would trigger emergency services
    alert('Emergency alert sent to authorities and emergency contacts!');
  };

  return (
    <motion.div
      className="hazard-hud"
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
      transition={{ duration: 0.6 }}
    >

      {/* HUD Header */}
      <motion.div
        className="hud-header"
        initial={{ y: -20, opacity: 0 }}
        animate={{ y: 0, opacity: 1 }}
        transition={{ delay: 0.2, duration: 0.6 }}
      >
        <div className="hud-title">
          <div className="title-icon">
            <svg width="24" height="24" viewBox="0 0 24 24" fill="none">
              <path
                d="M16 2L26 8V14C26 22 16 30 16 30S6 22 6 14V8L16 2Z"
                fill="url(#hudShieldGradient)"
              />
              <defs>
                <linearGradient id="hudShieldGradient" x1="0%" y1="0%" x2="100%" y2="100%">
                  <stop offset="0%" stopColor="#E41E26" />
                  <stop offset="100%" stopColor="#ff4757" />
                </linearGradient>
              </defs>
            </svg>
          </div>
          <span>SafeRoute AI</span>
        </div>

        <div className="hud-subtitle">EDGE-AI HAZARD DETECTION</div>
      </motion.div>

      {/* Camera Feed Container */}
      <motion.div
        className="camera-container"
        initial={{ scale: 0.95, opacity: 0 }}
        animate={{ scale: 1, opacity: 1 }}
        transition={{ delay: 0.4, duration: 0.8 }}
      >
        {/* HUD Frame */}
        <div className="hud-frame">
          <div className="frame-corner frame-corner-tl"></div>
          <div className="frame-corner frame-corner-tr"></div>
          <div className="frame-corner frame-corner-bl"></div>
          <div className="frame-corner frame-corner-br"></div>

          <div className="frame-edge frame-edge-top"></div>
          <div className="frame-edge frame-edge-bottom"></div>
          <div className="frame-edge frame-edge-left"></div>
          <div className="frame-edge frame-edge-right"></div>
        </div>

        {/* Camera Feed */}
        <div className="camera-feed">
          <video
            ref={videoRef}
            className="camera-video"
            autoPlay
            playsInline
            muted
          />
          {!videoRef.current?.srcObject && (
            <div className="camera-placeholder">
              <div className="placeholder-icon">
                <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
                  <path d="M23 19a2 2 0 0 1-2 2H3a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h4l2-3h6l2 3h4a2 2 0 0 1 2 2z"></path>
                  <circle cx="12" cy="13" r="4"></circle>
                </svg>
              </div>
              <span>Camera Feed Offline</span>
              <small>Using Edge AI Local Analysis</small>
            </div>
          )}

          {/* Camera overlay elements */}
          <div className="camera-overlay">
            {/* GPS Info */}
            <div className="gps-info">
              <div className="gps-coords">
                GPS: {hazardData?.gpsCoordinates.latitude.toFixed(4)}°N,
                {hazardData?.gpsCoordinates.longitude.toFixed(4)}°W
              </div>
            </div>

            {/* Camera Info */}
            <div className="camera-info">
              <div className="camera-details">
                <span>CAM ID: {hazardData?.cameraInfo.id}</span>
                <span>{hazardData?.cameraInfo.distance}</span>
                <span>{hazardData?.cameraInfo.direction}</span>
              </div>
            </div>

            {/* Crosshair */}
            <div className="crosshair">
              <div className="crosshair-h"></div>
              <div className="crosshair-v"></div>
            </div>

            {/* Grid overlay */}
            <div className="grid-overlay">
              {[...Array(8)].map((_, i) => (
                <div key={`h-${i}`} className="grid-line grid-line-h" style={{ top: `${(i + 1) * 12.5}%` }} />
              ))}
              {[...Array(12)].map((_, i) => (
                <div key={`v-${i}`} className="grid-line grid-line-v" style={{ left: `${(i + 1) * 8.33}%` }} />
              ))}
            </div>
          </div>

          {/* Hazard Detection Overlays */}
          {hazardData?.hazards.map((hazard) => (
            <HazardDetection key={hazard.id} hazard={hazard} />
          ))}

          {/* AR Navigation Overlay */}
          {navActive && currentStep && (
            <div className="ar-nav-overlay">
              <div className="ar-maneuver-icon">{maneuver.icon}</div>
              <div className="ar-nav-details">
                <div className="ar-nav-instruction">{maneuver.label}{currentStep.name ? ` onto ${currentStep.name}` : ''}</div>
                <div className="ar-nav-sub">Tactical AR Route Active</div>
              </div>
              <div className="ar-nav-meta">
                <div className="ar-nav-eta">{navInfo?.duration || '--'}</div>
                <div className="ar-nav-dist">{currentStep.distance ? `${(currentStep.distance / 1000).toFixed(1)} km` : '--'}</div>
              </div>
            </div>
          )}
        </div>

        {/* Detection Status */}
        <motion.div
          className="detection-status"
          animate={{
            opacity: isDetecting ? [0.7, 1, 0.7] : 0.5
          }}
          transition={{
            duration: 2,
            repeat: isDetecting ? Infinity : 0,
            ease: "easeInOut"
          }}
        >
          <div className="status-indicator">
            <div className={`status-dot ${isDetecting ? 'active' : ''}`}></div>
            <span>AI Detection: {isDetecting ? 'ACTIVE' : 'INACTIVE'}</span>
          </div>
        </motion.div>
      </motion.div>

      {/* Side Controls */}
      <motion.div
        className="side-controls"
        initial={{ x: -50, opacity: 0 }}
        animate={{ x: 0, opacity: 1 }}
        transition={{ delay: 0.6, duration: 0.6 }}
      >
        <button className="control-icon" onClick={() => { }}>
          <ShieldIcon />
        </button>
        <button className="control-icon" onClick={() => { }}>
          <CarIcon />
        </button>
        <button className="control-icon" onClick={() => { }}>
          <RadarIcon />
        </button>
      </motion.div>

      {/* Voice Reporting */}
      <motion.div
        className="voice-reporting"
        initial={{ y: 50, opacity: 0 }}
        animate={{ y: 0, opacity: 1 }}
        transition={{ delay: 0.8, duration: 0.6 }}
      >
        <div className="voice-waveform">
          {voiceReporting && (
            <motion.div className="waveform-container">
              {[...Array(20)].map((_, i) => (
                <motion.div
                  key={i}
                  className="waveform-bar"
                  animate={{
                    scaleY: voiceReporting ? [0.3, 1, 0.3] : 0.3
                  }}
                  transition={{
                    duration: 0.5,
                    repeat: voiceReporting ? Infinity : 0,
                    delay: i * 0.05,
                    ease: "easeInOut"
                  }}
                />
              ))}
            </motion.div>
          )}
        </div>

        <div className="voice-status">
          {voiceReporting ? (
            <span className="reporting-text">Reporting via Edge AI NLP...</span>
          ) : (
            <span className="ready-text">Voice Report Ready</span>
          )}
        </div>
      </motion.div>

      {/* Bottom Controls */}
      <motion.div
        className="bottom-controls"
        initial={{ y: 100, opacity: 0 }}
        animate={{ y: 0, opacity: 1 }}
        transition={{ delay: 1, duration: 0.6 }}
      >
        <button
          className="control-btn secondary map-switch"
          onClick={handleSwitchToMap}
          title="Switch to Map"
        >
          <RadarIcon />
        </button>

        <motion.button
          className={`voice-btn ${voiceReporting ? 'active' : ''}`}
          onClick={handleVoiceReport}
          disabled={voiceReporting}
          whileHover={{ scale: 1.05 }}
          whileTap={{ scale: 0.95 }}
        >
          <MicIcon />
          {voiceReporting && <div className="voice-pulse"></div>}
        </motion.button>

        <button
          className="control-btn emergency"
          onClick={handleEmergencyAlert}
        >
          <AlertIcon />
        </button>
      </motion.div>

    </motion.div>
  );
};

const HazardDetection = ({ hazard }) => {
  return (
    <motion.div
      className="hazard-detection"
      style={{
        left: hazard.bbox.x,
        top: hazard.bbox.y,
        width: hazard.bbox.width,
        height: hazard.bbox.height,
      }}
      initial={{ scale: 0, opacity: 0 }}
      animate={{ scale: 1, opacity: 1 }}
      exit={{ scale: 0, opacity: 0 }}
      transition={{ type: "spring", stiffness: 300 }}
    >
      {/* Detection Box */}
      <div className="detection-box">
        <div className="box-corner box-corner-tl"></div>
        <div className="box-corner box-corner-tr"></div>
        <div className="box-corner box-corner-bl"></div>
        <div className="box-corner box-corner-br"></div>
      </div>

      {/* Detection Label */}
      <motion.div
        className="detection-label"
        initial={{ y: -10, opacity: 0 }}
        animate={{ y: -30, opacity: 1 }}
        transition={{ delay: 0.2, duration: 0.4 }}
      >
        <div className="label-content">
          <span className="hazard-type">
            Hazard Detected: {hazard.type.charAt(0).toUpperCase() + hazard.type.slice(1)}
          </span>
          <span className="confidence">
            ({Math.round(hazard.confidence)}% Confidence)
          </span>
        </div>
        <div className="label-arrow"></div>
      </motion.div>
    </motion.div>
  );
};

// Icon Components
const ShieldIcon = () => (
  <svg width="20" height="20" viewBox="0 0 20 20" fill="none">
    <path d="M10 2L18 6V10C18 14 10 18 10 18S2 14 2 10V6L10 2Z" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
  </svg>
);

const CarIcon = () => (
  <svg width="20" height="20" viewBox="0 0 20 20" fill="none">
    <path d="M7 17C8.10457 17 9 16.1046 9 15C9 13.8954 8.10457 13 7 13C5.89543 13 5 13.8954 5 15C5 16.1046 5.89543 17 7 17Z" stroke="currentColor" strokeWidth="2" />
    <path d="M17 17C18.1046 17 19 16.1046 19 15C19 13.8954 18.1046 13 17 13C15.8954 13 15 13.8954 15 15C15 16.1046 15.8954 17 17 17Z" stroke="currentColor" strokeWidth="2" />
    <path d="M5 15H3V11L5 7H19L21 11V15H19" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
  </svg>
);

const RadarIcon = () => (
  <svg width="20" height="20" viewBox="0 0 20 20" fill="none">
    <circle cx="10" cy="10" r="8" stroke="currentColor" strokeWidth="2" />
    <circle cx="10" cy="10" r="4" stroke="currentColor" strokeWidth="2" />
    <path d="M10 2V10L14 14" stroke="currentColor" strokeWidth="2" strokeLinecap="round" />
  </svg>
);


const MicIcon = () => (
  <svg width="20" height="20" viewBox="0 0 20 20" fill="none">
    <path d="M12 1C12 0.447715 11.5523 0 11 0H9C8.44772 0 8 0.447715 8 1V7C8 7.55228 8.44772 8 9 8H11C11.5523 8 12 7.55228 12 7V1Z" fill="currentColor" />
    <path d="M19 10V11C19 15.4183 15.4183 19 11 19H9C4.58172 19 1 15.4183 1 11V10" stroke="currentColor" strokeWidth="2" strokeLinecap="round" />
    <path d="M10 19V23" stroke="currentColor" strokeWidth="2" strokeLinecap="round" />
    <path d="M6 23H14" stroke="currentColor" strokeWidth="2" strokeLinecap="round" />
  </svg>
);

const AlertIcon = () => (
  <svg width="20" height="20" viewBox="0 0 20 20" fill="none">
    <path d="M10.29 3.86L1.82 18C1.64466 18.3024 1.55611 18.6453 1.56331 18.9945C1.57051 19.3437 1.67319 19.6831 1.86 19.9784C2.04681 20.2737 2.31259 20.5141 2.62618 20.6747C2.93977 20.8352 3.28907 20.9099 3.64 20.89H20.36C20.7109 20.9099 21.0602 20.8352 21.3738 20.6747C21.6874 20.5141 21.9532 20.2737 22.14 19.9784C22.3268 19.6831 22.4295 19.3437 22.4367 18.9945C22.4439 18.6453 22.3553 18.3024 22.18 18L13.71 3.86C13.5317 3.56611 13.2807 3.32312 12.9812 3.15448C12.6817 2.98585 12.3438 2.89725 12 2.89725C11.6562 2.89725 11.3183 2.98585 11.0188 3.15448C10.7193 3.32312 10.4683 3.56611 10.29 3.86V3.86Z" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
    <path d="M12 9V13" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
    <path d="M12 17H12.01" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
  </svg>
);

export default HazardHUD;