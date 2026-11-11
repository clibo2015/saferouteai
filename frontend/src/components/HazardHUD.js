import React, { useState, useEffect, useRef, useCallback } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { useNavigate } from 'react-router-dom';

// TensorFlow.js & On-Device Object Detection
import * as tf from '@tensorflow/tfjs';
import * as cocoSsd from '@tensorflow-models/coco-ssd';

// Services
import { apiService } from '../services/apiService';
import {
  getNearbyHotspots,
  buildVoiceMessage,
  speak,
  shouldSuggestReroute,
  getRiskColor,
  getRiskLevel,
} from '../services/crimeHotspots';

// Styles
import './HazardHUD.css';

// ── Inline crime hotspot data (mirrors SafeRouteMapComponent) ─────────────────
// We import by reference so both components stay in sync.
import { SA_CRIME_HOTSPOTS } from '../data/crimeHotspotsData';

const HazardHUD = () => {
  const navigate = useNavigate();
  const videoRef = useRef(null);

  const [hazardData, setHazardData] = useState(null);
  const [isDetecting, setIsDetecting] = useState(true);
  const [modelLoaded, setModelLoaded] = useState(false);
  const [voiceReporting, setVoiceReporting] = useState(false);
  const modelRef = useRef(null);
  const requestAnimRef = useRef(null);
  const lastDetectionTimeRef = useRef(0);

  // ── Proximity Alert State ──────────────────────────────────────────────────
  const [dangerAlert, setDangerAlert] = useState(null);   // { hotspot, dismissed }
  const [showReroute, setShowReroute] = useState(false);
  const [voiceMuted, setVoiceMuted] = useState(false);
  const alertedHotspotsRef = useRef(new Set()); // track already-alerted IDs
  const proximityIntervalRef = useRef(null);

  // AR Navigation State
  const [navActive, setNavActive] = useState(false);
  const [navSteps, setNavSteps] = useState([]);
  const [stepIdx, setStepIdx] = useState(0);
  const [navInfo, setNavInfo] = useState(null);
  const [fullRouteCoords, setFullRouteCoords] = useState([]);
  const [simCoordIdx, setSimCoordIdx] = useState(0);
  const [isSimulating, setIsSimulating] = useState(localStorage.getItem('sr_sim_active') === 'true');
  const [simPos, setSimPos] = useState(() => {
    try {
      return JSON.parse(localStorage.getItem('sr_sim_pos') || 'null');
    } catch (e) {
      return null;
    }
  });
  const lastUpdateRef = useRef(Date.now());
  useEffect(() => {
    // Check for active navigation session
    const active = localStorage.getItem('sr_nav_active') === 'true';
    if (active) {
      setNavActive(true);
      try {
        setNavSteps(JSON.parse(localStorage.getItem('sr_nav_steps') || '[]'));
        setStepIdx(parseInt(localStorage.getItem('sr_nav_step_idx') || '0'));
        setNavInfo(JSON.parse(localStorage.getItem('sr_nav_info') || 'null'));
        setFullRouteCoords(JSON.parse(localStorage.getItem('sr_nav_full_coords') || '[]'));
        setSimCoordIdx(parseInt(localStorage.getItem('sr_sim_coord_idx') || '0', 10));
      } catch (e) {
        console.error('Failed to load AR nav state', e);
      }
    }

    // Auto-advance logic and simulation
    const startNavigationLogic = () => {
      const navInterval = setInterval(async () => {
        try {
          let currentPos;
          
          if (isSimulating) {
            // Simulation logic
            currentPos = moveSimulatedUser();
          } else {
            // Real location logic
            const location = await apiService.getCurrentLocation();
            currentPos = { lat: location.latitude, lng: location.longitude };
          }

          if (currentPos && navActive && navSteps.length > 0) {
            checkStepAdvancement(currentPos);
          }
        } catch (e) {
          console.error('Nav logic error', e);
        }
      }, 2000);

      return () => clearInterval(navInterval);
    };

    const initializeCamera = async () => {
      try {
        if (navigator.mediaDevices && navigator.mediaDevices.getUserMedia) {
          const stream = await navigator.mediaDevices.getUserMedia({
            video: { facingMode: 'environment', width: { ideal: 640 }, height: { ideal: 480 } }
          });
          if (videoRef.current) {
            videoRef.current.srcObject = stream;
            videoRef.current.play().catch(e => {
              if (e.name !== 'AbortError') console.error('Video play failed:', e);
            });
          }
        } else {
          console.warn('Camera access not supported');
        }
      } catch (error) {
        console.error('Camera initialization failed:', error);
      }
    };

    // ── Real On-Device TensorFlow.js COCO-SSD Detection Loop ────────────────
    const initializeTFModel = async () => {
      try {
        await tf.ready();
        // Load lightweight MobileNet-v2 SSD model for high FPS mobile inference
        const loadedModel = await cocoSsd.load({ base: 'lite_mobilenet_v2' });
        modelRef.current = loadedModel;
        setModelLoaded(true);
        startLiveInference();
      } catch (err) {
        console.warn('Could not load on-device TF model, using fallback:', err);
      }
    };

    const startLiveInference = () => {
      const detectFrame = async () => {
        const now = Date.now();
        // Run inference at ~5 to 8 FPS to prevent mobile device overheating while driving
        if (now - lastDetectionTimeRef.current > 150) {
          lastDetectionTimeRef.current = now;
          if (
            videoRef.current &&
            videoRef.current.readyState === 4 &&
            modelRef.current
          ) {
            try {
              const predictions = await modelRef.current.detect(videoRef.current);
              
              // Filter for driving-relevant hazards
              const relevantClasses = [
                'person', 'bicycle', 'car', 'motorcycle', 'bus', 'truck', 'dog', 'stop sign', 'traffic light'
              ];
              
              const detectedHazards = predictions
                .filter(p => relevantClasses.includes(p.class.toLowerCase()) && p.score > 0.45)
                .map((p, idx) => ({
                  id: `tf_${p.class}_${idx}`,
                  type: p.class === 'person' ? 'Pedestrian' : p.class.toUpperCase(),
                  confidence: p.score * 100,
                  bbox: {
                    x: p.bbox[0],
                    y: p.bbox[1],
                    width: p.bbox[2],
                    height: p.bbox[3],
                  }
                }));

              setHazardData(prev => ({
                ...prev,
                hazards: detectedHazards,
                cameraInfo: {
                  id: 'EDGE-AI-TFJS-COCO',
                  distance: detectedHazards.length > 0 ? `${detectedHazards.length} Objects Tracked` : 'Clear Road',
                  direction: 'FORWARD'
                }
              }));
            } catch (inferErr) {
              // Ignore single-frame drops
            }
          }
        }
        requestAnimRef.current = requestAnimationFrame(detectFrame);
      };

      requestAnimRef.current = requestAnimationFrame(detectFrame);
    };

    const initializeHazardDetection = async () => {
      await initializeCamera();
      await initializeTFModel();
    };

    const detectorCleanup = initializeHazardDetection();
    const navLogicCleanup = startNavigationLogic();

    // Listen for cross-tab storage changes
    const handleStorageChange = (e) => {
      if (e.key === 'sr_sim_active') {
        setIsSimulating(e.newValue === 'true');
      } else if (e.key === 'sr_sim_pos' && e.newValue) {
        try {
          setSimPos(JSON.parse(e.newValue));
        } catch (_) {}
      } else if (e.key === 'sr_sim_coord_idx' && e.newValue) {
        setSimCoordIdx(parseInt(e.newValue, 10));
      } else if (e.key === 'sr_nav_step_idx' && e.newValue) {
        setStepIdx(parseInt(e.newValue, 10));
      } else if (e.key === 'sr_nav_full_coords' && e.newValue) {
        setFullRouteCoords(JSON.parse(e.newValue));
      }
    };
    window.addEventListener('storage', handleStorageChange);

    return () => {
      detectorCleanup.then(cleanupFn => cleanupFn && cleanupFn());
      navLogicCleanup();
      window.removeEventListener('storage', handleStorageChange);
      cleanup();
    };
  }, [isSimulating, navActive, navSteps, stepIdx]);

  // ── Proximity Scan Loop — runs every 3 seconds while navigating ───────────
  const runProximityScan = useCallback(async () => {
    if (!navActive && !isSimulating) return;

    let pos = null;
    if (isSimulating && simPos) {
      pos = simPos;
    } else {
      try {
        const loc = await apiService.getCurrentLocation();
        pos = { lat: loc.latitude, lng: loc.longitude };
      } catch (_) { return; }
    }

    if (!pos || !SA_CRIME_HOTSPOTS?.length) return;

    const nearby = getNearbyHotspots(pos.lat, pos.lng, SA_CRIME_HOTSPOTS);
    if (!nearby.length) return;

    const closest = nearby[0];

    // Only alert once per hotspot entry (reset when user moves away)
    if (alertedHotspotsRef.current.has(closest.id)) return;
    alertedHotspotsRef.current.add(closest.id);

    // Show visual danger banner
    setDangerAlert(closest);
    setShowReroute(shouldSuggestReroute(closest));

    // Voice warning (unless muted)
    if (!voiceMuted) {
      speak(buildVoiceMessage(closest));
    }

    // Auto-dismiss banner after 12 seconds if user doesn't act
    setTimeout(() => {
      setDangerAlert(prev => prev?.id === closest.id ? null : prev);
    }, 12000);
  }, [navActive, isSimulating, simPos, voiceMuted]);

  // Clear alerted hotspot cache when user moves >500m from it
  const cleanupAlertCache = useCallback(async () => {
    if (!alertedHotspotsRef.current.size) return;
    let pos = isSimulating && simPos ? simPos : null;
    if (!pos) {
      try {
        const loc = await apiService.getCurrentLocation();
        pos = { lat: loc.latitude, lng: loc.longitude };
      } catch (_) { return; }
    }
    if (!pos) return;

    import('../services/crimeHotspots').then(({ haversineKm }) => {
      SA_CRIME_HOTSPOTS?.forEach(h => {
        if (alertedHotspotsRef.current.has(h.id)) {
          if (haversineKm(pos.lat, pos.lng, h.lat, h.lng) > 0.5) {
            alertedHotspotsRef.current.delete(h.id);
          }
        }
      });
    });
  }, [isSimulating, simPos]);

  useEffect(() => {
    proximityIntervalRef.current = setInterval(() => {
      runProximityScan();
      cleanupAlertCache();
    }, 3000);
    return () => clearInterval(proximityIntervalRef.current);
  }, [runProximityScan, cleanupAlertCache]);

  // Broadcast re-route request to the map tab via localStorage
  const requestReroute = useCallback(() => {
    if (!dangerAlert) return;
    localStorage.setItem('sr_reroute_request', JSON.stringify({
      ts: Date.now(),
      avoidLat: dangerAlert.lat,
      avoidLng: dangerAlert.lng,
      reason: dangerAlert.name,
    }));
    speak(`Re-routing to avoid ${dangerAlert.name}. Calculating safer route.`);
    setDangerAlert(null);
    setShowReroute(false);
  }, [dangerAlert]);

  // dismiss alert
  const dismissAlert = useCallback(() => {
    setDangerAlert(null);
    setShowReroute(false);
  }, []);

  const checkStepAdvancement = (pos) => {
    if (stepIdx >= navSteps.length - 1) return;

    const nextStep = navSteps[stepIdx + 1];
    if (nextStep && nextStep.maneuver && nextStep.maneuver.location) {
      const [sLng, sLat] = nextStep.maneuver.location;
      const dist = haversineKm(pos.lat, pos.lng, sLat, sLng);
      
      // If within 50 meters of the next maneuver point, advance
      if (dist < 0.05) {
        const newIdx = stepIdx + 1;
        setStepIdx(newIdx);
        localStorage.setItem('sr_nav_step_idx', newIdx.toString());
        console.log(`Step advanced to ${newIdx}: ${nextStep.name || 'Next maneuver'}`);
      }
    }
  };

  const moveSimulatedUser = () => {
    if (!fullRouteCoords.length) return null;

    const now = Date.now();
    const dt = (now - lastUpdateRef.current) / 1000; // seconds
    lastUpdateRef.current = now;

    // Simulation speed: ~40 km/h = 11.1 m/s
    const speed = 0.0111; // km/s
    let distanceToMove = speed * dt;

    let curIdx = simCoordIdx;
    let pos = simPos;

    // If no simPos yet, start at current coord location
    if (!pos && fullRouteCoords[curIdx]) {
      pos = { lat: fullRouteCoords[curIdx][0], lng: fullRouteCoords[curIdx][1] };
    }

    while (distanceToMove > 0 && curIdx < fullRouteCoords.length - 1) {
      const nextCoord = fullRouteCoords[curIdx + 1];
      const dist = haversineKm(pos.lat, pos.lng, nextCoord[0], nextCoord[1]);

      if (distanceToMove >= dist) {
        distanceToMove -= dist;
        curIdx++;
        pos = { lat: nextCoord[0], lng: nextCoord[1] };
      } else {
        const ratio = distanceToMove / dist;
        pos = {
          lat: pos.lat + (nextCoord[0] - pos.lat) * ratio,
          lng: pos.lng + (nextCoord[1] - pos.lng) * ratio
        };
        distanceToMove = 0;
      }
    }

    setSimPos(pos);
    setSimCoordIdx(curIdx);
    localStorage.setItem('sr_sim_pos', JSON.stringify(pos));
    localStorage.setItem('sr_sim_coord_idx', curIdx.toString());
    return pos;
  };

  const haversineKm = (lat1, lng1, lat2, lng2) => {
    const R = 6371;
    const dLat = (lat2 - lat1) * Math.PI / 180;
    const dLng = (lng2 - lng1) * Math.PI / 180;
    const a = Math.sin(dLat / 2) ** 2 + Math.cos(lat1 * Math.PI / 180) * Math.cos(lat2 * Math.PI / 180) * Math.sin(dLng / 2) ** 2;
    return R * 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));
  };

  const cleanup = () => {
    if (requestAnimRef.current) {
      cancelAnimationFrame(requestAnimRef.current);
    }
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

  const toggleSimulation = () => {
    const newState = !isSimulating;
    setIsSimulating(newState);
    localStorage.setItem('sr_sim_active', newState ? 'true' : 'false');
    lastUpdateRef.current = Date.now();
    if (newState) {
      // Starting simulation, find closest coordinate
      if (fullRouteCoords.length > 0) {
        let startPos;
        let startIdx = 0;
        
        if (navSteps[stepIdx]) {
          const [lng, lat] = navSteps[stepIdx].maneuver.location;
          startPos = { lat, lng };
          
          let minDist = Infinity;
          fullRouteCoords.forEach((c, i) => {
            const d = haversineKm(lat, lng, c[0], c[1]);
            if (d < minDist) {
              minDist = d;
              startIdx = i;
            }
          });
        } else {
          startPos = { lat: fullRouteCoords[0][0], lng: fullRouteCoords[0][1] };
        }

        setSimPos(startPos);
        setSimCoordIdx(startIdx);
        localStorage.setItem('sr_sim_pos', JSON.stringify(startPos));
        localStorage.setItem('sr_sim_coord_idx', startIdx.toString());
      }
    }
  };

  const resetSimulation = () => {
    setIsSimulating(false);
    setSimPos(null);
    setSimCoordIdx(0);
    localStorage.removeItem('sr_sim_active');
    localStorage.removeItem('sr_sim_pos');
    localStorage.removeItem('sr_sim_coord_idx');
    localStorage.removeItem('sr_nav_active');
    // Force a fresh GPS check logic
    apiService.getCurrentLocation();
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

      {/* ── LIVE DANGER PROXIMITY BANNER ─────────────────────────────── */}
      <AnimatePresence>
        {dangerAlert && (
          <motion.div
            className="danger-proximity-banner"
            style={{ borderColor: getRiskColor(dangerAlert.risk), boxShadow: `0 0 24px ${getRiskColor(dangerAlert.risk)}88` }}
            initial={{ y: -80, opacity: 0 }}
            animate={{ y: 0, opacity: 1 }}
            exit={{ y: -80, opacity: 0 }}
            transition={{ duration: 0.35, ease: 'easeOut' }}
          >
            <div className="dpb-icon" style={{ color: getRiskColor(dangerAlert.risk) }}>⚠️</div>
            <div className="dpb-body">
              <div className="dpb-level" style={{ color: getRiskColor(dangerAlert.risk) }}>
                {getRiskLevel(dangerAlert.risk)} RISK — {dangerAlert.type?.toUpperCase()}
              </div>
              <div className="dpb-name">{dangerAlert.name}</div>
              <div className="dpb-street">{dangerAlert.street}</div>
              <div className="dpb-dist">{dangerAlert.distM}m ahead · {dangerAlert.label}</div>
            </div>
            <div className="dpb-actions">
              {showReroute && (
                <button className="dpb-btn dpb-reroute" onClick={requestReroute}>
                  🔃 Safer Route
                </button>
              )}
              <button
                className="dpb-btn dpb-mute"
                onClick={() => setVoiceMuted(m => !m)}
                title={voiceMuted ? 'Unmute voice' : 'Mute voice'}
              >
                {voiceMuted ? '🔇' : '🔊'}
              </button>
              <button className="dpb-btn dpb-dismiss" onClick={dismissAlert}>✕</button>
            </div>
          </motion.div>
        )}
      </AnimatePresence>

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
                GPS: {(simPos?.lat || hazardData?.gpsCoordinates.latitude || 0).toFixed(4)}°N,
                {(simPos?.lng || hazardData?.gpsCoordinates.longitude || 0).toFixed(4)}°W
              </div>
              {isSimulating && <div className="sim-badge">SIMULATION ACTIVE</div>}
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
            <div className={`status-dot ${modelLoaded ? 'active' : ''}`}></div>
            <span>{modelLoaded ? 'EDGE AI: NEURAL VISION ACTIVE' : 'EDGE AI: LOADING MODEL...'}</span>
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
        <button 
          className={`control-icon sim-toggle ${isSimulating ? 'active' : ''}`} 
          onClick={toggleSimulation}
          title={isSimulating ? "Stop Simulation" : "Start Simulation"}
        >
          {isSimulating ? '⏹️' : '🚀'}
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

        {isSimulating && (
          <button
            className="control-btn secondary go-live"
            onClick={resetSimulation}
            style={{ color: '#ff6b6b', borderColor: 'rgba(255, 107, 107, 0.4)' }}
            title="Return to Real Location"
          >
            🛰️
          </button>
        )}

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