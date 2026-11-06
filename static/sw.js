/**
 * DisasterSafe Offline Service Worker
 * Pre-caches essential disaster safety assets, decision tree JSON files,
 * and falls back gracefully when offline.
 */

const CACHE_NAME = 'disastersafe-cache-v1';
const ASSETS_TO_CACHE = [
  '/',
  '/chat?hazard=flood',
  '/chat?hazard=earthquake',
  '/chat?hazard=landslide',
  '/flowchart?hazard=flood',
  '/kit',
  '/plan',
  '/quiz',
  '/insights',
  '/about',
  '/static/css/main.css',
  '/static/js/app.js',
  '/static/js/chat.js',
  '/static/js/flowchart.js',
  '/static/js/kit.js',
  '/static/js/plan.js',
  '/static/img/icon-192.png',
  '/static/img/icon-512.png',
  '/static/manifest.json',
  '/api/tree/flood',
  '/api/tree/earthquake',
  '/api/tree/landslide',
  '/api/hazards'
];

self.addEventListener('install', (event) => {
  event.waitUntil(
    caches.open(CACHE_NAME).then((cache) => {
      console.log('[SW] Pre-caching disaster offline resources');
      return cache.addAll(ASSETS_TO_CACHE);
    }).then(() => self.skipWaiting())
  );
});

self.addEventListener('activate', (event) => {
  event.waitUntil(
    caches.keys().then((keys) => {
      return Promise.all(
        keys.map((k) => {
          if (k !== CACHE_NAME) {
            console.log('[SW] Clearing old cache:', k);
            return caches.delete(k);
          }
        })
      );
    }).then(() => self.clients.claim())
  );
});

self.addEventListener('fetch', (event) => {
  // Network first with cache fallback
  event.respondWith(
    fetch(event.request)
      .then((networkResponse) => {
        if (event.request.method === 'GET' && networkResponse.status === 200) {
          const respClone = networkResponse.clone();
          caches.open(CACHE_NAME).then((cache) => {
            cache.put(event.request, respClone);
          });
        }
        return networkResponse;
      })
      .catch(() => {
        return caches.match(event.request).then((cachedResponse) => {
          if (cachedResponse) return cachedResponse;
          if (event.request.headers.get('accept') && event.request.headers.get('accept').includes('text/html')) {
            return caches.match('/');
          }
        });
      })
  );
});

