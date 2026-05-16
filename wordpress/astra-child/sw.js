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

const BUILD_TIMESTAMP = '2026-05-15T07:00:00.000Z';  // Update this to force SW refresh
const CACHE_VERSION = 'amt-v5.9.15';
const STATIC_CACHE = `${CACHE_VERSION}-static`;
const API_CACHE = `${CACHE_VERSION}-api`;
const NAVIGATION_TIMEOUT_MS = 5000;

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
    return response;
  } catch (err) {
    if (timeoutId) clearTimeout(timeoutId);

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
    <p>Connection is taking longer than expected. We will retry automatically in a moment.</p>
    <div class="actions">
      <button class="primary" id="retry-btn" type="button">Try now</button>
      <button id="audio-btn" type="button" aria-pressed="false">Play calm intro</button>
      <button id="autoplay-btn" type="button" aria-pressed="false">Autoplay off</button>
    </div>
  </div>
  <script>
    (function() {
      var retried = false;
      var stopAudio = null;
      var AUTO_PLAY_KEY = 'amt_launch_audio_autoplay';

      function normalizeMoodPreset(mood) {
        var clean = String(mood || '').trim().toLowerCase();
        if (clean === 'warm') return 'Warm';
        if (clean === 'hopeful') return 'Hopeful';
        return 'Calm';
      }

      var THEME_MOOD_EXACT_MAP = {
        'self-worth': 'Warm',
        'self worth': 'Warm',
        'self-love': 'Warm',
        'self love': 'Warm',
        'self-compassion': 'Warm',
        'self compassion': 'Warm',
        'relationships': 'Warm',
        'relationship': 'Warm',
        'love': 'Warm',
        'family': 'Warm',
        'friendship': 'Warm',
        'belonging': 'Warm',
        'gratitude': 'Warm',
        'forgiveness': 'Warm',
        'inner peace': 'Calm',
        'healing': 'Calm',
        'anxiety': 'Calm',
        'stress': 'Calm',
        'fear': 'Calm',
        'grief': 'Calm',
        'rest': 'Calm',
        'burnout': 'Calm',
        'trauma': 'Calm',
        'loneliness': 'Calm',
        'faith': 'Hopeful',
        'hope': 'Hopeful',
        'purpose': 'Hopeful',
        'calling': 'Hopeful',
        'growth': 'Hopeful',
        'clarity': 'Hopeful',
        'confidence': 'Hopeful',
        'courage': 'Hopeful',
        'vision': 'Hopeful',
        'leadership': 'Hopeful',
        'career': 'Hopeful'
      };

      var THEME_MOOD_PHRASE_RULES = [
        { mood: 'Calm', test: /night reflection|evening reflection|rest and reset|release and rest|calm your mind/ },
        { mood: 'Hopeful', test: /midday reflection|purpose reset|next step|future self|fresh start|new chapter/ },
        { mood: 'Warm', test: /self[-\s]?worth|self[-\s]?love|self[-\s]?compassion|belonging|connection|relationships?/ },
        { mood: 'Calm', test: /inner peace|grief|anx|fear|stress|overwhelm|burnout|healing|forgive|loneliness/ },
        { mood: 'Hopeful', test: /purpose|calling|growth|clarity|confidence|courage|vision|career|momentum|breakthrough/ }
      ];

      function normalizeThemeKey(value) {
        return String(value || '')
          .trim()
          .toLowerCase()
          .replace(/[_-]+/g, ' ')
          .replace(/\s+/g, ' ');
      }

      function inferMoodFromThemeText(themeText) {
        var text = normalizeThemeKey(themeText);
        if (!text) return 'Calm';

        if (THEME_MOOD_EXACT_MAP[text]) {
          return THEME_MOOD_EXACT_MAP[text];
        }

        for (var exactTheme in THEME_MOOD_EXACT_MAP) {
          if (Object.prototype.hasOwnProperty.call(THEME_MOOD_EXACT_MAP, exactTheme) && text.indexOf(exactTheme) !== -1) {
            return THEME_MOOD_EXACT_MAP[exactTheme];
          }
        }

        for (var i = 0; i < THEME_MOOD_PHRASE_RULES.length; i += 1) {
          if (THEME_MOOD_PHRASE_RULES[i].test.test(text)) return THEME_MOOD_PHRASE_RULES[i].mood;
        }

        if (/calm|peace|quiet|still|gentle|breathe|slow/.test(text)) return 'Calm';
        if (/love|heart|care|compassion|kindness|bond|together/.test(text)) return 'Warm';
        if (/hope|rise|build|grow|dream|believe|advance|thrive/.test(text)) return 'Hopeful';

        return 'Calm';
      }

      function getMoodPresetConfig(mood) {
        var key = normalizeMoodPreset(mood);
        var presets = {
          Calm: {
            cycleMs: 520,
            masterGain: 0.038,
            padGain: 0.026,
            pulsePattern: [0.65, 0, 0.32, 0, 0.55, 0, 0.22, 0],
            melodyPattern: [392.0, 349.23, 329.63, 349.23, 392.0, 440.0, 392.0, 349.23],
            chordPattern: [[196.0, 246.94], [174.61, 220.0], [146.83, 196.0], [174.61, 220.0]]
          },
          Warm: {
            cycleMs: 500,
            masterGain: 0.042,
            padGain: 0.028,
            pulsePattern: [0.8, 0, 0.45, 0, 0.72, 0, 0.38, 0],
            melodyPattern: [392.0, 440.0, 493.88, 440.0, 392.0, 349.23, 329.63, 349.23],
            chordPattern: [[196.0, 246.94], [220.0, 261.63], [174.61, 220.0], [196.0, 246.94]]
          },
          Hopeful: {
            cycleMs: 470,
            masterGain: 0.045,
            padGain: 0.03,
            pulsePattern: [1, 0, 0.6, 0, 0.86, 0, 0.5, 0],
            melodyPattern: [392.0, 440.0, 493.88, 523.25, 493.88, 440.0, 392.0, 349.23],
            chordPattern: [[196.0, 246.94], [220.0, 277.18], [246.94, 293.66], [220.0, 277.18]]
          }
        };
        return presets[key] || presets.Calm;
      }

      function resolveMoodPreset() {
        try {
          var params = new URLSearchParams(window.location.search);
          if (params.get('night_reflection') === '1') return 'Calm';
          if (params.get('midday_reflection') === '1') return 'Hopeful';
          if (params.get('invite_reflection') === '1') return 'Warm';
          var theme = params.get('theme') || '';
          if (theme) return inferMoodFromThemeText(theme);
          var intent = params.get('intent') || '';
          if (intent) return inferMoodFromThemeText(intent);
        } catch (e) {}

        try {
          var qotdRaw = localStorage.getItem('amt_latest_qotd');
          if (qotdRaw) {
            var qotd = JSON.parse(qotdRaw);
            if (qotd && qotd.theme) return inferMoodFromThemeText(qotd.theme);
          }
        } catch (e) {}

        var hour = new Date().getHours();
        if (hour >= 22 || hour < 6) return 'Calm';
        if (hour >= 11 && hour <= 16) return 'Hopeful';
        return 'Warm';
      }

      function readAutoplayPreference() {
        try {
          return localStorage.getItem(AUTO_PLAY_KEY) === '1';
        } catch (e) {
          return false;
        }
      }

      function writeAutoplayPreference(enabled) {
        try {
          localStorage.setItem(AUTO_PLAY_KEY, enabled ? '1' : '0');
        } catch (e) {}
      }

      function updateAutoplayButtonLabel(button, enabled) {
        button.setAttribute('aria-pressed', enabled ? 'true' : 'false');
        button.textContent = enabled ? 'Autoplay on' : 'Autoplay off';
      }

      function createAmbientTrack(mood) {
        var AudioContextCtor = window.AudioContext || window.webkitAudioContext;
        if (!AudioContextCtor) return null;

        var preset = getMoodPresetConfig(mood);

        var context = new AudioContextCtor();
        var master = context.createGain();
        var padGain = context.createGain();
        var rhythmGain = context.createGain();
        var melodyGain = context.createGain();
        var lowPad = context.createOscillator();
        var highPad = context.createOscillator();
        var pulse = context.createOscillator();
        var melody = context.createOscillator();

        lowPad.type = 'sine';
        lowPad.frequency.value = 196.0;
        highPad.type = 'triangle';
        highPad.frequency.value = 246.94;
        pulse.type = 'sine';
        pulse.frequency.value = 98.0;
        melody.type = 'triangle';
        melody.frequency.value = 392.0;

        master.gain.setValueAtTime(0.0001, context.currentTime);
        padGain.gain.setValueAtTime(0.0001, context.currentTime);
        rhythmGain.gain.setValueAtTime(0.0001, context.currentTime);
        melodyGain.gain.setValueAtTime(0.0001, context.currentTime);

        lowPad.connect(padGain);
        highPad.connect(padGain);
        pulse.connect(rhythmGain);
        melody.connect(melodyGain);

        padGain.connect(master);
        rhythmGain.connect(master);
        melodyGain.connect(master);
        master.connect(context.destination);

        lowPad.start();
        highPad.start();
        pulse.start();
        melody.start();

        var now = context.currentTime;
        master.gain.linearRampToValueAtTime(preset.masterGain, now + 1.4);
        padGain.gain.linearRampToValueAtTime(preset.padGain, now + 1.1);
        rhythmGain.gain.linearRampToValueAtTime(0.0001, now + 1.2);
        melodyGain.gain.linearRampToValueAtTime(0.0001, now + 1.2);

        var step = 0;
        var pulsePattern = preset.pulsePattern;
        var melodyPattern = preset.melodyPattern;
        var chordPattern = preset.chordPattern;

        var interval = setInterval(function() {
          var t = context.currentTime;
          var pulseStrength = pulsePattern[step % pulsePattern.length];
          var melodyFreq = melodyPattern[step % melodyPattern.length];
          var chord = chordPattern[Math.floor(step / 2) % chordPattern.length];

          lowPad.frequency.setTargetAtTime(chord[0], t, 0.18);
          highPad.frequency.setTargetAtTime(chord[1], t, 0.2);

          pulse.frequency.setTargetAtTime(chord[0] / 2, t, 0.08);
          rhythmGain.gain.cancelScheduledValues(t);
          rhythmGain.gain.setValueAtTime(0.012, t);
          rhythmGain.gain.linearRampToValueAtTime(0.02 + (preset.masterGain * pulseStrength), t + 0.08);
          rhythmGain.gain.linearRampToValueAtTime(0.01, t + 0.38);

          melody.frequency.setTargetAtTime(melodyFreq, t, 0.06);
          melodyGain.gain.cancelScheduledValues(t);
          melodyGain.gain.setValueAtTime(0.0001, t);
          melodyGain.gain.linearRampToValueAtTime(0.012, t + 0.12);
          melodyGain.gain.linearRampToValueAtTime(0.0001, t + 0.42);

          step += 1;
        }, 480);

        if (typeof context.resume === 'function') {
          context.resume().catch(function() {});
        }

        return function() {
          clearInterval(interval);
          var endAt = context.currentTime + 0.85;
          master.gain.cancelScheduledValues(context.currentTime);
          master.gain.setValueAtTime(master.gain.value, context.currentTime);
          master.gain.linearRampToValueAtTime(0.0001, endAt);
          setTimeout(function() {
            try { lowPad.stop(); } catch (e) {}
            try { highPad.stop(); } catch (e) {}
            try { pulse.stop(); } catch (e) {}
            try { melody.stop(); } catch (e) {}
            try { context.close(); } catch (e) {}
          }, 920);
        };
      }

      function retryNow() {
        if (stopAudio) {
          stopAudio();
          stopAudio = null;
        }
        location.reload();
      }

      document.getElementById('retry-btn').addEventListener('click', retryNow);

      var audioBtn = document.getElementById('audio-btn');
      var autoPlayBtn = document.getElementById('autoplay-btn');
      var mood = resolveMoodPreset();
      var autoPlayEnabled = readAutoplayPreference();
      audioBtn.textContent = 'Play ' + mood.toLowerCase() + ' intro';
      updateAutoplayButtonLabel(autoPlayBtn, autoPlayEnabled);

      audioBtn.addEventListener('click', function() {
        if (stopAudio) {
          stopAudio();
          stopAudio = null;
          audioBtn.textContent = 'Play ' + mood.toLowerCase() + ' intro';
          audioBtn.setAttribute('aria-pressed', 'false');
          return;
        }

        var stopper = createAmbientTrack(mood);
        if (!stopper) {
          audioBtn.textContent = 'Audio unavailable on this device';
          audioBtn.disabled = true;
          return;
        }

        stopAudio = stopper;
        audioBtn.textContent = 'Stop calm intro';
        audioBtn.setAttribute('aria-pressed', 'true');
      });

      autoPlayBtn.addEventListener('click', function() {
        autoPlayEnabled = !readAutoplayPreference();
        writeAutoplayPreference(autoPlayEnabled);
        updateAutoplayButtonLabel(autoPlayBtn, autoPlayEnabled);

        if (autoPlayEnabled && !stopAudio) {
          var stopper = createAmbientTrack(mood);
          if (stopper) {
            stopAudio = stopper;
            audioBtn.textContent = 'Stop calm intro';
            audioBtn.setAttribute('aria-pressed', 'true');
          }
        }
      });

      if (autoPlayEnabled) {
        setTimeout(function() {
          if (stopAudio) return;
          var stopper = createAmbientTrack(mood);
          if (stopper) {
            stopAudio = stopper;
            audioBtn.textContent = 'Stop calm intro';
            audioBtn.setAttribute('aria-pressed', 'true');
          }
        }, 50);
      }

      setTimeout(function() {
        if (retried) return;
        retried = true;
        retryNow();
      }, 3500);
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
