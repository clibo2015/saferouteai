import React, { useEffect, useRef, useState } from 'react';
import { MapContainer, TileLayer, Marker, Popup, Polyline, Circle, useMap } from 'react-leaflet';
import L from 'leaflet';
import './LeafletMapComponent.css';

// Fix for default marker icons in Leaflet
delete L.Icon.Default.prototype._getIconUrl;
L.Icon.Default.mergeOptions({
  iconRetinaUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-icon-2x.png',
  iconUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-icon.png',
  shadowUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-shadow.png',
});

const LeafletMapComponent = ({
  center = { lat: -26.2041, lng: 28.0473 }, // Johannesburg, South Africa
  zoom = 13,
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
  const mapRef = useRef();
  const [mapLoaded, setMapLoaded] = useState(false);
  const [backendConnected, setBackendConnected] = useState(false);

  // Custom icons for different marker types
  const createCustomIcon = (type, severity = 0) => {
    const getColor = () => {
      if (severity > 0.7) return '#ff4757'; // Red for high risk
      if (severity > 0.4) return '#ffa502'; // Orange for medium
      return '#2ed573'; // Green for low risk
    };

    return L.divIcon({
      className: `custom-marker ${type}`,
      html: `
        <div class="marker-container" style="background-color: ${getColor()}; border: 3px solid white; box-shadow: 0 4px 12px rgba(0, 0, 0, 0.4);">
          <div class="marker-inner">
            ${type === 'user' ? '📍' : 
              type === 'hazard' ? '⚠️' : 
              type === 'crime' ? '🚨' : 
              type === 'safe' ? '✅' : '📌'}
          </div>
        </div>
      `,
      iconSize: [36, 36],
      iconAnchor: [18, 36],
      popupAnchor: [0, -36]
    });
  };

  // Map controller component for programmatic control
  const MapController = ({ center, zoom }) => {
    const map = useMap();
    
    useEffect(() => {
      if (center && map) {
        map.setView([center.lat, center.lng], zoom);
      }
    }, [center, zoom, map]);

    return null;
  };

  // Route polyline component
  const RoutePolyline = ({ routeData }) => {
    if (!routeData || !routeData.segments) return null;

    const getColor = (riskScore) => {
      if (riskScore > 0.7) return '#ff4757'; // Red for danger
      if (riskScore > 0.4) return '#ffa502'; // Orange for moderate
      return '#2ed573'; // Green for safe
    };

    const getClass = (riskScore) => {
      if (riskScore > 0.7) return 'danger-route-glow';
      if (riskScore > 0.4) return 'moderate-route-glow';
      return 'safe-route-glow';
    };

    return (
      <>
        {routeData.segments.map((segment, index) => (
          <Polyline
            key={index}
            positions={[
              [segment.start_lat, segment.start_lng],
              [segment.end_lat, segment.end_lng]
            ]}
            color={getColor(segment.risk_score)}
            weight={8}
            opacity={0.9}
            className={getClass(segment.risk_score)}
          />
        ))}
      </>
    );
  };

  // Hazard zones as circles
  const HazardZones = () => {
    // Sample hazard zones - in real implementation, fetch from backend
    const sampleHazards = [
      {
        id: 'hazard_1',
        center: { lat: -26.2000, lng: 28.0500 },
        radius: 500,
        severity: 0.8,
        type: 'high_crime'
      },
      {
        id: 'hazard_2',
        center: { lat: -26.2100, lng: 28.0400 },
        radius: 300,
        severity: 0.6,
        type: 'road_hazard'
      },
      {
        id: 'hazard_3',
        center: { lat: -26.1900, lng: 28.0450 },
        radius: 400,
        severity: 0.7,
        type: 'construction_zone'
      }
    ];

    return (
      <>
        {sampleHazards.map(hazard => (
          <Circle
            key={hazard.id}
            center={[hazard.center.lat, hazard.center.lng]}
            radius={hazard.radius}
            fillColor={hazard.severity > 0.7 ? '#ff4757' : '#ffa502'}
            fillOpacity={0.3}
            color={hazard.severity > 0.7 ? '#ff4757' : '#ffa502'}
            opacity={0.8}
            weight={2}
          >
            <Popup>
              <div className="hazard-popup">
                <h4>{hazard.type.replace('_', ' ').toUpperCase()}</h4>
                <p>Risk Level: {(hazard.severity * 100).toFixed(0)}%</p>
                <div className="severity-bar">
                  <div 
                    className="severity-fill" 
                    style={{ 
                      width: `${hazard.severity * 100}%`,
                      backgroundColor: hazard.severity > 0.7 ? '#ff4757' : '#ffa502'
                    }}
                  ></div>
                </div>
              </div>
            </Popup>
          </Circle>
        ))}
      </>
    );
  };

  // Crime hotspots markers
  const CrimeHotspots = () => {
    // Sample crime hotspots - in real implementation, fetch from your model
    const sampleHotspots = [
      {
        id: 'crime_1',
        position: { lat: -26.1950, lng: 28.0450 },
        title: 'High Crime Area',
        description: 'Recent incidents reported',
        severity: 0.85,
        type: 'crime_hotspot'
      },
      {
        id: 'crime_2',
        position: { lat: -26.2080, lng: 28.0520 },
        title: 'Medium Risk Zone',
        description: 'Occasional incidents',
        severity: 0.6,
        type: 'crime_watch'
      },
      {
        id: 'crime_3',
        position: { lat: -26.2000, lng: 28.0400 },
        title: 'Robbery Hotspot',
        description: 'Active robbery zone',
        severity: 0.9,
        type: 'robbery'
      },
      {
        id: 'crime_4',
        position: { lat: -26.2150, lng: 28.0480 },
        title: 'Carjacking Area',
        description: 'Recent carjackings reported',
        severity: 0.75,
        type: 'carjacking'
      }
    ];

    return (
      <>
        {sampleHotspots.map(marker => (
          <Marker
            key={marker.id}
            position={[marker.position.lat, marker.position.lng]}
            icon={createCustomIcon('crime', marker.severity)}
            eventHandlers={{
              click: () => {
                if (onMarkerClick) onMarkerClick(marker);
              }
            }}
          >
            <Popup>
              <div className="marker-popup">
                <h3>{marker.title}</h3>
                <p>{marker.description}</p>
                <div className="severity-indicator">
                  <span>Risk: {(marker.severity * 100).toFixed(0)}%</span>
                  <div className="severity-bar">
                    <div 
                      className="severity-fill" 
                      style={{ 
                        width: `${marker.severity * 100}%`,
                        backgroundColor: marker.severity > 0.7 ? '#ff4757' : '#ffa502'
                      }}
                    ></div>
                  </div>
                </div>
              </div>
            </Popup>
          </Marker>
        ))}
      </>
    );
  };

  useEffect(() => {
    // Simulate backend connection
    setTimeout(() => {
      setBackendConnected(true);
      setMapLoaded(true);
      if (onMapReady) onMapReady();
    }, 1000);
  }, [onMapReady]);

  return (
    <div className="leaflet-map-container">
      <MapContainer
        center={[center.lat, center.lng]}
        zoom={zoom}
        ref={mapRef}
        className="leaflet-map"
        zoomControl={true}
      >
        <TileLayer
          url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
          attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
          maxZoom={18}
          minZoom={8}
        />
        
        <MapController center={center} zoom={zoom} />
        
        {userLocation && (
          <Marker
            position={[userLocation.latitude, userLocation.longitude]}
            icon={createCustomIcon('user')}
          >
            <Popup>
              <div className="user-popup">
                <h3>Your Location</h3>
                <p>Accuracy: {userLocation.accuracy}m</p>
              </div>
            </Popup>
          </Marker>
        )}
        
        {route && <RoutePolyline routeData={route} />}
        
        {showHazardZones && <HazardZones />}
        
        {showCrimeHotspots && <CrimeHotspots />}
        
      </MapContainer>

      {/* Loading overlay */}
      {!mapLoaded && (
        <div className="map-loading-overlay">
          <div className="loading-spinner"></div>
          <p>Loading SafeRoute Map...</p>
          <small>Connecting to real-time safety data...</small>
        </div>
      )}

      {/* Map controls and legend */}
      {mapLoaded && (
        <div className="map-controls">
          <div className="map-legend">
            <h4>🛡️ SafeRouteAI Legend</h4>
            <div className="legend-item">
              <span className="legend-color" style={{ backgroundColor: '#2ed573' }}></span>
              <span>Low Risk Areas</span>
            </div>
            <div className="legend-item">
              <span className="legend-color" style={{ backgroundColor: '#ffa502' }}></span>
              <span>Moderate Risk Areas</span>
            </div>
            <div className="legend-item">
              <span className="legend-color" style={{ backgroundColor: '#ff4757' }}></span>
              <span>High Risk Areas</span>
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
                <span>📍 12 Crime Hotspots</span>
                <span>🗺️ Heatmap Active</span>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
};

export default LeafletMapComponent;