import React, { useEffect, useRef, useState } from 'react';
import './HuaweiMapComponent.css';
import { apiService } from '../services/apiService';

const HuaweiMapComponent = ({
  center = { lat: -26.2041, lng: 28.0473 }, // Johannesburg, South Africa
  zoom = 10,
  onMapReady = null,
  showHazards = true,
  showHeatmap = true,
  onMarkerClick = null,
  onHazardDetected = null,
  showHazardZones = true,
  showCrimeHotspots = true,
  autoUpdate = false,
  updateInterval = 30000,
  route = null,
  userLocation = null
}) => {
  const mapRef = useRef(null);
  const [map, setMap] = useState(null);
  const [mapLoaded, setMapLoaded] = useState(false);
  const [error, setError] = useState(null);
  const [markersLoaded, setMarkersLoaded] = useState(0);
  const [heatmapLoaded, setHeatmapLoaded] = useState(false);
  const [backendConnected, setBackendConnected] = useState(false);

  useEffect(() => {
    loadHuaweiMapKit();

    // Set up auto-update if enabled
    let updateTimer;
    if (autoUpdate && updateInterval > 0) {
      updateTimer = setInterval(() => {
        if (map && backendConnected) {
          console.log('🔄 Auto-updating map data...');
          if (showHazards) loadHazardMarkers(map);
          if (showHeatmap) loadSafetyHeatmap(map);
        }
      }, updateInterval);
    }

    return () => {
      if (updateTimer) clearInterval(updateTimer);
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [autoUpdate, updateInterval, map, backendConnected]);

  useEffect(() => {
    if (map && route) {
      drawRoute(map, route);
    }
    if (map && userLocation) {
      updateUserLocationMarker(map, userLocation);
    }
  }, [map, route, userLocation]);

  const routePolylinesRef = useRef([]);
  const userMarkerRef = useRef(null);

  const loadHuaweiMapKit = async () => {
    try {
      // Get Map Kit configuration from backend - using apiService for authenticated request
      const response = await apiService.request('/api/v1/map/config');

      setBackendConnected(true);
      const mapConfig = response.map_config;

      // Load Huawei Map Kit JavaScript API using official method
      if (!window.HWMapJsSDK) {
        await loadMapScript(mapConfig);
      } else {
        // If already loaded, initialize directly
        initializeMap(mapConfig);
      }

    } catch (err) {
      console.error('Map Kit loading error:', err);
      setError(err.message);
    }
  };

  const loadMapScript = (mapConfig) => {
    const encodedApiKey = mapConfig.api_key;
    return new Promise((resolve, reject) => {
      // Create global callback function for Huawei Map Kit
      window.initHuaweiMap = () => {
        try {
          initializeMap({ api_key: encodedApiKey });
          resolve();
        } catch (err) {
          reject(err);
        }
      };

      // Official Huawei Map Kit script loading method
      // Using global mapapi.cloud.huawei.com with region=DE for DRE cluster compatibility
      const baseScriptUrl = mapConfig.js_api_url || 'https://mapapi.cloud.huawei.com/mapjs/v1/api/js';
      const scriptUrl = `${baseScriptUrl}?callback=initHuaweiMap&key=${encodedApiKey}&region=DE`;

      console.log('📡 Loading Huawei Map Kit from:', scriptUrl.split('&key=')[0] + '&key=HIDDEN');

      if (document.querySelector(`script[src*="mapapi.cloud.huawei.com"]`)) {
        // Script already exists, call callback directly
        window.initHuaweiMap();
        return;
      }

      const script = document.createElement('script');
      script.src = scriptUrl;
      script.async = true;
      script.onerror = (err) => {
        console.error('❌ Script load error:', err);
        reject(new Error('Failed to load Huawei Map Kit script. Possible causes: Invalid API Key, Domain not authorized, or Region mismatch.'));
      };

      // Note: onload is not needed because callback handles initialization
      document.head.appendChild(script);
    });
  };

  const initializeMap = (mapConfig) => {
    if (!mapRef.current || !window.HWMapJsSDK) {
      console.error('Map container or HWMapJsSDK not available');
      return;
    }

    try {
      // Official Huawei Map Kit initialization
      const mapOptions = {
        center: { lat: center.lat, lng: center.lng },
        zoom: zoom,
        language: 'ENG',
        sourceType: 'raster',
        gestureHandling: 'greedy',
        zoomControl: true,
        mapTypeControl: true,
        streetViewControl: false,
        fullscreenControl: true,
        rotateControl: true,
        scaleControl: true
      };

      const mapInstance = new window.HWMapJsSDK.HWMap(mapRef.current, mapOptions);

      setMap(mapInstance);
      setMapLoaded(true);

      // Load SafeRouteAI specific data
      if (showHazards || showCrimeHotspots) {
        loadHazardMarkers(mapInstance);
      }

      if (showHeatmap) {
        loadSafetyHeatmap(mapInstance);
      }

      if (showHazardZones) {
        loadHazardZones(mapInstance);
      }

      // Notify parent component
      if (onMapReady) {
        onMapReady(mapInstance);
      }

      console.log('✅ Huawei Map Kit initialized successfully');

    } catch (err) {
      console.error('Map initialization error:', err);
      setError('Failed to initialize Huawei Map Kit');
    }
  };

  const updateUserLocationMarker = (mapInstance, location) => {
    if (!window.HWMapJsSDK) return;

    if (userMarkerRef.current) {
      userMarkerRef.current.setPosition(new window.HWMapJsSDK.LatLng(location.latitude, location.longitude));
    } else {
      userMarkerRef.current = new window.HWMapJsSDK.Marker({
        position: new window.HWMapJsSDK.LatLng(location.latitude, location.longitude),
        map: mapInstance,
        title: 'Your Location',
        icon: {
          url: '/icons/user-location.png',
          scaledSize: new window.HWMapJsSDK.Size(36, 36)
        },
        zIndex: 100
      });
    }

    // Smoothly pan to user
    mapInstance.setCenter(new window.HWMapJsSDK.LatLng(location.latitude, location.longitude));
  };

  const drawRoute = (mapInstance, routeData) => {
    if (!window.HWMapJsSDK || !routeData || !routeData.segments) return;

    // Clear existing route
    routePolylinesRef.current.forEach(polyline => polyline.setMap(null));
    routePolylinesRef.current = [];

    // Draw each segment with appropriate safety color
    routeData.segments.forEach(segment => {
      // Color based on risk score (lower is safer/greener)
      // Risk score: 0.0 (safe) to 1.0 (dangerous)
      const color = segment.risk_score > 0.7 ? '#ff4757' : // Red for danger
        segment.risk_score > 0.4 ? '#ffa502' : // Orange for moderate
          '#2ed573'; // Green for safe

      const path = [
        new window.HWMapJsSDK.LatLng(segment.start_lat, segment.start_lng),
        new window.HWMapJsSDK.LatLng(segment.end_lat, segment.end_lng)
      ];

      const polyline = new window.HWMapJsSDK.Polyline({
        path: path,
        map: mapInstance,
        strokeColor: color,
        strokeWeight: 6,
        strokeOpacity: 0.8,
        lineCap: 'round',
        lineJoin: 'round'
      });

      routePolylinesRef.current.push(polyline);
    });

    // Fit bounds to route
    const bounds = new window.HWMapJsSDK.LatLngBounds();
    routeData.segments.forEach(segment => {
      bounds.extend(new window.HWMapJsSDK.LatLng(segment.start_lat, segment.start_lng));
      bounds.extend(new window.HWMapJsSDK.LatLng(segment.end_lat, segment.end_lng));
    });
    mapInstance.fitBounds(bounds);
  };

  const loadHazardMarkers = async (mapInstance) => {
    try {
      const data = await apiService.request('/api/v1/map/markers');

      if (data.success && window.HWMapJsSDK) {
        data.markers.forEach(marker => {
          // Create Huawei Map Kit marker
          const mapMarker = new window.HWMapJsSDK.Marker({
            position: new window.HWMapJsSDK.LatLng(
              marker.position.lat,
              marker.position.lng
            ),
            map: mapInstance,
            title: marker.title,
            icon: {
              url: marker.icon?.url || '/icons/default-marker.png',
              scaledSize: new window.HWMapJsSDK.Size(32, 32)
            }
          });

          // Add info window
          const infoWindow = new window.HWMapJsSDK.InfoWindow({
            content: `
              <div class="marker-info">
                <h4>${marker.title}</h4>
                <p>${marker.description}</p>
                <div class="severity-indicator">
                  <span>Risk Level: ${(marker.severity * 100).toFixed(0)}%</span>
                  <div class="severity-bar">
                    <div class="severity-fill" style="width: ${marker.severity * 100}%; background-color: ${marker.severity > 0.7 ? '#ff4757' : marker.severity > 0.4 ? '#ffa502' : '#2ed573'}"></div>
                  </div>
                </div>
              </div>
            `
          });

          mapMarker.addListener('click', () => {
            infoWindow.open(mapInstance, mapMarker);
            if (onMarkerClick) onMarkerClick(marker);
          });
        });

        setMarkersLoaded(data.markers.length);
      }
    } catch (err) {
      console.error('Failed to load hazard markers:', err);
    }
  };

  const loadSafetyHeatmap = async (mapInstance) => {
    try {
      const data = await apiService.request('/api/v1/map/safety-heatmap');

      if (data.success && window.HWMapJsSDK && window.HWMapJsSDK.visualization) {
        const heatmapData = data.heatmap_data.map(point => ({
          location: new window.HWMapJsSDK.LatLng(
            point.location.lat,
            point.location.lng
          ),
          weight: point.weight
        }));

        // Create safety heatmap overlay
        // eslint-disable-next-line no-unused-vars
        const _heatmap = new window.HWMapJsSDK.visualization.HeatmapLayer({
          data: heatmapData,
          map: mapInstance,
          radius: 50,
          opacity: 0.6,
          gradient: [
            'rgba(0, 255, 255, 0)',
            'rgba(0, 255, 255, 1)',
            'rgba(0, 191, 255, 1)',
            'rgba(0, 127, 255, 1)',
            'rgba(0, 63, 255, 1)',
            'rgba(0, 0, 255, 1)',
            'rgba(0, 0, 223, 1)',
            'rgba(0, 0, 191, 1)',
            'rgba(0, 0, 159, 1)',
            'rgba(0, 0, 127, 1)',
            'rgba(63, 0, 91, 1)',
            'rgba(127, 0, 63, 1)',
            'rgba(191, 0, 31, 1)',
            'rgba(255, 0, 0, 1)'
          ]
        });

        setHeatmapLoaded(true);
      }
    } catch (err) {
      console.error('Failed to load safety heatmap:', err);
    }
  };

  const loadHazardZones = async (mapInstance) => {
    try {
      const data = await apiService.request('/api/v1/map/hazard-zones');

      if (data.success && window.HWMapJsSDK && data.hazard_zones) {
        data.hazard_zones.forEach(zone => {
          // Create hazard zone circle overlay
          const hazardZone = new window.HWMapJsSDK.Circle({
            center: new window.HWMapJsSDK.LatLng(zone.center.lat, zone.center.lng),
            radius: zone.radius,
            map: mapInstance,
            fillColor: zone.fillColor || '#ff4757',
            fillOpacity: zone.fillOpacity || 0.3,
            strokeColor: zone.strokeColor || '#ff4757',
            strokeOpacity: zone.strokeOpacity || 0.8,
            strokeWeight: zone.strokeWeight || 2
          });

          // Add click listener for hazard zone details
          hazardZone.addListener('click', () => {
            if (onHazardDetected) {
              onHazardDetected(zone);
            }
          });
        });
      }
    } catch (err) {
      console.error('Failed to load hazard zones:', err);
    }
  };

  if (error) {
    return (
      <div className="map-error">
        <h3>🗺️ Map Loading Error</h3>
        <p>{error}</p>
        <div className="error-details">
          <p><strong>Possible solutions:</strong></p>
          <ul>
            <li>Check your internet connection</li>
            <li>Verify API key configuration in AppGallery Connect</li>
            <li>Ensure authorized domains are configured</li>
            <li>Try refreshing the page</li>
          </ul>
        </div>
      </div>
    );
  }

  return (
    <div className="huawei-map-container">
      <div
        ref={mapRef}
        className="huawei-map"
        style={{ width: '100%', height: '400px' }}
      />
      {!mapLoaded && (
        <div className="map-loading" role="status" aria-live="polite">
          <div className="loading-spinner" aria-hidden="true"></div>
          <p>Loading Huawei Map Kit for South Africa...</p>
          <small>Connecting to real-time crime data...</small>
          <div className="loading-progress">
            <div className="progress-bar">
              <div
                className="progress-fill"
                style={{ width: `${backendConnected ? 50 : 25}%` }}
              ></div>
            </div>
            <span className="progress-text">
              {backendConnected ? 'Connected to backend' : 'Connecting...'}
            </span>
          </div>
        </div>
      )}
      {mapLoaded && (
        <div className="map-controls">
          <div className="map-legend">
            <h4>🛡️ SafeRouteAI Legend</h4>
            <div className="legend-item">
              <span className="legend-color" style={{ backgroundColor: '#ff4757' }}></span>
              <span>High Risk Areas</span>
            </div>
            <div className="legend-item">
              <span className="legend-color" style={{ backgroundColor: '#ffa502' }}></span>
              <span>Moderate Risk Areas</span>
            </div>
            <div className="legend-item">
              <span className="legend-color" style={{ backgroundColor: '#2ed573' }}></span>
              <span>Low Risk Areas</span>
            </div>
          </div>

          <div className="map-status">
            <div className={`status-indicator ${backendConnected ? 'connected' : 'disconnected'}`}>
              <span className="status-dot"></span>
              <span className="status-text">
                {backendConnected ? 'Live Data' : 'Offline'}
              </span>
            </div>
            {backendConnected && (
              <div className="data-stats">
                <span>📍 {markersLoaded} Crime Hotspots</span>
                <span>🗺️ {heatmapLoaded ? 'Heatmap Active' : 'Loading...'}</span>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
};

export default HuaweiMapComponent;