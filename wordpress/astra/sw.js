/**
 * Ask Mirror Talk — Service Worker
 * Provides offline caching, instant repeat loads, and background answer caching.
 *
 * Cache strategy:
 *   - App shell (CSS/JS/HTML): cache-first, updated in background
 *   - API answers: network-first with cache fallback (so users see cached answers offline)
 *   - Audio: network-only (too large to cache)
 */

const CACHE_VERSION = 'amt-v3.8.0';
const STATIC_CACHE = `${CACHE_VERSION}-static`;
const API_CACHE = `${CACHE_VERSION}-api`;

// App shell files to pre-cache on install
const APP_SHELL = [
  '/',
  '/wp-content/themes/astra/ask-mirror-talk.css',
  '/wp-content/themes/astra/ask-mirror-talk.js',
  '/wp-content/themes/astra/analytics-addon.js',
];

// API base for caching answers
const API_BASE = 'https://ask-mirror-talk-production.up.railway.app';

// ── Install: pre-cache app shell ──
self.addEventListener('install', (event) => {
  console.log('[SW] Installing', CACHE_VERSION);
  event.waitUntil(
    caches.open(STATIC_CACHE)
      .then((cache) => cache.addAll(APP_SHELL))
      .then(() => self.skipWaiting())
      .catch((err) => {
        console.warn('[SW] Pre-cache failed (non-fatal):', err);
        return self.skipWaiting();
      })
  );
});

// ── Activate: clean up old caches ──
self.addEventListener('activate', (event) => {
  console.log('[SW] Activating', CACHE_VERSION);
  event.waitUntil(
    caches.keys().then((keys) => {
      return Promise.all(
        keys
          .filter((key) => key !== STATIC_CACHE && key !== API_CACHE)
          .map((key) => {
            console.log('[SW] Removing old cache:', key);
            return caches.delete(key);
          })
      );
    }).then(() => self.clients.claim())
  );
});

// ── Fetch: smart caching per resource type ──
self.addEventListener('fetch', (event) => {
  const { request } = event;
  const url = new URL(request.url);

  // Skip non-GET requests (POST /ask, etc.) — except read-through for API GETs
  if (request.method !== 'GET') return;

  // Skip streaming endpoints
  if (url.pathname.includes('/ask/stream')) return;

  // Skip audio files (too large)
  if (url.pathname.includes('/audio/') || url.href.includes('cloudfront.net')) return;

  // Skip admin, login, preview pages
  if (url.pathname.startsWith('/wp-admin') || url.pathname.startsWith('/wp-login')) return;

  // API calls: network-first with cache fallback
  if (url.origin === API_BASE || url.href.startsWith(API_BASE)) {
    event.respondWith(networkFirstWithCache(request, API_CACHE));
    return;
  }

  // Static assets: cache-first with network update
  if (isStaticAsset(url)) {
    event.respondWith(cacheFirstWithUpdate(request, STATIC_CACHE));
    return;
  }

  // HTML pages: network-first for freshness
  if (request.headers.get('accept')?.includes('text/html')) {
    event.respondWith(networkFirstWithCache(request, STATIC_CACHE));
    return;
  }
});

// ── Cache strategies ──

/**
 * Cache-first: serve from cache instantly, update in background.
 * Best for static assets (CSS, JS, images).
 */
async function cacheFirstWithUpdate(request, cacheName) {
  const cache = await caches.open(cacheName);
  const cached = await cache.match(request);

  // Update in background regardless
  const networkPromise = fetch(request)
    .then((response) => {
      if (response.ok) {
        cache.put(request, response.clone());
      }
      return response;
    })
    .catch(() => null);

  // Return cached immediately, or wait for network
  return cached || (await networkPromise) || new Response('Offline', { status: 503 });
}

/**
 * Network-first: try network, fall back to cache.
 * Best for API responses and HTML pages.
 */
async function networkFirstWithCache(request, cacheName) {
  const cache = await caches.open(cacheName);

  try {
    const response = await fetch(request);
    if (response.ok) {
      cache.put(request, response.clone());
    }
    return response;
  } catch (err) {
    const cached = await cache.match(request);
    if (cached) {
      console.log('[SW] Serving from cache (offline):', request.url);
      return cached;
    }

    // If it's a page request, show a friendly offline message
    if (request.headers.get('accept')?.includes('text/html')) {
      return new Response(offlineHTML(), {
        headers: { 'Content-Type': 'text/html' },
        status: 503,
      });
    }

    return new Response('Offline', { status: 503 });
  }
}

function isStaticAsset(url) {
  return /\.(css|js|png|jpg|jpeg|svg|webp|woff2?|ttf|ico)(\?.*)?$/.test(url.pathname);
}

// ── Push Notifications ──
self.addEventListener('push', (event) => {
  if (!event.data) return;

  let payload;
  try {
    payload = event.data.json();
  } catch (e) {
    payload = {
      title: 'Mirror Talk',
      body: event.data.text(),
      icon: '/wp-content/themes/astra/pwa-icon-192.png',
      url: '/',
    };
  }

  const options = {
    body: payload.body || '',
    icon: payload.icon || '/wp-content/themes/astra/pwa-icon-192.png',
    badge: payload.badge || '/wp-content/themes/astra/pwa-icon-192.png',
    tag: payload.tag || 'mirror-talk',
    data: {
      url: payload.url || '/',
      ...payload.data,
    },
    actions: [
      { action: 'open', title: 'Open' },
      { action: 'dismiss', title: 'Later' },
    ],
    vibrate: [100, 50, 100],
    requireInteraction: false,
  };

  event.waitUntil(
    self.registration.showNotification(payload.title || 'Mirror Talk', options)
  );
});

// ── Notification click ──
self.addEventListener('notificationclick', (event) => {
  event.notification.close();

  if (event.action === 'dismiss') return;

  const targetUrl = event.notification.data?.url || '/';

  event.waitUntil(
    clients.matchAll({ type: 'window', includeUncontrolled: true }).then((clientList) => {
      // If the site is already open, focus it and navigate
      for (const client of clientList) {
        if (client.url.includes(self.location.origin) && 'focus' in client) {
          client.focus();
          client.navigate(targetUrl);
          return;
        }
      }
      // Otherwise open a new window
      return clients.openWindow(targetUrl);
    })
  );
});


function offlineHTML() {
  return `<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Ask Mirror Talk — Offline</title>
  <style>
    body {
      font-family: "Source Serif 4", Georgia, serif;
      background: #faf8f4;
      color: #2e2a24;
      display: flex;
      align-items: center;
      justify-content: center;
      min-height: 100vh;
      margin: 0;
      padding: 20px;
      text-align: center;
    }
    .offline-card {
      max-width: 400px;
      padding: 40px 30px;
      background: #fff;
      border-radius: 12px;
      box-shadow: 0 4px 24px rgba(0,0,0,0.06);
      border: 1px solid #e6e2dc;
    }
    h1 { font-size: 24px; margin: 0 0 12px; }
    p { color: #6b665d; line-height: 1.6; margin: 0 0 20px; }
    button {
      background: #2e2a24; color: #fff; border: none;
      padding: 12px 28px; border-radius: 8px; font-size: 16px;
      cursor: pointer; font-family: inherit;
    }
    button:hover { background: #3d3731; }
  </style>
</head>
<body>
  <div class="offline-card">
    <h1>You're offline</h1>
    <p>Mirror Talk needs an internet connection to search podcast episodes and generate answers. Please reconnect and try again.</p>
    <button onclick="location.reload()">Try Again</button>
  </div>
</body>
</html>`;
}
