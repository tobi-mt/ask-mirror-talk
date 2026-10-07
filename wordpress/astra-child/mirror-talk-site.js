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
})();
