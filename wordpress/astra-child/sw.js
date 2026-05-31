/**
 * Ask Mirror Talk — Service Worker
 * Provides offline caching, instant repeat loads, and background answer caching.
 *
 * Cache strategy:
 *   - App shell (CSS/JS/HTML): cache-first, updated in background
 *   - API answers: network-first with cache fallback (so users see cached answers offline)
 *   - Audio: network-only (too large to cache)
 *   
 * FORCE UPDATE: Build timestamp to ensure browser detects changes
 */

const BUILD_TIMESTAMP = '2026-05-31T16:10:00.000Z';  // Update this to force SW refresh
const CACHE_VERSION = 'amt-v5.9.31';
const STATIC_CACHE = `${CACHE_VERSION}-static`;
const API_CACHE = `${CACHE_VERSION}-api`;
const NAVIGATION_CACHE = `${CACHE_VERSION}-pages`;
const NAVIGATION_TIMEOUT_MS = 4500;

// App shell files to pre-cache on install
// NOTE: '/' (homepage HTML) is intentionally excluded — the HTML must always
// be fetched fresh so that sw-init.js can update the service worker. Offline
// users get the dedicated offlineHTML() fallback instead.
const APP_SHELL = [
  '/wp-content/themes/astra-child/ask-mirror-talk.css',
  '/wp-content/themes/astra-child/ask-mirror-talk-enhanced.css',
  '/wp-content/themes/astra-child/ask-mirror-talk-premium.css',
  '/wp-content/themes/astra-child/ask-mirror-talk.js',
  '/wp-content/themes/astra-child/ask-mirror-talk-enhanced.js',
  '/wp-content/themes/astra-child/ask-mirror-talk-premium.js',
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

// ── Activate: clean up old caches, then notify visible pages ──
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
        // Only notify VISIBLE tabs about the update - don't force reload
        // This prevents disruptive reloads when users resume from background
        return self.clients.matchAll({ type: 'window', includeUncontrolled: true })
          .then((windowClients) => {
            windowClients.forEach((client) => {
              // Check if the client is focused/visible before notifying
              // This prevents reload spam when user just minimized/resumed
              if (client.visibilityState === 'visible' || client.focused) {
                // Send a gentle notification instead of forcing reload
                client.postMessage({ 
                  type: 'SW_UPDATED',
                  version: CACHE_VERSION,
                  timestamp: Date.now()
                });
              } else {
                console.log('[SW] Skipping hidden/unfocused tab - update will apply on next visit');
              }
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

  // Core app shell files should prefer the network when available so installed
  // PWAs pick up visual/theme changes quickly instead of waiting behind an older
  // cached shell.
  if (isAppShellAsset(url)) {
    event.respondWith(networkFirstWithCache(request, STATIC_CACHE));
    return;
  }

  // Static assets: cache-first with network update
  if (isStaticAsset(url)) {
    event.respondWith(cacheFirstWithUpdate(request, STATIC_CACHE));
    return;
  }

  // HTML pages: network-first with a fast timeout fallback so users never sit
  // on a blank white screen when the network is slow. We still avoid persistent
  // HTML caching to keep visual/app updates landing quickly for PWA users.
  if (request.headers.get('accept')?.includes('text/html')) {
    event.respondWith(networkPageWithOfflineFallback(request));
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

async function networkPageWithOfflineFallback(request) {
  const navCache = await caches.open(NAVIGATION_CACHE);
  const supportsAbort = typeof AbortController !== 'undefined';
  let timeoutId = null;
  const controller = supportsAbort ? new AbortController() : null;

  if (controller) {
    timeoutId = setTimeout(() => controller.abort(), NAVIGATION_TIMEOUT_MS);
  }

  try {
    const response = await fetch(request, {
      cache: 'no-store',
      signal: controller ? controller.signal : undefined,
    });
    if (timeoutId) clearTimeout(timeoutId);

    if (response && response.ok) {
      const contentType = response.headers.get('content-type') || '';
      if (contentType.includes('text/html')) {
        navCache.put(request, response.clone()).catch(() => {});
      }
    }

    return response;
  } catch (err) {
    if (timeoutId) clearTimeout(timeoutId);

    // Prefer any stale navigation HTML before showing the loading fallback.
    // Try exact URL first, then ignore query params as a safer fallback.
    let cached = await navCache.match(request);
    if (!cached) {
      cached = await navCache.match(request, { ignoreSearch: true });
    }
    if (cached) {
      return cached;
    }

    if (err && err.name === 'AbortError') {
      return new Response(loadingHTML(), {
        headers: { 'Content-Type': 'text/html' },
        status: 200,
      });
    }

    return new Response(offlineHTML(), {
      headers: { 'Content-Type': 'text/html' },
      status: 503,
    });
  }
}

function loadingHTML() {
  return `<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Ask Mirror Talk - Loading</title>
  <style>
    :root { color-scheme: light; }
    body {
      font-family: "Source Serif 4", Georgia, serif;
      background:
        radial-gradient(circle at 12% 10%, rgba(212, 168, 87, 0.24), transparent 38%),
        radial-gradient(circle at 86% 18%, rgba(139, 115, 85, 0.22), transparent 42%),
        linear-gradient(160deg, #f7f3ed 0%, #efe8de 50%, #e8ddd1 100%);
      color: #2e2a24;
      display: grid;
      place-items: center;
      min-height: 100vh;
      margin: 0;
      padding: 22px;
      text-align: center;
    }
    .loading-card {
      width: min(100%, 430px);
      padding: 30px 26px;
      background: rgba(255, 252, 247, 0.92);
      border-radius: 18px;
      border: 1px solid rgba(139, 115, 85, 0.2);
      box-shadow: 0 16px 36px rgba(46,42,36,0.12);
    }
    .mark {
      display: flex;
      justify-content: center;
      align-items: flex-end;
      gap: 7px;
      height: 24px;
      margin-bottom: 10px;
    }
    .mark span {
      width: 5px;
      border-radius: 999px;
      background: linear-gradient(180deg, #a6845f 0%, #4b3f33 100%);
      animation: pulse 1.2s ease-in-out infinite;
    }
    .mark span:nth-child(1) { height: 10px; animation-delay: 0s; }
    .mark span:nth-child(2) { height: 18px; animation-delay: 0.16s; }
    .mark span:nth-child(3) { height: 13px; animation-delay: 0.32s; }
    .eyebrow {
      margin: 0 0 8px;
      letter-spacing: 0.17em;
      text-transform: uppercase;
      font-size: 11px;
      font-weight: 700;
      color: #7d664b;
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
    }
    h1 { margin: 0; font-size: 28px; line-height: 1.18; }
    p {
      margin: 10px 0 0;
      color: #6b665d;
      line-height: 1.55;
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
      font-size: 14px;
    }
    .actions {
      display: flex;
      flex-wrap: wrap;
      justify-content: center;
      gap: 10px;
      margin-top: 16px;
    }
    button {
      border: 1px solid #cab79c;
      background: rgba(255,255,255,0.95);
      color: #4b3f33;
      border-radius: 999px;
      padding: 9px 14px;
      font-size: 12px;
      font-weight: 650;
      letter-spacing: 0.03em;
      cursor: pointer;
    }
    button.primary {
      border-color: #806747;
      background: linear-gradient(135deg, #f9f2e8, #efe3d2);
    }
    @keyframes pulse {
      0%, 100% { transform: translateY(0); opacity: 0.45; }
      50% { transform: translateY(-2px); opacity: 1; }
    }
  </style>
</head>
<body>
  <div class="loading-card">
    <div class="mark" aria-hidden="true"><span></span><span></span><span></span></div>
    <p class="eyebrow">ASK MIRROR TALK</p>
    <h1>Preparing your reflection space</h1>
    <p>Connection is taking longer than expected. We will retry automatically a few times.</p>
    <div class="actions">
      <button class="primary" id="retry-btn" type="button">Try now</button>
    </div>
  </div>
  <script>
    (function() {
      var RETRY_STATE_KEY = 'amt_sw_nav_retry_state';
      var RETRY_WINDOW_MS = 120000;
      var MAX_AUTO_RETRIES = 3;
      var RETRY_BACKOFF_MS = [3500, 7000, 12000];

      function nowMs() {
        return Date.now();
      }

      function readRetryState() {
        try {
          var raw = sessionStorage.getItem(RETRY_STATE_KEY);
          if (!raw) return { count: 0, ts: 0 };
          var parsed = JSON.parse(raw);
          var count = Number(parsed && parsed.count) || 0;
          var ts = Number(parsed && parsed.ts) || 0;
          if ((nowMs() - ts) > RETRY_WINDOW_MS) return { count: 0, ts: 0 };
          return { count: count, ts: ts };
        } catch (e) {
          return { count: 0, ts: 0 };
        }
      }

      function writeRetryState(count) {
        try {
          sessionStorage.setItem(RETRY_STATE_KEY, JSON.stringify({ count: count, ts: nowMs() }));
        } catch (e) {}
      }

      function retryNow() {
        try {
          sessionStorage.setItem('amt_skip_launch_splash_once', '1');
        } catch (e) {}
        location.reload();
      }

      document.getElementById('retry-btn').addEventListener('click', retryNow);

      var state = readRetryState();
      if (state.count < MAX_AUTO_RETRIES) {
        var attempt = state.count + 1;
        writeRetryState(attempt);
        var delay = RETRY_BACKOFF_MS[Math.min(state.count, RETRY_BACKOFF_MS.length - 1)];
        setTimeout(function() {
          retryNow();
        }, delay);
      }
    })();
  <\/script>
</body>
</html>`;
}

function isStaticAsset(url) {
  return /\.(css|js|png|jpg|jpeg|svg|webp|woff2?|ttf|ico)(\?.*)?$/.test(url.pathname);
}

function isAppShellAsset(url) {
  return /\/wp-content\/themes\/astra-child\/(ask-mirror-talk(?:-enhanced)?\.(?:css|js)|analytics-addon\.js)$/.test(url.pathname);
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
  const notificationType = data?.type || '';

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
  } else if (notificationType === 'midday_motivation') {
    const cleanBase = base
      .replace(/([?&])midday_reflection=[^&]*/g, '')
      .replace(/([?&])night_reflection=[^&]*/g, '')
      .replace(/[?&]$/, '');
    const sep = cleanBase.includes('?') ? '&' : '?';
    targetUrl = `${cleanBase}${sep}midday_reflection=1${hash}`;
  } else if (notificationType === 'night_reflection') {
    const cleanBase = base
      .replace(/([?&])night_reflection=[^&]*/g, '')
      .replace(/([?&])midday_reflection=[^&]*/g, '')
      .replace(/[?&]$/, '');
    const sep = cleanBase.includes('?') ? '&' : '?';
    targetUrl = `${cleanBase}${sep}night_reflection=1${hash}`;
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
        if (notificationType === 'midday_motivation') {
          return targetClient.navigate(targetUrl)
            .then(navigated => { if (navigated) navigated.focus(); })
            .catch(() => {
              targetClient.postMessage({ type: 'AUTO_START_MIDDAY_REFLECTION' });
              return targetClient.focus();
            });
        }
        if (notificationType === 'night_reflection') {
          return targetClient.navigate(targetUrl)
            .then(navigated => { if (navigated) navigated.focus(); })
            .catch(() => {
              targetClient.postMessage({ type: 'AUTO_START_NIGHT_REFLECTION' });
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
