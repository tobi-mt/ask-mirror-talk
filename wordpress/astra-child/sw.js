/**
 * Ask Mirror Talk — Service Worker
 * Provides offline caching, instant repeat loads, and background answer caching.
 *
 * Cache strategy:
 *   - App shell (CSS/JS/HTML): cache-first, updated in background
 *   - API answers: network-first with cache fallback (so users see cached answers offline)
 *   - Audio: network-only (too large to cache)
 */

const CACHE_VERSION = 'amt-v5.4.41';
const STATIC_CACHE = `${CACHE_VERSION}-static`;
const API_CACHE = `${CACHE_VERSION}-api`;

// App shell files to pre-cache on install
// NOTE: '/' (homepage HTML) is intentionally excluded — the HTML must always
// be fetched fresh so that sw-init.js can update the service worker. Offline
// users get the dedicated offlineHTML() fallback instead.
const APP_SHELL = [
  '/wp-content/themes/astra-child/ask-mirror-talk.css',
  '/wp-content/themes/astra-child/ask-mirror-talk-enhanced.css',
  '/wp-content/themes/astra-child/ask-mirror-talk.js',
  '/wp-content/themes/astra-child/ask-mirror-talk-enhanced.js',
  '/wp-content/themes/astra-child/analytics-addon.js',
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

// ── Activate: clean up old caches, then tell open pages to reload ──
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
      .then(() => {
        // Force-navigate every visible open tab so the new SW takes over
        // immediately — no JS listener needed in the old page (which may be
        // running a version that predates the SW_UPDATED postMessage handler).
        return self.clients.matchAll({ type: 'window', includeUncontrolled: true })
          .then((windowClients) => {
            windowClients.forEach((client) => {
              // navigate() reloads the page under the new SW
              client.navigate(client.url).catch(() => {
                // Fallback: postMessage for browsers that don't support navigate()
                client.postMessage({ type: 'SW_UPDATED' });
              });
            });
          });
      })
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

  // Never cache the service worker or its init script — PHP must always serve these fresh
  if (url.pathname.endsWith('sw.js') || url.pathname === '/sw-init' || url.pathname.endsWith('sw-init.js')) return;

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

// ── Push Notifications (Premium) ──
self.addEventListener('push', (event) => {
  if (!event.data) return;

  let payload;
  try {
    payload = event.data.json();
  } catch (e) {
    payload = {
      title: 'Mirror Talk',
      body: event.data.text(),
      icon: '/wp-content/themes/astra-child/pwa-icon-192.png',
      url: '/',
    };
  }

  // Premium notification options with custom actions and vibration
  const options = {
    body: payload.body || '',
    icon: payload.icon || '/wp-content/themes/astra-child/pwa-icon-192.png',
    badge: payload.badge || '/wp-content/themes/astra-child/pwa-icon-192.png',
    tag: payload.tag || 'mirror-talk',
    data: {
      url: payload.url || '/',
      ...payload.data,
    },
    // Use custom actions from payload, or defaults
    actions: payload.actions || [
      { action: 'open', title: '💬 Read Now', icon: '/wp-content/themes/astra-child/pwa-icon-192.png' },
      { action: 'dismiss', title: '🔖 Later', icon: '/wp-content/themes/astra-child/pwa-icon-192.png' },
    ],
    // Custom vibration pattern from payload
    vibrate: payload.vibrate || [200, 100, 200],
    // Require interaction for QOTD, allow auto-dismiss for others
    requireInteraction: payload.requireInteraction || false,
    // Add image if provided
    image: payload.image || undefined,
    // Silent: false ensures sound/vibration
    silent: false,
    // Renotify: true for important updates
    renotify: payload.renotify || false,
  };

  event.waitUntil(
    self.registration.showNotification(payload.title || 'Mirror Talk', options)
  );
});

// ── Notification click (Premium Actions) ──
self.addEventListener('notificationclick', (event) => {
  event.notification.close();

  const action = event.action;
  const data = event.notification.data;
  const baseUrl = data?.url || '/';

  // Handle dismiss/save actions without opening the app
  if (action === 'dismiss') {
    return;
  }

  if (action === 'save' || action === 'remind') {
    event.waitUntil(
      self.clients.matchAll({ type: 'window' }).then((windowClients) => {
        if (windowClients.length > 0) {
          windowClients[0].postMessage({
            type: 'SAVE_NOTIFICATION',
            data: {
              title: event.notification.title,
              body: event.notification.body,
              url: baseUrl,
              savedAt: Date.now(),
            }
          });
        }
      })
    );
    return;
  }

  // Build the target URL with ?autoask= when we have a question.
  // Strip any hash from baseUrl before appending params, then restore hash.
  const question = data?.question;
  const hashIdx = baseUrl.indexOf('#');
  const hash = hashIdx !== -1 ? baseUrl.slice(hashIdx) : '#ask-mirror-talk-form';
  const base = hashIdx !== -1 ? baseUrl.slice(0, hashIdx) : baseUrl;
  let targetUrl = baseUrl;
  if (question) {
    // Build a clean URL — strip any existing autoask param first, then append fresh one
    const cleanBase = base.replace(/([?&])autoask=[^&]*/g, '').replace(/[?&]$/, '');
    const sep = cleanBase.includes('?') ? '&' : '?';
    targetUrl = `${cleanBase}${sep}autoask=${encodeURIComponent(question)}${hash}`;
  }

  event.waitUntil(
    clients.matchAll({ type: 'window', includeUncontrolled: true }).then((clientList) => {
      // Prefer a client already on the exact notification page; fall back to any
      // same-origin window so we can reuse an existing tab instead of stacking new ones.
      const normalise = u => u.split('?')[0].split('#')[0].replace(/\/$/, '');
      const baseNorm  = normalise(base);
      const exactClient = clientList.find(c => normalise(c.url) === baseNorm);
      const anyClient   = clientList.find(c => c.url.startsWith(self.location.origin));
      const targetClient = exactClient || anyClient;

      if (targetClient) {
        if (question) {
          // Navigate the existing tab to the URL with ?autoask=.
          // This is reliable even when the tab has been discarded/suspended by
          // the browser — navigate() forces a fresh load and checkAutoAsk() fires.
          // postMessage alone fails for discarded tabs because the message is lost.
          return targetClient.navigate(targetUrl)
            .then(navigated => { if (navigated) navigated.focus(); })
            .catch(() => {
              // navigate() not available (old iOS Safari < 15.4) — fall back to
              // postMessage for tabs that are still alive, then focus.
              targetClient.postMessage({ type: 'AUTO_SUBMIT', question });
              return targetClient.focus();
            });
        }
        // No specific question (streak / generic motivation) — bring app to front.
        // Navigate to baseUrl so the user lands on the ask page even if they had
        // browsed elsewhere, without the overhead of building an autoask URL.
        return targetClient.navigate(base + hash)
          .then(navigated => { if (navigated) navigated.focus(); })
          .catch(() => targetClient.focus().catch(() => null));
      }

      // No window open at all — open a fresh tab.
      return clients.openWindow(targetUrl);
    })
  );
});

// ── Version query (used by page to detect a stale SW and trigger a hard reset) ──
self.addEventListener('message', (event) => {
  if (event.data === 'GET_VERSION' && event.ports && event.ports[0]) {
    event.ports[0].postMessage({ version: CACHE_VERSION });
  }
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
