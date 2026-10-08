(() => {
  'use strict';
  const config = window.MirrorTalkIntelligence || {};
  if (!config.endpoint) return;
  const consentKey = 'amt_analytics_consent_v1';
  const deviceKey = 'amt_device_id';
  const visitKey = 'mt_visit_count_v1';
  const choice = document.querySelector('[data-mt-privacy-choice]');
  const consent = () => { try { return localStorage.getItem(consentKey) || 'unset'; } catch (_) { return 'unset'; } };
  const deviceId = () => {
    try {
      let value = localStorage.getItem(deviceKey);
      if (!value) { value = crypto.randomUUID ? crypto.randomUUID() : `${Date.now()}-${Math.random()}`; localStorage.setItem(deviceKey, value); }
      return value;
    } catch (_) { return ''; }
  };
  const send = (eventName, metadata = {}) => {
    if (consent() !== 'granted') return;
    const body = JSON.stringify({ event_name: eventName, metadata: { ...metadata, device_id: deviceId() } });
    fetch(config.endpoint, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body, keepalive: true }).catch(() => {});
  };
  window.MirrorTalkTrack = send;
  window.addEventListener('mt:intelligence-event', (event) => send(event.detail?.name, event.detail?.metadata));
  window.addEventListener('amt:product-event', (event) => {
    const detail = event.detail || {}; const theme = String(detail.metadata?.theme || '').trim().slice(0, 80);
    if (!theme || !['question_origin_selected', 'answer_rendered', 'continuation_action_used'].includes(detail.eventName)) return;
    if (/\b(?:health|healing|faith|religion|trauma|grief|anxiety|depression|sexuality|politics)\b/i.test(theme)) return;
    send('safe_topic_view', { path: location.pathname, search_term: theme });
  });

  const revealConsent = () => {
    if (consent() !== 'unset' || !choice) return;
    choice.hidden = false;
    document.documentElement.classList.add('mt-consent-pending');
  };
  if (location.pathname.includes('/ask-mirror-talk/') && consent() === 'unset') {
    let attempts = 0;
    const waitForOnboarding = window.setInterval(() => {
      attempts += 1;
      let ready = false;
      try { ready = localStorage.getItem('amt_onboarded') === '1'; } catch (_) { ready = true; }
      if (ready || attempts >= 120) { window.clearInterval(waitForOnboarding); revealConsent(); }
    }, 500);
  } else revealConsent();
  choice?.addEventListener('click', (event) => {
    const button = event.target.closest('[data-mt-consent]');
    if (!button) return;
    try { localStorage.setItem(consentKey, button.dataset.mtConsent); } catch (_) {}
    choice.hidden = true;
    document.documentElement.classList.remove('mt-consent-pending');
    if (button.dataset.mtConsent === 'granted') trackPageView();
  });

  const cleanPath = (url) => `${url.pathname}${url.searchParams.has('s') ? '?s=' : ''}`.slice(0, 300);
  const deviceClass = innerWidth < 640 ? 'mobile' : innerWidth < 1024 ? 'tablet' : 'desktop';
  function trackPageView() {
    let visits = 0;
    try { visits = Number(localStorage.getItem(visitKey) || 0) + 1; localStorage.setItem(visitKey, String(visits)); } catch (_) {}
    const url = new URL(location.href); const ref = document.referrer ? new URL(document.referrer) : null;
    let entryPath = cleanPath(url);
    try { entryPath = sessionStorage.getItem('mt_entry_path') || entryPath; } catch (_) {}
    send('site_page_view', { path: cleanPath(url), referrer_host: ref?.hostname || 'direct', campaign_source: url.searchParams.get('utm_source') || '', campaign_medium: url.searchParams.get('utm_medium') || '', campaign_name: url.searchParams.get('utm_campaign') || '', entry_path: entryPath, device_class: deviceClass, language: navigator.language, timezone: Intl.DateTimeFormat().resolvedOptions().timeZone, returning: visits > 1 });
    const internalSearch = url.searchParams.get('s');
    if (internalSearch) send('internal_search', { path: cleanPath(url), search_term: internalSearch });
    try { if (!sessionStorage.getItem('mt_entry_path')) sessionStorage.setItem('mt_entry_path', cleanPath(url)); } catch (_) {}
    setTimeout(() => send('site_engaged', { path: cleanPath(url) }), 30000);
  }
  if (consent() === 'granted') trackPageView();

  document.addEventListener('click', (event) => {
    const link = event.target.closest('a[href]'); if (!link) return;
    const destination = new URL(link.href, location.href);
    if (destination.hostname === location.hostname) send('site_internal_journey', { previous_path: location.pathname, destination_path: destination.pathname });
    else send('site_outbound_click', { path: location.pathname, link_host: destination.hostname });
  });
  window.addEventListener('error', (event) => {
    const target = event.target; const url = target?.src || target?.href;
    if (url) send('broken_link_seen', { path: location.pathname, target: String(url).slice(0, 500), status: 'resource_error' });
  }, true);

  const vital = (metric, value, boundaries) => send('web_vital', { metric, value: Math.round(value), rating: value <= boundaries[0] ? 'good' : value <= boundaries[1] ? 'needs-improvement' : 'poor', path: location.pathname, connection: navigator.connection?.effectiveType || '' });
  try {
    let cls = 0; let lcp = 0; let inp = 0; let vitalsSent = false;
    new PerformanceObserver((list) => list.getEntries().forEach((entry) => { lcp = Math.max(lcp, entry.startTime); })).observe({ type: 'largest-contentful-paint', buffered: true });
    new PerformanceObserver((list) => list.getEntries().forEach((entry) => { if (!entry.hadRecentInput) cls += entry.value; })).observe({ type: 'layout-shift', buffered: true });
    new PerformanceObserver((list) => list.getEntries().forEach((entry) => { inp = Math.max(inp, entry.duration || 0); })).observe({ type: 'event', buffered: true, durationThreshold: 40 });
    const flushVitals = () => {
      if (vitalsSent) return; vitalsSent = true;
      if (lcp) vital('LCP', lcp, [2500, 4000]);
      vital('CLS', cls * 1000, [100, 250]);
      if (inp) vital('INP', inp, [200, 500]);
    };
    addEventListener('pagehide', flushVitals, { once: true });
    document.addEventListener('visibilitychange', () => { if (document.visibilityState === 'hidden') flushVitals(); }, { once: true });
  } catch (_) {}
})();
