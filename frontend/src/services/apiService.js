/**
 * SafeRouteAI API Service with Neon Authentication
 * Handles all communication with the Python backend including user auth
 */

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://110.238.78.155:8004';

class ApiService {
  constructor() {
    this.baseURL = API_BASE_URL;
    this.token = localStorage.getItem('saferoute_token');
  }

  // Helper method for making HTTP requests with retry mechanism
  async request(endpoint, options = {}, retries = 2) {
    const url = `${this.baseURL}${endpoint}`;
    const config = {
      headers: {
        'Content-Type': 'application/json',
        ...options.headers,
      },
      timeout: 30000, // 30 second timeout
      ...options,
    };

    // Add authorization header if token exists
    if (this.token && !config.headers.Authorization) {
      config.headers.Authorization = `Bearer ${this.token}`;
    }

    try {
      const controller = new AbortController();
      const timeoutId = setTimeout(() => controller.abort(), config.timeout);

      const response = await fetch(url, {
        ...config,
        signal: controller.signal
      });

      clearTimeout(timeoutId);

      // Handle 401 Unauthorized - token expired
      if (response.status === 401) {
        this.logout();
        throw new Error('Session expired. Please log in again.');
      }

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.detail || `HTTP error! status: ${response.status}`);
      }

      const data = await response.json();
      return data;
    } catch (error) {
      console.error(`API request failed (retries left: ${retries}): ${endpoint}`, error);

      // Check for transient network errors to retry
      const isNetworkError = error.name === 'TypeError' && error.message === 'Failed to fetch';
      const isTimeout = error.name === 'AbortError';

      if ((isNetworkError || isTimeout) && retries > 0) {
        console.log(`Retrying request to ${endpoint}...`);
        // Wait a bit before retrying (exponential backoff)
        await new Promise(resolve => setTimeout(resolve, 1000 * (3 - retries)));
        return this.request(endpoint, options, retries - 1);
      }

      // Check if we're offline
      if (!navigator.onLine) {
        throw new Error('You are currently offline. Please check your internet connection.');
      }

      // Handle final timeout
      if (error.name === 'AbortError') {
        throw new Error('Request timed out. Please try again when your connection is stronger.');
      }

      if (error.message === 'Failed to fetch') {
        throw new Error('Unable to connect to security server. This may be due to poor signal or network restrictions.');
      }

      throw error;
    }
  }

  // Authentication methods
  setToken(token) {
    this.token = token;
    localStorage.setItem('saferoute_token', token);
  }

  getToken() {
    return this.token || localStorage.getItem('saferoute_token');
  }

  clearToken() {
    this.token = null;
    localStorage.removeItem('saferoute_token');
  }

  isAuthenticated() {
    return !!this.getToken();
  }

  async register(email, name, password) {
    const response = await this.request('/api/v1/auth/register', {
      method: 'POST',
      body: JSON.stringify({ email, name, password }),
    });

    if (response.success && response.access_token) {
      this.setToken(response.access_token);
    }

    return response;
  }

  async login(email, password) {
    const response = await this.request('/api/v1/auth/login', {
      method: 'POST',
      body: JSON.stringify({ email, password }),
    });

    if (response.success && response.access_token) {
      this.setToken(response.access_token);
    }

    return response;
  }

  async logout() {
    try {
      // Optional: notify backend of logout
      if (this.isAuthenticated()) {
        await this.request('/api/v1/auth/logout', { method: 'POST' });
      }
    } catch (error) {
      console.warn('Logout request failed:', error);
    } finally {
      this.clearToken();
    }
  }

  async getCurrentUser() {
    if (!this.isAuthenticated()) {
      throw new Error('Not authenticated');
    }

    return this.request('/api/v1/auth/me');
  }

  async updatePreferences(preferences) {
    return this.request('/api/v1/auth/preferences', {
      method: 'PUT',
      body: JSON.stringify(preferences),
    });
  }

  async refreshToken() {
    const response = await this.request('/api/v1/auth/refresh', {
      method: 'POST',
    });

    if (response.success && response.access_token) {
      this.setToken(response.access_token);
    }

    return response;
  }

  // Journey management
  async saveJourney(journeyData) {
    return this.request('/api/v1/journeys', {
      method: 'POST',
      body: JSON.stringify(journeyData),
    });
  }

  async getUserJourneys(limit = 10) {
    return this.request(`/api/v1/journeys?limit=${limit}`);
  }

  async getUserHazardReports() {
    return this.request('/api/v1/hazards');
  }

  // GET request helper
  async get(endpoint) {
    return this.request(endpoint, { method: 'GET' });
  }

  // POST request helper
  async post(endpoint, data) {
    return this.request(endpoint, {
      method: 'POST',
      body: JSON.stringify(data),
    });
  }

  // API Status and Health
  async getStatus() {
    return this.get('/');
  }

  async getApiInfo() {
    return this.get('/');
  }

  // Pre-emptive warm-up call (helpful for Render's free tier)
  async warmup() {
    try {
      // Fire and forget, don't await the 30s timeout if it's purely for waking up
      fetch(this.baseURL).catch(() => {});
    } catch (e) {}
  }

  // Data Management
  async uploadData() {
    return this.post('/data/upload');
  }

  // Training and Model Management
  async startTraining(jobConfig) {
    return this.post('/training/start', jobConfig);
  }

  async getTrainingJobs() {
    return this.get('/training/jobs');
  }

  async getTrainingJob(jobId) {
    return this.get(`/training/jobs/${jobId}`);
  }

  async deployModel(jobId, endpointName = 'saferoute-frontend') {
    return this.post(`/model/deploy/${jobId}?endpoint_name=${endpointName}`);
  }

  // Risk Prediction
  async predictRisk(location) {
    return this.post('/predict/risk', {
      latitude: location.latitude,
      longitude: location.longitude,
      hour: location.hour || new Date().getHours(),
      day_of_week: location.day_of_week || new Date().getDay() + 1,
    });
  }

  // Route Optimization
  async optimizeRoute(routeRequest) {
    return this.post('/api/v1/optimize-route', routeRequest);
  }

  // Geocoding
  async geocode(address) {
    return this.post('/api/v1/map/geocode', { address });
  }

  // Map Kit Integration
  async getMapConfig() {
    return this.get('/api/v1/map/config');
  }

  async getMapMarkers(bounds = null) {
    const query = bounds ?
      `?north=${bounds.north}&south=${bounds.south}&east=${bounds.east}&west=${bounds.west}` : '';
    return this.get(`/api/v1/map/markers${query}`);
  }

  async getHazardZones(bounds = null) {
    const query = bounds ?
      `?north=${bounds.north}&south=${bounds.south}&east=${bounds.east}&west=${bounds.west}` : '';
    return this.get(`/api/v1/map/hazard-zones${query}`);
  }

  async getSafetyHeatmap(bounds = null) {
    const query = bounds ?
      `?north=${bounds.north}&south=${bounds.south}&east=${bounds.east}&west=${bounds.west}` : '';
    return this.get(`/api/v1/map/safety-heatmap${query}`);
  }

  async reportHazard(hazardData) {
    return this.post('/api/v1/map/report-hazard', hazardData);
  }

  async analyzeRouteSafety(waypoints) {
    return this.post('/api/v1/map/analyze-route-safety', { waypoints });
  }

  // Demo and Testing
  async runFullWorkflow() {
    return this.get('/demo/full-workflow');
  }

  // DEPRECATED: Mock data functions removed for production
  // These functions previously returned fake data for offline mode.
  // The frontend now uses proper error states when backend is unavailable.

  getMockDashboardData() {
    console.warn('DEPRECATED: getMockDashboardData() should not be called in production');
    throw new Error('Mock data is disabled in production mode');
  }

  getMockNavigationData() {
    console.warn('DEPRECATED: getMockNavigationData() should not be called in production');
    throw new Error('Mock data is disabled in production mode');
  }

  getMockHazardData() {
    console.warn('DEPRECATED: getMockHazardData() should not be called in production');
    throw new Error('Mock data is disabled in production mode');
  }

  // Utility methods
  async checkBackendHealth() {
    try {
      const status = await this.getStatus();
      return {
        isOnline: true,
        mode: status.mock_mode ? 'Mock' : 'Production',
        services: {
          obs: status.obs_storage?.status === 'RUNNING',
          modelarts: status.modelarts_training?.status === 'RUNNING',
          inference: status.inference_service?.status === 'RUNNING',
        },
      };
    } catch (error) {
      return {
        isOnline: false,
        mode: 'Offline',
        services: {
          obs: false,
          modelarts: false,
          inference: false,
        },
      };
    }
  }

  // Location utilities
  getCurrentLocation() {
    return new Promise((resolve, reject) => {
      if (!navigator.geolocation) {
        reject(new Error('Geolocation is not supported'));
        return;
      }

      navigator.geolocation.getCurrentPosition(
        (position) => {
          resolve({
            latitude: position.coords.latitude,
            longitude: position.coords.longitude,
            accuracy: position.coords.accuracy,
          });
        },
        (error) => {
          // Fallback to Johannesburg coordinates for demo
          resolve({
            latitude: -26.2041,
            longitude: 28.0473,
            accuracy: 100,
            isDemo: true,
          });
        },
        {
          enableHighAccuracy: true,
          timeout: 10000,
          maximumAge: 300000, // 5 minutes
        }
      );
    });
  }

  // Cache management
  setCacheItem(key, data, ttl = 300000) { // 5 minutes default TTL
    const item = {
      data,
      timestamp: Date.now(),
      ttl,
    };
    localStorage.setItem(`saferoute_${key}`, JSON.stringify(item));
  }

  getCacheItem(key) {
    try {
      const item = JSON.parse(localStorage.getItem(`saferoute_${key}`));
      if (!item) return null;

      const now = Date.now();
      if (now - item.timestamp > item.ttl) {
        localStorage.removeItem(`saferoute_${key}`);
        return null;
      }

      return item.data;
    } catch (error) {
      return null;
    }
  }

  clearCache() {
    const keys = Object.keys(localStorage);
    keys.forEach(key => {
      if (key.startsWith('saferoute_')) {
        localStorage.removeItem(key);
      }
    });
  }
}

// Create and export singleton instance
export const apiService = new ApiService();
export default apiService;