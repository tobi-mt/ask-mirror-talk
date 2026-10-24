(() => {
  'use strict';

  const siteHeader = document.querySelector('[data-mt-site-header]');
  if (siteHeader) {
    const navToggle = siteHeader.querySelector('[data-mt-nav-toggle]');
    const nav = siteHeader.querySelector('[data-mt-site-nav]');
    const setNavigation = (open) => {
      siteHeader.classList.toggle('is-navigation-open', open);
      navToggle.setAttribute('aria-expanded', String(open));
      if (!open) nav.querySelectorAll('.menu-item-has-children').forEach((item) => item.classList.remove('is-submenu-open'));
    };
    navToggle.addEventListener('click', () => setNavigation(navToggle.getAttribute('aria-expanded') !== 'true'));
    nav.querySelectorAll('.menu-item-has-children > a').forEach((link) => link.addEventListener('click', (event) => {
      if (window.matchMedia('(max-width: 860px)').matches && !link.parentElement.classList.contains('is-submenu-open')) {
        event.preventDefault();
        link.parentElement.classList.add('is-submenu-open');
      }
    }));
    nav.addEventListener('click', (event) => { if (event.target.closest('a') && !event.target.parentElement.classList.contains('menu-item-has-children')) setNavigation(false); });
    document.addEventListener('click', (event) => { if (!siteHeader.contains(event.target)) setNavigation(false); });
    document.addEventListener('keydown', (event) => { if (event.key === 'Escape') { setNavigation(false); navToggle.focus(); } });
  }

  const reduceMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  const preferenceKey = 'mt_preferences_v1';
  const safeRead = () => {
    try { return JSON.parse(localStorage.getItem(preferenceKey) || '{}'); } catch (_) { return {}; }
  };
  const safeWrite = (value) => {
    try { localStorage.setItem(preferenceKey, JSON.stringify(value)); } catch (_) {}
  };

  // First-party, on-device context only. Nothing in this profile is transmitted.
  const preferences = safeRead();

  // Remove a legacy page-builder hero that some WordPress posts pages render
  // ahead of the theme-owned Blog header. This targets its exact historic copy
  // and leaves all real post content untouched.
  if (document.body.classList.contains('blog')) {
    const library = document.querySelector('main.mt-library');
    document.querySelectorAll('h1, h2, h3').forEach((heading) => {
      if (heading.textContent.trim().toLowerCase() !== 'inspiring conversations for personal growth') return;
      const legacy = heading.closest('article, section, .elementor, .elementor-section, .e-con, .wp-block-group');
      if (legacy && !legacy.contains(library)) {
        legacy.classList.add('mt-legacy-blog-hero');
        legacy.setAttribute('aria-hidden', 'true');
      }
    });
  }
  preferences.visits = Math.min(999, Number(preferences.visits || 0) + 1);
  preferences.topics = preferences.topics && typeof preferences.topics === 'object' ? preferences.topics : {};
  preferences.locale = document.documentElement.lang || navigator.language || 'en';
  preferences.timezone = Intl.DateTimeFormat().resolvedOptions().timeZone || '';
  preferences.lastVisit = Date.now();
  safeWrite(preferences);

  const topicPath = window.location.pathname.match(/\/explore\/(purpose|resilience|relationships|faith|healing|leadership)\/?/);
  if (topicPath) {
    const visitMarker = `mt_topic_visit_${topicPath[1]}`;
    let countedThisSession = false;
    try { countedThisSession = sessionStorage.getItem(visitMarker) === '1'; } catch (_) {}
    if (!countedThisSession) {
      preferences.topics[topicPath[1]] = Math.min(20, Number(preferences.topics[topicPath[1]] || 0) + 1);
      safeWrite(preferences);
      try { sessionStorage.setItem(visitMarker, '1'); } catch (_) {}
    }
  }

  document.querySelectorAll('[data-mt-topic-link]').forEach((link) => {
    link.addEventListener('click', () => {
      const state = safeRead();
      state.topics = state.topics && typeof state.topics === 'object' ? state.topics : {};
      const topic = link.dataset.mtTopicLink;
      state.topics[topic] = Math.min(20, Number(state.topics[topic] || 0) + 2);
      safeWrite(state);
    });
  });

  const welcome = document.querySelector('[data-mt-welcome]');
  if (welcome) {
    const hour = new Date().getHours();
    const moment = hour < 12 ? 'Good morning' : hour < 18 ? 'Good afternoon' : 'Good evening';
    welcome.textContent = preferences.visits > 1
      ? `${moment}. Welcome back to your quiet space.`
      : `${moment}. Take a breath and begin where you are.`;
  }

  document.querySelectorAll('[data-mt-slider]').forEach((slider) => {
    const slides = Array.from(slider.querySelectorAll('[data-mt-slide]'));
    const previous = slider.querySelector('[data-mt-slider-prev]');
    const next = slider.querySelector('[data-mt-slider-next]');
    const current = slider.querySelector('[data-mt-slider-current]');
    const toggle = slider.querySelector('[data-mt-slider-toggle]');
    const progress = slider.querySelector('[data-mt-slider-progress]');
    const note = slider.querySelector('[data-mt-personalization-note]');

    if (slides.length < 2) return;

    const rankedTopics = Object.entries(preferences.topics)
      .sort((left, right) => Number(right[1]) - Number(left[1]));
    const rankedTopic = rankedTopics.length ? rankedTopics[0][0] : '';
    const preferredIndex = rankedTopic ? slides.findIndex((slide) => slide.dataset.mtTopic === rankedTopic) : -1;
    let index = preferredIndex >= 0 ? preferredIndex : 0;
    let timer = null;
    let duration = 7000;
    let manuallyPaused = reduceMotion;
    let pointerStart = null;

    if (preferredIndex >= 0 && note) {
      note.textContent = `Selected on this device from your interest in ${rankedTopic}. Your preferences stay in this browser.`;
      note.hidden = false;
    }

    const resetProgress = () => {
      if (!progress) return;
      progress.style.transition = 'none';
      progress.style.transform = 'scaleX(0)';
      requestAnimationFrame(() => requestAnimationFrame(() => {
        progress.style.transition = `transform ${duration}ms linear`;
        progress.style.transform = manuallyPaused ? 'scaleX(0)' : 'scaleX(1)';
      }));
    };

    const show = (nextIndex, announce = true) => {
      index = (nextIndex + slides.length) % slides.length;
      slides.forEach((slide, slideIndex) => {
        const active = slideIndex === index;
        slide.classList.toggle('is-active', active);
        slide.setAttribute('aria-hidden', active ? 'false' : 'true');
        slide.querySelectorAll('a, button').forEach((control) => { control.tabIndex = active ? 0 : -1; });
      });
      if (current) {
        current.textContent = String(index + 1);
        const liveRegion = current.closest('[aria-live]');
        if (!announce && liveRegion) liveRegion.setAttribute('aria-live', 'off');
      }
      duration = Math.max(6500, Math.min(11000, 5200 + Number(slides[index].dataset.mtWords || 0) * 55));
      resetProgress();
    };

    const stop = () => {
      if (timer) window.clearTimeout(timer);
      timer = null;
      if (progress) progress.style.transitionPlayState = 'paused';
    };

    const start = () => {
      stop();
      if (!manuallyPaused && !reduceMotion && !document.hidden) {
        if (progress) progress.style.transitionPlayState = 'running';
        resetProgress();
        timer = window.setTimeout(() => { show(index + 1, false); start(); }, duration);
      }
    };

    if (previous) previous.addEventListener('click', () => { show(index - 1); start(); });
    if (next) next.addEventListener('click', () => { show(index + 1); start(); });
    slider.addEventListener('mouseenter', stop);
    slider.addEventListener('mouseleave', () => { if (!manuallyPaused) start(); });
    slider.addEventListener('focusin', stop);
    slider.addEventListener('focusout', (event) => {
      if (!slider.contains(event.relatedTarget) && !manuallyPaused) start();
    });
    slider.addEventListener('pointerdown', (event) => { pointerStart = event.clientX; });
    slider.addEventListener('pointerup', (event) => {
      if (pointerStart === null || Math.abs(event.clientX - pointerStart) < 45) { pointerStart = null; return; }
      show(index + (event.clientX < pointerStart ? 1 : -1));
      pointerStart = null;
      start();
    });
    document.addEventListener('visibilitychange', () => {
      if (document.hidden) stop(); else if (!manuallyPaused) start();
    });

    if ('IntersectionObserver' in window) {
      const observer = new IntersectionObserver((entries) => {
        if (entries[0].isIntersecting && !manuallyPaused) start(); else stop();
      }, { threshold: 0.35 });
      observer.observe(slider);
    }

    show(index, false);
    start();
  });

  // A cache-free, root-scoped worker keeps Web Push healthy without taking
  // control of page requests or creating cross-browser HTML cache variants.
  const siteConfig = window.MirrorTalkSite || {};
  const qotdStatus = (message) => {
    document.querySelectorAll('[data-mt-qotd-status]').forEach((node) => { node.textContent = message; });
  };
  const reportQotd = (name, metadata = {}) => window.dispatchEvent(new CustomEvent('mt:intelligence-event', {
    detail: { name, metadata: { path: location.pathname, ...metadata } },
  }));
  const base64Key = (value) => {
    const padded = `${value}${'='.repeat((4 - value.length % 4) % 4)}`.replace(/-/g, '+').replace(/_/g, '/');
    return Uint8Array.from(window.atob(padded), (character) => character.charCodeAt(0));
  };
  const rememberPushConsent = () => {
    try { localStorage.setItem('amt_push_subscribed', 'true'); } catch (_) {}
    document.cookie = 'amt_ps=1; Max-Age=31536000; Path=/; SameSite=Lax; Secure';
  };
  const hadPushConsent = () => {
    try {
      if (localStorage.getItem('amt_push_subscribed') === 'true') return true;
    } catch (_) {}
    return document.cookie.split(';').some((entry) => entry.trim() === 'amt_ps=1');
  };
  const pushPayload = (subscription) => {
    const json = subscription.toJSON();
    return {
      endpoint: json.endpoint,
      keys: json.keys,
      timezone: Intl.DateTimeFormat().resolvedOptions().timeZone || 'UTC',
      preferred_qotd_hour: 8,
    };
  };
  const registerPushWorker = async () => {
    if (!('serviceWorker' in navigator) || !siteConfig.pushWorkerUrl) return null;
    const registration = await navigator.serviceWorker.register(siteConfig.pushWorkerUrl, {
      scope: '/',
      updateViaCache: 'none',
    });
    registration.update().catch(() => {});
    return registration;
  };
  const currentVapid = async () => {
    const response = await fetch(`${siteConfig.apiBase}/api/push/vapid-key`, { cache: 'no-store' });
    if (!response.ok) throw new Error('Notification service is not configured');
    const data = await response.json();
    return { encoded: data.public_key, bytes: base64Key(data.public_key) };
  };
  const sameApplicationKey = (subscription, expected) => {
    const existing = subscription?.options?.applicationServerKey;
    if (!existing) return true;
    const left = new Uint8Array(existing);
    if (left.length !== expected.length) return false;
    return left.every((value, index) => value === expected[index]);
  };
  const postPush = async (path, payload) => fetch(`${siteConfig.apiBase}${path}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  });
  const renewSubscription = async (registration, vapid) => {
    const old = await registration.pushManager.getSubscription();
    if (old) await old.unsubscribe().catch(() => false);
    return registration.pushManager.subscribe({ userVisibleOnly: true, applicationServerKey: vapid.bytes });
  };
  const recoverPushSubscription = async () => {
    if (!('Notification' in window) || Notification.permission !== 'granted') return false;
    const registration = await registerPushWorker();
    if (!registration) return false;
    const vapid = await currentVapid();
    let subscription = await registration.pushManager.getSubscription();

    if (!subscription) {
      if (!hadPushConsent()) return false;
      subscription = await renewSubscription(registration, vapid);
    } else if (!sameApplicationKey(subscription, vapid.bytes)) {
      subscription = await renewSubscription(registration, vapid);
    }

    let response = await postPush('/api/push/recover', pushPayload(subscription));
    if (response.status === 409) {
      const detail = await response.json().catch(() => ({}));
      if (/opted out/i.test(String(detail.detail || ''))) return false;
      subscription = await renewSubscription(registration, vapid);
      response = await postPush('/api/push/recover', pushPayload(subscription));
    }
    if (!response.ok) return false;
    rememberPushConsent();
    return true;
  };
  const subscribeToDailyQuestion = async () => {
    if (!('Notification' in window) || !('PushManager' in window)) {
      throw new Error('Daily browser reminders are not supported on this device.');
    }
    const permission = await Notification.requestPermission();
    if (permission !== 'granted') throw new Error('Notifications remain off. You can change this in your browser settings.');
    const registration = await registerPushWorker();
    const vapid = await currentVapid();
    let subscription = await registration.pushManager.getSubscription();
    if (!subscription || !sameApplicationKey(subscription, vapid.bytes)) {
      subscription = await renewSubscription(registration, vapid);
    }
    const payload = pushPayload(subscription);
    payload.notify_qotd = true;
    payload.notify_new_episodes = false;
    payload.notify_midday = false;
    const response = await postPush('/api/push/subscribe', payload);
    if (!response.ok) throw new Error('The reminder could not be saved. Please try again.');
    rememberPushConsent();
    return true;
  };

  // Registration is lightweight and has no fetch handler. Recovery runs at
  // most once daily and only for a browser that already granted permission.
  if ('serviceWorker' in navigator) {
    window.addEventListener('load', () => {
      registerPushWorker().catch(() => {});
      let checked = false;
      try {
        const last = Number(localStorage.getItem('mt_push_health_checked') || 0);
        checked = Date.now() - last < 20 * 60 * 60 * 1000;
      } catch (_) {}
      if (!checked) recoverPushSubscription().then((healthy) => {
        if (!healthy) return;
        try { localStorage.setItem('mt_push_health_checked', String(Date.now())); } catch (_) {}
        reportQotd('qotd_subscription_recovered');
      }).catch(() => {});
    }, { once: true });
  }

  // Page caches may outlive one calendar day. Refresh only the small visible
  // card payload, while keeping the server-rendered question as an immediate
  // and fully accessible fallback.
  const refreshLivingQuestion = async () => {
    const cards = document.querySelectorAll('[data-mt-living-question]');
    if (!cards.length || !siteConfig.apiBase) return;
    let data = null;
    try {
      const stored = JSON.parse(sessionStorage.getItem('mt_qotd_live') || 'null');
      const today = new Date().toISOString().slice(0, 10);
      if (stored?.date === today && stored.question) data = stored;
    } catch (_) {}
    if (!data) {
      const response = await fetch(`${siteConfig.apiBase}/api/question-of-the-day`, { cache: 'no-store' });
      if (!response.ok) return;
      data = await response.json();
      try { sessionStorage.setItem('mt_qotd_live', JSON.stringify(data)); } catch (_) {}
    }
    if (!data?.question) return;
    cards.forEach((card) => {
      card.dataset.mtQotdDate = data.date || '';
      const question = card.querySelector('[data-mt-qotd-question]');
      const theme = card.querySelector('[data-mt-qotd-theme-label]');
      const time = card.querySelector('[data-mt-qotd-time]');
      const answer = card.querySelector('[data-mt-qotd-answer]');
      if (question) question.textContent = data.question;
      if (theme) theme.textContent = data.theme || 'Reflection';
      if (time && data.date) {
        time.dateTime = data.date;
        time.textContent = new Intl.DateTimeFormat(document.documentElement.lang || 'en', { weekday: 'long', month: 'long', day: 'numeric', timeZone: 'UTC' }).format(new Date(`${data.date}T12:00:00Z`));
      }
      if (answer) {
        const target = new URL(answer.href, location.href);
        target.searchParams.set('autoask', data.question);
        target.searchParams.set('utm_campaign', data.date || new Date().toISOString().slice(0, 10));
        answer.href = `${target.toString().split('#')[0]}#ask-mirror-talk-form`;
        answer.dataset.mtQotdTheme = data.theme || '';
      }
    });
  };
  refreshLivingQuestion().catch(() => {});

  document.querySelectorAll('[data-mt-qotd-answer]').forEach((link) => link.addEventListener('click', () => {
    reportQotd('qotd_answer_opened', { theme: link.dataset.mtQotdTheme || '' });
  }));
  document.querySelectorAll('[data-mt-qotd-reminder]').forEach((button) => button.addEventListener('click', async () => {
    const buttons = document.querySelectorAll('[data-mt-qotd-reminder]');
    buttons.forEach((item) => { item.disabled = true; });
    qotdStatus('Opening your browser’s notification permission…');
    try {
      await subscribeToDailyQuestion();
      qotdStatus('You’re subscribed. Tomorrow’s question will arrive at about 8:00 in your local time.');
      buttons.forEach((item) => { item.textContent = 'Daily question enabled'; });
      reportQotd('qotd_reminder_enabled');
    } catch (error) {
      qotdStatus(error?.message || 'The reminder could not be enabled. Please try again.');
      buttons.forEach((item) => { item.disabled = false; });
    }
  }));
})();
