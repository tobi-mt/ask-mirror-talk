/* Mirror Talk push-only service worker.
 *
 * It intentionally has no fetch handler and creates no caches. Pages, scripts
 * and styles therefore always follow the site's normal cache policy while Web
 * Push retains the persistent root-scoped worker it requires.
 */

const MT_PUSH_WORKER_VERSION = '8.33.0';

self.addEventListener('install', (event) => {
  event.waitUntil(self.skipWaiting());
});

self.addEventListener('activate', (event) => {
  event.waitUntil(self.clients.claim());
});

self.addEventListener('push', (event) => {
  if (!event.data) return;
  let payload;
  try {
    payload = event.data.json();
  } catch (_) {
    payload = { title: 'Mirror Talk', body: event.data.text(), url: '/' };
  }

  const options = {
    body: payload.body || '',
    icon: payload.icon || '/wp-content/themes/astra-child/pwa-icon-192.png',
    badge: payload.badge || '/wp-content/themes/astra-child/pwa-icon-192.png',
    tag: payload.tag || 'mirror-talk',
    data: { url: payload.url || '/', ...(payload.data || {}) },
    actions: payload.actions || [
      { action: 'open', title: 'Read now' },
      { action: 'dismiss', title: 'Later' },
    ],
    vibrate: payload.vibrate || [120, 50, 120],
    requireInteraction: Boolean(payload.requireInteraction),
    image: payload.image || undefined,
    silent: false,
    renotify: Boolean(payload.renotify),
  };
  event.waitUntil(self.registration.showNotification(payload.title || 'Mirror Talk', options));
});

self.addEventListener('notificationclick', (event) => {
  event.notification.close();
  if (event.action === 'dismiss') return;

  const data = event.notification.data || {};
  const baseUrl = data.url || '/';
  if (event.action === 'save' || event.action === 'remind') {
    event.waitUntil(self.clients.matchAll({ type: 'window', includeUncontrolled: true }).then((windows) => {
      if (!windows.length) return undefined;
      windows[0].postMessage({
        type: 'SAVE_NOTIFICATION',
        data: {
          title: event.notification.title,
          body: event.notification.body,
          url: baseUrl,
          savedAt: Date.now(),
        },
      });
      return undefined;
    }));
    return;
  }

  const hashIndex = baseUrl.indexOf('#');
  const hash = hashIndex >= 0 ? baseUrl.slice(hashIndex) : '#ask-mirror-talk-form';
  const base = hashIndex >= 0 ? baseUrl.slice(0, hashIndex) : baseUrl;
  let targetUrl = baseUrl;

  if (data.question) {
    const clean = base.replace(/([?&])autoask=[^&]*/g, '').replace(/[?&]$/, '');
    targetUrl = `${clean}${clean.includes('?') ? '&' : '?'}autoask=${encodeURIComponent(data.question)}${hash}`;
  } else if (data.type === 'midday_motivation' || data.type === 'night_reflection') {
    const parameter = data.type === 'midday_motivation' ? 'midday_reflection' : 'night_reflection';
    const clean = base.replace(/([?&])(midday_reflection|night_reflection)=[^&]*/g, '').replace(/[?&]$/, '');
    targetUrl = `${clean}${clean.includes('?') ? '&' : '?'}${parameter}=1${hash}`;
  }

  event.waitUntil(self.clients.matchAll({ type: 'window', includeUncontrolled: true }).then((windows) => {
    const sameOrigin = windows.find((client) => client.url.startsWith(self.location.origin));
    if (sameOrigin) {
      return sameOrigin.navigate(targetUrl)
        .then((client) => client && client.focus())
        .catch(() => sameOrigin.focus());
    }
    return self.clients.openWindow(targetUrl);
  }));
});

self.addEventListener('message', (event) => {
  if (event.data === 'GET_VERSION' && event.ports && event.ports[0]) {
    event.ports[0].postMessage({ version: MT_PUSH_WORKER_VERSION });
  }
});
