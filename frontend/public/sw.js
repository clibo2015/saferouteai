// SafeRouteAI Service Worker
// Provides offline functionality and caching

const CACHE_NAME = 'saferoute-ai-v1.0.0';
const STATIC_CACHE_URLS = [
  '/',
  '/static/js/bundle.js',
  '/static/css/main.css',
  '/manifest.json'
];

const API_CACHE_NAME = 'saferoute-api-cache';
const API_CACHE_URLS = [
  '/api/v1/map/config',
  '/api/v1/map/markers'
];

// Install event - cache static assets
self.addEventListener('install', (event) => {
  event.waitUntil(
    caches.open(CACHE_NAME)
      .then((cache) => {
        console.log('SafeRouteAI: Caching static assets');
        return cache.addAll(STATIC_CACHE_URLS);
      })
      .catch((error) => {
        console.error('SafeRouteAI: Cache installation failed:', error);
      })
  );
  self.skipWaiting();
});

// Activate event - clean up old caches
self.addEventListener('activate', (event) => {
  event.waitUntil(
    caches.keys().then((cacheNames) => {
      return Promise.all(
        cacheNames.map((cacheName) => {
          if (cacheName !== CACHE_NAME && cacheName !== API_CACHE_NAME) {
            console.log('SafeRouteAI: Deleting old cache:', cacheName);
            return caches.delete(cacheName);
          }
        })
      );
    })
  );
  self.clients.claim();
});

// Fetch event - serve from cache when offline
self.addEventListener('fetch', (event) => {
  const { request } = event;
  const url = new URL(request.url);

  // Handle API requests
  if (url.pathname.startsWith('/api/')) {
    event.respondWith(
      fetch(request)
        .then((response) => {
          // Cache successful API responses
          if (response.ok && request.method === 'GET') {
            const responseClone = response.clone();
            caches.open(API_CACHE_NAME).then((cache) => {
              cache.put(request, responseClone);
            });
          }
          return response;
        })
        .catch(() => {
          // Serve from cache when offline
          return caches.match(request).then((cachedResponse) => {
            if (cachedResponse) {
              return cachedResponse;
            }
            // Return offline fallback for critical endpoints
            if (url.pathname === '/api/v1/map/config') {
              return new Response(JSON.stringify({
                success: false,
                error: 'Offline mode',
                offline: true
              }), {
                headers: { 'Content-Type': 'application/json' }
              });
            }
            throw new Error('No cached response available');
          });
        })
    );
    return;
  }

  // Handle static assets
  event.respondWith(
    caches.match(request)
      .then((cachedResponse) => {
        if (cachedResponse) {
          return cachedResponse;
        }
        return fetch(request);
      })
      .catch(() => {
        // Fallback for navigation requests
        if (request.mode === 'navigate') {
          return caches.match('/');
        }
        throw new Error('Network request failed and no cache available');
      })
  );
});

// Background sync for offline actions
self.addEventListener('sync', (event) => {
  if (event.tag === 'hazard-report') {
    event.waitUntil(syncHazardReports());
  }
});

// Sync hazard reports when back online
async function syncHazardReports() {
  try {
    // Get pending reports from IndexedDB
    const pendingReports = await getPendingHazardReports();
    
    for (const report of pendingReports) {
      try {
        await fetch('/api/v1/map/report-hazard', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(report.data)
        });
        
        // Remove from pending queue
        await removePendingHazardReport(report.id);
        
        // Notify user of successful sync
        self.registration.showNotification('SafeRouteAI', {
          body: 'Hazard report synced successfully',
          icon: '/logo192.png',
          badge: '/logo192.png'
        });
      } catch (error) {
        console.error('Failed to sync hazard report:', error);
      }
    }
  } catch (error) {
    console.error('Background sync failed:', error);
  }
}

// IndexedDB helpers (simplified)
async function getPendingHazardReports() {
  // In a real implementation, this would use IndexedDB
  return [];
}

async function removePendingHazardReport(id) {
  // In a real implementation, this would remove from IndexedDB
  console.log('Removing pending report:', id);
}

// Push notification handler
self.addEventListener('push', (event) => {
  if (!event.data) return;

  const data = event.data.json();
  const options = {
    body: data.body,
    icon: '/logo192.png',
    badge: '/logo192.png',
    vibrate: [200, 100, 200],
    data: data.data,
    actions: [
      {
        action: 'view',
        title: 'View Details'
      },
      {
        action: 'dismiss',
        title: 'Dismiss'
      }
    ]
  };

  event.waitUntil(
    self.registration.showNotification(data.title, options)
  );
});

// Notification click handler
self.addEventListener('notificationclick', (event) => {
  event.notification.close();

  if (event.action === 'view') {
    event.waitUntil(
      clients.openWindow('/dashboard')
    );
  }
});