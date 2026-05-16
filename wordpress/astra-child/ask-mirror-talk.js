(function() {
  'use strict';

  // ─── Debug Logging ──────────────────────────────────────────
  const DEBUG = window.location.hostname === 'localhost' || window.location.search.includes('debug=1');
  const log = DEBUG ? console.log.bind(console, '[AMT]') : () => {};
  const warn = DEBUG ? console.warn.bind(console, '[AMT]') : () => {};
  const error = console.error.bind(console, '[AMT Error]'); // Always log errors

  // Track when the page loaded (for service worker update detection)
  window.amtLoadTime = Date.now();

  log('Ask Mirror Talk Widget v5.9.18 loaded');

  const form = document.querySelector("#ask-mirror-talk-form");
  const input = document.querySelector("#ask-mirror-talk-input");
  const submitBtn = document.querySelector("#ask-mirror-talk-submit");
  const output = document.querySelector("#ask-mirror-talk-output");
  const citations = document.querySelector("#ask-mirror-talk-citations");
  const citationsContainer = document.querySelector(".ask-mirror-talk-citations");
  const responseContainer = document.querySelector(".ask-mirror-talk-response");
  const suggestionsContainer = document.querySelector("#ask-mirror-talk-suggestions");
  const suggestionsList = suggestionsContainer ? suggestionsContainer.querySelector(".amt-suggestions-list") : null;
  const followupsContainer = document.querySelector("#ask-mirror-talk-followups");
  const followupsList = followupsContainer ? followupsContainer.querySelector(".amt-followups-list") : null;
  const topicsContainer = document.querySelector("#ask-mirror-talk-topics");
  const topicsList = topicsContainer ? topicsContainer.querySelector(".amt-topics-list") : null;
  const qotdContainer = document.querySelector("#ask-mirror-talk-qotd");
  const starterJourneysContainer = document.querySelector('#amt-starter-journeys');
  const activationChecklistContainer = document.querySelector('#amt-activation-checklist');
  const exploreExpander = document.querySelector('#amt-explore-expander');
  const exploreToggle = document.querySelector('#amt-explore-toggle');
  const explorePanel = document.querySelector('#amt-explore-panel');
  const exploreIcons = document.querySelector('#amt-explore-icons');
  const journeyCard = document.querySelector('#amt-journey-card');
  const momentumCard = document.querySelector('#amt-momentum-card');
  const weeklyRecapCard = document.querySelector('#amt-weekly-recap');
  const streakRevivalCard = document.querySelector('#amt-streak-revival-card');
  const answerContext = document.querySelector('#amt-answer-context');
  const continuationStrip = document.querySelector('#amt-continuation-strip');
  const answerUtilities = document.querySelector('#amt-answer-utilities');
  const citationTrustNote = document.querySelector('#amt-citation-trust-note');
  const questionCoach = document.querySelector('#amt-question-coach');
  const workflowBar = document.querySelector('#amt-workflow-bar');
  const workflowNudge = document.querySelector('#amt-workflow-nudge');
  const workflowNudgeText = document.querySelector('#amt-workflow-nudge-text');
  const workflowNudgeActions = document.querySelector('#amt-workflow-nudge-actions');
  const widgetRoot = form ? form.closest('.ask-mirror-talk') : document.querySelector('.ask-mirror-talk');
  const launchSplash = document.querySelector('#amt-launch-splash');
  const launchSplashStatus = document.querySelector('#amt-launch-splash-status');
  const workflowPanelsRoot = document.querySelector('#amt-workflow-panels');
  const workflowPanels = {
    ask: document.querySelector('#amt-workflow-panel-ask'),
    explore: document.querySelector('#amt-workflow-panel-explore'),
    save_share: document.querySelector('#amt-workflow-panel-save-share'),
    progress: document.querySelector('#amt-workflow-panel-progress')
  };
  const saveShareHub = document.querySelector('#amt-save-share-hub');

  // Check if we're in test mode before checking for form
  const ENABLE_TEST_EXPORTS = !!window.__AMT_ENABLE_TEST_EXPORTS__;
  // Intro audio intentionally disabled globally due unreliable autoplay behavior across devices.
  const ENABLE_LAUNCH_AUDIO = false;
  const ACTIVATION_CHECKLIST_KEY = 'amt_activation_checklist_v1';

  let hasHiddenLaunchSplash = false;
  let launchSplashAudioStop = null;
  let launchSplashAudioStarting = false;
  let launchSplashMood = 'Calm';

  if (hasHiddenLaunchSplash && launchSplash) launchSplash.style.display = 'none';
  if (!form && !ENABLE_TEST_EXPORTS) {
    if (launchSplash) launchSplash.style.display = 'none';
    warn('⚠️ Ask Mirror Talk form not found on this page');
    return;
  }

  function hideLaunchSplash(message) {
    if (hasHiddenLaunchSplash || !launchSplash) return;
    hasHiddenLaunchSplash = true;

    if (launchSplashStatus && message) {
      launchSplashStatus.textContent = String(message).slice(0, 120);
    }

    if (typeof launchSplashAudioStop === 'function') {
      launchSplashAudioStop();
      launchSplashAudioStop = null;
    }

    launchSplash.classList.add('amt-launch-splash-exit');
    setTimeout(() => {
      launchSplash.style.display = 'none';
      launchSplash.setAttribute('aria-hidden', 'true');
    }, 500);
  }

  function normalizeMoodPreset(mood) {
    const clean = String(mood || '').trim().toLowerCase();
    if (clean === 'warm') return 'Warm';
    if (clean === 'hopeful') return 'Hopeful';
    return 'Calm';
  }

  const THEME_MOOD_EXACT_MAP = {
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
    'career': 'Hopeful',
  };

  const THEME_MOOD_PHRASE_RULES = [
    { mood: 'Calm', test: /night reflection|evening reflection|rest and reset|release and rest|calm your mind/ },
    { mood: 'Hopeful', test: /midday reflection|purpose reset|next step|future self|fresh start|new chapter/ },
    { mood: 'Warm', test: /self[-\s]?worth|self[-\s]?love|self[-\s]?compassion|belonging|connection|relationships?/ },
    { mood: 'Calm', test: /inner peace|grief|anx|fear|stress|overwhelm|burnout|healing|forgive|loneliness/ },
    { mood: 'Hopeful', test: /purpose|calling|growth|clarity|confidence|courage|vision|career|momentum|breakthrough/ },
  ];

  function normalizeThemeKey(value) {
    return String(value || '')
      .trim()
      .toLowerCase()
      .replace(/[_-]+/g, ' ')
      .replace(/\s+/g, ' ');
  }

  function inferMoodFromThemeText(themeText) {
    const text = normalizeThemeKey(themeText);
    if (!text) return 'Calm';

    if (THEME_MOOD_EXACT_MAP[text]) {
      return THEME_MOOD_EXACT_MAP[text];
    }

    for (const [exactTheme, mood] of Object.entries(THEME_MOOD_EXACT_MAP)) {
      if (text.includes(exactTheme)) return mood;
    }

    for (const rule of THEME_MOOD_PHRASE_RULES) {
      if (rule.test.test(text)) return rule.mood;
    }

    if (/calm|peace|quiet|still|gentle|breathe|slow/.test(text)) return 'Calm';
    if (/love|heart|care|compassion|kindness|bond|together/.test(text)) return 'Warm';
    if (/hope|rise|build|grow|dream|believe|advance|thrive/.test(text)) return 'Hopeful';

    return 'Calm';
  }

  function resolveLaunchMoodPreset() {
    try {
      const params = new URLSearchParams(window.location.search);
      if (params.get('night_reflection') === '1') return 'Calm';
      if (params.get('midday_reflection') === '1') return 'Hopeful';
      if (params.get('invite_reflection') === '1') return 'Warm';

      const intent = params.get('intent') || '';
      if (intent) return inferMoodFromThemeText(intent);

      const theme = params.get('theme') || '';
      if (theme) return inferMoodFromThemeText(theme);
    } catch (e) {}

    try {
      const qotdRaw = localStorage.getItem('amt_latest_qotd');
      if (qotdRaw) {
        const qotd = JSON.parse(qotdRaw);
        if (qotd && qotd.theme) return inferMoodFromThemeText(qotd.theme);
      }
    } catch (e) {}

    const hour = new Date().getHours();
    if (hour >= 22 || hour < 6) return 'Calm';
    if (hour >= 11 && hour <= 16) return 'Hopeful';
    return 'Warm';
  }

  function getMoodPresetConfig(mood) {
    const key = normalizeMoodPreset(mood);
    const presets = {
      Calm: {
        cycleMs: 520,
        masterGain: 0.30,
        padGain: 0.18,
        pulsePattern: [0.65, 0, 0.32, 0, 0.55, 0, 0.22, 0],
        melodyPattern: [392.0, 349.23, 329.63, 349.23, 392.0, 440.0, 392.0, 349.23],
        chordPattern: [[196.0, 246.94], [174.61, 220.0], [146.83, 196.0], [174.61, 220.0]],
      },
      Warm: {
        cycleMs: 500,
        masterGain: 0.34,
        padGain: 0.20,
        pulsePattern: [0.8, 0, 0.45, 0, 0.72, 0, 0.38, 0],
        melodyPattern: [392.0, 440.0, 493.88, 440.0, 392.0, 349.23, 329.63, 349.23],
        chordPattern: [[196.0, 246.94], [220.0, 261.63], [174.61, 220.0], [196.0, 246.94]],
      },
      Hopeful: {
        cycleMs: 470,
        masterGain: 0.38,
        padGain: 0.22,
        pulsePattern: [1, 0, 0.6, 0, 0.86, 0, 0.5, 0],
        melodyPattern: [392.0, 440.0, 493.88, 523.25, 493.88, 440.0, 392.0, 349.23],
        chordPattern: [[196.0, 246.94], [220.0, 277.18], [246.94, 293.66], [220.0, 277.18]],
      },
    };
    return presets[key] || presets.Calm;
  }

  function readLaunchAutoplayPreference() {
    return !!ENABLE_LAUNCH_AUDIO;
  }

  async function createLaunchSplashAmbientTrack(mood) {
    const AudioContextCtor = window.AudioContext || window.webkitAudioContext;
    if (!AudioContextCtor) return null;

    const preset = getMoodPresetConfig(mood);

    const context = new AudioContextCtor();

    // Resume first and only continue if the context is actually running.
    // If autoplay is blocked, return null so user-gesture retries can proceed.
    if (typeof context.resume === 'function') {
      try {
        await context.resume();
      } catch (err) {
        console.warn('AudioContext.resume() failed:', err && err.message ? err.message : err);
      }
    }
    if (context.state !== 'running') {
      try { context.close(); } catch (e) {}
      return null;
    }

    const master = context.createGain();
    const padGain = context.createGain();
    const rhythmGain = context.createGain();
    const melodyGain = context.createGain();
    const lowPad = context.createOscillator();
    const highPad = context.createOscillator();
    const pulse = context.createOscillator();
    const melody = context.createOscillator();

    lowPad.type = 'sine';
    lowPad.frequency.value = 196.0; // G3

    highPad.type = 'triangle';
    highPad.frequency.value = 246.94; // B3

    pulse.type = 'sine';
    pulse.frequency.value = 98.0; // G2 pulse bass

    melody.type = 'triangle';
    melody.frequency.value = 392.0; // G4

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

    const now = context.currentTime;
    // Intro: slower ramp so the sound blooms in softly.
    master.gain.linearRampToValueAtTime(preset.masterGain, now + 1.4);
    padGain.gain.linearRampToValueAtTime(preset.padGain, now + 1.1);
    // Keep rhythmic/melody layers audible during intro so sound is noticeable
    // on small mobile speakers where low pads alone can be too subtle.
    rhythmGain.gain.linearRampToValueAtTime(0.022, now + 1.2);
    melodyGain.gain.linearRampToValueAtTime(0.028, now + 1.2);

    let step = 0;
    const cycleMs = preset.cycleMs;
    const pulsePattern = preset.pulsePattern;
    const melodyPattern = preset.melodyPattern;
    const chordPattern = preset.chordPattern;

    const interval = window.setInterval(() => {
      const t = context.currentTime;
      const pulseStrength = pulsePattern[step % pulsePattern.length];
      const melodyFreq = melodyPattern[step % melodyPattern.length];
      const chord = chordPattern[Math.floor(step / 2) % chordPattern.length];

      lowPad.frequency.setTargetAtTime(chord[0], t, 0.18);
      highPad.frequency.setTargetAtTime(chord[1], t, 0.2);

      pulse.frequency.setTargetAtTime(chord[0] / 2, t, 0.08);
      rhythmGain.gain.cancelScheduledValues(t);
      rhythmGain.gain.setValueAtTime(0.018, t);
      rhythmGain.gain.linearRampToValueAtTime(0.032 + (preset.masterGain * pulseStrength), t + 0.08);
      rhythmGain.gain.linearRampToValueAtTime(0.014, t + 0.38);

      melody.frequency.setTargetAtTime(melodyFreq, t, 0.06);
      melodyGain.gain.cancelScheduledValues(t);
      melodyGain.gain.setValueAtTime(0.006, t);
      melodyGain.gain.linearRampToValueAtTime(0.02, t + 0.12);
      melodyGain.gain.linearRampToValueAtTime(0.004, t + 0.42);

      step += 1;
    }, cycleMs);

    return () => {
      window.clearInterval(interval);
      const endAt = context.currentTime + 0.85;
      master.gain.cancelScheduledValues(context.currentTime);
      master.gain.setValueAtTime(master.gain.value, context.currentTime);
      master.gain.linearRampToValueAtTime(0.0001, endAt);

      window.setTimeout(() => {
        try { lowPad.stop(); } catch (e) {}
        try { highPad.stop(); } catch (e) {}
        try { pulse.stop(); } catch (e) {}
        try { melody.stop(); } catch (e) {}
        try { context.close(); } catch (e) {}
      }, 920);
    };
  }

  function initLaunchSplash() {
    if (!launchSplash) return;

    // Always show splash on each real app launch.
    launchSplash.style.display = '';

    launchSplashMood = resolveLaunchMoodPreset();

    if (launchSplashStatus) {
      launchSplashStatus.textContent = `Loading your premium ${launchSplashMood.toLowerCase()} mode...`;
    }

    const autoplayEnabled = readLaunchAutoplayPreference();

    // Hard maximum: always dismiss after 9 seconds.
    window.setTimeout(() => {
      hideLaunchSplash('Ready to reflect');
    }, 9000);

    // Minimum visible duration before any event-driven dismiss is honored.
    // This prevents the splash from flashing for ~300ms on cached PWA loads
    // where window.load fires almost instantly from the service worker cache.
    const SPLASH_MIN_MS = 1800;
    const _splashShowTime = Date.now();
    function _hideSplashAfterMin(msg) {
      const remaining = Math.max(0, SPLASH_MIN_MS - (Date.now() - _splashShowTime));
      window.setTimeout(() => hideLaunchSplash(msg), remaining);
    }

    // Check multiple ready states to ensure we never dismiss too early:
    // - If the document is already fully loaded, apply the minimum timeout
    // - If it's interactive (DOMContentLoaded), also apply minimum
    // - If it's loading, wait for the load event and apply minimum
    if (document.readyState === 'complete') {
      _hideSplashAfterMin('Ready to reflect');
    } else if (document.readyState === 'interactive') {
      _hideSplashAfterMin('Ready to reflect');
    } else {
      window.addEventListener('load', () => {
        _hideSplashAfterMin('Ready to reflect');
      }, { once: true });
    }

    // Autoplay: trigger audio playback automatically if user has enabled it.
    // The audio is now controlled from the Settings panel, but defaults to on.
    // Try to start audio immediately, then again on first user interaction as fallback.
    async function tryStartAudio() {
      if (launchSplashAudioStop || hasHiddenLaunchSplash || launchSplashAudioStarting) return false;
      launchSplashAudioStarting = true;
      try {
        const stopAudio = await createLaunchSplashAmbientTrack(launchSplashMood);
        if (stopAudio) {
          launchSplashAudioStop = stopAudio;
          return true;
        }
        return false;
      } finally {
        launchSplashAudioStarting = false;
      }
    }

    if (autoplayEnabled && !hasHiddenLaunchSplash) {
      // Try immediately (may work on non-iOS or if user interacted with page)
      window.setTimeout(tryStartAudio, 60);

      // Fallback: if user touches/clicks the splash, try audio again.
      // This handles iOS autoplay policy which requires user gesture.
      const removeAudioFallbackListeners = () => {
        if (launchSplash) launchSplash.removeEventListener('click', fallbackHandler);
        if (launchSplash) launchSplash.removeEventListener('touchstart', fallbackHandler);
        window.removeEventListener('pointerdown', fallbackHandler);
        window.removeEventListener('keydown', fallbackHandler);
      };

      const fallbackHandler = async () => {
        const started = await tryStartAudio();
        if (started || hasHiddenLaunchSplash) {
          removeAudioFallbackListeners();
        }
      };
      if (launchSplash && autoplayEnabled) {
        launchSplash.addEventListener('click', fallbackHandler);
        launchSplash.addEventListener('touchstart', fallbackHandler);
        window.addEventListener('pointerdown', fallbackHandler);
        window.addEventListener('keydown', fallbackHandler);

        window.setTimeout(() => {
          if (!launchSplashAudioStop) {
            removeAudioFallbackListeners();
          }
        }, 10000);
      }
    }
  }

  initLaunchSplash();

  // ─── API URL ────────────────────────────────────────────────
  const API_BASE = (typeof AskMirrorTalk !== 'undefined' ? (AskMirrorTalk.apiUrl || 'https://ask-mirror-talk-production.up.railway.app') : 'https://ask-mirror-talk-production.up.railway.app');
  const BASE_PAGE_URL = 'https://mirrortalkpodcast.com/ask-mirror-talk';
  const REFLECTION_CARD_QR_URL = `${BASE_PAGE_URL}?ref=card_qr`;
  const REFLECTION_CARD_URL_LABEL = 'mirrortalkpodcast.com/ask-mirror-talk';
  const DEBUG_NO_CACHE = new URLSearchParams(window.location.search).get('amt_nocache') === '1';
  const CAMPAIGN_SESSION_KEY = 'amt_campaign_context';
  const REFERRAL_CTA_DISMISS_KEY = 'amt_referral_cta_dismiss_until';
  const REFERRAL_CTA_SHOWN_SESSION_KEY = 'amt_referral_cta_shown';
  const RECENT_EXPLORE_THEMES_KEY = 'amt_recent_explore_themes';
  const RECENT_NIGHT_THEMES_KEY = 'amt_recent_night_themes';
  const WORKFLOW_SESSION_KEY = 'amt_active_workflow_step';
  const AUTO_START_SESSION_KEY = 'amt_auto_start_processed';
  const TEST_FORCE_FAMILY = String(window.__AMT_TEST_FORCE_FAMILY__ || '').trim();
  let lastShownCitations = [];
  let pendingQuestionOrigin = 'typed';
  let activeCampaignContext = null;

  function hasStrongSupport(citationsList) {
    return Array.isArray(citationsList) && citationsList.length > 0;
  }

  function _readStorage(key) {
    try { return localStorage.getItem(key); } catch (e) { return null; }
  }

  function _writeStorage(key, value) {
    try { localStorage.setItem(key, value); } catch (e) {}
  }

  function sanitizeCampaignValue(value, maxLen) {
    const clean = String(value || '').trim();
    if (!clean) return '';
    return clean.slice(0, maxLen || 120);
  }

  function loadCampaignContext() {
    const params = new URLSearchParams(window.location.search);
    const fromUrl = {
      source: sanitizeCampaignValue(params.get('utm_source'), 80),
      medium: sanitizeCampaignValue(params.get('utm_medium'), 80),
      campaign: sanitizeCampaignValue(params.get('utm_campaign'), 120),
      content: sanitizeCampaignValue(params.get('utm_content'), 120),
      ref: sanitizeCampaignValue(params.get('ref'), 80),
      intent: sanitizeCampaignValue(params.get('intent'), 80),
      theme: sanitizeCampaignValue(params.get('theme'), 80),
      question: sanitizeCampaignValue(params.get('question') || params.get('q'), 220),
      landedAt: Date.now()
    };

    const hasUrlContext = !!(fromUrl.source || fromUrl.medium || fromUrl.campaign || fromUrl.ref || fromUrl.intent || fromUrl.theme || fromUrl.question);
    if (hasUrlContext) {
      _writeStorage(CAMPAIGN_SESSION_KEY, JSON.stringify(fromUrl));
      return fromUrl;
    }

    try {
      const raw = _readStorage(CAMPAIGN_SESSION_KEY);
      if (!raw) return null;
      const parsed = JSON.parse(raw);
      const landedAt = parseInt(parsed.landedAt || '0', 10);
      if (landedAt && Date.now() - landedAt > 7 * 24 * 60 * 60 * 1000) {
        localStorage.removeItem(CAMPAIGN_SESSION_KEY);
        return null;
      }
      return parsed;
    } catch (e) {
      return null;
    }
  }

  function getCampaignMetadata() {
    const context = activeCampaignContext || loadCampaignContext();
    if (!context) return {};
    return {
      campaign_source: context.source || null,
      campaign_medium: context.medium || null,
      campaign_name: context.campaign || null,
      campaign_content: context.content || null,
      campaign_ref: context.ref || null,
      campaign_intent: context.intent || null,
      campaign_theme: context.theme || null
    };
  }

  function buildTrackedPageUrl(overrides) {
    const data = Object.assign({}, activeCampaignContext || {}, overrides || {});
    const url = new URL(BASE_PAGE_URL);
    if (data.source) url.searchParams.set('utm_source', data.source);
    if (data.medium) url.searchParams.set('utm_medium', data.medium);
    if (data.campaign) url.searchParams.set('utm_campaign', data.campaign);
    if (data.content) url.searchParams.set('utm_content', data.content);
    if (data.ref) url.searchParams.set('ref', data.ref);
    if (data.intent) url.searchParams.set('intent', data.intent);
    if (data.theme) url.searchParams.set('theme', data.theme);
    if (data.question) url.searchParams.set('q', sanitizeCampaignValue(data.question, 120));
    if (data.inviteReflection) url.searchParams.set('invite_reflection', '1');
    return url.toString();
  }

  function shouldShowReferralCta() {
    try {
      const dismissedUntil = parseInt(localStorage.getItem(REFERRAL_CTA_DISMISS_KEY) || '0', 10);
      if (dismissedUntil && Date.now() < dismissedUntil) return false;
    } catch (e) {}
    return true;
  }

  function dismissReferralCta(days) {
    const safeDays = Math.max(1, parseInt(days || '3', 10));
    try {
      const until = Date.now() + safeDays * 24 * 60 * 60 * 1000;
      localStorage.setItem(REFERRAL_CTA_DISMISS_KEY, String(until));
    } catch (e) {}
  }

  function markReferralCtaShownOncePerSession() {
    try {
      if (sessionStorage.getItem(REFERRAL_CTA_SHOWN_SESSION_KEY) === '1') return false;
      sessionStorage.setItem(REFERRAL_CTA_SHOWN_SESSION_KEY, '1');
      return true;
    } catch (e) {
      return true;
    }
  }

  function buildReferralInvitePayload(questionText, themeText) {
    const safeQuestion = sanitizeCampaignValue(questionText || '', 120);
    const safeTheme = sanitizeCampaignValue(themeText || '', 80);
    const inviteUrl = buildTrackedPageUrl({
      source: 'referral',
      medium: 'in_app',
      campaign: 'first_1000_growth',
      ref: 'save_share_referral',
      intent: 'friend_invite',
      question: safeQuestion,
      theme: safeTheme,
      inviteReflection: true,
    });
    const questionCopy = safeQuestion || 'What is on your heart right now?';
    return {
      title: 'Ask Mirror Talk',
      text: `Ask Mirror Talk helped me reflect on this question: "${questionCopy}". If this feels useful for you too, start here: ${inviteUrl}`,
      url: inviteUrl,
    };
  }

  // Device ID helpers
  function getOrCreateDeviceId() {
    const STORAGE_KEY = 'amt_device_id';
    let id = null;
    try {
      id = localStorage.getItem(STORAGE_KEY);
    } catch (e) {}
    if (id && typeof id === 'string' && id.length >= 16) return id;
    // Generate a new random device ID (UUID v4-like)
    id = ([1e7]+-1e3+-4e3+-8e3+-1e11).replace(/[018]/g, c =>
      (c ^ crypto.getRandomValues(new Uint8Array(1))[0] & 15 >> c / 4).toString(16)
    );
    try {
      localStorage.setItem(STORAGE_KEY, id);
    } catch (e) {}
    return id;
  }

  function emitProductEvent(name, metadata) {
    try {
      const deviceId = getOrCreateDeviceId();
      const merged = Object.assign({}, getCampaignMetadata(), metadata || {}, { device_id: deviceId });
      window.dispatchEvent(new CustomEvent('amt:product-event', {
        detail: {
          eventName: name,
          metadata: merged
        }
      }));
    } catch (e) {}
  }

  function loadActivationChecklistState() {
    const defaults = {
      askedFirstQuestion: false,
      usedGuidedEntry: false,
      savedOrShared: false,
      completedAt: 0,
    };
    try {
      const raw = localStorage.getItem(ACTIVATION_CHECKLIST_KEY);
      if (!raw) return defaults;
      const parsed = JSON.parse(raw);
      return Object.assign({}, defaults, parsed || {});
    } catch (e) {
      return defaults;
    }
  }

  function saveActivationChecklistState(nextState) {
    try {
      localStorage.setItem(ACTIVATION_CHECKLIST_KEY, JSON.stringify(nextState || {}));
    } catch (e) {}
  }

  function countActivationChecklistCompleted(state) {
    const s = state || loadActivationChecklistState();
    let total = 0;
    if (s.askedFirstQuestion) total += 1;
    if (s.usedGuidedEntry) total += 1;
    if (s.savedOrShared) total += 1;
    return total;
  }

  function markActivationChecklistStep(step, metadata) {
    const state = loadActivationChecklistState();
    if (!Object.prototype.hasOwnProperty.call(state, step) || state[step]) return;

    state[step] = true;
    if (countActivationChecklistCompleted(state) >= 3 && !state.completedAt) {
      state.completedAt = Date.now();
    }
    saveActivationChecklistState(state);

    emitProductEvent('activation_step_completed', Object.assign({
      step,
      completed_count: countActivationChecklistCompleted(state),
    }, metadata || {}));

    renderActivationChecklist();
  }

  function getStarterJourneysByMood(mood) {
    const key = normalizeMoodPreset(mood);
    const journeys = {
      Calm: [
        { label: 'Ease anxiety', question: 'I feel anxious right now. What gentle step can help me feel steady again?' },
        { label: 'Carry grief softly', question: 'I am carrying grief today. How can I move through it with honesty and peace?' },
        { label: 'Release pressure', question: 'I feel pressure building up. How can I release it without shutting down?' },
        { label: 'Night reset', question: 'Before I sleep, what should I release and what should I keep?' },
      ],
      Warm: [
        { label: 'Build self-worth', question: 'How can I rebuild self-worth in a practical way this week?' },
        { label: 'Heal a relationship', question: 'What is one honest way to improve a relationship that matters to me?' },
        { label: 'Lead with compassion', question: 'How can I speak truth with compassion in a difficult conversation?' },
        { label: 'Find belonging', question: 'Why do I feel alone lately, and how can I reconnect with people safely?' },
      ],
      Hopeful: [
        { label: 'Find purpose', question: 'I need clarity about purpose. What should I focus on right now?' },
        { label: 'Grow confidence', question: 'How can I grow confidence without pretending to be someone I am not?' },
        { label: 'Take next step', question: 'What is one courageous next step I can take this week?' },
        { label: 'Midday reset', question: 'In the middle of today, what would help me reset and move with intention?' },
      ],
    };
    return journeys[key] || journeys.Calm;
  }

  function renderStarterJourneys() {
    if (!starterJourneysContainer) return;
    const mood = launchSplashMood || resolveLaunchMoodPreset();
    const journeys = getStarterJourneysByMood(mood);
    starterJourneysContainer.innerHTML = `
      <p class="amt-starter-journeys-head">Quick start (${escapeHtml(String(mood).toLowerCase())} mode)</p>
      <div class="amt-starter-journeys-list">
        ${journeys.map(item => `<button type="button" class="amt-starter-journey-btn" data-q="${escapeHtml(item.question)}">${escapeHtml(item.label)}</button>`).join('')}
      </div>
    `;

    starterJourneysContainer.querySelectorAll('.amt-starter-journey-btn').forEach(btn => {
      btn.addEventListener('click', () => {
        const q = btn.getAttribute('data-q') || '';
        setQuestionOrigin('starter_journey', { mood });
        markActivationChecklistStep('usedGuidedEntry', { source: 'starter_journey' });
        submitQuestionFromPrompt(q);
      });
    });
  }

  function renderActivationChecklist() {
    if (!activationChecklistContainer) return;
    const state = loadActivationChecklistState();
    const doneCount = countActivationChecklistCompleted(state);

    if (doneCount >= 3) {
      activationChecklistContainer.style.display = 'none';
      activationChecklistContainer.innerHTML = '';
      return;
    }

    const tasks = [
      { key: 'askedFirstQuestion', label: 'Ask your first reflection question' },
      { key: 'usedGuidedEntry', label: 'Use a guided entry (QOTD or quick start)' },
      { key: 'savedOrShared', label: 'Save or share one reflection' },
    ];

    const nextAction = !state.askedFirstQuestion
      ? 'ask'
      : (!state.usedGuidedEntry ? 'guided' : 'share');

    activationChecklistContainer.innerHTML = `
      <div class="amt-activation-checklist-head">
        <p class="amt-activation-checklist-title">Your first 3 wins</p>
        <span class="amt-activation-checklist-progress">${doneCount}/3 done</span>
      </div>
      <ul class="amt-activation-checklist-list">
        ${tasks.map(task => `
          <li class="amt-activation-checklist-item${state[task.key] ? ' done' : ''}">
            <span class="amt-activation-checklist-dot" aria-hidden="true"></span>
            <span>${state[task.key] ? '<strong>Done:</strong> ' : ''}${escapeHtml(task.label)}</span>
          </li>
        `).join('')}
      </ul>
      <div class="amt-activation-checklist-actions">
        ${nextAction === 'ask' ? '<button type="button" class="amt-activation-checklist-btn" data-action="focus-ask">Start with your first question</button>' : ''}
        ${nextAction === 'guided' ? '<button type="button" class="amt-activation-checklist-btn" data-action="try-guided">Try a guided quick start</button>' : ''}
        ${nextAction === 'share' ? '<button type="button" class="amt-activation-checklist-btn" data-action="open-share">Open Save & Share</button>' : ''}
      </div>
    `;

    activationChecklistContainer.style.display = '';

    activationChecklistContainer.querySelectorAll('[data-action]').forEach(btn => {
      btn.addEventListener('click', () => {
        const action = btn.getAttribute('data-action');
        if (action === 'focus-ask') {
          runWorkflowAction('ask', { persist: true, scroll: true });
          if (input) input.focus();
          return;
        }
        if (action === 'try-guided') {
          const firstStarter = starterJourneysContainer?.querySelector('.amt-starter-journey-btn');
          if (firstStarter) {
            firstStarter.click();
            return;
          }
        }
        if (action === 'open-share') {
          runWorkflowAction('save_share', { persist: true, scroll: true });
        }
      });
    });
  }

  function initActivationExperience() {
    renderStarterJourneys();
    renderActivationChecklist();

    window.addEventListener('amt:product-event', (event) => {
      const detail = event && event.detail ? event.detail : {};
      const name = detail.eventName || '';
      const metadata = detail.metadata || {};
      if (!name || name === 'activation_step_completed') return;

      if (name === 'question_submitted') {
        markActivationChecklistStep('askedFirstQuestion', { source: 'submit' });
      }

      if (name === 'question_origin_selected') {
        const origin = String((metadata && metadata.origin) || '').toLowerCase();
        if (['qotd', 'starter_journey', 'topic_starter', 'question_coach', 'suggested_question', 'continue_reflection'].includes(origin)) {
          markActivationChecklistStep('usedGuidedEntry', { source: origin });
        }
      }

      if (name === 'share_cta_used' || name === 'reflection_note_saved') {
        markActivationChecklistStep('savedOrShared', { source: name });
      }
    });
  }

  function setQuestionOrigin(origin, metadata) {
    pendingQuestionOrigin = origin || 'typed';
    emitProductEvent('question_origin_selected', Object.assign({ origin: pendingQuestionOrigin }, metadata || {}));
  }

  // ─── Nonce management ───────────────────────────────────────
  let currentNonce = AskMirrorTalk.nonce;

  async function refreshNonce() {
    try {
      const body = new URLSearchParams();
      body.set('action', 'ask_mirror_talk_refresh_nonce');
      const res = await fetch(AskMirrorTalk.ajaxUrl, {
        method: 'POST',
        headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
        body: body.toString()
      });
      if (!res.ok) throw new Error('Nonce refresh failed');
      const json = await res.json();
      if (json.success && json.data && json.data.nonce) {
        currentNonce = json.data.nonce;
        log('✓ Nonce refreshed');
        return true;
      }
    } catch (e) {
      warn('Nonce refresh error:', e);
    }
    return false;
  }

  // Response container: hidden if empty on page load, immediately visible if it has content.
  if (responseContainer) {
    if (!output.innerHTML || output.innerHTML.trim() === '') {
      responseContainer.style.display = 'none';
    } else {
      // Pre-existing content (e.g. cached answer visible on page load) — show immediately.
      responseContainer.classList.add('amt-visible');
    }
  }
  // Screen readers announced streaming content progressively
  if (output) {
    output.setAttribute('aria-live', 'polite');
    output.setAttribute('aria-atomic', 'false');
  }
  // Citations: CSS default is display:none so the h3 heading doesn't create blank space.

  // ─── Question of the Day ─────────────────────────────────────
  function renderQuestionOfTheDay(data, options) {
    if (!qotdContainer) return;
    const source = data || {};
    if (!source.question) {
      qotdContainer.style.display = 'none';
      return;
    }

    qotdContainer.innerHTML = `
      <div class="amt-qotd-inner">
        <div class="amt-qotd-header">
          <span class="amt-qotd-badge">✨ Question of the Day</span>
          <span class="amt-qotd-theme">${escapeHtml(source.theme || '')}</span>
        </div>
        <p class="amt-qotd-text">"${escapeHtml(source.question)}"</p>
        <button type="button" class="amt-qotd-ask">Ask this →</button>
      </div>
    `;

    qotdContainer.querySelector('.amt-qotd-ask').addEventListener('click', () => {
      setQuestionOrigin('qotd', { theme: source.theme || null });
      qotdContainer.style.display = 'none';
      submitQuestionFromPrompt(source.question);
    });

    if (!options || options.persist !== false) {
      try {
        localStorage.setItem('amt_latest_qotd', JSON.stringify({
          question: String(source.question || '').slice(0, 500),
          theme: String(source.theme || '').slice(0, 80),
          date: todayStr ? todayStr() : null,
          savedAt: Date.now()
        }));
      } catch (e) {}
    }

    qotdContainer.style.display = '';
  }

  function renderCachedQuestionOfTheDay() {
    const cached = loadLatestQotd();
    if (!cached || !cached.question) return false;
    renderQuestionOfTheDay(cached, { persist: false });
    return true;
  }

  function loadQuestionOfTheDay() {
    if (!qotdContainer) return;

    fetch(`${API_BASE}/api/question-of-the-day`)
      .then(res => res.json())
      .then(data => {
        if (!data.question) {
          if (!renderCachedQuestionOfTheDay()) qotdContainer.style.display = 'none';
          return;
        }

        renderQuestionOfTheDay(data);
      })
      .catch(err => {
        warn('Could not load Question of the Day:', err);
        if (!renderCachedQuestionOfTheDay()) qotdContainer.style.display = 'none';
      });
    
    // ─── Predictive Loading: Preload QOTD answer ──────────────────────────
    // Prefetch the QOTD answer in background for instant response
    setTimeout(preloadQOTDAnswer, 2000);
  }
  
  function preloadQOTDAnswer() {
    const qotd = _readStorage('amt_qotd_cache');
    if (!qotd) return;
    
    try {
      const data = JSON.parse(qotd);
      if (!data.question) return;
      
      // Check if we already have a cached answer
      const cached = _readStorage('amt_qotd_answer_cache');
      if (cached) {
        const cachedData = JSON.parse(cached);
        if (cachedData.timestamp && (Date.now() - cachedData.timestamp < 3600000)) {
          log('QOTD answer already cached');
          return;
        }
      }
      
      // Prefetch answer in background
      fetch(`${API_BASE}/ask`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ question: data.question })
      })
        .then(res => res.json())
        .then(answer => {
          _writeStorage('amt_qotd_answer_cache', JSON.stringify({
            question: data.question,
            answer,
            timestamp: Date.now()
          }));
          log('QOTD answer preloaded');
        })
        .catch(() => {}); // Silent fail
    } catch (e) {}
  }

  // ─── Auto-submit helper ──────────────────────────────────────
  // Used by both the URL ?autoask= path and the SW postMessage path.
  function autoSubmitQuestion(question, origin, metadata) {
    if (!question || !form) return;
    // Don't fire a second concurrent request if one is already in-flight
    // (guards the postMessage fallback path for old iOS Safari < 15.4).
    if (submitBtn && submitBtn.disabled) return;
    setQuestionOrigin(origin || 'notification_autoask', metadata || {});
    input.value = question;
    runWorkflowAction('ask', { persist: true, scroll: false });
    // Hide the QOTD card so the answer takes centre stage
    if (qotdContainer) qotdContainer.style.display = 'none';
    // Scroll the form into view smoothly before firing
    form.scrollIntoView({ behavior: 'smooth', block: 'center' });
    // Short delay so the scroll completes and the page paint is visible
    setTimeout(() => {
      form.dispatchEvent(new Event('submit', { cancelable: true }));
    }, 300);
  }

  function loadLatestQotd() {
    try {
      const raw = localStorage.getItem('amt_latest_qotd');
      if (!raw) return null;
      const parsed = JSON.parse(raw);
      return parsed && parsed.question ? parsed : null;
    } catch (e) {
      return null;
    }
  }

  function loadRecentThemeHistory(key) {
    try {
      const raw = localStorage.getItem(key);
      if (!raw) return [];
      const parsed = JSON.parse(raw);
      return Array.isArray(parsed) ? parsed.filter(Boolean).map(String) : [];
    } catch (e) {
      return [];
    }
  }

  function saveRecentThemeHistory(key, themes) {
    try {
      localStorage.setItem(key, JSON.stringify((themes || []).slice(0, 6)));
    } catch (e) {}
  }

  function rememberRecentTheme(key, theme) {
    const clean = String(theme || '').trim();
    if (!clean) return;
    const updated = [clean, ...loadRecentThemeHistory(key).filter(item => item !== clean)];
    saveRecentThemeHistory(key, updated);
  }

  function chooseRotatingTheme(candidates, fallbackTheme, storageKey) {
    const cleanCandidates = Array.from(new Set((candidates || []).filter(Boolean).map(String)));
    const recent = loadRecentThemeHistory(storageKey);
    const preferred = cleanCandidates.filter(theme => !recent.includes(theme));
    const pool = preferred.length ? preferred : cleanCandidates;
    const fallback = fallbackTheme || pool[0] || '';
    if (!pool.length) return fallback;

    const seedSource = `${todayStr()}|${pool.join('|')}|${recent.join('|')}`;
    let seed = 0;
    for (let i = 0; i < seedSource.length; i++) {
      seed = ((seed << 5) - seed) + seedSource.charCodeAt(i);
      seed |= 0;
    }
    const chosen = pool[Math.abs(seed) % pool.length] || fallback;
    if (chosen) rememberRecentTheme(storageKey, chosen);
    return chosen || fallback;
  }

  function buildThemeReflectionQuestion(theme, moment) {
    const cleanTheme = String(theme || '').trim();
    const themeKey = cleanTheme.toLowerCase();
    const nightly = moment === 'night';
    const prompts = {
      'self-worth': nightly
        ? 'What does Mirror Talk teach about resting in my worth instead of proving myself?'
        : 'What does Mirror Talk teach about returning to my worth without comparing myself?',
      boundaries: nightly
        ? 'What does Mirror Talk teach about ending the day with healthier boundaries?'
        : 'How can I honor my boundaries without losing compassion?',
      grief: nightly
        ? 'How can I carry grief gently without losing myself?'
        : 'What does Mirror Talk teach about carrying grief with honesty and hope?',
      healing: nightly
        ? 'What does Mirror Talk teach about giving healing a gentler place to begin?'
        : 'How do I start the healing process with honesty and patience?',
      relationships: nightly
        ? 'What does Mirror Talk teach about bringing honesty and tenderness into relationships?'
        : 'How can I love with honesty without losing myself?',
      gratitude: nightly
        ? 'What role does gratitude play in helping me carry today with more peace?'
        : 'How can gratitude shift the way I move through hardship?',
      purpose: nightly
        ? 'What does Mirror Talk teach about listening to purpose without forcing clarity?'
        : 'How do I find my purpose without rushing the process?',
      faith: nightly
        ? 'How can I hold faith and doubt with honesty before I rest?'
        : 'How do I reconnect with my faith in a more honest way?',
      courage: nightly
        ? 'What does courage look like when I am tired but still trying to grow?'
        : 'What does courage look like in everyday life?',
      fear: nightly
        ? 'What is fear asking me to notice before I move forward?'
        : 'How can I move with courage when fear is still present?',
      community: nightly
        ? 'What does Mirror Talk teach about the kind of community that helps me become whole?'
        : 'What does Mirror Talk teach about the power of community?',
      leadership: nightly
        ? 'What does Mirror Talk teach about leading with vulnerability and integrity?'
        : 'What does it look like to lead with vulnerability?',
      parenting: nightly
        ? 'How can I parent with more presence, repair, and emotional steadiness?'
        : 'How do I raise kids who are emotionally resilient?',
      growth: nightly
        ? 'How do I know whether growth is really changing me over time?'
        : 'What can I learn from the growth this season is asking of me?',
      communication: nightly
        ? 'What does Mirror Talk teach about speaking truth with care?'
        : 'How do I have hard conversations without damaging the relationship?',
      identity: nightly
        ? 'What does it mean to live authentically without losing my voice?'
        : 'How do I discover my true identity?'
    };
    if (prompts[themeKey]) return prompts[themeKey];
    if (cleanTheme) {
      return nightly
        ? `What does Mirror Talk teach about carrying ${cleanTheme} with more honesty and peace?`
        : `What does Mirror Talk teach about ${cleanTheme} in everyday life?`;
    }
    return nightly
      ? 'What does Mirror Talk teach about turning today into wisdom before I rest?'
      : 'What does Mirror Talk teach about paying attention to what matters today?';
  }

  function buildNightReflectionPrompt() {
    const today = todayStr();
    const lastSession = loadLastSession() || null;
    const activity = loadActivityLog().filter(entry => entry && entry.day === today);
    const notes = loadReflectionNotes().filter(entry => {
      if (!entry || !entry.savedAt) return false;
      return formatLocalDate(new Date(entry.savedAt)) === today;
    });
    const insights = loadInsights().map(normalizeInsightRecord).filter(entry => {
      if (!entry || !entry.savedAt) return false;
      return formatLocalDate(new Date(entry.savedAt)) === today;
    });
    const recap = getWeeklyRecapData ? getWeeklyRecapData() : null;
    const latestQotd = loadLatestQotd();
    const recentNightThemes = loadRecentThemeHistory(RECENT_NIGHT_THEMES_KEY);

    const todayTheme = (
      activity.find(entry => entry.type === 'question' && entry.theme)?.theme ||
      (lastSession && lastSession.time && formatLocalDate(new Date(lastSession.time)) === today ? lastSession.theme : '') ||
      (insights[0] && insights[0].theme) ||
      (latestQotd && latestQotd.theme) ||
      ''
    );

    if (lastSession && lastSession.question && lastSession.time && formatLocalDate(new Date(lastSession.time)) === today) {
      if (todayTheme) rememberRecentTheme(RECENT_NIGHT_THEMES_KEY, todayTheme);
      
      // Check if this theme keeps returning for the user
      const recentHistory = loadRecentThemeHistory(RECENT_NIGHT_THEMES_KEY);
      const isRecurringTheme = todayTheme && recentHistory.filter(t => t === todayTheme).length >= 2;
      
      if (isRecurringTheme) {
        return {
          question: buildThemeReflectionQuestion(todayTheme, 'night'),
          strategy: 'recurring_theme_session',
          theme: todayTheme || null
        };
      }
      
      return {
        question: buildThemeReflectionQuestion(todayTheme, 'night'),
        strategy: 'today_last_session',
        theme: todayTheme || null
      };
    }

    if (notes.length > 0) {
      if (todayTheme) rememberRecentTheme(RECENT_NIGHT_THEMES_KEY, todayTheme);
      return {
        question: buildThemeReflectionQuestion(todayTheme, 'night'),
        strategy: 'today_note',
        theme: todayTheme || null
      };
    }

    if (insights.length > 0) {
      if (todayTheme) rememberRecentTheme(RECENT_NIGHT_THEMES_KEY, todayTheme);
      return {
        question: buildThemeReflectionQuestion(todayTheme, 'night'),
        strategy: 'today_saved_insight',
        theme: todayTheme || null
      };
    }

    if (recap && recap.topTheme) {
      const recapCandidates = [
        recap.topTheme,
        latestQotd && latestQotd.theme,
        lastSession && lastSession.theme,
      ].filter(Boolean).filter(theme => theme !== todayTheme);
      const rotatedTheme = chooseRotatingTheme(recapCandidates, recap.topTheme, RECENT_NIGHT_THEMES_KEY);
      return {
        question: buildThemeReflectionQuestion(rotatedTheme, 'night'),
        strategy: 'weekly_recap',
        theme: rotatedTheme
      };
    }

    if (latestQotd && latestQotd.question) {
      const qotdTheme = latestQotd.theme || inferTheme(latestQotd.question, '');
      if (latestQotd.theme && !recentNightThemes.includes(latestQotd.theme)) {
        rememberRecentTheme(RECENT_NIGHT_THEMES_KEY, latestQotd.theme);
      }
      return {
        question: buildThemeReflectionQuestion(qotdTheme, 'night'),
        strategy: 'qotd_fallback',
        theme: qotdTheme || null
      };
    }

    return {
      question: buildThemeReflectionQuestion('', 'night'),
      strategy: 'default',
      theme: null
    };
  }

  function buildMiddayReflectionPrompt() {
    const today = todayStr();
    const lastSession = loadLastSession() || null;
    const activity = loadActivityLog().filter(entry => entry && entry.day === today);
    const latestQotd = loadLatestQotd();
    const recap = getWeeklyRecapData ? getWeeklyRecapData() : null;

    const todayTheme = (
      activity.find(entry => entry.type === 'question' && entry.theme)?.theme ||
      (lastSession && lastSession.time && formatLocalDate(new Date(lastSession.time)) === today ? lastSession.theme : '') ||
      (latestQotd && latestQotd.theme) ||
      (recap && recap.topTheme) ||
      ''
    );

    if (lastSession && lastSession.question && lastSession.time && formatLocalDate(new Date(lastSession.time)) === today) {
      return {
        question: buildThemeReflectionQuestion(todayTheme, 'midday'),
        strategy: 'today_last_session',
        theme: todayTheme || null
      };
    }

    if (latestQotd && latestQotd.question) {
      const qotdTheme = latestQotd.theme || inferTheme(latestQotd.question, '');
      return {
        question: buildThemeReflectionQuestion(qotdTheme, 'midday'),
        strategy: 'qotd_fallback',
        theme: qotdTheme || null
      };
    }

    if (recap && recap.topTheme) {
      return {
        question: buildThemeReflectionQuestion(recap.topTheme, 'midday'),
        strategy: 'weekly_recap',
        theme: recap.topTheme
      };
    }

    return {
      question: buildThemeReflectionQuestion('', 'midday'),
      strategy: 'default',
      theme: null
    };
  }

  function buildInviteFriendPrompt() {
    const context = activeCampaignContext || loadCampaignContext() || {};
    const sharedQuestion = String(context.question || '').trim();
    const sharedTheme = String(context.theme || '').trim();
    const themeKey = sharedTheme.toLowerCase();

    if (sharedQuestion) {
      return {
        question: sharedQuestion,
        strategy: 'shared_question',
        theme: sharedTheme || inferTheme(sharedQuestion, '') || null
      };
    }

    const themePrompts = {
      'self-worth': 'What would healthier self-worth look like in my life right now?',
      fear: 'What is fear trying to protect in me right now?',
      healing: 'What needs healing attention in me right now?',
      grief: 'What does grief need from me today?',
      relationships: 'What would a healthier relationship pattern look like right now?',
      faith: 'How do I reconnect with my faith in a more honest way?'
    };

    if (sharedTheme) {
      return {
        question: themePrompts[themeKey] || `What is this season asking me to notice about ${sharedTheme}?`,
        strategy: 'shared_theme',
        theme: sharedTheme
      };
    }

    return {
      question: 'What feels most true for me to explore right now?',
      strategy: 'default',
      theme: null
    };
  }

  function autoStartMiddayReflection() {
    const resolved = buildMiddayReflectionPrompt();
    emitProductEvent('midday_reflection_opened', {
      strategy: resolved.strategy,
      theme: resolved.theme || null
    });
    autoSubmitQuestion(resolved.question, 'midday_reflection', {
      strategy: resolved.strategy,
      theme: resolved.theme || null
    });
  }

  function autoStartNightReflection() {
    const resolved = buildNightReflectionPrompt();
    emitProductEvent('night_reflection_opened', {
      strategy: resolved.strategy,
      theme: resolved.theme || null
    });
    autoSubmitQuestion(resolved.question, 'night_reflection', {
      strategy: resolved.strategy,
      theme: resolved.theme || null
    });
  }

  function autoStartInviteFriendReflection() {
    const resolved = buildInviteFriendPrompt();
    emitProductEvent('invite_reflection_opened', {
      strategy: resolved.strategy,
      theme: resolved.theme || null
    });
    autoSubmitQuestion(resolved.question, 'invite_friend', {
      strategy: resolved.strategy,
      theme: resolved.theme || null
    });
  }

  function runWhenReady(callback, delay) {
    const waitMs = typeof delay === 'number' ? delay : 120;
    if (document.readyState === 'loading') {
      document.addEventListener('DOMContentLoaded', () => setTimeout(callback, waitMs), { once: true });
    } else {
      setTimeout(callback, waitMs);
    }
  }

  function markAutoStartProcessed(key) {
    const clean = String(key || '').slice(0, 700);
    if (!clean) return true;
    try {
      const previous = sessionStorage.getItem(AUTO_START_SESSION_KEY);
      if (previous === clean) return false;
      sessionStorage.setItem(AUTO_START_SESSION_KEY, clean);
    } catch (e) {}
    return true;
  }

  function removeAutoStartParams(keys) {
    try {
      const url = new URL(window.location.href);
      keys.forEach(key => url.searchParams.delete(key));
      const cleanUrl = `${url.pathname}${url.search}${url.hash}`;
      history.replaceState(null, '', cleanUrl || window.location.pathname);
    } catch (e) {
      const params = new URLSearchParams(window.location.search);
      keys.forEach(key => params.delete(key));
      history.replaceState(null, '', `${window.location.pathname}${params.toString() ? `?${params}` : ''}${window.location.hash}`);
    }
  }

  // ─── Handle ?autoask= URL param (notification click → new tab) ─
  (function checkAutoAsk() {
    const params = new URLSearchParams(window.location.search);
    const raw = params.get('autoask');
    const nightReflection = params.get('night_reflection');
    const middayReflection = params.get('midday_reflection');
    const inviteReflection = params.get('invite_reflection');
    const inviteIntent = String(params.get('intent') || '').toLowerCase();
    const inviteRef = String(params.get('ref') || '').toLowerCase();
    const hasInviteQuestion = !!String(params.get('q') || '').trim();
    const hasInviteTheme = !!String(params.get('theme') || '').trim();
    const inferredInviteReflection =
      inviteIntent === 'friend_invite' ||
      inviteRef === 'save_share_referral' ||
      inviteRef === 'invite_friend';
    // Cap length before any processing to prevent oversized input
    const question = raw ? raw.slice(0, 500) : null;
    if (question) {
      removeAutoStartParams(['autoask', 'midday_reflection']);
      if (markAutoStartProcessed(`autoask:${question}`)) {
        runWhenReady(() => autoSubmitQuestion(question, 'notification_autoask'), 100);
      }
      return;
    }

    if (nightReflection === '1') {
      removeAutoStartParams(['night_reflection']);
      runWhenReady(() => autoStartNightReflection(), 120);
      return;
    }

    if (middayReflection === '1') {
      removeAutoStartParams(['midday_reflection']);
      runWhenReady(() => autoStartMiddayReflection(), 120);
      return;
    }

    if (inviteReflection === '1' || (inferredInviteReflection && (hasInviteQuestion || hasInviteTheme))) {
      removeAutoStartParams(['invite_reflection']);
      const inviteKey = `invite_reflection:${params.get('q') || params.get('theme') || todayStr()}`;
      if (markAutoStartProcessed(inviteKey)) {
        runWhenReady(() => autoStartInviteFriendReflection(), 120);
      }
    }
  })();

  // ─── Visual Viewport Stabilization (prevents PWA resize on keyboard) ────────
  // Handle visual viewport changes when mobile keyboard appears/disappears
  // This prevents unnecessary resizing of the PWA container
  if (window.visualViewport) {
    const viewportHandler = () => {
      const viewport = window.visualViewport;
      // Store viewport height as CSS variable for flexible layouts
      document.documentElement.style.setProperty('--viewport-height', `${viewport.height}px`);
    };
    
    window.visualViewport.addEventListener('resize', viewportHandler);
    window.visualViewport.addEventListener('scroll', viewportHandler);
    viewportHandler(); // Initialize
    
    log('Visual viewport stabilization enabled');
  }

  // ─── Handle messages from service worker (already-open tab) ───
  if ('serviceWorker' in navigator) {
    // controllerchange fires natively when a new SW takes control — works on
    // iOS Safari PWA where client.navigate() and postMessage may be unreliable.
    // Guard: only reload if there was ALREADY a controller (i.e. an SW update
    // happened), not on the very first install.
    var _hadController = !!navigator.serviceWorker.controller;
    navigator.serviceWorker.addEventListener('controllerchange', function() {
      if (!_hadController) { _hadController = true; return; }
      
      // Check if user is actively working before forcing reload
      const hasResults = document.querySelector('.amt-result-card');
      const hasTextInProgress = input && input.value.trim().length > 0;
      const timeSinceLoad = Date.now() - (window.amtLoadTime || Date.now());
      const justOpened = timeSinceLoad < 30000;
      
      if (hasResults || hasTextInProgress || justOpened) {
        console.log('[AMT] Controller changed, but deferring reload (user active)');
        return;
      }
      
      try {
        if (!sessionStorage.getItem('amt_sw_reloaded')) {
          sessionStorage.setItem('amt_sw_reloaded', '1');
          window.location.reload();
        }
      } catch (e) { window.location.reload(); }
    });

    navigator.serviceWorker.addEventListener('message', (event) => {
      if (event.data && event.data.type === 'AUTO_SUBMIT' && event.data.question) {
        // QOTD notification clicked while app was open — auto-submit the question.
        autoSubmitQuestion(event.data.question);
      } else if (event.data && event.data.type === 'AUTO_START_MIDDAY_REFLECTION') {
        autoStartMiddayReflection();
      } else if (event.data && event.data.type === 'AUTO_START_NIGHT_REFLECTION') {
        autoStartNightReflection();
      } else if (event.data && event.data.type === 'NAVIGATE_TO_FORM') {
        // Legacy service-worker fallback path: focus the asking surface only.
        // Auto-starting here made normal PWA launches feel like the app was
        // forcing a reflection without a clear notification intent.
        runWorkflowAction('ask', { persist: true, scroll: true });
      } else if (event.data && event.data.type === 'SW_UPDATED') {
        // New service worker activated. Instead of forcing immediate reload,
        // check if the user is actively using the app. Only reload if idle.
        
        // Skip reload if user has results displayed or text in progress
        const hasResults = document.querySelector('.amt-result-card');
        const hasTextInProgress = input && input.value.trim().length > 0;
        const hasUnsavedWork = hasResults || hasTextInProgress;
        
        // Skip reload if it's been less than 30 seconds since page load (user just opened app)
        const timeSinceLoad = Date.now() - (window.amtLoadTime || Date.now());
        const justOpened = timeSinceLoad < 30000;
        
        if (hasUnsavedWork || justOpened) {
          console.log('[AMT] Service worker updated, but deferring reload (user active)');
          // Show a subtle notification that update is available
          // The update will apply on next page load naturally
          return;
        }
        
        // Only reload if page appears idle and we haven't already reloaded
        try {
          if (!sessionStorage.getItem('amt_sw_reloaded')) {
            sessionStorage.setItem('amt_sw_reloaded', '1');
            console.log('[AMT] Reloading to apply service worker update');
            window.location.reload();
          }
        } catch (e) { 
          // If sessionStorage fails, reload anyway (likely private mode)
          window.location.reload(); 
        }
      }
    });
    
    // Clear the reload flag when page becomes visible again
    // This allows future SW updates to reload after user has seen the current version
    document.addEventListener('visibilitychange', function() {
      if (!document.hidden) {
        // Page is now visible - clear reload flag after a delay
        // This ensures user has seen the current version
        setTimeout(function() {
          try {
            sessionStorage.removeItem('amt_sw_reloaded');
          } catch (e) {}
        }, 5000); // 5 second delay before allowing next reload
      }
    });
  }

  loadQuestionOfTheDay();
  initActivationExperience();

  // ─── Suggested Questions ────────────────────────────────────
  function loadSuggestedQuestions() {
    if (!suggestionsContainer || !suggestionsList) return;

    fetch(`${API_BASE}/api/suggested-questions`)
      .then(res => res.json())
      .then(data => {
        const questions = data.questions || [];
        if (questions.length === 0) {
          suggestionsContainer.style.display = 'none';
          return;
        }
        suggestionsList.innerHTML = '';
        questions.forEach(q => {
          const btn = document.createElement('button');
          btn.type = 'button';
          btn.className = 'amt-suggestion-btn';
          btn.textContent = q;
          btn.addEventListener('click', () => {
            setQuestionOrigin('suggested_question');
            submitQuestionFromPrompt(q);
          });
          suggestionsList.appendChild(btn);
        });
        suggestionsContainer.style.display = '';
        updateExploreExpander();
      })
      .catch(err => {
        warn('Could not load suggested questions:', err);
        suggestionsContainer.style.display = 'none';
      });
  }

  // Load on init
  loadSuggestedQuestions();

  // ─── Browse by Topic ───────────────────────────────────────
  function loadTopics() {
    if (!topicsContainer || !topicsList) return;

    fetch(`${API_BASE}/api/topics`)
      .then(res => res.json())
      .then(data => {
        const topics = data.topics || [];
        if (topics.length === 0) {
          topicsContainer.style.display = 'none';
          return;
        }
        topicsList.innerHTML = '';
        topics.forEach(t => {
          const item = document.createElement('div');
          item.className = 'amt-topic-item';

          const starters = t.starters || [];
          const startersHtml = starters.length ? `
            <div class="amt-topic-starter-list">
              ${starters.map(q => `<button type="button" class="amt-topic-starter-btn" data-q="${q.replace(/"/g,'&quot;')}">${q}</button>`).join('')}
              <button type="button" class="amt-topic-starter-btn amt-topic-main-btn" data-q="${t.query.replace(/"/g,'&quot;')}">✦ ${t.query}</button>
            </div>
          ` : '';

          item.innerHTML = `
            <button type="button" class="amt-topic-btn" title="Explore ${escapeHtml(t.label)}${t.episode_count ? ` (${t.episode_count} episodes)` : ''}">
              <span class="amt-topic-icon">${t.icon}</span>
              <span class="amt-topic-name">${escapeHtml(t.label)}</span>
              ${t.episode_count ? `<span style="font-size:0.75rem;opacity:0.45;margin-left:auto;padding-right:4px;">${t.episode_count}</span>` : ''}
              <span class="amt-topic-expand-arrow">▶</span>
            </button>
            ${startersHtml}
          `;

          // Toggle expand on main button click
          const topicBtn = item.querySelector('.amt-topic-btn');
          topicBtn.setAttribute('aria-expanded', 'false');
          topicBtn.addEventListener('click', () => {
            const isOpen = item.classList.contains('amt-topic-open');
            // Close all others
            topicsList.querySelectorAll('.amt-topic-item.amt-topic-open').forEach(el => {
              el.classList.remove('amt-topic-open');
              el.querySelector('.amt-topic-btn').setAttribute('aria-expanded', 'false');
            });
            if (!isOpen) {
              item.classList.add('amt-topic-open');
              topicBtn.setAttribute('aria-expanded', 'true');
            }
          });

          // Starter question clicks
          item.querySelectorAll('.amt-topic-starter-btn').forEach(btn => {
            btn.addEventListener('click', () => {
              setQuestionOrigin('topic_starter', { topic: t.label || null });
              topicsContainer.style.display = 'none';
              submitQuestionFromPrompt(btn.dataset.q);
            });
          });

          topicsList.appendChild(item);
        });
        const icons = topics.slice(0, 5).map(t => t.icon).join(' ');
        if (exploreIcons) exploreIcons.textContent = icons;
        topicsContainer.style.display = '';
        updateExploreExpander();
      })
      .catch(err => {
        warn('Could not load topics:', err);
        topicsContainer.style.display = 'none';
      });
  }

  loadTopics();

  // ─── Explore Expander ──────────────────────────────────────
  function collapseExploreExpander() {
    if (!exploreToggle || !explorePanel) return;
    exploreToggle.setAttribute('aria-expanded', 'false');
    explorePanel.classList.remove('amt-explore-panel--open');
  }

  function updateExploreExpander() {
    if (!exploreExpander) return;
    const hasContent = (topicsContainer && topicsContainer.style.display !== 'none') ||
                       (suggestionsContainer && suggestionsContainer.style.display !== 'none');
    exploreExpander.style.display = hasContent ? '' : 'none';
    if (hasContent && exploreToggle && exploreToggle.getAttribute('aria-expanded') !== 'true') {
      collapseExploreExpander();
    }
    updateWorkflowBarState();
  }

  function restoreExploreContent() {
    const hasTopicItems = !!(topicsList && topicsList.children.length > 0);
    const hasSuggestionItems = !!(suggestionsList && suggestionsList.children.length > 0);

    if (topicsContainer && hasTopicItems) {
      topicsContainer.style.display = '';
    }
    if (suggestionsContainer && hasSuggestionItems) {
      suggestionsContainer.style.display = '';
    }

    // If the lists were somehow cleared during the answer flow, repopulate them
    // instead of leaving the expander visible but empty after the next tap.
    if (!hasTopicItems) {
      loadTopics();
    }
    if (!hasSuggestionItems) {
      loadSuggestedQuestions();
    }

    updateExploreExpander();
  }

  if (exploreToggle && explorePanel) {
    exploreToggle.addEventListener('click', () => {
      const isOpen = exploreToggle.getAttribute('aria-expanded') === 'true';
      exploreToggle.setAttribute('aria-expanded', String(!isOpen));
      explorePanel.classList.toggle('amt-explore-panel--open', !isOpen);
    });
  }

  // ─── Follow-up Questions ────────────────────────────────────
  function inferFollowUpTheme(text) {
    const value = String(text || '').toLowerCase();
    const checks = [
      ['relationships', ['relationship', 'dating', 'marriage', 'love', 'attachment', 'trust', 'partner', 'spouse']],
      ['healing', ['grief', 'loss', 'trauma', 'heal', 'healing', 'pain', 'forgive', 'forgiveness']],
      ['courage', ['fear', 'courage', 'brave', 'bold', 'risk', 'confidence']],
      ['purpose', ['purpose', 'calling', 'meaning', 'identity', 'soul', 'direction']],
      ['habits', ['habit', 'addiction', 'discipline', 'routine', 'change', 'stuck']],
      ['faith', ['faith', 'doubt', 'god', 'prayer', 'spiritual', 'surrender']],
      ['peace', ['peace', 'rest', 'stillness', 'anxiety', 'uncertain', 'overwhelm']],
      ['leadership', ['leader', 'leadership', 'work', 'ambition', 'success']]
    ];

    const match = checks.find(([, keywords]) => keywords.some(keyword => value.includes(keyword)));
    return match ? match[0] : 'reflection';
  }

  function followUpPromptsForTheme(theme) {
    const prompts = {
      relationships: [
        'How can I understand my relationship patterns with more honesty?',
        'What would love look like here without losing myself?',
        'What is one healthier way to respond in this relationship?'
      ],
      healing: [
        'What would healing ask me to be gentle with today?',
        'What part of this pain needs attention rather than pressure?',
        'How can I take one honest step toward repair?'
      ],
      courage: [
        'What would courage look like in this part of my life?',
        'Where is fear asking for reassurance instead of control?',
        'What small brave step could I take today?'
      ],
      purpose: [
        'What is this reflection asking me to notice about my purpose?',
        'What keeps calling me forward, even quietly?',
        'What next step would feel aligned rather than forced?'
      ],
      habits: [
        'What is the smallest wise step I can take to interrupt this habit?',
        'What environment change would make the better choice easier?',
        'What support would help me stay honest with this change?'
      ],
      faith: [
        'How can I make room for faith without pretending doubt is not there?',
        'What would trust look like in one small decision today?',
        'Where might I need honesty before certainty?'
      ],
      peace: [
        'What would help me return to a steadier inner place today?',
        'What noise can I set down so I can hear myself clearly?',
        'What small practice would make peace more reachable?'
      ],
      leadership: [
        'How can I lead this situation with more clarity and humility?',
        'What would responsibility look like without pressure or performance?',
        'What is one aligned decision I can make today?'
      ],
      reflection: [
        'What is the next honest question this reflection invites me to ask?',
        'How can I apply this insight in one small way today?',
        'What part of this answer should I carry with me next?'
      ]
    };
    return prompts[theme] || prompts.reflection;
  }

  function polishFollowUpQuestion(raw, index) {
    const original = String(raw || '').replace(/\s+/g, ' ').trim().replace(/^["“”]+|["“”]+$/g, '');
    if (!original) return '';

    const legacyTitle = original.match(/^tell me more about\s+["“](.+?)["”]?$/i);
    if (legacyTitle || original.length > 118) {
      const theme = inferFollowUpTheme(legacyTitle ? legacyTitle[1] : original);
      const themedPrompts = followUpPromptsForTheme(theme);
      return themedPrompts[index % themedPrompts.length];
    }

    return /[?]$/.test(original) ? original : `${original.replace(/[.!,:;]+$/g, '')}?`;
  }

  function showFollowUpQuestions(questions, options) {
    if (!followupsContainer || !followupsList || !questions || questions.length === 0) {
      if (followupsContainer) followupsContainer.style.display = 'none';
      return;
    }

    const label = (options && options.label) || 'You might also want to ask:';
    const labelEl = followupsContainer.querySelector('.amt-followups-label');
    if (labelEl) {
      labelEl.textContent = label;
    }

    followupsList.innerHTML = '';
    questions.map(polishFollowUpQuestion).filter(Boolean).slice(0, 3).forEach(q => {
      const btn = document.createElement('button');
      btn.type = 'button';
      btn.className = 'amt-followup-btn';
      btn.textContent = q;
      btn.addEventListener('click', () => {
        setQuestionOrigin('follow_up');
        followupsContainer.style.display = 'none';
        submitQuestionFromPrompt(q);
      });
      followupsList.appendChild(btn);
    });
    followupsContainer.style.display = '';
    // No auto-scroll to follow-ups — user is reading the answer from top to bottom.
  }

  function ensureLowMatchFollowUps(question, theme) {
    if (!followupsContainer || !followupsList) return;
    if (followupsContainer.style.display !== 'none' && followupsList.children.length > 0) return;
    showFollowUpQuestions(generateLowMatchPrompts(question, theme), {
      label: 'Try reframing with:'
    });
  }

  function getCitationSupportMeta(citationsList) {
    const count = Array.isArray(citationsList) ? citationsList.length : 0;
    if (count >= 4) {
      return {
        count,
        hasReferences: true,
        level: 'Strong grounding',
        trustLead: `${count} episode references support this reflection`,
        trustDetail: 'The strongest source moment appears first. Preview it, then open the full episode if you want the wider conversation.',
        contextKicker: 'Grounded in Mirror Talk',
        contextSummary: `${count} episode references support this reflection.`,
        contextDetail: 'Use the source moments below to verify the answer, listen to the strongest clip, or open the full episode.',
        supportPill: 'Strong grounding'
      };
    }
    if (count > 0) {
      return {
        count,
        hasReferences: true,
        level: 'Some grounding',
        trustLead: `${count} episode reference${count === 1 ? '' : 's'} support${count === 1 ? 's' : ''} this reflection`,
        trustDetail: 'You have direct source moments below. A narrower follow-up can still surface a tighter match.',
        contextKicker: 'Grounded in Mirror Talk',
        contextSummary: `${count} episode reference${count === 1 ? '' : 's'} support this reflection.`,
        contextDetail: 'Use the source moments below to verify the answer, then tighten the question if you want a sharper match.',
        supportPill: 'Partial grounding'
      };
    }
    return {
      count,
      hasReferences: false,
      level: 'Broader reflection',
      trustLead: 'No direct episode moment surfaced this time',
      trustDetail: 'This answer may still be useful, but it is less grounded than usual. Try a narrower follow-up for a stronger match.',
      contextKicker: 'Broader Mirror Talk reflection',
      contextSummary: 'This reflection is shaped by the library, but without a direct source moment yet.',
      contextDetail: 'A more specific follow-up will usually surface a clearer episode match and stronger citations.',
      supportPill: 'Needs a narrower question'
    };
  }

  // Rotating loading messages for engagement
  const loadingMessages = [
    'Searching through podcast episodes…',
    'Listening to Mirror Talk wisdom…',
    'Finding the best insights for you…',
    'Connecting the dots across episodes…',
    'Almost there — crafting your answer…'
  ];

  let loadingInterval = null;
  let activePlayer = null;

  // Helper: Format timestamp for display (HH:MM:SS)
  function formatTimestamp(seconds) {
    if (!seconds && seconds !== 0) return '';
    const hrs = Math.floor(seconds / 3600);
    const mins = Math.floor((seconds % 3600) / 60);
    const secs = Math.floor(seconds % 60);
    if (hrs > 0) {
      return `${hrs}:${String(mins).padStart(2, '0')}:${String(secs).padStart(2, '0')}`;
    }
    return `${mins}:${String(secs).padStart(2, '0')}`;
  }

  // Helper: Parse timestamp string to seconds
  function parseTimestampToSeconds(timestamp) {
    if (!timestamp) return 0;
    const parts = timestamp.split(':').map(p => parseInt(p, 10));
    if (parts.length === 3) return parts[0] * 3600 + parts[1] * 60 + parts[2];
    if (parts.length === 2) return parts[0] * 60 + parts[1];
    return parseInt(timestamp, 10) || 0;
  }

  // Helper: Convert markdown-style formatting to HTML
  function formatMarkdownToHtml(text) {
    if (!text) return '';
    
    text = text.replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>');
    text = text.replace(/\*(.+?)\*/g, '<em>$1</em>');
    
    const lines = text.split('\n');
    let inOrderedList = false;
    let inUnorderedList = false;
    const formattedLines = [];
    
    for (let i = 0; i < lines.length; i++) {
      const line = lines[i];
      const trimmedLine = line.trim();
      
      if (trimmedLine === '') {
        if (inOrderedList) { formattedLines.push('</ol>'); inOrderedList = false; }
        if (inUnorderedList) { formattedLines.push('</ul>'); inUnorderedList = false; }
        formattedLines.push('');
        continue;
      }
      
      const numberedMatch = trimmedLine.match(/^(\d+)\.\s+(.+)$/);
      if (numberedMatch) {
        if (!inOrderedList) {
          if (inUnorderedList) { formattedLines.push('</ul>'); inUnorderedList = false; }
          formattedLines.push('<ol>');
          inOrderedList = true;
        }
        let itemContent = numberedMatch[2]
          .replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>')
          .replace(/\*(.+?)\*/g, '<em>$1</em>');
        formattedLines.push(`<li>${itemContent}</li>`);
        continue;
      }
      
      const bulletMatch = trimmedLine.match(/^[-]\s+(.+)$/);
      if (bulletMatch) {
        if (!inUnorderedList) {
          if (inOrderedList) { formattedLines.push('</ol>'); inOrderedList = false; }
          formattedLines.push('<ul>');
          inUnorderedList = true;
        }
        let itemContent = bulletMatch[1]
          .replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>')
          .replace(/\*(.+?)\*/g, '<em>$1</em>');
        formattedLines.push(`<li>${itemContent}</li>`);
        continue;
      }
      
      if (inOrderedList) { formattedLines.push('</ol>'); inOrderedList = false; }
      if (inUnorderedList) { formattedLines.push('</ul>'); inUnorderedList = false; }
      formattedLines.push(line);
    }
    
    if (inOrderedList) formattedLines.push('</ol>');
    if (inUnorderedList) formattedLines.push('</ul>');
    
    return formattedLines.join('\n');
  }

  // Show loading state
  function setLoading(isLoading) {
    if (isLoading) {
      try { delete output.dataset.amtPostAnswerApplied; } catch (e) {}
      submitBtn.disabled = true;
      submitBtn.textContent = 'Thinking…';
      input.disabled = true;

      // Hide suggestions and topics while loading
      if (qotdContainer) qotdContainer.style.display = 'none';
      if (suggestionsContainer) suggestionsContainer.style.display = 'none';
      if (topicsContainer) topicsContainer.style.display = 'none';
      if (followupsContainer) followupsContainer.style.display = 'none';

      const oldFeedback = document.getElementById('amt-feedback-section');
      if (oldFeedback) oldFeedback.remove();
      const oldEmail = document.getElementById('amt-email-section');
      if (oldEmail) oldEmail.remove();
      const oldRelated = document.getElementById('amt-related-section');
      if (oldRelated) oldRelated.remove();

      // Reveal response container with smooth fade-in (display:none → block then opacity transition)
      responseContainer.style.display = '';
      responseContainer.classList.add('amt-loading-state');
      // rAF: let browser paint display:block first, then trigger opacity transition
      requestAnimationFrame(() => responseContainer.classList.add('amt-visible'));
      const responseH3 = responseContainer.querySelector('h3');
      if (responseH3) responseH3.textContent = 'Response';

      output.innerHTML = `
        <div class="amt-loading">
          <div class="amt-skeleton-answer">
            <div class="amt-skeleton-line" style="width: 92%"></div>
            <div class="amt-skeleton-line" style="width: 96%"></div>
            <div class="amt-skeleton-line" style="width: 89%"></div>
            <div class="amt-skeleton-line" style="width: 94%"></div>
            <div class="amt-skeleton-line" style="width: 85%"></div>
            <div class="amt-skeleton-line" style="width: 78%"></div>
          </div>
          <div class="amt-loading-text">${loadingMessages[0]}</div>
        </div>
      `;

      let msgIndex = 0;
      loadingInterval = setInterval(() => {
        msgIndex = (msgIndex + 1) % loadingMessages.length;
        const textEl = output.querySelector('.amt-loading-text');
        if (textEl) {
          textEl.style.opacity = '0';
          setTimeout(() => {
            textEl.textContent = loadingMessages[msgIndex];
            textEl.style.opacity = '1';
          }, 200);
        }
      }, 3000);

      citations.innerHTML = "";
      // Hide citations smoothly — remove visible class; display:none needed since CSS opacity:0 alone
      // doesn't prevent citations from taking vertical space in some browsers when non-empty
      citationsContainer.classList.remove('amt-visible');
      setTimeout(() => {
        if (!citationsContainer.classList.contains('amt-visible')) {
          citationsContainer.style.display = 'none';
        }
      }, 350);
    } else {
      clearInterval(loadingInterval);
      loadingInterval = null;
      submitBtn.disabled = false;
      submitBtn.textContent = 'Ask';
      input.disabled = false;
      responseContainer.classList.remove('amt-streaming', 'amt-loading-state');
    }
  }

  // Show smart, contextual error messages
  function showError(message, errorType = 'generic') {
    const smartMessages = {
      'network': '📡 Can\'t reach the server. Check your internet connection and try again.',
      'timeout': '⏱️ This is taking longer than usual. The answer will arrive soon—keep waiting or try a shorter question.',
      'rate_limit': '🌊 You\'re asking questions quickly! Take a breath and try again in 30 seconds.',
      'server_error': '🔧 Our servers are having a moment. We\'ve been notified and are fixing it.',
      'empty_response': '💭 Hmm, we couldn\'t find a strong answer. Try rephrasing your question or exploring a different theme.',
      'generic': message || '⚠️ Something unexpected happened. Please try again.'
    };
    
    const errorMessage = smartMessages[errorType] || smartMessages.generic;
    
    responseContainer.style.display = '';
    requestAnimationFrame(() => responseContainer.classList.add('amt-visible'));
    responseContainer.classList.remove('amt-streaming', 'amt-loading-state');
    responseContainer.classList.add('error');
    output.innerHTML = `
      <div class="amt-error-message">
        <p><strong>${errorMessage}</strong></p>
        <button onclick="document.querySelector('#ask-mirror-talk-form').dispatchEvent(new Event('submit'))" class="amt-retry-btn" style="margin-top: 1rem; padding: 0.5rem 1.5rem; background: var(--amt-accent, #943e08); color: white; border: none; border-radius: 6px; cursor: pointer; font-weight: 600;">
          Try Again
        </button>
      </div>
    `;
    citations.innerHTML = "";
    citationsContainer.style.display = "none";
    if (followupsContainer) followupsContainer.style.display = 'none';
  }

  // ========================================
  // Inline Audio Player
  // ========================================

  /**
   * Create and show an inline audio player below the clicked citation
   */
  function showInlinePlayer(citationItem, audioUrl, startSeconds, endSeconds, episodeTitle, episodeUrl) {
    // If clicking the same citation that's already playing, toggle it
    const existingPlayer = citationItem.querySelector('.amt-inline-player');
    if (existingPlayer) {
      closeInlinePlayer(existingPlayer);
      return;
    }

    // Close any other open player
    if (activePlayer) {
      closeInlinePlayer(activePlayer);
    }

    // Mark this citation as active
    citationItem.classList.add('citation-playing');

    const playerHTML = `
      <div class="amt-inline-player">
        <div class="amt-player-header">
          <span class="amt-player-title">🎧 Now Playing</span>
          <button class="amt-player-close" title="Close player" aria-label="Close player">✕</button>
        </div>
        <div class="amt-player-episode">${escapeHtml(episodeTitle)}</div>
        <audio class="amt-audio" controls preload="auto">
          <source src="${audioUrl}" type="audio/mpeg">
          Your browser does not support audio playback.
        </audio>
        <div class="amt-player-actions">
          <button class="amt-player-skip-back" title="Back 10s">⏪ 10s</button>
          <button class="amt-player-skip-fwd" title="Forward 10s">10s ⏩</button>
          <button type="button" class="amt-player-full" title="Play full episode">Play full episode</button>
        </div>
      </div>
    `;

    citationItem.insertAdjacentHTML('beforeend', playerHTML);

    const playerEl = citationItem.querySelector('.amt-inline-player');
    const audio = playerEl.querySelector('.amt-audio');
    activePlayer = playerEl;

    // Set start time and play
    audio.addEventListener('loadedmetadata', function onLoaded() {
      audio.currentTime = startSeconds || 0;
      audio.play().catch(() => {
        // Autoplay blocked — user will click play manually
        console.log('Autoplay blocked — user can press play');
      });
      audio.removeEventListener('loadedmetadata', onLoaded);
    }, { once: true });

    // If audio is already loaded (cached), set time directly
    if (audio.readyState >= 1) {
      audio.currentTime = startSeconds || 0;
      audio.play().catch(() => {});
    }

    // Optional: pause at end timestamp
    let stopAtExcerpt = null;
    if (endSeconds && endSeconds > startSeconds) {
      stopAtExcerpt = function checkEnd() {
        if (audio.currentTime >= endSeconds) {
          audio.pause();
          audio.removeEventListener('timeupdate', checkEnd);
          stopAtExcerpt = null;
        }
      };
      audio.addEventListener('timeupdate', stopAtExcerpt);
    }

    // Close button
    playerEl.querySelector('.amt-player-close').addEventListener('click', (e) => {
      e.stopPropagation();
      closeInlinePlayer(playerEl);
    });

    // Skip buttons
    playerEl.querySelector('.amt-player-skip-back').addEventListener('click', (e) => {
      e.stopPropagation();
      audio.currentTime = Math.max(0, audio.currentTime - 10);
    });

    playerEl.querySelector('.amt-player-skip-fwd').addEventListener('click', (e) => {
      e.stopPropagation();
      audio.currentTime = Math.min(audio.duration || Infinity, audio.currentTime + 10);
    });

    playerEl.querySelector('.amt-player-full').addEventListener('click', (e) => {
      e.stopPropagation();
      if (stopAtExcerpt) {
        audio.removeEventListener('timeupdate', stopAtExcerpt);
        stopAtExcerpt = null;
      }
      audio.currentTime = 0;
      audio.play().catch(() => {});
      emitProductEvent('citation_action_used', {
        action: 'play_full_episode_inline',
        episode_title: episodeTitle,
        source: 'inline_player'
      });
    });

    // Prevent clicks inside player from triggering citation link
    playerEl.addEventListener('click', (e) => {
      e.stopPropagation();
    });

    // Smooth scroll to player
    setTimeout(() => {
      playerEl.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
    }, 100);
  }

  /**
   * Close an inline player and clean up
   */
  function closeInlinePlayer(playerEl) {
    const audio = playerEl.querySelector('.amt-audio');
    if (audio) {
      audio.pause();
      audio.src = ''; // Release resource
    }
    const citationItem = playerEl.closest('.citation-item');
    if (citationItem) {
      citationItem.classList.remove('citation-playing');
    }
    playerEl.classList.add('amt-player-closing');
    setTimeout(() => {
      playerEl.remove();
    }, 300);
    if (activePlayer === playerEl) {
      activePlayer = null;
    }
  }

  // ========================================
  // Show Citations (extracted for reuse)
  // ========================================

  function showCitations(citationsList) {
    if (activePlayer) {
      closeInlinePlayer(activePlayer);
    }

    lastShownCitations = Array.isArray(citationsList) ? citationsList.slice() : [];
    updateCitationTrustNote(lastShownCitations);

    if (citationsList && citationsList.length > 0) {
      citations.innerHTML = "";
      
      citationsList.forEach((citation, index) => {
        const li = document.createElement("li");
        li.className = index === 0 ? "citation-item citation-item-primary" : "citation-item";
        
        const episodeTitle = citation.episode_title || "Unknown Episode";
        const startSeconds = citation.timestamp_start_seconds !== undefined 
          ? citation.timestamp_start_seconds 
          : parseTimestampToSeconds(citation.timestamp_start);
        const endSeconds = citation.timestamp_end_seconds !== undefined 
          ? citation.timestamp_end_seconds 
          : parseTimestampToSeconds(citation.timestamp_end);
        
        const timestampStart = formatTimestamp(startSeconds);
        const timestampEnd = formatTimestamp(endSeconds);
        const audioUrl = citation.audio_url || '';
        const podcastUrl = citation.episode_url || (audioUrl && startSeconds ? `${audioUrl}#t=${startSeconds}` : audioUrl);

        const timeDisplay = startSeconds > 0
          ? ((startSeconds !== endSeconds && timestampEnd)
              ? `${timestampStart} – ${timestampEnd}`
              : timestampStart)
          : '';
        const timeHtml = timeDisplay ? `<span class="citation-time">▶ ${timeDisplay}</span>` : '';
        const matchBadgeHtml = citation.is_strongest_match
          ? '<span class="citation-match-badge">Strongest match</span>'
          : '';

        if (podcastUrl) {
          const link = document.createElement("a");
          link.href = podcastUrl;
          link.className = "citation-link";
          link.title = startSeconds > 0 ? `Listen from ${timestampStart}` : episodeTitle;
          link.setAttribute('data-episode-id', citation.episode_id);
          link.setAttribute('data-timestamp', startSeconds);
          link.setAttribute('data-audio-url', audioUrl);
          link.setAttribute('data-start', startSeconds);
          link.setAttribute('data-end', endSeconds);

          // Build the quote snippet (truncated text already returned by API)
          const quoteText = citation.text || '';
          const quoteHtml = quoteText
            ? `<span class="citation-quote">"${escapeHtml(quoteText)}"</span>`
            : '';

          const yearHtml = citation.episode_year
            ? `<span class="citation-year">${escapeHtml(String(citation.episode_year))}</span>`
            : '';

          link.innerHTML = `
            <div class="citation-info">
              ${matchBadgeHtml}
              <span class="citation-title">${escapeHtml(episodeTitle)}${yearHtml}</span>
              ${quoteHtml}
            </div>
            ${timeHtml}
          `;

          // Intercept click for inline playback
          link.addEventListener('click', function(e) {
            e.preventDefault();
            const url = this.getAttribute('data-audio-url');
            const start = parseFloat(this.getAttribute('data-start')) || 0;
            const end = parseFloat(this.getAttribute('data-end')) || 0;
            const title = this.querySelector('.citation-title')?.textContent || episodeTitle;
            emitProductEvent('citation_action_used', {
              action: url ? 'listen_from_timestamp' : 'open_reference_link',
              position: index + 1,
              episode_id: citation.episode_id || null,
              has_audio: !!url
            });
            if (url) {
              showInlinePlayer(li, url, start, end, title, podcastUrl);
            } else {
              window.open(this.href, '_blank');
            }
          });

          li.appendChild(link);

          // "Preview 30s" button
          if (audioUrl) {
            const previewBtn = document.createElement('button');
            previewBtn.type = 'button';
            previewBtn.className = 'citation-preview-btn';
            previewBtn.title = 'Preview the strongest 30 seconds';
            previewBtn.innerHTML = 'Preview 30s';
            previewBtn.addEventListener('click', (e) => {
              e.stopPropagation();
              const existingPreview = li.querySelector('.amt-preview-audio');
              if (existingPreview) {
                existingPreview.pause();
                existingPreview.remove();
                previewBtn.innerHTML = 'Preview 30s';
                return;
              }
              // Stop any preview playing in another citation item
              document.querySelectorAll('.amt-preview-audio').forEach(otherAudio => {
                otherAudio.pause();
                const otherBtn = otherAudio.closest('.citation-item')?.querySelector('.citation-preview-btn');
                if (otherBtn) otherBtn.innerHTML = 'Preview 30s';
                otherAudio.remove();
              });
              const previewAudio = document.createElement('audio');
              previewAudio.className = 'amt-preview-audio';
              previewAudio.style.display = 'none';
              previewAudio.src = audioUrl;
              li.appendChild(previewAudio);
              previewBtn.innerHTML = 'Stop preview';
              emitProductEvent('citation_action_used', {
                action: 'preview_clip',
                position: index + 1,
                episode_id: citation.episode_id || null
              });
              const clipStart = startSeconds || 0;
              const clipEnd = clipStart + 30;
              previewAudio.addEventListener('loadedmetadata', () => {
                previewAudio.currentTime = clipStart;
                previewAudio.play().catch(() => {});
              });
              if (previewAudio.readyState >= 1) {
                previewAudio.currentTime = clipStart;
                previewAudio.play().catch(() => {});
              }
              previewAudio.addEventListener('timeupdate', function stopAt() {
                if (previewAudio.currentTime >= clipEnd) {
                  previewAudio.pause();
                  previewAudio.remove();
                  previewBtn.innerHTML = 'Preview 30s';
                  previewAudio.removeEventListener('timeupdate', stopAt);
                }
              });
              previewAudio.addEventListener('ended', () => {
                previewAudio.remove();
                previewBtn.innerHTML = 'Preview 30s';
              });
            });
            li.appendChild(previewBtn);
          }

        } else {
          const quoteText = citation.text || '';
          const quoteHtml = quoteText
            ? `<p class="citation-quote">"${escapeHtml(quoteText)}"</p>`
            : '';

          const yearHtml = citation.episode_year
            ? `<span class="citation-year">${escapeHtml(String(citation.episode_year))}</span>`
            : '';

          li.innerHTML = `
            <div class="citation-info">
              ${matchBadgeHtml}
              <span class="citation-title">${escapeHtml(episodeTitle)}${yearHtml}</span>
              ${quoteHtml}
            </div>
            ${timeHtml}
          `;
        }
        
        citations.appendChild(li);
      });

      // Reveal citations: must explicitly set display:block (not '') because the CSS
      // default for .ask-mirror-talk-citations is display:none — clearing the inline
      // style would just fall back to the CSS rule and keep it hidden.
      citationsContainer.style.display = 'block';
      requestAnimationFrame(() => citationsContainer.classList.add('amt-visible'));
    } else {
      citations.innerHTML = "";
      citationsContainer.classList.remove('amt-visible');
      updateCitationTrustNote([]);
      setTimeout(() => {
        if (!citationsContainer.classList.contains('amt-visible')) {
          citationsContainer.style.display = 'none';
        }
      }, 350);
    }
  }

  // ========================================
  // SSE Streaming Answer
  // ========================================

  // ─── Conversation Memory ────────────────────────────────────
  // Keep last 6 turns (3 questions + 3 answers) for follow-up context
  let conversationContext = [];

  function appendConversationTurn(question, answer) {
    conversationContext.push({ role: 'user', content: question });
    conversationContext.push({ role: 'assistant', content: answer.substring(0, 600) });
    // Cap at 6 turns
    if (conversationContext.length > 6) {
      conversationContext = conversationContext.slice(-6);
    }
  }

  /**
   * Stream an answer via SSE (Server-Sent Events).
   * Falls back to the non-streaming /ask endpoint on error.
   */
  async function askStreaming(question) {
    const streamUrl = DEBUG_NO_CACHE ? `${API_BASE}/ask/stream?bypass_cache=1` : `${API_BASE}/ask/stream`;
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), 60000);
    let response;
    try {
      response = await fetch(streamUrl, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ question, context: conversationContext.length ? conversationContext : undefined }),
        signal: controller.signal
      });
    } catch (fetchErr) {
      clearTimeout(timeoutId);
      throw fetchErr;
    }

    if (!response.ok) {
      throw new Error(`Stream request failed: ${response.status}`);
    }

    const reader = response.body.getReader();
    const decoder = new TextDecoder();
    let answerText = '';
    let buffer = '';

    // Clear error state and prepare for streaming — keep loading dots visible
    // until the first chunk of answer text arrives
    output.classList.remove('amt-complete');
    responseContainer.classList.remove('error');
    responseContainer.classList.add('amt-streaming');

    // Scroll response into view once at start — use 'nearest' to avoid forcing
    // a scroll when the user is already looking at the right area.
    responseContainer.scrollIntoView({ behavior: 'smooth', block: 'nearest' });

    while (true) {
      const { done, value } = await reader.read();
      if (done) break;

      buffer += decoder.decode(value, { stream: true });
      const lines = buffer.split('\n');
      // Keep the last incomplete line in the buffer
      buffer = lines.pop() || '';

      for (const line of lines) {
        if (!line.startsWith('data: ')) continue;
        const jsonStr = line.slice(6).trim();
        if (!jsonStr) continue;

        try {
          const event = JSON.parse(jsonStr);

          if (event.type === 'status') {
            // Update the loading text with backend progress
            const textEl = output.querySelector('.amt-loading-text');
            if (textEl) {
              textEl.style.opacity = '0';
              setTimeout(() => {
                textEl.textContent = event.message;
                textEl.style.opacity = '1';
              }, 150);
            }
          }

          if (event.type === 'chunk') {
            // First chunk received — clear the loading indicator and stop rotation
            if (!answerText) {
              output.innerHTML = '';
              clearInterval(loadingInterval);
              loadingInterval = null;
            }
            answerText += event.text;
            // Render incrementally — format the accumulated text
            const formatted = formatMarkdownToHtml(answerText);
            const paragraphs = formatted.split('\n\n').filter(p => p.trim());
            const htmlParagraphs = paragraphs.map(p => {
              const trimmed = p.trim();
              if (trimmed.startsWith('<ol>') || trimmed.startsWith('<ul>')) return trimmed;
              return '<p>' + trimmed.replace(/\n/g, '<br>') + '</p>';
            });
            output.innerHTML = htmlParagraphs.join('');
          }

          if (event.type === 'citations') {
            showCitations(event.citations);
            // Capture the first citation's theme for the explorer badge
            if (event.citations && event.citations[0] && event.citations[0].theme) {
              window._amtLastTheme = event.citations[0].theme;
            }
          }

          if (event.type === 'follow_up') {
            showFollowUpQuestions(event.questions);
          }

          if (event.type === 'headline') {
            // Store the shareable headline for use in card generation
            const rawHeadline = event.text || '';
            const sanitizedHeadline = ensureReflectionSentence(rawHeadline);
            window._amtLastShareableHeadline = sanitizedHeadline || '';
            console.log('[SSE] Received shareable_headline:', rawHeadline);
            if (!sanitizedHeadline && rawHeadline) {
              console.log('[SSE] Rejected weak headline candidate for share card');
            }
          }

          if (event.type === 'done') {
            // Expose qa_log_id for analytics addon
            window._amtLastQALogId = event.qa_log_id;
            // Remove streaming class and add completion class for CSS animations
            responseContainer.classList.remove('amt-streaming');
            output.classList.add('amt-complete');

            const answerMeta = {
              answerSource: event.answer_source || event.answerSource || '',
              answerStatus: event.answer_status || event.answerStatus || '',
              fallbackReason: event.fallback_reason || event.fallbackReason || ''
            };
            window._amtLastAnswerMeta = answerMeta;

            console.log('✅ Stream complete', {
              qa_log_id: event.qa_log_id,
              latency_ms: event.latency_ms,
              cached: event.cached || false,
              answer_status: answerMeta.answerStatus || 'generated'
            });
            // Add share button, related questions, and SEO schema after answer is complete
            addShareButton(question, answerText, window._amtLastTheme || null, answerMeta);
            addSaveToEmailButton(question, answerText);
            showRelatedQuestions(event.qa_log_id);
            injectFAQSchema(question, answerText);
            finalizeAnswerPresentation(question, answerText, lastShownCitations, window._amtLastTheme || null, answerMeta);
            restoreExploreContent();
            showReflectPrompt();
            initCopyAnswerButton(answerText);
            setTimeout(() => showMoodReactions(), 400);

            // Gamification: record the answered question
            onQuestionAnswered(question, window._amtLastTheme || null);
            window._amtLastTheme = null;

            // Conversation memory: append this turn
            appendConversationTurn(question, answerText);
            runPostAnswerExtras(question, answerText);

            // Scroll response into view only if it's not already visible.
            // Using 'nearest' avoids yanking the user back if they've already scrolled down.
            setTimeout(() => {
              responseContainer.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
            }, 100);
          }
        } catch (parseErr) {
          warn('SSE parse error:', parseErr, jsonStr);
        }
      }
    }
    clearTimeout(timeoutId);
    return answerText;
  }

  // Show answer (used for non-streaming fallback)
  function showAnswer(answer, citationsList, followUpQuestions, answerMeta) {
    responseContainer.classList.remove('error', 'amt-streaming');
    
    let formattedAnswer = formatMarkdownToHtml(answer);
    const paragraphs = formattedAnswer.split('\n\n').filter(p => p.trim());
    const htmlParagraphs = paragraphs.map(p => {
      const trimmed = p.trim();
      if (trimmed.startsWith('<ol>') || trimmed.startsWith('<ul>')) return trimmed;
      return '<p>' + trimmed.replace(/\n/g, '<br>') + '</p>';
    });
    output.innerHTML = htmlParagraphs.join('');
    output.classList.add('amt-complete');

    showCitations(citationsList);
    if (citationsList && citationsList[0] && citationsList[0].theme) {
      window._amtLastTheme = citationsList[0].theme;
    }
    showFollowUpQuestions(followUpQuestions);

    // Add share button and SEO schema
    const questionText = input.value.trim();
    const meta = answerMeta || {};
    window._amtLastAnswerMeta = meta;
    addShareButton(questionText, answer, window._amtLastTheme || null, meta);
    addSaveToEmailButton(questionText, answer);
    injectFAQSchema(questionText, answer);
    finalizeAnswerPresentation(questionText, answer, citationsList, null, meta);
    restoreExploreContent();
    showReflectPrompt();
    initCopyAnswerButton(answer);
    setTimeout(() => showMoodReactions(), 400);
    onQuestionAnswered(questionText, window._amtLastTheme || null);
    window._amtLastTheme = null;
    appendConversationTurn(questionText, answer);
    runPostAnswerExtras(questionText, answer);

    // ═══ PREMIUM FEATURES INTEGRATION ═══
    if (window.AskMirrorTalkPremium) {
      // Save reflection to local database
      window.AskMirrorTalkPremium.saveReflection({
        question: questionText,
        answer: answer,
        citations: citationsList,
        metadata: meta
      }).catch(err => warn('Failed to save reflection:', err));
      
      // Show follow-up suggestions from history
      window.AskMirrorTalkPremium.suggestFollowUps().then(suggestions => {
        if (suggestions && suggestions.length > 0 && followupsContainer && followupsList) {
          const existingFollowups = Array.from(followupsList.children || [])
            .map(btn => btn.textContent.trim());
          
          suggestions.forEach(suggestion => {
            if (!existingFollowups.includes(suggestion)) {
              const btn = document.createElement('button');
              btn.className = 'amt-followup-btn amt-smart-followup';
              btn.textContent = suggestion;
              btn.addEventListener('click', () => {
                if (typeof submitQuestionFromPrompt === 'function') {
                  submitQuestionFromPrompt(suggestion);
                }
              });
              followupsList.appendChild(btn);
            }
          });
          
          followupsContainer.style.display = 'block';
        }
      }).catch(err => warn('Failed to suggest follow-ups:', err));
      
      // Show pattern insights periodically (every 5th question)
      window.AskMirrorTalkPremium.getCachedPatterns().then(patterns => {
        if (patterns && patterns.totalReflections > 0 && patterns.totalReflections % 5 === 0) {
          if (typeof showPatternInsight === 'function') {
            showPatternInsight(patterns);
          }
        }
      }).catch(err => warn('Failed to get patterns:', err));
    }

    responseContainer.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
  }

  // ========================================
  // Save to Email
  // ========================================

  function addSaveToEmailButton(question, answer) {
    const existing = document.getElementById('amt-email-section');
    if (existing) existing.remove();
    if (!question || !answer) return;

    const section = document.createElement('div');
    section.id = 'amt-email-section';
    section.className = 'amt-email-section';
    section.innerHTML = `<button class="amt-email-btn" type="button" title="Save to email">📧 Email this reflection</button>`;

    getAnswerUtilitiesRoot().appendChild(section);

    section.querySelector('.amt-email-btn').addEventListener('click', () => {
      const subject = encodeURIComponent(`Mirror Talk: ${question.substring(0, 80)}`);
      const body = encodeURIComponent(
        `Question: ${question}\n\n` +
        `Answer from Mirror Talk:\n${answer}\n\n` +
        `— Answered by Ask Mirror Talk\nhttps://mirrortalkpodcast.com/ask-mirror-talk/`
      );
      window.location.href = `mailto:?subject=${subject}&body=${body}`;
    });
  }

  // ========================================
  // Related Questions ("Others also wondered…")
  // ========================================

  // Escape HTML entities for safe insertion into innerHTML
  function escapeHtml(str) {
    return String(str)
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;')
      .replace(/'/g, '&#39;');
  }

  const THEME_STARTERS = {
    'Self-worth': 'How do I stop comparing myself to others?',
    'Forgiveness': 'What does it mean to truly forgive someone?',
    'Inner peace': 'How do I find peace when everything feels uncertain?',
    'Purpose': 'How do I find my purpose in life?',
    'Surrender': 'What does it look like to let go and surrender?',
    'Leadership': 'What makes a great leader?',
    'Relationships': 'What\'s the key to building healthy relationships?',
    'Gratitude': 'What role does gratitude play in overcoming hardship?',
    'Boundaries': 'How do I set boundaries without feeling guilty?',
    'Healing': 'How do I start the healing process?',
    'Grief': 'How do I deal with grief and loss?',
    'Fear': 'How can I overcome fear and self-doubt?',
    'Parenting': 'How do I raise kids who are emotionally resilient?',
    'Growth': 'What can I learn from failure?',
    'Communication': 'How do I have hard conversations without damaging the relationship?',
    'Faith': 'What role does faith play in personal growth?',
    'Identity': 'How do I discover my true identity?',
    'Empowerment': 'How do I find my voice when I\'ve been silenced?',
    'Transition': 'How do I move forward after a major life change?',
    'Community': 'What does Mirror Talk teach about the power of community?'
  };

  const INTENT_STARTERS = [
    { label: 'I feel stuck', prompt: 'I feel stuck in this season of life. What question should I be asking myself first?' },
    { label: 'I need clarity', prompt: 'How do I find clarity when my thoughts are pulling me in too many directions?' },
    { label: 'I am carrying grief', prompt: 'I am carrying grief right now. How can I move through it with honesty and strength?' },
    { label: 'I need courage', prompt: 'How do I find courage when fear and self-doubt keep taking over?' }
  ];

  function truncateText(text, maxLen) {
    const value = String(text || '').trim();
    if (value.length <= maxLen) return value;
    return value.slice(0, Math.max(0, maxLen - 1)).trimEnd() + '…';
  }

  function normalizeReflectionText(text) {
    return String(text || '')
      .replace(/\s+/g, ' ')
      .replace(/^\s+|\s+$/g, '');
  }

  function joinReflectionTextParts(parts) {
    const cleanParts = (parts || [])
      .map(part => normalizeReflectionText(part))
      .filter(Boolean)
      .filter(part => /[.!?]$/.test(part) && !/…|\.\.\./.test(part));
    return cleanParts.join(' ');
  }

  function escapeRegExp(text) {
    return String(text || '').replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
  }

  function splitReflectionSentences(text) {
    const clean = normalizeReflectionText(text);
    if (!clean) return [];
    const matches = clean.match(/[^.!?]+[.!?]?/g) || [clean];
    return matches
      .map(sentence => sentence.trim())
      .filter(Boolean);
  }

  function isCompleteReflectionSentence(text) {
    const clean = normalizeReflectionText(text);
    console.log('[isCompleteReflectionSentence] Input:', text);
    console.log('[isCompleteReflectionSentence] Clean:', clean);
    if (!clean || clean.length < 28) {
      console.log('[isCompleteReflectionSentence] REJECT: Too short');
      return false;
    }
    
    // Must end with proper punctuation
    if (!/[.!?]$/.test(clean)) {
      console.log('[isCompleteReflectionSentence] REJECT: No ending punctuation');
      return false;
    }
    if (/…|\.\.\./.test(clean)) {
      console.log('[isCompleteReflectionSentence] REJECT: Has ellipsis');
      return false;
    }
    if (/\b[a-z]{1,2}\s+[A-Z][a-z]/.test(clean)) {
      console.log('[isCompleteReflectionSentence] REJECT: Mid-sentence capitalization');
      return false;
    }
    
    // Check for unbalanced quotes and parentheses (critical for shareability)
    const openParens = (clean.match(/\(/g) || []).length;
    const closeParens = (clean.match(/\)/g) || []).length;
    if (openParens !== closeParens) {
      console.log('[isCompleteReflectionSentence] REJECT: Unbalanced parentheses');
      return false;
    }
    
    const openBrackets = (clean.match(/\[/g) || []).length;
    const closeBrackets = (clean.match(/\]/g) || []).length;
    if (openBrackets !== closeBrackets) {
      console.log('[isCompleteReflectionSentence] REJECT: Unbalanced brackets');
      return false;
    }
    
    // Check for unbalanced quotes (straight and curly)
    const straightDoubleQuotes = (clean.match(/"/g) || []).length;
    if (straightDoubleQuotes % 2 !== 0) {
      console.log('[isCompleteReflectionSentence] REJECT: Unbalanced straight quotes');
      return false;
    }
    
    const curlyOpenQuotes = (clean.match(/[""]/g) || []).length;
    const curlyCloseQuotes = (clean.match(/[""]/g) || []).length;
    if (curlyOpenQuotes !== curlyCloseQuotes) {
      console.log('[isCompleteReflectionSentence] REJECT: Unbalanced curly quotes');
      return false;
    }
    
    const singleQuotes = (clean.match(/'/g) || []).length;
    const curlyOpenSingle = (clean.match(/'/g) || []).length;
    const curlyCloseSingle = (clean.match(/'/g) || []).length;
    // Only check unbalanced single quotes if they're not used as apostrophes
    if (singleQuotes >= 2 && singleQuotes % 2 !== 0) {
      // Allow single quotes that are likely apostrophes (preceded/followed by letters)
      const apostrophes = (clean.match(/[a-z]'[a-z]/gi) || []).length;
      if ((singleQuotes - apostrophes) % 2 !== 0) {
        console.log('[isCompleteReflectionSentence] REJECT: Unbalanced single quotes');
        return false;
      }
    }
    if (curlyOpenSingle !== curlyCloseSingle) {
      console.log('[isCompleteReflectionSentence] REJECT: Unbalanced curly single quotes');
      return false;
    }
    
    // Can't be a question
    if (/^(how|what|why|when|where|who|can|could|should|would|do|does|did|is|are|am|will)\b/i.test(clean)) {
      console.log('[isCompleteReflectionSentence] REJECT: Starts like a question');
      return false;
    }
    if (isWeakShareHeadlineCandidate(clean)) {
      console.log('[isCompleteReflectionSentence] REJECT: Weak headline');
      return false;
    }
    
    // Can't end mid-thought with conjunctions
    if (/[,:;]\s*(and|or|but|because|which|that|about|with|for)$/i.test(clean)) {
      console.log('[isCompleteReflectionSentence] REJECT: Ends with conjunction after comma');
      return false;
    }
    const weakEndPattern = /\b(and|or|but|because|which|that|about|around|into|with|for|of|on|to|from|can|could|would|should|may|might|enhance|transform|deep|honest)[.!?]$/i;
    if (weakEndPattern.test(clean)) {
      console.log('[isCompleteReflectionSentence] REJECT: Ends with weak word:', clean.match(weakEndPattern)[0]);
      return false;
    }
    if (/,\s*(deep|honest|gentle|steady|quiet|open|real|true)[.!?]$/i.test(clean)) {
      console.log('[isCompleteReflectionSentence] REJECT: Ends with adjective after comma');
      return false;
    }
    
    // Must have reasonable word count for a complete thought
    const words = clean.split(/\s+/).filter(Boolean);
    if (words.length < 5) {
      console.log('[isCompleteReflectionSentence] REJECT: Too few words');
      return false;
    }
    const lastWord = (words[words.length - 1] || '').replace(/[^A-Za-z']/g, '').replace(/^'+|'+$/g, '');
    const allowedShortEndings = new Set(['me', 'us', 'it', 'be', 'go', 'do']);
    if (lastWord && lastWord.length <= 2 && !allowedShortEndings.has(lastWord.toLowerCase())) {
      console.log('[isCompleteReflectionSentence] REJECT: Last word too short:', lastWord);
      return false;
    }
    
    // Should have action or being verb for completeness
    const hasVerb = /\b(is|are|was|were|be|been|being|have|has|had|do|does|did|can|could|will|would|should|shall|may|might|must|means|begins|starts|looks|feels|helps|lets|gives|give|make|makes|remember|remembers|remind|reminds|notice|notices|open|opens|repair|repairs|rebuild|rebuilds|restore|restores|reconnect|reconnects|transform|transforms|strengthen|strengthens|ground|grounds|anchor|anchors|soften|softens|require|requires|invite|invites|call|calls|create|creates|grow|grows|become|becomes|allow|allows|ask|asks|teach|teaches|reveal|reveals|hold|holds|carry|carries|stay|trust|return|release|choose|protect|honor|pause|listen|lead|follow|speak|learn|face|faced|succeed|succeeded|build|builds|steer|steers|shape|shapes|enable|enables|manifest|manifests|discuss|discusses|align|aligns|suggest|suggests|cultivate|cultivates|reflect|reflects|mirror|mirrors|reinforce|reinforces|expand|expands|confront|confronts|embrace|embracing|act|acting|set|sets)\b/i.test(clean);
    
    if (!hasVerb) {
      console.log('[isCompleteReflectionSentence] REJECT: No action/being verb');
      return false;
    }
    
    console.log('[isCompleteReflectionSentence] ACCEPT: Passed all checks');
    return true;
  }

  function ensureReflectionSentence(text) {
    console.log('[ensureReflectionSentence] Input:', text);
    let clean = cleanReflectionSentenceCandidate(text);
    console.log('[ensureReflectionSentence] After cleanReflectionSentenceCandidate:', clean);
    if (clean) return clean;

    clean = trimDanglingHeadlineTail(text);
    console.log('[ensureReflectionSentence] After trimDanglingHeadlineTail:', clean);
    if (!clean) return '';
    
    // Remove trailing commas and semicolons
    clean = clean.replace(/[,:;]+$/g, '').trim();

    const isComplete = isCompleteReflectionSentence(clean);
    console.log('[ensureReflectionSentence] isCompleteReflectionSentence result:', isComplete);
    return isComplete ? clean : '';
  }

  function capitalizeReflectionSentence(text) {
    const clean = normalizeReflectionText(text);
    if (!clean) return '';
    return clean.charAt(0).toUpperCase() + clean.slice(1);
  }

  function cleanReflectionSentenceCandidate(text) {
    let clean = normalizeReflectionText(stripSpeakerAttribution(text) || text);
    if (!clean) return '';
    clean = clean
      .replace(/^[-–—•\s]+/, '')
      .replace(/^["'“”]+|["'“”]+$/g, '')
      .trim();
    clean = trimDanglingHeadlineTail(clean);
    clean = clean.replace(/[,:;]+$/g, '').trim();
    clean = capitalizeReflectionSentence(clean);
    return isCompleteReflectionSentence(clean) ? clean : '';
  }

  function stripSpeakerAttribution(text) {
    let clean = normalizeReflectionText(text);
    if (!clean) return '';
    clean = clean.replace(
      /^[A-Z][a-z]+(?:\s+[A-Z][a-z]+){0,2}\s+(?:emphasizes|says|shares|notes|explains|reminds(?:\s+us)?|suggests|teaches)\s+that\s+/,
      ''
    );
    clean = clean.replace(
      /^[A-Z][a-z]+(?:\s+[A-Z][a-z]+){0,2}\s+(?:believes|argues|offers|shows)\s+/,
      ''
    );
    return clean.trim();
  }

  function getThemeReflectionKeywords(theme) {
    const lower = String(theme || '').toLowerCase().trim();
    const tokens = lower.split(/[^a-z]+/).filter(token => token.length >= 4);
    const map = {
      relationships: ['relationship', 'relationships', 'love', 'connection', 'respect', 'partnership'],
      relationship: ['relationship', 'relationships', 'love', 'connection', 'respect', 'partnership'],
      grief: ['grief', 'loss', 'mourning', 'sorrow', 'healing', 'heartache'],
      healing: ['healing', 'repair', 'restore', 'restoration', 'wholeness', 'mend'],
      forgiveness: ['forgiveness', 'forgive', 'release', 'trust', 'reconcile'],
      boundaries: ['boundaries', 'boundary', 'needs', 'self-respect', 'guilt', 'protect'],
      leadership: ['leadership', 'leader', 'leaders', 'leading', 'influence', 'stewardship'],
      courage: ['courage', 'fear', 'brave', 'bravery', 'risk', 'bold', 'challenge', 'challenges', 'strength', 'succeeded', 'resilience'],
      faith: ['faith', 'trust', 'hope', 'prayer', 'god', 'belief'],
      selfworth: ['worth', 'worthy', 'value', 'identity', 'comparison', 'confidence'],
      'self-worth': ['worth', 'worthy', 'value', 'identity', 'comparison', 'confidence'],
      growth: ['growth', 'growing', 'becoming', 'progress', 'change', 'transform'],
      peace: ['peace', 'calm', 'rest', 'quiet', 'steady', 'stillness'],
      'inner-peace': ['peace', 'calm', 'rest', 'quiet', 'steady', 'stillness'],
      'inner peace': ['peace', 'calm', 'rest', 'quiet', 'steady', 'stillness'],
      purpose: ['purpose', 'calling', 'meaning', 'direction', 'clarity'],
      vulnerability: ['vulnerability', 'honesty', 'open', 'authentic', 'truth'],
      fear: ['fear', 'anxiety', 'doubt', 'brave', 'courage'],
      empowerment: ['voice', 'confidence', 'power', 'agency', 'speak'],
      transition: ['transition', 'change', 'season', 'move', 'beginning'],
      communication: ['conversation', 'communicate', 'listening', 'speak', 'repair'],
      community: ['community', 'belonging', 'support', 'together', 'care'],
      identity: ['identity', 'becoming', 'name', 'self', 'worth']
    };
    const normalizedKey = lower.replace(/[^a-z]+/g, '');
    return Array.from(new Set([].concat(tokens, map[lower] || [], map[normalizedKey] || [])));
  }

  function scoreReflectionSentence(sentence, options) {
    const text = cleanReflectionSentenceCandidate(sentence);
    const lower = text.toLowerCase();
    const words = text.split(/\s+/).filter(Boolean);
    if (!text || words.length < 5) return -100;

    let score = 0;

    
    // Heavily penalize unbalanced quotes and parentheses (critical for shareability)
    const openParens = (text.match(/\(/g) || []).length;
    const closeParens = (text.match(/\)/g) || []).length;
    if (openParens !== closeParens) score -= 50; // Massive penalty
    
    const straightDoubleQuotes = (text.match(/"/g) || []).length;
    if (straightDoubleQuotes % 2 !== 0) score -= 50;
    
    const curlyOpenQuotes = (text.match(/[""]/g) || []).length;
    const curlyCloseQuotes = (text.match(/[""]/g) || []).length;
    if (curlyOpenQuotes !== curlyCloseQuotes) score -= 50;
    
    const length = text.length;
    if (length >= 58 && length <= 150) score += 5;
    else if (length >= 42 && length <= 175) score += 3;
    else if (length > 200) score -= 4;
    else score -= 1;

    if (words.length >= 9 && words.length <= 22) score += 3;
    else if (words.length >= 6 && words.length <= 26) score += 1;
    else if (words.length > 30) score -= 3;

    if (/[.!?]$/.test(String(sentence || '').trim())) score += 2;
    if (!/[,:;]\s*(and|or|but)$/i.test(text)) score += 1;
    if (isCompleteReflectionSentence(String(sentence || '').trim())) score += 3;

    if (/^(how|what|why|when|where|who|can|could|should|would|do|does|did|is|are|am|will)\b/i.test(lower)) score -= 8;
    if (/^(this reflection|what stayed with me|what likely stayed with you|one thing that stood out|in this reflection)\b/i.test(lower)) score -= 8;
    if (/^(i|i['’]?m|i['’]?ve|i['’]?d|my)\b/i.test(lower)) score -= 3;
    if (/^(there is|there are|it is|it can be|sometimes|often|maybe)\b/i.test(lower)) score -= 1;

    if (/\b(you|your|healing|grief|forgiveness|boundaries|courage|faith|peace|trust|hope|love|rest|clarity|strength|vulnerability|leadership|connection|respect|worth)\b/i.test(lower)) {
      score += 3;
    }

    if (/\b(means|begins|starts|requires|invites|calls|creates|grows|becomes|allows|asks|teaches|reveals|reminds)\b/i.test(lower)) {
      score += 2;
    }

    if (/\b(stay with|return to|carry|notice|trust|allow|honor|protect|release|choose|create space|hold|listen)\b/i.test(lower)) {
      score += 2;
    }

    if (/\b(journey|process|season|practice|rhythm|steady|gentle|honest|sacred|quiet)\b/i.test(lower)) {
      score += 1;
    }

    if (/\b(maybe|perhaps|for example|for instance|kind of|sort of|really|actually)\b/i.test(lower)) score -= 2;
    if (/\b(podcast|episode|guest|speaker|story|program|tool)\b/i.test(lower)) score -= 3;
    if (/\b(thank you|welcome back|let me ask|one thing i love|what i want to ask)\b/i.test(lower)) score -= 6;
    if (/^[A-Z][a-z]+(?:\s+[A-Z][a-z]+){0,2}\s+(emphasizes|says|shares|notes|explains|reminds|suggests)\b/.test(String(sentence || '').trim())) score -= 8;

    const themeKeywords = (options && options.themeKeywords) || [];
    const matchedKeywords = themeKeywords.filter(keyword => lower.includes(keyword));
    if (matchedKeywords.length >= 2) score += 4;
    else if (matchedKeywords.length === 1) score += 2;

    if ((options && options.preferUniversal) && !/^(i|i['’]?m|i['’]?ve|my)\b/i.test(lower)) score += 2;
    if ((options && options.preferShort) && length <= 120) score += 1;
    if ((options && options.excludeText) && lower === String(options.excludeText || '').toLowerCase().trim()) score -= 10;

    return score;
  }

  function selectReflectionLine(text, options) {
    const sentences = splitReflectionSentences(text);
    if (!sentences.length) return '';

    let best = '';
    let bestScore = -Infinity;

    sentences.forEach(sentence => {
      const cleaned = ensureReflectionSentence(stripSpeakerAttribution(sentence) || sentence);
      if (!cleaned) return;
      const score = scoreReflectionSentence(cleaned, options);
      if (score > bestScore || (score === bestScore && cleaned.length > best.length)) {
        best = cleaned;
        bestScore = score;
      }
    });

    return ensureReflectionSentence(best);
  }

  function listSupportingReflectionCandidates(text, theme, headline) {
    const clean = normalizeReflectionText(text);
    if (!clean) return [];

    const themeKeywords = getThemeReflectionKeywords(theme);
    const headlineLower = trimDanglingHeadlineTail(headline || '').toLowerCase();
    const sentences = splitReflectionSentences(clean);
    const ranked = sentences
      .map(sentence => {
        const cleaned = ensureReflectionSentence(stripSpeakerAttribution(sentence) || sentence);
        return {
          text: cleaned,
          score: scoreReflectionSentence(cleaned || sentence, {
            themeKeywords,
            preferUniversal: true,
            excludeText: headline || ''
          })
        };
      })
      .filter(item => {
        if (!item.text || !isCompleteReflectionSentence(item.text)) return false;
        if (trimDanglingHeadlineTail(item.text).toLowerCase() === headlineLower) return false;
        return !isDuplicateReflectionLine(item.text, headline);
      })
      .sort((a, b) => b.score - a.score)
      .map(item => item.text);

    const unique = [];
    ranked.forEach(candidate => {
      if (!candidate) return;
      if (!unique.some(existing => isDuplicateReflectionLine(existing, candidate))) {
        unique.push(candidate);
      }
    });
    return unique;
  }

  function selectSupportingReflectionLine(text, theme, headline) {
    return listSupportingReflectionCandidates(text, theme, headline)[0] || '';
  }

  function selectFittingReflectionLine(ctx, candidates, fitOptions) {
    const unique = [];
    (candidates || []).forEach(candidate => {
      const clean = ensureReflectionSentence(candidate);
      if (!clean) return;
      if (!unique.some(existing => isDuplicateReflectionLine(existing, clean))) unique.push(clean);
    });

    return unique.find(candidate =>
      canRenderCanvasTextFully(
        ctx,
        candidate,
        fitOptions.maxWidth,
        fitOptions.maxHeight,
        fitOptions.maxLines,
        fitOptions.fontTemplate,
        fitOptions.maxSize,
        fitOptions.minSize,
        fitOptions.lineHeightRatio
      )
    ) || '';
  }

  function scoreShareHeadlineCandidate(text, themeKeywords) {
    const clean = ensureReflectionSentence(stripSpeakerAttribution(text) || text);
    if (!clean) return -Infinity;

    const words = clean.split(/\s+/).filter(Boolean);
    const length = clean.length;
    let score = scoreReflectionSentence(clean, {
      themeKeywords: themeKeywords || [],
      preferUniversal: true
    });

    if (isWeakShareHeadlineCandidate(clean)) score -= 35;

    if (length >= 60 && length <= 150) score += 10;
    else if (length >= 45 && length <= 180) score += 6;
    else if (length < 38) score -= 8;
    else if (length > 220) score -= 6;

    if (words.length >= 9 && words.length <= 22) score += 8;
    else if (words.length >= 7 && words.length <= 26) score += 4;
    else if (words.length > 30) score -= 5;
    else if (words.length < 5) score -= 8;

    if (/\b(you|your|we|our|this|today|season|truth|heart|self|growth|courage|healing|peace|faith|grace|worth|clarity|wisdom|change|choice|honesty|patience|resilience|connection|trust|strength)\b/i.test(clean)) {
      score += 3;
    }

    if (/\b(remind|teaches?|shows?|helps?|invites?|allows?|requires?|protects?|releases?|restores?|grounds?|becomes?|carries?|chooses?|trusts?|honors?|listens?|speaks?|leads?|holds?|returns?|stays?|reveals?|shapes?|guides?)\b/i.test(clean)) {
      score += 2;
    }

    if (/^[A-Z][a-z]+(?:\s+[A-Z][a-z]+){0,2}\s+(says|shares|notes|explains|reminds|suggests|teaches)\b/.test(clean)) score -= 8;
    if (/^(what|how|why|when|where|who|can|could|should|would|do|does|did|is|are|am|will)\b/i.test(clean)) score -= 10;
    if (/^(in this reflection|this reflection|one thing that stood out|here are grounded reflections|i found a few mirror talk moments|the clearest thread is this|one source moment says)\b/i.test(clean.toLowerCase())) score -= 15;

    if (/[,:;]$/.test(clean)) score -= 4;
    if (/[,;:]/.test(clean)) score += 1;

    return score;
  }

  function inferReflectionArtifactTheme(questionText, bodyText, providedTheme) {
    const provided = String(providedTheme || '').trim();
    if (provided && provided.toLowerCase() !== 'reflection') return provided;

    const primary = normalizeReflectionText(bodyText).toLowerCase();
    const secondary = normalizeReflectionText(questionText).toLowerCase();
    const includesKeyword = (haystack, keyword) => {
      const needle = String(keyword || '').toLowerCase().trim();
      if (!needle) return false;
      if (/[^a-z0-9]/i.test(needle)) return haystack.includes(needle);
      return new RegExp(`(^|[^a-z0-9])${escapeRegExp(needle)}(?=$|[^a-z0-9])`, 'i').test(haystack);
    };
    let bestTheme = '';
    let bestScore = 0;

    const cardThemes = Array.from(new Set(AMT_THEMES.concat(['Courage'])));
    cardThemes.forEach(theme => {
      const themeKey = theme.toLowerCase();
      const keywords = Array.from(new Set([themeKey].concat(getThemeReflectionKeywords(theme))));
      let score = 0;

      keywords.forEach(keyword => {
        if (!keyword) return;
        if (includesKeyword(primary, keyword)) score += keyword === themeKey ? 7 : 3;
        if (includesKeyword(secondary, keyword)) score += keyword === themeKey ? 3 : 1;
      });

      if (score > bestScore) {
        bestScore = score;
        bestTheme = theme;
      }
    });

    return bestTheme || inferTheme(questionText, bodyText) || provided || 'Reflection';
  }

  function buildThemeReflectionFallback(theme) {
    const key = String(theme || '').toLowerCase().trim();
    const fallbacks = {
      relationships: 'Return to the kind of connection you want to build and protect.',
      grief: 'Stay gently with what hurts without turning away from it.',
      healing: 'Honor what is still healing and what is slowly becoming whole.',
      faith: 'Return to what still feels sacred and quietly alive.',
      courage: 'Trust the next brave step more than the need to feel ready.',
      fear: 'Listen for what fear is trying to protect before you answer it.',
      boundaries: 'Make room for honesty, self-respect, and a steadier no.',
      'self-worth': 'Come back to the truth that your worth does not need proving.',
      leadership: 'Lead from clarity, steadiness, and the courage to stay human.',
      purpose: 'Follow the thread that keeps calling you forward.',
      gratitude: 'Let gratitude return your attention to what is still giving life.',
      forgiveness: 'Release what keeps your heart closed while protecting what wisdom has taught you.',
      'inner peace': 'Stillness gives your heart room to hear what is true.',
      growth: 'Let this season teach you without requiring you to become perfect.',
      communication: 'Speak with enough honesty to be clear and enough care to stay connected.',
      community: 'Let yourself be supported by the people who can hold the truth with you.',
      identity: 'Return to the name and worth that do not depend on performance.',
      transition: 'Trust that a new season can begin before every answer is clear.',
      empowerment: 'Let your voice return with steadiness, truth, and self-respect.'
    };
    const fallback = fallbacks[key] || 'Pause with one honest thought that still feels worth carrying forward.';
    return ensureReflectionSentence(fallback) || 'Pause with one honest thought that still feels worth carrying forward.';
  }

  function extractReflectionBody(answerText, theme, headline) {
    const sentences = splitReflectionSentences(answerText);
    if (!sentences.length) return buildThemeReflectionFallback(theme);

    const themeKeywords = getThemeReflectionKeywords(theme);
    const headlineLower = trimDanglingHeadlineTail(headline || '').toLowerCase();
    const ranked = sentences
      .map(sentence => ({
        text: ensureReflectionSentence(stripSpeakerAttribution(sentence) || sentence),
        score: scoreReflectionSentence(sentence, {
          themeKeywords,
          preferUniversal: true,
          excludeText: headline || ''
        })
      }))
      .filter(item => item.text && item.text.toLowerCase() !== headlineLower && isCompleteReflectionSentence(item.text))
      .sort((a, b) => b.score - a.score);

    const primary = ranked.find(item => item.score >= 4) || ranked[0];
    if (!primary) return buildThemeReflectionFallback(theme);

    const secondary = ranked.find(item =>
      item !== primary &&
      item.score >= 5 &&
      (primary.text.length + item.text.length) <= 210
    );

    const combined = secondary ? `${primary.text} ${secondary.text}` : primary.text;
    return combined.length <= 220 ? combined.trim() : primary.text;
  }

  function extractCardHeadline(text, theme) {
    const sentences = splitReflectionSentences(text);
    if (!sentences.length) return buildThemeReflectionFallback(theme);

    const themeKeywords = getThemeReflectionKeywords(theme);
    const ranked = sentences
      .map(sentence => {
        const cleaned = ensureReflectionSentence(stripSpeakerAttribution(sentence) || sentence);
        const score = scoreShareHeadlineCandidate(cleaned, themeKeywords);
        const words = cleaned.split(/\s+/).filter(Boolean);
        return {
          text: cleaned,
          score,
          fitsHero: cleaned.length >= 38 && cleaned.length <= 170 && words.length >= 6 && words.length <= 26
        };
      })
      .filter(item => item.text && item.score >= 0 && isCompleteReflectionSentence(item.text))
      .sort((a, b) => b.score - a.score);

    const bestHero = ranked.find(item => item.fitsHero && item.score >= 3);
    return bestHero ? bestHero.text : buildThemeReflectionFallback(theme);
  }

  function listCardHeadlineCandidates(text, theme, options) {
    const opts = options || {};
    const includeFallback = opts.includeFallback !== false;
    const sentences = splitReflectionSentences(text);
    const themeKeywords = getThemeReflectionKeywords(theme);
    const ranked = sentences
      .map(sentence => {
        const cleaned = ensureReflectionSentence(stripSpeakerAttribution(sentence) || sentence);
        const words = cleaned.split(/\s+/).filter(Boolean);
        const score = scoreShareHeadlineCandidate(cleaned, themeKeywords);
        return {
          text: cleaned,
          score,
          fitsHero: cleaned.length >= 38 && cleaned.length <= 170 && words.length >= 6 && words.length <= 26
        };
      })
      .filter(item => item.text && item.score >= 0 && item.fitsHero && isCompleteReflectionSentence(item.text))
      .sort((a, b) => b.score - a.score)
      .map(item => item.text);

    const compact = listCompactSourceReflectionCandidates(text);
    const fallback = buildThemeReflectionFallback(theme);
    const unique = [];
    [...ranked, ...compact, ...(includeFallback ? [fallback] : [])].forEach(item => {
      if (!item) return;
      if (!unique.includes(item)) unique.push(item);
    });
    return unique;
  }

  function listCompactSourceReflectionCandidates(text) {
    const candidates = [];
    const add = (value) => {
      const clean = ensureReflectionSentence(value);
      if (!clean) return;
      const words = clean.split(/\s+/).filter(Boolean);
      if (clean.length > 150 || words.length > 22) return;
      if (!candidates.some(existing => areReflectionLinesTooSimilar(existing, clean))) {
        candidates.push(clean);
      }
    };

    splitReflectionSentences(text).forEach(sentence => {
      const raw = normalizeReflectionText(stripSpeakerAttribution(sentence) || sentence);
      if (!raw) return;
      const withoutAside = normalizeReflectionText(
        raw
          .replace(/\s*[—–]\s*[^—–]{3,140}\s*[—–]\s*/g, ' ')
          .replace(/\([^)]{3,140}\)/g, ' ')
      );
      const variants = Array.from(new Set([raw, withoutAside]));

      variants.forEach(variant => {
        add(variant);

        const whenYou = variant.match(/\bwhen\s+you\s+(remember|trust|choose|honor|protect|release|return|pause|listen|lead|speak|carry|stay|create|remind|reconnect|notice|allow)\b([^.!?]*[.!?])/i);
        if (whenYou) {
          add(`${whenYou[1]}${whenYou[2]}`);
        }

        const youClause = variant.match(/\b(you\s+(?:can|could|will|would|are|have|need|return|remember|remind|trust|choose|honor|create|carry|stay|let|begin|start|become|reconnect|notice|allow)\b[^.!?]*[.!?])/i);
        if (youClause) {
          add(youClause[1]);
        }

        const yourClause = variant.match(/\b(your\s+[^.!?]*(?:is|are|becomes|can|will|does|need|needs|returns|grows|deepens|strengthens)\b[^.!?]*[.!?])/i);
        if (yourClause) {
          add(yourClause[1]);
        }

        const imperative = variant.match(/\b((?:remember|trust|choose|honor|protect|release|return|pause|listen|lead|speak|let|make|create|notice|allow)\b[^.!?]*[.!?])/i);
        if (imperative) {
          add(imperative[1]);
        }
      });
    });

    return candidates;
  }

  function areReflectionLinesTooSimilar(a, b) {
    const left = normalizeReflectionText(stripSpeakerAttribution(a) || a).toLowerCase();
    const right = normalizeReflectionText(stripSpeakerAttribution(b) || b).toLowerCase();
    if (!left || !right) return false;
    if (left === right) return true;
    if (left.includes(right) || right.includes(left)) return true;

    const fillerWords = new Set([
      'about', 'after', 'again', 'also', 'because', 'before', 'central', 'could',
      'deeper', 'does', 'from', 'genuine', 'insight', 'itself', 'just', 'know',
      'likely', 'more', 'most', 'simple', 'still', 'that', 'their', 'there',
      'these', 'this', 'those', 'today', 'when', 'where', 'with', 'without',
      'world', 'would', 'your'
    ]);
    const toWordSet = (value) => new Set(
      value
        .split(/[^a-z0-9]+/)
        .map(word => word.replace(/’/g, "'").replace(/'s$/, ''))
        .filter(word => word.length >= 4 && !fillerWords.has(word))
    );
    const leftWords = toWordSet(left);
    const rightWords = toWordSet(right);
    if (!leftWords.size || !rightWords.size) return false;
    let overlap = 0;
    leftWords.forEach(word => {
      if (rightWords.has(word)) overlap += 1;
    });
    const ratio = overlap / Math.max(1, Math.min(leftWords.size, rightWords.size));
    return ratio >= 0.56 || (overlap >= 5 && ratio >= 0.45);
  }

  function isDuplicateReflectionLine(a, b) {
    const normalize = (value) => trimDanglingHeadlineTail(ensureReflectionSentence(value) || value)
      .toLowerCase()
      .replace(/\s+/g, ' ')
      .trim();
    const left = normalize(a);
    const right = normalize(b);
    if (!left || !right) return false;
    if (left === right) return true;

    const leftBare = left.replace(/[^a-z0-9\s]/g, '').trim();
    const rightBare = right.replace(/[^a-z0-9\s]/g, '').trim();
    if (leftBare && rightBare && (leftBare === rightBare || leftBare.includes(rightBare) || rightBare.includes(leftBare))) {
      return true;
    }

    if (areReflectionLinesTooSimilar(left, right)) return true;

    const stopwords = new Set([
      'about', 'after', 'again', 'also', 'already', 'before', 'being', 'between', 'could', 'does', 'doing',
      'down', 'each', 'even', 'every', 'feels', 'from', 'have', 'into', 'itself', 'just', 'like', 'likely',
      'more', 'most', 'need', 'other', 'others', 'perhaps', 'really', 'should', 'some', 'still', 'that',
      'their', 'them', 'then', 'there', 'these', 'they', 'this', 'those', 'through', 'today', 'toward',
      'under', 'when', 'where', 'while', 'with', 'without', 'worth', 'would', 'your', 'youre', 'youve', 'yourself'
    ]);
    const stem = (term) => {
      let value = String(term || '').toLowerCase();
      if (value.endsWith('ing') && value.length > 6) value = value.slice(0, -3);
      else if (value.endsWith('ed') && value.length > 5) value = value.slice(0, -2);
      else if (value.endsWith('es') && value.length > 5) value = value.slice(0, -2);
      else if (value.endsWith('s') && value.length > 4) value = value.slice(0, -1);
      return value;
    };
    const significantTerms = (text) => {
      const set = new Set();
      const words = String(text || '').match(/[a-z][a-z']+/g) || [];
      words.forEach(raw => {
        const term = stem(raw.replace(/'/g, ''));
        if (term.length < 4 || stopwords.has(term)) return;
        set.add(term);
      });
      return set;
    };

    const leftTerms = significantTerms(left);
    const rightTerms = significantTerms(right);
    if (!leftTerms.size || !rightTerms.size) return false;

    let overlap = 0;
    leftTerms.forEach(term => {
      if (rightTerms.has(term)) overlap += 1;
    });
    const ratio = overlap / Math.max(1, Math.min(leftTerms.size, rightTerms.size));
    return ratio >= 0.56 || (overlap >= 5 && ratio >= 0.45);
  }

  function getThemeStarter(theme) {
    return THEME_STARTERS[theme] || `What does Mirror Talk say about ${String(theme || 'this theme').toLowerCase()}?`;
  }

  function getRhythmReflectionQuestion(preferredTheme, options) {
    const opts = options || {};
    const cleanTheme = String(preferredTheme || '').trim();
    const latestQotd = typeof loadLatestQotd === 'function' ? loadLatestQotd() : null;
    if (opts.preferQotd !== false && latestQotd && latestQotd.question) {
      return latestQotd.question;
    }

    if (cleanTheme) {
      return getThemeStarter(cleanTheme);
    }

    const lastSession = typeof loadLastSession === 'function' ? loadLastSession() : null;
    const lastTheme = String((lastSession && lastSession.theme) || '').trim();
    if (lastTheme) {
      return getThemeStarter(lastTheme);
    }

    if (latestQotd && latestQotd.question) {
      return latestQotd.question;
    }

    return 'What do I need to notice before today ends?';
  }

  function submitRhythmQuestion(question, origin, metadata) {
    const cleanQuestion = String(question || '').trim();
    if (!cleanQuestion) {
      runWorkflowAction('ask', { persist: true, scroll: true });
      return;
    }
    setQuestionOrigin(origin || 'rhythm', metadata || {});
    submitQuestionFromPrompt(cleanQuestion);
  }

  function generateLowMatchPrompts(question, theme) {
    const activeTheme = theme || inferTheme(question, '') || 'this';
    return [
      `Can you answer this through the lens of ${String(activeTheme).toLowerCase()}?`,
      'What part of this question should I narrow first?',
      'Can you help me rephrase this into one clearer question?'
    ];
  }

  function focusFormWithQuestion(question) {
    if (!question || !form || !input) return;
    input.value = question;
    input.focus();
    input.dispatchEvent(new Event('input', { bubbles: true }));
    form.scrollIntoView({ behavior: 'smooth', block: 'center' });
  }

  function submitQuestionFromPrompt(question) {
    if (!question || !form || !input) return;
    input.value = question;
    input.focus();
    input.dispatchEvent(new Event('input', { bubbles: true }));
    runWorkflowAction('ask', { persist: true, scroll: false });
    form.scrollIntoView({ behavior: 'smooth', block: 'center' });
    setTimeout(() => form.dispatchEvent(new Event('submit', { cancelable: true })), 180);
  }

  function sanitizeQuestionFragment(value) {
    return String(value || '')
      .replace(/[?!.]+$/g, '')
      .replace(/\s+/g, ' ')
      .trim();
  }

  function buildQuestionCoachPrompts(rawInput) {
    const fragment = sanitizeQuestionFragment(rawInput);
    if (!fragment || fragment.length < 4) return [];

    const lower = fragment.toLowerCase();
    
    // Extract the core topic from common question patterns
    const extractTopic = (text) => {
      const patterns = [
        /^tell me about\s+(.+)/i,
        /^what (?:is|are)\s+(.+)/i,
        /^how do i\s+(.+)/i,
        /^can you (?:explain|tell me about)\s+(.+)/i,
        /^explain\s+(.+)/i,
        /^describe\s+(.+)/i,
        /^help me (?:understand|with)\s+(.+)/i,
        /^i (?:want to know|need to understand)\s+(?:about\s+)?(.+)/i,
        /^i am (?:trying to|wanting to)?\s*(?:learn(?:ing)?|understand(?:ing)?)(?:\s+more)?\s+about\s+(.+?)(?:,|$)/i,
      ];
      
      for (const pattern of patterns) {
        const match = text.match(pattern);
        if (match && match[1]) {
          return match[1].trim();
        }
      }
      
      // If no pattern matched, try to extract topic from "about X" anywhere in the text
      const aboutMatch = text.match(/\babout\s+([^,]+?)(?:,|$)/i);
      if (aboutMatch && aboutMatch[1]) {
        return aboutMatch[1].trim();
      }
      
      return text; // If no pattern matches, use the original text
    };
    
    const topic = extractTopic(lower);
    const prompts = [];
    const addPrompt = (label, questionText) => {
      const cleanQuestion = String(questionText || '').trim();
      if (!cleanQuestion) return;
      if (prompts.some(item => item.question === cleanQuestion)) return;
      prompts.push({ label, question: cleanQuestion });
    };

    if (!/[?]$/.test(String(rawInput || '').trim()) || fragment.length < 26) {
      addPrompt('Make it more specific', `How do I navigate ${topic} with honesty and clarity?`);
    }

    addPrompt('Ask for a first step', `What is the first step I should take with ${topic}?`);
    addPrompt('Ground it in Mirror Talk', `What does Mirror Talk say about ${topic}?`);

    if (lower.includes('feel ') || lower.includes('feeling')) {
      addPrompt('Explore the feeling', `What might this feeling be trying to show me about ${topic}?`);
    }

    return prompts.slice(0, 2);
  }

  function renderQuestionCoach(rawInput) {
    if (!questionCoach) return;

    const prompts = buildQuestionCoachPrompts(rawInput);
    if (!prompts.length) {
      questionCoach.innerHTML = '';
      questionCoach.style.display = 'none';
      return;
    }

    questionCoach.innerHTML = `
      <div class="amt-question-coach-inner">
        <span class="amt-question-coach-kicker">Shape the question</span>
        <p class="amt-question-coach-text">Turn this into a stronger prompt with one tap.</p>
        <div class="amt-question-coach-actions">
          ${prompts.map(item => `
            <button type="button" class="amt-question-coach-btn" data-question="${escapeHtml(item.question)}">
              <span class="amt-question-coach-btn-label">${escapeHtml(item.label)}</span>
              <span class="amt-question-coach-btn-text">${escapeHtml(item.question)}</span>
            </button>
          `).join('')}
        </div>
      </div>
    `;
    questionCoach.style.display = '';

    questionCoach.querySelectorAll('.amt-question-coach-btn').forEach(btn => {
      btn.addEventListener('click', () => {
        const suggestedQuestion = btn.dataset.question || '';
        emitProductEvent('question_coach_used', { suggestion: suggestedQuestion });
        setQuestionOrigin('question_coach');
        focusFormWithQuestion(suggestedQuestion);
      });
    });
  }

  function inferTheme(question, answerText) {
    const haystack = `${question || ''} ${answerText || ''}`.toLowerCase();
    for (const theme of AMT_THEMES) {
      if (haystack.includes(theme.toLowerCase())) return theme;
    }

    const themeKeywords = [
      ['Relationships', ['relationship', 'marriage', 'partner', 'dating', 'friendship']],
      ['Boundaries', ['boundary', 'boundaries', 'people pleasing', 'people-pleasing']],
      ['Healing', ['heal', 'healing', 'recover', 'restoration']],
      ['Grief', ['grief', 'loss', 'mourning']],
      ['Fear', ['fear', 'anxiety', 'afraid', 'self-doubt']],
      ['Purpose', ['purpose', 'calling', 'direction']],
      ['Identity', ['identity', 'who am i', 'self image', 'self-image']],
      ['Forgiveness', ['forgive', 'forgiveness', 'resentment']],
      ['Inner peace', ['peace', 'calm', 'stillness', 'inner weather']],
      ['Communication', ['conversation', 'communicate', 'conflict', 'hard talk']],
      ['Empowerment', ['voice', 'speak up', 'confidence', 'empower']],
      ['Transition', ['transition', 'change', 'new season', 'move on']],
      ['Self-worth', ['worthy', 'worth', 'comparison', 'confidence']],
      ['Faith', ['faith', 'god', 'spiritual']],
      ['Courage', ['courage', 'brave', 'challenge', 'challenges', 'strength', 'shy']],
      ['Community', ['community', 'belonging', 'support system']]
    ];

    for (const [theme, keywords] of themeKeywords) {
      if (keywords.some(keyword => haystack.includes(keyword))) return theme;
    }

    return null;
  }

  function extractInsightExcerpt(answerText, theme) {
    const clean = normalizeReflectionText(answerText);
    if (!clean) return '';

    const headlineCandidate = selectReflectionLine(clean, {
      themeKeywords: getThemeReflectionKeywords(theme),
      preferUniversal: true,
      preferShort: true
    }) || buildThemeReflectionFallback(theme);
    return extractReflectionBody(clean, theme, headlineCandidate);
  }

  function extractShareHeadline(insight) {
    const theme = insight.theme || '';
    const themeKeywords = getThemeReflectionKeywords(theme);
    const fallback = buildThemeReflectionFallback(theme);
    const allowSyntheticFallback = (insight.shareSource || '') === 'current_answer' || !(insight.shareSource || '').trim();
    const excerpt = ensureReflectionSentence(insight.excerpt || '');
    const answerHeadline = ensureReflectionSentence(extractCardHeadline(insight.answer || '', theme));
    const answerExcerpt = ensureReflectionSentence(extractInsightExcerpt(insight.answer || '', theme));
    const excerptHeadline = excerpt ? ensureReflectionSentence(extractCardHeadline(excerpt, theme) || excerpt) : '';
    const apiHeadline = (insight.shareable_headline && typeof insight.shareable_headline === 'string')
      ? ensureReflectionSentence(insight.shareable_headline)
      : '';

    const scoreQuestionRelevance = (candidate) => {
      const question = String(insight.question || '').toLowerCase();
      const candidateLower = String(candidate || '').toLowerCase();
      if (!question || !candidateLower) return 0;
      
      const stopwords = new Set([
        'a', 'an', 'and', 'are', 'as', 'at', 'be', 'but', 'by', 'for', 'from', 'has', 'he', 'in',
        'is', 'it', 'its', 'my', 'not', 'of', 'on', 'or', 'that', 'the', 'to', 'was', 'will', 'with'
      ]);
      
      const extractKeyTerms = (text) => {
        return text.split(/\s+/)
          .map(word => word.replace(/[^a-z0-9]/g, '').toLowerCase())
          .filter(word => word.length > 3 && !stopwords.has(word));
      };
      
      const questionTerms = new Set(extractKeyTerms(question));
      const candidateTerms = new Set(extractKeyTerms(candidateLower));
      
      let matches = 0;
      questionTerms.forEach(term => {
        if (candidateTerms.has(term)) matches += 1;
      });
      
      return (matches / Math.max(1, questionTerms.size)) * 4;
    };

    const rawCandidates = [apiHeadline, excerptHeadline, answerHeadline, answerExcerpt, excerpt]
      .filter(Boolean)
      .map(value => ensureReflectionSentence(value))
      .filter(Boolean);

    const uniqueCandidates = [];
    rawCandidates.forEach(candidate => {
      if (!uniqueCandidates.some(existing => areReflectionLinesTooSimilar(existing, candidate))) {
        uniqueCandidates.push(candidate);
      }
    });

    const ranked = uniqueCandidates
      .map(candidate => ({
        text: candidate,
        score: scoreShareHeadlineCandidate(candidate, themeKeywords),
        relevance: scoreQuestionRelevance(candidate)
      }))
      .filter(item => item.text && item.score > -Infinity && !isWeakShareHeadlineCandidate(item.text))
      .sort((a, b) => {
        // Primary: presentation score
        if (Math.abs(a.score - b.score) > 0.5) return b.score - a.score;
        // Tiebreak: question relevance
        return b.relevance - a.relevance;
      });

    if (ranked.length) {
      return ranked[0].text;
    }

    if (!allowSyntheticFallback) {
      return excerpt ||
        selectReflectionLine(joinReflectionTextParts([insight.answer || '', insight.excerpt || '']), {
          themeKeywords,
          preferUniversal: true
        }) ||
        fallback;
    }

    return answerHeadline || answerExcerpt || excerpt || fallback;
  }

  function trimDanglingHeadlineTail(text) {
    let cleaned = String(text || '')
      .replace(/^["'""]+|["'""]+$/g, '')
      .replace(/\s+/g, ' ')
      .trim();

    // Remove incomplete quoted sections (opening quote/paren without closing)
    // Remove from last opening quote/paren to end if not balanced
    const openParenIndex = cleaned.lastIndexOf('(');
    const closeParenIndex = cleaned.lastIndexOf(')');
    if (openParenIndex > closeParenIndex) {
      cleaned = cleaned.substring(0, openParenIndex).trim();
    }
    
    // Check for unbalanced double quotes and truncate at last unmatched opening quote
    const quoteMatches = [...cleaned.matchAll(/["""]/g)];
    if (quoteMatches.length % 2 !== 0) {
      // Find the last opening quote
      const lastQuoteIndex = quoteMatches[quoteMatches.length - 1].index;
      cleaned = cleaned.substring(0, lastQuoteIndex).trim();
    }

    cleaned = cleaned
      .replace(/[,:;]\s*(and|or|but)$/i, '')
      .replace(/\b(and|or|but|because|which|that|about|around|into|with|for|of|on|to)$/i, '')
      .trim()
      .replace(/[,:;]+$/g, '')
      .trim();

    return cleaned;
  }

  function isWeakShareHeadlineCandidate(text) {
    const cleaned = trimDanglingHeadlineTail(text);
    console.log('[isWeakShareHeadlineCandidate] After trimming:', cleaned);
    const lower = cleaned.toLowerCase();
    if (!cleaned) {
      console.log('[isWeakShareHeadlineCandidate] WEAK: Empty after trimming');
      return true;
    }
    if (cleaned.length < 32) {
      console.log('[isWeakShareHeadlineCandidate] WEAK: Too short (<32 chars)');
      return true;
    }
    if (
      lower.startsWith('what likely stayed with you') ||
      lower.startsWith('what stayed with me') ||
      lower.startsWith('what stayed with you') ||
      lower.startsWith('what from today') ||
      lower.startsWith('what keeps returning for me') ||
      lower.startsWith("what is today's question") ||
      lower.startsWith('what needs my attention most') ||
      lower.startsWith('one thing that stood out') ||
      lower.startsWith('here are grounded reflections') ||
      lower.startsWith('i found a few mirror talk moments') ||
      lower.startsWith('the clearest thread is this') ||
      lower.startsWith('one source moment says') ||
      lower.startsWith('in this reflection') ||
      lower.startsWith('this reflection')
    ) {
      console.log('[isWeakShareHeadlineCandidate] WEAK: Generic phrase detected');
      return true;
    }
    console.log('[isWeakShareHeadlineCandidate] STRONG: Passed all checks');
    return false;
  }

  function isFallbackAnswerMeta(meta) {
    const source = String((meta && (meta.answerSource || meta.answer_source)) || '').toLowerCase();
    const status = String((meta && (meta.answerStatus || meta.answer_status)) || '').toLowerCase();
    return source === 'basic_fallback' ||
      source === 'no_match' ||
      status === 'source_moments_only' ||
      status === 'generation_failed' ||
      status === 'needs_refinement';
  }

  function isShareableReflectionText(text) {
    const clean = ensureReflectionSentence(text);
    if (!clean) return false;
    if (isWeakShareHeadlineCandidate(clean)) return false;
    if (/^\d+[.)]\s/.test(clean)) return false;
    if (/\b(here are|i found|source moment|grounded reflections|speak to your question|partial grounding)\b/i.test(clean)) return false;
    return true;
  }

  function formatRelativeTime(timestamp) {
    if (!timestamp) return 'Recently';

    const diffMs = Date.now() - timestamp;
    const minutes = Math.max(1, Math.round(diffMs / 60000));
    if (minutes < 60) return `${minutes} minute${minutes === 1 ? '' : 's'} ago`;

    const hours = Math.round(minutes / 60);
    if (hours < 24) return `${hours} hour${hours === 1 ? '' : 's'} ago`;

    const days = Math.round(hours / 24);
    if (days < 7) return `${days} day${days === 1 ? '' : 's'} ago`;

    return new Date(timestamp).toLocaleDateString();
  }

  function getAnswerUtilitiesRoot() {
    return answerUtilities || responseContainer;
  }

  function setWorkflowActive(action) {
    if (!workflowBar) return;
    if (widgetRoot) {
      ['ask', 'explore', 'save_share', 'progress'].forEach(mode => {
        widgetRoot.classList.toggle(`amt-workflow-mode-${mode}`, mode === action);
      });
    }
    Object.entries(workflowPanels).forEach(([mode, panel]) => {
      if (!panel) return;
      const isActive = mode === action;
      panel.toggleAttribute('hidden', !isActive);
      panel.setAttribute('aria-hidden', String(!isActive));
    });
    workflowBar.querySelectorAll('.amt-workflow-step').forEach(step => {
      const isActive = step.dataset.workflowAction === action;
      step.classList.toggle('amt-workflow-step-active', isActive);
      if (isActive) {
        step.setAttribute('aria-current', 'step');
      } else {
        step.removeAttribute('aria-current');
      }
    });
  }

  function setWorkflowHint(action, hint) {
    if (!workflowBar) return;
    const step = workflowBar.querySelector(`[data-workflow-action="${action}"] .amt-workflow-hint`);
    if (step) step.textContent = hint;
  }

  function setWorkflowNudge(text) {
    if (!workflowNudge || !text) return;
    const textTarget = workflowNudgeText || workflowNudge;
    textTarget.textContent = text;
  }

  function getWorkflowNudge(action, state) {
    const current = state || {};
    if (action === 'explore') {
      if (current.hasContinuation) return 'Continue your reflection here, then choose a follow-up when you want to go deeper.';
      if (current.hasFollowups) return 'Choose a follow-up when you want to keep the reflection close.';
      if (current.hasCitations) return 'Open the referenced episodes when you want to hear where the answer came from.';
      return 'Explore prompts and themes when you want help finding the next honest question.';
    }
    if (action === 'save_share') {
      if (current.hasShareSection) return 'Keep what mattered, email it to yourself, or pass the reflection on.';
      if (current.hasReflectPrompt) return 'Pause here to write what landed, then keep or pass on what mattered.';
      if (current.insightCount > 0) return 'Your saved insights stay here, ready to revisit or turn into a card.';
      if (current.hasLastSession) return 'Your last reflection is ready to revisit, save, or share when you return.';
      return 'After an answer, this becomes the place to save, email, or share the reflection.';
    }
    if (action === 'progress') {
      if (current.hasProgress) return 'Your Momentum, badges, Reflection Pass, and weekly recap live here.';
      return 'Your reflection rhythm begins here, even before the first question today.';
    }
    if (current.hasAnswer) {
      return 'Explore the thread when you want to go deeper, then keep or share what mattered.';
    }
    return 'Move through the path at your pace: ask, explore, keep what matters, and build a rhythm.';
  }

  function getWorkflowNudgeActions(action, state) {
    const current = state || {};
    const hasSomethingToKeep = !!(current.hasAnswer || current.hasLastSession || current.insightCount > 0);

    if (action === 'explore') {
      return hasSomethingToKeep
        ? [
            { action: 'save_share', label: 'Keep or share', primary: true },
            { action: 'ask', label: 'Back to answer' },
            { action: 'progress', label: 'View rhythm' }
          ]
        : [
            { action: 'ask', label: 'Ask a question', primary: true },
            { action: 'progress', label: 'View rhythm' }
          ];
    }

    if (action === 'save_share') {
      return [
        { action: 'progress', label: 'View rhythm', primary: true },
        { action: 'explore', label: 'Explore next' },
        { action: 'ask', label: current.hasAnswer ? 'Ask another' : 'Ask first' }
      ];
    }

    if (action === 'progress') {
      return current.hasAnswer
        ? [
            { action: 'save_share', label: 'Keep or share', primary: true },
            { action: 'explore', label: 'Explore next' },
            { action: 'ask', label: 'Ask another' }
          ]
        : hasSomethingToKeep
        ? [
            { action: 'save_share', label: 'Keep or share', primary: true },
            { action: 'explore', label: 'Explore prompts' },
            { action: 'ask', label: 'Ask today' }
          ]
        : [
            { action: 'ask', label: 'Ask today', primary: true },
            { action: 'explore', label: 'Explore prompts' }
          ];
    }

    if (current.hasAnswer) {
      return [
        { action: 'explore', label: 'Explore next', primary: true },
        { action: 'save_share', label: 'Keep or share' },
        { action: 'progress', label: 'View rhythm' }
      ];
    }

    if (hasSomethingToKeep) {
      return [
        { action: 'save_share', label: 'Keep or share', primary: true },
        { action: 'explore', label: 'Explore prompts' },
        { action: 'progress', label: 'View rhythm' }
      ];
    }

    return [
      { action: 'explore', label: 'Explore prompts', primary: true },
      { action: 'save_share', label: 'Keep or share' },
      { action: 'progress', label: 'View rhythm' }
    ];
  }

  function renderWorkflowNudgeActions(action, state) {
    if (!workflowNudgeActions) return;
    const actions = getWorkflowNudgeActions(action, state);
    workflowNudgeActions.innerHTML = actions.map(item => `
      <button type="button" class="amt-workflow-nudge-btn${item.primary ? ' amt-workflow-nudge-btn-primary' : ''}" data-workflow-nudge-action="${item.action}">
        ${escapeHtml(item.label)}
      </button>
    `).join('');
    workflowNudgeActions.querySelectorAll('[data-workflow-nudge-action]').forEach(btn => {
      btn.addEventListener('click', () => {
        runWorkflowAction(btn.dataset.workflowNudgeAction, { persist: true, scroll: true });
      });
    });
  }

  function getWorkflowState() {
    const answerText = normalizeReflectionText(output ? (output.innerText || output.textContent || '') : '');
    const hasAnswer = answerText.length > 24 && responseContainer && responseContainer.style.display !== 'none';
    const shareSection = document.getElementById('amt-share-section');
    const insights = typeof loadInsights === 'function' ? loadInsights() : [];
    const stats = typeof loadStats === 'function' ? loadStats() : null;
    const hasExplore = !!(exploreExpander && exploreExpander.style.display !== 'none');
    const hasContinuation = !!(continuationStrip && continuationStrip.style.display !== 'none');
    const hasFollowups = !!(followupsContainer && followupsContainer.style.display !== 'none');
    const hasCitations = !!(citationsContainer && citationsContainer.style.display !== 'none');
    const hasReflectPrompt = !!(document.getElementById('amt-reflect-section')?.style.display !== 'none');
    const hasLastSession = !!(loadLastSession && loadLastSession());
    const hasProgress = !!(stats && (stats.totalQuestions > 0 || stats.currentStreak > 0 || stats.earnedBadges.size > 0));
    return {
      hasAnswer,
      hasShareSection: !!shareSection,
      hasExplore,
      hasContinuation,
      hasFollowups,
      hasCitations,
      hasReflectPrompt,
      hasProgress,
      hasLastSession,
      insightCount: insights.length
    };
  }

  function getActiveWorkflowPanel(action) {
    return workflowPanels[action] || workflowPanels.ask || workflowPanelsRoot || widgetRoot;
  }

  function scrollToWorkflowPanel(action) {
    const target = getActiveWorkflowPanel(action);
    if (!target) return;
    target.scrollIntoView({ behavior: 'smooth', block: 'start' });
  }

  function renderSaveShareHub(state) {
    if (!saveShareHub) return;
    const current = state || getWorkflowState();
    const lastSession = loadLastSession ? loadLastSession() : null;
    const insights = typeof loadInsights === 'function' ? loadInsights().map(normalizeInsightRecord) : [];
    const answerText = normalizeReflectionText(output ? (output.innerText || output.textContent || '') : '');
    const hasCurrentAnswer = current.hasAnswer && answerText.length > 24;
    const lastQuestion = lastSession && lastSession.question ? String(lastSession.question) : '';
    const lastTheme = lastSession && lastSession.theme ? String(lastSession.theme) : inferTheme(lastQuestion, lastSession && lastSession.answer ? lastSession.answer : '') || 'Reflection';
    const lastExcerpt = lastSession
      ? ensureReflectionSentence(lastSession.excerpt || extractInsightExcerpt(lastSession.answer || '', lastTheme) || '')
      : '';
    const referralEligible = shouldShowReferralCta() && (hasCurrentAnswer || (lastSession && lastQuestion));

    const referralQuestion = hasCurrentAnswer
      ? String((input && input.value) || lastQuestion || '').trim()
      : lastQuestion;
    const referralTheme = hasCurrentAnswer
      ? (window._amtLastTheme || inferTheme(referralQuestion, answerText) || 'Reflection')
      : lastTheme;

    const referralBlock = referralEligible ? `
      <div class="amt-referral-cta">
        <p class="amt-referral-cta-text">Invite one person who asked for support, not a mass blast.</p>
        <div class="amt-referral-cta-actions">
          <button type="button" class="amt-save-share-hub-btn" data-save-share-action="referral_share">Invite one friend</button>
          <button type="button" class="amt-save-share-hub-btn amt-save-share-hub-btn-secondary" data-save-share-action="referral_dismiss">Not now</button>
        </div>
      </div>
    ` : '';

    if (referralEligible && markReferralCtaShownOncePerSession()) {
      emitProductEvent('referral_cta_shown', {
        context: hasCurrentAnswer ? 'current_answer' : 'last_session',
        theme: referralTheme || null,
      });
    }

    if (hasCurrentAnswer) {
      const currentQuestion = input ? (input.value || 'your reflection') : 'your reflection';
      const currentTheme = window._amtLastTheme || inferTheme(currentQuestion, answerText) || 'Reflection';
      
      saveShareHub.innerHTML = `
        <div class="amt-save-share-hub-card">
          <span class="amt-save-share-kicker">This reflection is ready to keep.</span>
          <h3>Choose what should happen next.</h3>
          <p>Write a private note, save the insight, email it to yourself, or pass on a card when the line is complete enough to share.</p>
          ${referralBlock}
        </div>
      `;
    } else if (lastSession && lastQuestion) {
      saveShareHub.innerHTML = `
        <div class="amt-save-share-hub-card">
          <span class="amt-save-share-kicker">${escapeHtml(lastTheme || 'Last reflection')}</span>
          <h3>Return to your last reflection.</h3>
          <p class="amt-save-share-question">${escapeHtml(lastQuestion)}</p>
          ${lastExcerpt ? `<p class="amt-save-share-excerpt">“${escapeHtml(lastExcerpt)}”</p>` : ''}
          <div class="amt-save-share-hub-actions">
            <button type="button" class="amt-save-share-hub-btn" data-save-share-action="revisit">Revisit this reflection</button>
            <button type="button" class="amt-save-share-hub-btn amt-save-share-hub-btn-secondary" data-save-share-action="insights">Open saved insights</button>
          </div>
          ${referralBlock}
        </div>
      `;
    } else {
      saveShareHub.innerHTML = `
        <div class="amt-save-share-hub-card">
          <span class="amt-save-share-kicker">Nothing to keep yet.</span>
          <h3>Ask first, then keep what matters.</h3>
          <p>After your first answer, this section becomes your calm place for private notes, saved insights, email, cards, and invitations.</p>
          <div class="amt-save-share-hub-actions">
            <button type="button" class="amt-save-share-hub-btn" data-save-share-action="ask">Ask a reflection</button>
            ${insights.length ? '<button type="button" class="amt-save-share-hub-btn amt-save-share-hub-btn-secondary" data-save-share-action="insights">Open saved insights</button>' : ''}
          </div>
        </div>
      `;
    }

    saveShareHub.querySelectorAll('[data-save-share-action]').forEach(btn => {
      btn.addEventListener('click', async () => {
        const action = btn.dataset.saveShareAction;
        if (action === 'revisit' && lastQuestion) {
          setQuestionOrigin('saved_reflection_revisit', { theme: lastTheme || null });
          submitQuestionFromPrompt(lastQuestion);
          return;
        }
        if (action === 'insights') {
          renderInsightsPanel();
          return;
        }
        if (action === 'referral_dismiss') {
          dismissReferralCta(3);
          emitProductEvent('referral_cta_dismissed', {
            context: hasCurrentAnswer ? 'current_answer' : 'last_session',
          });
          renderSaveShareHub();
          return;
        }
        if (action === 'referral_share') {
          const payload = buildReferralInvitePayload(referralQuestion, referralTheme);
          emitProductEvent('referral_cta_used', {
            context: hasCurrentAnswer ? 'current_answer' : 'last_session',
            guardrail: 'single_friend_only',
            theme: referralTheme || null,
          });

          try {
            if (navigator.share) {
              await navigator.share({ title: payload.title, text: payload.text, url: payload.url });
              emitProductEvent('share_cta_used', { action: 'invite_friend_save_share', method: 'native_share' });
              return;
            }
          } catch (e) {
            if (e.name !== 'AbortError') warn('Referral share failed:', e);
          }

          try {
            await navigator.clipboard.writeText(payload.text);
            emitProductEvent('share_cta_used', { action: 'invite_friend_save_share', method: 'copy_link' });
            const originalText = btn.textContent;
            btn.textContent = 'Invite link copied';
            setTimeout(() => { btn.textContent = originalText; }, 2200);
            return;
          } catch (e) {
            warn('Referral copy failed:', e);
          }
          return;
        }
        runWorkflowAction('ask', { persist: true, scroll: true });
      });
    });
  }

  function getSavedWorkflowAction() {
    try {
      const action = sessionStorage.getItem(WORKFLOW_SESSION_KEY);
      return ['ask', 'explore', 'save_share', 'progress'].includes(action) ? action : '';
    } catch (e) {
      return '';
    }
  }

  function persistWorkflowAction(action) {
    try {
      if (action) sessionStorage.setItem(WORKFLOW_SESSION_KEY, action);
    } catch (e) {}
  }

  function isWorkflowActionAvailable(action, state) {
    if (action === 'ask') return true;
    if (action === 'explore') return true;
    if (action === 'save_share') return true;
    if (action === 'progress') return true;
    return false;
  }

  function updateWorkflowBarState() {
    if (!workflowBar) return;
    const state = getWorkflowState();
    const savedAction = getSavedWorkflowAction();

    workflowBar.classList.toggle('amt-workflow-has-answer', !!state.hasAnswer);
    workflowBar.querySelector('[data-workflow-action="explore"]')?.classList.toggle('amt-workflow-step-available', isWorkflowActionAvailable('explore', state));
    workflowBar.querySelector('[data-workflow-action="save_share"]')?.classList.toggle('amt-workflow-step-available', isWorkflowActionAvailable('save_share', state));
    workflowBar.querySelector('[data-workflow-action="progress"]')?.classList.toggle('amt-workflow-step-available', isWorkflowActionAvailable('progress', state));

    setWorkflowHint('explore', state.hasContinuation ? 'Continue' : (state.hasFollowups ? 'Follow-up' : (state.hasAnswer ? 'Next' : 'Prompts')));
    setWorkflowHint('save_share', state.hasShareSection ? 'Ready' : (state.insightCount ? `${state.insightCount} kept` : (state.hasAnswer ? 'Keep it' : 'Ready')));
    const progressStats = typeof loadStats === 'function' ? loadStats() : null;
    setWorkflowHint('progress', progressStats && progressStats.totalQuestions > 0 ? 'Momentum' : 'Recap');

    renderSaveShareHub(state);

    const activeAction = savedAction && isWorkflowActionAvailable(savedAction, state) ? savedAction : 'ask';
    setWorkflowActive(activeAction);
    setWorkflowNudge(getWorkflowNudge(activeAction, state));
    renderWorkflowNudgeActions(activeAction, state);
  }

  function scrollToElementSafely(element, block) {
    if (!element) return;
    element.scrollIntoView({ behavior: 'smooth', block: block || 'center' });
  }

  function runWorkflowAction(action, options) {
    const opts = options || {};
    const shouldPersist = opts.persist !== false;
    const shouldScroll = opts.scroll !== false;
    const state = getWorkflowState();

    if (shouldPersist) persistWorkflowAction(action);
    setWorkflowActive(action);
    setWorkflowNudge(getWorkflowNudge(action, state));
    renderWorkflowNudgeActions(action, state);

    if (action === 'ask') {
      if (state.hasAnswer && responseContainer && responseContainer.style.display !== 'none') {
        if (shouldScroll) scrollToWorkflowPanel('ask');
        return;
      }
      if (shouldScroll) focusFormWithQuestion(input ? input.value : '');
      if (shouldScroll && input) input.focus();
      return;
    }

    if (action === 'explore') {
      restoreExploreContent();
      collapseExploreExpander();
      if (shouldScroll) {
        // Scroll after content is restored
        setTimeout(() => scrollToWorkflowPanel('explore'), 50);
      }
      return;
    }

    if (action === 'save_share') {
      renderSaveShareHub(state);
      const shareSection = document.getElementById('amt-share-section');
      const insightsBtn = document.getElementById('amt-insights-btn');
      const insights = typeof loadInsights === 'function' ? loadInsights() : [];
      const emailSection = document.getElementById('amt-email-section');
      const saveInsightSection = document.getElementById('amt-save-insight-section');
      const reflectSection = document.getElementById('amt-reflect-section');
      
      // Scroll to the save/share panel first, then highlight specific section
      if (shouldScroll) {
        setTimeout(() => scrollToWorkflowPanel('save_share'), 50);
      }
      
      if (shareSection) {
        shareSection.classList.add('amt-workflow-focus-pulse');
        setTimeout(() => shareSection.classList.remove('amt-workflow-focus-pulse'), 900);
        return;
      }
      if (saveInsightSection || emailSection) {
        return;
      }
      if (reflectSection && reflectSection.style.display !== 'none') {
        return;
      }
      if (insights.length && insightsBtn) {
        renderInsightsPanel();
        return;
      }
      return;
    }

    if (action === 'progress') {
      const stats = loadStats();
      renderStatsBar(stats);
      renderBadgeShelf(stats);
      renderMomentumCard(stats);
      renderWeeklyRecap();
      renderStreakRevivalCard(stats);
      const shelf = document.getElementById('amt-badge-shelf');
      const momentum = document.getElementById('amt-momentum-card');
      const recap = document.getElementById('amt-weekly-recap-card');
      const revival = document.getElementById('amt-streak-revival-card');
      const badgesBtn = document.getElementById('amt-badges-btn');
      if (shelf) shelf.style.display = '';
      if (badgesBtn) badgesBtn.setAttribute('aria-expanded', 'true');
      
      // Scroll after all rhythm content is rendered
      if (shouldScroll) {
        setTimeout(() => scrollToWorkflowPanel('progress'), 50);
      }
    }
  }

  function initWorkflowBar() {
    if (!workflowBar) return;
    workflowBar.querySelectorAll('.amt-workflow-step').forEach(step => {
      step.addEventListener('click', () => {
        runWorkflowAction(step.dataset.workflowAction, { persist: true, scroll: true });
      });
    });

    const workflowObserver = new MutationObserver(() => updateWorkflowBarState());
    if (output) workflowObserver.observe(output, { childList: true, subtree: true, characterData: true, attributes: true });
    if (answerUtilities) workflowObserver.observe(answerUtilities, { childList: true, subtree: true });
    if (exploreExpander) workflowObserver.observe(exploreExpander, { attributes: true, attributeFilter: ['style', 'class'] });
    updateWorkflowBarState();
    setTimeout(() => {
      const savedAction = getSavedWorkflowAction();
      const state = getWorkflowState();
      if (savedAction && savedAction !== 'ask' && isWorkflowActionAvailable(savedAction, state)) {
        runWorkflowAction(savedAction, { persist: false, scroll: false });
      }
    }, 150);
  }

  function updateCitationTrustNote(citationsList) {
    if (!citationTrustNote) return;
    const meta = getCitationSupportMeta(citationsList);

    if (!meta.hasReferences) {
      emitProductEvent('low_match_shown', { citations: 0 });
      citationTrustNote.innerHTML = `
        <div class="amt-citation-trust-copy amt-citation-trust-copy-soft">
          <span class="amt-citation-trust-level amt-citation-trust-level-soft">${escapeHtml(meta.level)}</span>
          <strong>${escapeHtml(meta.trustLead)}</strong>
          <span>${escapeHtml(meta.trustDetail)}</span>
        </div>
      `;
      citationTrustNote.style.display = '';
      return;
    }

    citationTrustNote.innerHTML = `
      <div class="amt-citation-trust-copy">
        <span class="amt-citation-trust-level">${escapeHtml(meta.level)}</span>
        <strong>${escapeHtml(meta.trustLead)}</strong>
        <span>${escapeHtml(meta.trustDetail)}</span>
      </div>
    `;
    citationTrustNote.style.display = '';
  }

  function renderAnswerContext(question, answerText, citationsList, answerMeta) {
    if (!answerContext) return;

    const theme = inferTheme(question, answerText);
    const meta = getCitationSupportMeta(citationsList);
    const fallbackAnswer = isFallbackAnswerMeta(answerMeta);
    const lowMatch = !meta.hasReferences || fallbackAnswer;
    const contextKicker = fallbackAnswer ? 'Source moments only' : meta.contextKicker;
    const contextSummary = fallbackAnswer
      ? 'The app found related Mirror Talk material, but it did not complete the premium reflection answer.'
      : meta.contextSummary;
    const contextDetail = fallbackAnswer
      ? 'Use these source moments for listening or refining the question. Reflection cards are held back until the answer is complete enough to share.'
      : meta.contextDetail;
    const supportPill = fallbackAnswer ? 'Refine before sharing' : meta.supportPill;
    const sourceCount = Array.isArray(citationsList) ? citationsList.length : 0;
    const trustSummary = fallbackAnswer
      ? 'Source moments only'
      : (sourceCount > 0 ? `${sourceCount} source moment${sourceCount === 1 ? '' : 's'}` : 'Light source grounding');
    const trustDetails = fallbackAnswer
      ? [
          'The app found related source moments, but full premium reflection generation did not complete.',
          sourceCount > 0 ? `There are ${sourceCount} source moment${sourceCount === 1 ? '' : 's'} available below.` : 'No direct source moment was detected for this question yet.',
          'Refining the question usually restores a complete reflection answer.',
        ]
      : [
          sourceCount > 0 ? `Grounded in ${sourceCount} source moment${sourceCount === 1 ? '' : 's'}.` : 'Grounding is lighter than usual right now.',
          `Support level: ${meta.level}.`,
          'Theme and next-step guidance are inferred from your question and response language.',
        ];

    answerContext.innerHTML = `
      <div class="amt-answer-context-copy${lowMatch ? ' amt-answer-context-copy-soft' : ''}">
        <span class="amt-answer-context-kicker">${escapeHtml(contextKicker)}</span>
        <p class="amt-answer-context-summary">${escapeHtml(contextSummary)}</p>
        <p class="amt-answer-context-detail">${escapeHtml(contextDetail)}</p>
      </div>
      <button type="button" class="amt-answer-trust-toggle" aria-expanded="false">Why this answer? ${escapeHtml(trustSummary)}</button>
      <div class="amt-answer-trust-capsule" style="display:none;" aria-hidden="true">
        <ul>
          ${trustDetails.map(item => `<li>${escapeHtml(item)}</li>`).join('')}
        </ul>
      </div>
      <div class="amt-answer-context-pills">
        ${theme ? `<span class="amt-answer-pill">${escapeHtml(theme)}</span>` : ''}
        <span class="amt-answer-pill">${escapeHtml(supportPill)}</span>
      </div>
    `;

    const trustToggle = answerContext.querySelector('.amt-answer-trust-toggle');
    const trustCapsule = answerContext.querySelector('.amt-answer-trust-capsule');
    if (trustToggle && trustCapsule) {
      trustToggle.addEventListener('click', () => {
        const isExpanded = trustToggle.getAttribute('aria-expanded') === 'true';
        trustToggle.setAttribute('aria-expanded', isExpanded ? 'false' : 'true');
        trustCapsule.style.display = isExpanded ? 'none' : '';
        trustCapsule.setAttribute('aria-hidden', isExpanded ? 'true' : 'false');
        if (!isExpanded) {
          emitProductEvent('trust_capsule_opened', {
            fallback_mode: fallbackAnswer,
            source_count: sourceCount,
            support_level: meta.level,
          });
        }
      });
    }

    answerContext.style.display = '';
  }

  function saveLastSession(question, answer, themeHint) {
    const theme = themeHint || inferTheme(question, answer) || '';
    const excerpt = extractInsightExcerpt(answer, theme);
    saveLastSessionRecord({
      question,
      answer: answer.substring(0, 2000),
      excerpt,
      theme,
      time: Date.now(),
    });
  }

  function finalizeAnswerPresentation(question, answerText, citationsList, themeHint, answerMeta) {
    const theme = themeHint || inferTheme(question, answerText);
    saveLastSession(question, answerText, theme);
    renderAnswerContext(question, answerText, citationsList, answerMeta);
    if (!hasStrongSupport(citationsList) || isFallbackAnswerMeta(answerMeta)) {
      ensureLowMatchFollowUps(question, theme);
    }
    renderContinuationStrip(question, answerText, citationsList, theme, answerMeta);
    renderJourneyCard();
  }

  function renderJourneyCard() {
    if (!journeyCard) return;

    const lastSession = loadLastSession() || {};
    const lastQ = lastSession.question || '';
    const lastA = lastSession.answer || lastSession.excerpt || '';
    const lastTheme = lastSession.theme || '';
    const lastTime = parseInt(lastSession.time || '0', 10);

    const stats = loadStats();
    const hasHistory = !!lastQ || stats.totalQuestions > 0;
    if (!hasHistory) {
      journeyCard.innerHTML = '';
      journeyCard.style.display = 'none';
      return;
    }

    const exploredThemes = stats.themesExplored || new Set();
    const unexploredThemes = AMT_THEMES.filter(theme => !exploredThemes.has(theme));
    const recentExploreThemes = loadRecentThemeHistory(RECENT_EXPLORE_THEMES_KEY);
    const nextThemeCandidates = [
      ...unexploredThemes,
      ...AMT_THEMES.filter(theme => theme !== lastTheme),
    ].filter(Boolean).filter(theme => theme !== lastTheme || unexploredThemes.length === 0);
    const nextTheme = chooseRotatingTheme(nextThemeCandidates, lastTheme || AMT_THEMES[0], RECENT_EXPLORE_THEMES_KEY);
    const continueQuestion = lastQ || getThemeStarter(lastTheme || nextTheme);
    const continueLabel = lastQ ? 'Continue where you left off' : 'Pick up your reflection';
    const continueExcerpt = extractInsightExcerpt(lastA);
    const nextPrompt = getThemeStarter(nextTheme);
    const continuityLine = lastTheme
      ? `Last time you explored ${lastTheme}.`
      : `You have explored ${stats.themesExplored.size} theme${stats.themesExplored.size === 1 ? '' : 's'} so far.`;
    const timeLine = lastTime ? `Last visit ${formatRelativeTime(lastTime)}.` : '';
    const varietyLine = recentExploreThemes.includes(nextTheme)
      ? 'A different angle may open something new.'
      : `Next up: ${nextTheme}.`;

    journeyCard.innerHTML = `
      <div class="amt-journey-card-inner">
        <div class="amt-journey-card-copy">
          <span class="amt-journey-kicker">Continue your reflection</span>
          <h3 class="amt-journey-title">${escapeHtml(continueLabel)}</h3>
          <p class="amt-journey-text">${escapeHtml(continuityLine)} ${escapeHtml(timeLine)} ${escapeHtml(varietyLine)}</p>
          ${continueExcerpt ? `<p class="amt-journey-quote">“${escapeHtml(continueExcerpt)}”</p>` : ''}
        </div>
        <div class="amt-journey-actions">
          <button type="button" class="amt-journey-btn amt-journey-btn-primary" data-q="${escapeHtml(continueQuestion)}">${escapeHtml(truncateText(continueQuestion, 82))}</button>
          <button type="button" class="amt-journey-btn amt-journey-btn-secondary" data-q="${escapeHtml(nextPrompt)}">Explore next: ${escapeHtml(nextTheme)}</button>
        </div>
      </div>
    `;
    journeyCard.style.display = '';

    journeyCard.querySelectorAll('.amt-journey-btn').forEach(btn => {
      btn.addEventListener('click', () => {
        setQuestionOrigin('continue_reflection', { theme: btn === journeyCard.querySelector('.amt-journey-btn-secondary') ? nextTheme : lastTheme || null });
        submitQuestionFromPrompt(btn.dataset.q || '');
      });
    });
  }

  function showRelatedQuestions(qaLogId) {
    // Remove previous section if exists
    const existing = document.getElementById('amt-related-section');
    if (existing) existing.remove();
    if (!qaLogId) return;

    fetch(`${API_BASE}/api/related-questions?qa_log_id=${qaLogId}`)
      .then(r => r.json())
      .then(data => {
        const questions = data.questions || [];
        if (questions.length === 0) return;

        const section = document.createElement('div');
        section.id = 'amt-related-section';
        section.className = 'amt-related-section';

        const label = document.createElement('div');
        label.className = 'amt-related-label';
        label.textContent = 'Others also wondered…';
        section.appendChild(label);

        const list = document.createElement('div');
        list.className = 'amt-related-list';
        questions.forEach(q => {
          const btn = document.createElement('button');
          btn.type = 'button';
          btn.className = 'amt-related-btn';
          btn.textContent = q;  // textContent is XSS-safe
          btn.addEventListener('click', () => {
            input.value = q;
            input.focus();
            form.dispatchEvent(new Event('submit', { cancelable: true }));
          });
          list.appendChild(btn);
        });
        section.appendChild(list);
        responseContainer.appendChild(section);
      })
      .catch(() => {}); // silently fail
  }

  function openStrongestReference() {
    if (!citationsContainer || citationsContainer.style.display === 'none') return;
    emitProductEvent('continuation_action_used', { action: 'strongest_reference_opened' });
    citationsContainer.scrollIntoView({ behavior: 'smooth', block: 'center' });
    const previewBtn = citationsContainer.querySelector('.citation-preview-btn');
    if (previewBtn) {
      setTimeout(() => previewBtn.click(), 220);
      return;
    }
    const citationLink = citationsContainer.querySelector('.citation-link');
    if (citationLink) {
      setTimeout(() => citationLink.click(), 220);
    }
  }

  function renderContinuationStrip(question, answerText, citationsList, themeHint, answerMeta) {
    if (!continuationStrip) return;

    const activeTheme = themeHint || inferTheme(question, answerText) || 'Growth';
    const lastSession = loadLastSession() || {};
    const stats = loadStats();
    const exploredThemes = Array.from((stats && stats.themesExplored) || []);
    const themeCandidates = [
      lastSession.theme,
      ...exploredThemes,
      ...AMT_THEMES,
    ].filter(Boolean);
    const nextTheme = themeCandidates.find(theme => theme !== activeTheme) || activeTheme;
    const deeperQuestion = `Go deeper on ${activeTheme.toLowerCase()}: ${getThemeStarter(activeTheme)}`;
    const tomorrowQuestion = getThemeStarter(nextTheme);
    const meta = getCitationSupportMeta(citationsList);
    const fallbackAnswer = isFallbackAnswerMeta(answerMeta);
    const hasReferences = meta.hasReferences && !fallbackAnswer;
    const stripText = fallbackAnswer
      ? 'The source material is present, but the answer needs one more pass before it should become a saved or shared reflection.'
      : (hasReferences ? 'Go deeper, verify the strongest moment, or carry a fresh question into tomorrow.' : 'Refine the question, recover a stronger match, or carry a clearer theme into tomorrow.');

    continuationStrip.innerHTML = `
      <div class="amt-continuation-strip-inner">
        <div class="amt-continuation-strip-copy">
          <span class="amt-continuation-kicker">Keep the reflection moving</span>
          <p class="amt-continuation-text">${escapeHtml(stripText)}</p>
        </div>
        <div class="amt-continuation-actions">
          <button type="button" class="amt-continuation-btn amt-continuation-btn-primary" data-action="deeper">${hasReferences ? 'Go deeper on this' : 'Refine this question'}</button>
          ${hasReferences ? '<button type="button" class="amt-continuation-btn" data-action="reference">Listen to the strongest moment</button>' : ''}
          <button type="button" class="amt-continuation-btn" data-action="tomorrow">Come back with ${escapeHtml(nextTheme)}</button>
        </div>
      </div>
    `;
    continuationStrip.style.display = '';

    continuationStrip.querySelectorAll('.amt-continuation-btn').forEach(btn => {
      btn.addEventListener('click', () => {
        const action = btn.dataset.action;
        if (action === 'deeper') {
          emitProductEvent('continuation_action_used', { action: hasReferences ? 'go_deeper' : 'refine_question', theme: activeTheme });
          if (!hasReferences) emitProductEvent('low_match_action', { action: 'refine_question', theme: activeTheme });
          submitQuestionFromPrompt(deeperQuestion);
          return;
        }
        if (action === 'reference') {
          openStrongestReference();
          return;
        }
        if (action === 'tomorrow') {
          emitProductEvent('continuation_action_used', { action: 'come_back_with_theme', theme: nextTheme });
          if (!hasReferences) emitProductEvent('low_match_action', { action: 'come_back_with_theme', theme: nextTheme });
          submitQuestionFromPrompt(tomorrowQuestion);
        }
      });
    });
  }

  // ========================================
  // Rating (Thumbs Up / Down)
  // ========================================
  // Share Button
  // ========================================

  function addShareButton(question, answer, themeHint, answerMeta) {
    addShareButtonV2(question, answer, themeHint, answerMeta);
  }

  // ========================================
  // SEO: Inject FAQ Schema.org Markup
  // ========================================

  function injectFAQSchema(question, answer) {
    // Remove previous schema if exists
    const existing = document.getElementById('amt-faq-schema');
    if (existing) existing.remove();

    if (!question || !answer) return;

    const schema = {
      "@context": "https://schema.org",
      "@type": "FAQPage",
      "mainEntity": [{
        "@type": "Question",
        "name": question,
        "acceptedAnswer": {
          "@type": "Answer",
          "text": answer.substring(0, 1000)
        }
      }]
    };

    const script = document.createElement('script');
    script.type = 'application/ld+json';
    script.id = 'amt-faq-schema';
    script.textContent = JSON.stringify(schema);
    document.head.appendChild(script);
  }

  // ========================================
  // Form Submission — try SSE, fallback to /ask
  // ========================================

  form.addEventListener("submit", async (event) => {
    event.preventDefault();

    const question = input.value.trim();
    emitProductEvent('question_submitted', { origin: pendingQuestionOrigin, length: question.length });
    if (!question) {
      showError("Please enter a question.", 'generic');
      return;
    }
    if (question.length < 3) {
      showError("Please enter a more detailed question.", 'generic');
      return;
    }

    if (continuationStrip) {
      continuationStrip.style.display = 'none';
      continuationStrip.innerHTML = '';
    }

    window._amtLastShareableHeadline = '';

    setLoading(true);

    try {
      // Try SSE streaming first
      await askStreaming(question);
    } catch (streamError) {
      warn('SSE streaming failed, falling back to /ask:', streamError);
      responseContainer.classList.remove('amt-streaming');

      // Fallback: non-streaming via WordPress AJAX or direct API
      try {
        const result = await askWithRetry(question);
        if (!result.success) {
          throw new Error(result.data?.message || "The service couldn't process your question.");
        }
        const data = result.data;
        if (!data.answer) throw new Error("No answer received from the service.");
        // Store shareable headline if provided
        window._amtLastShareableHeadline = data.shareable_headline || '';
        showAnswer(data.answer, data.citations || [], data.follow_up_questions || [], {
          answerSource: data.answer_source || data.answerSource || '',
          answerStatus: data.answer_status || data.answerStatus || '',
          fallbackReason: data.fallback_reason || data.fallbackReason || ''
        });
      } catch (fallbackError) {
        console.error("Ask Mirror Talk Error:", fallbackError);
        if (fallbackError.name === 'AbortError') {
          showError("The request took too long. Please try again.");
        } else if (fallbackError.message.includes('Failed to fetch') || fallbackError.message.includes('NetworkError')) {
          showError("Unable to reach the service. Please check your connection and try again.");
        } else {
          showError(fallbackError.message || "Something went wrong. Please try again later.");
        }
      }
    } finally {
      pendingQuestionOrigin = 'typed';
      setLoading(false);
    }
  });

  // ========================================
  // Fallback: Non-streaming requests
  // ========================================

  async function askWithRetry(question, retried = false) {
    if (DEBUG_NO_CACHE) {
      return askDirectAPI(question);
    }

    const body = new URLSearchParams();
    body.set("action", "ask_mirror_talk");
    body.set("nonce", currentNonce);
    body.set("question", question);

    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), 45000);

    const response = await fetch(AskMirrorTalk.ajaxUrl, {
      method: "POST",
      headers: { "Content-Type": "application/x-www-form-urlencoded" },
      body: body.toString(),
      signal: controller.signal
    });

    clearTimeout(timeoutId);

    if (response.status === 403 && !retried) {
      console.warn('403 received — refreshing nonce and retrying…');
      const refreshed = await refreshNonce();
      if (refreshed) {
        return askWithRetry(question, true);
      }
    }

    if (!response.ok) {
      console.warn(`WordPress AJAX failed (${response.status}), falling back to direct API…`);
      return await askDirectAPI(question);
    }

    return await response.json();
  }

  async function askDirectAPI(question) {
    const apiUrl = DEBUG_NO_CACHE ? `${API_BASE}/ask?bypass_cache=1` : `${API_BASE}/ask`;

    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), 45000);

    const response = await fetch(apiUrl, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ question: question }),
      signal: controller.signal
    });

    clearTimeout(timeoutId);

    if (!response.ok) {
      throw new Error(`Server returned ${response.status}`);
    }

    const data = await response.json();
    return { success: true, data: data };
  }

  // ========================================
  // Input interactions
  // ========================================

  input.addEventListener('focus', function() {
    if (!this.value) {
      this.setAttribute('placeholder', 'e.g. How do I deal with grief? What does the Bible say about forgiveness?');
    }
    renderQuestionCoach(this.value);
    
    // Prevent unwanted scroll on mobile when keyboard appears
    if (/iPhone|iPad|iPod|Android/i.test(navigator.userAgent)) {
      // Small delay to let browser handle focus first
      setTimeout(() => {
        // Scroll to ensure input is visible without triggering resize
        this.scrollIntoView({ behavior: 'smooth', block: 'center', inline: 'nearest' });
      }, 100);
    }
  });

  input.addEventListener('blur', function() {
    this.setAttribute('placeholder', 'Ask a question...');
  });

  // Ctrl/Cmd+Enter keyboard shortcut to submit
  input.addEventListener('keydown', function(e) {
    if ((e.ctrlKey || e.metaKey) && e.key === 'Enter') {
      e.preventDefault();
      form.dispatchEvent(new Event('submit', { cancelable: true, bubbles: true }));
    }
  });

  const charCounter = document.getElementById('amt-char-counter');

  input.addEventListener('input', function() {
    if (charCounter) {
      const len = this.value.length;
      charCounter.textContent = `${len} / 500`;
      charCounter.classList.toggle('amt-char-counter-warn', len > 450);
    }

    renderQuestionCoach(this.value);

    if (this.value.trim() === '') {
      output.innerHTML = '';
      citations.innerHTML = '';
      citationsContainer.style.display = 'none';
      responseContainer.style.display = 'none';
      if (answerContext) {
        answerContext.innerHTML = '';
        answerContext.style.display = 'none';
      }
      if (answerUtilities) {
        answerUtilities.innerHTML = '';
      }
      if (citationTrustNote) {
        citationTrustNote.innerHTML = '';
        citationTrustNote.style.display = 'none';
      }
      lastShownCitations = [];
      if (followupsContainer) followupsContainer.style.display = 'none';
      if (suggestionsContainer) suggestionsContainer.style.display = '';
      if (topicsContainer) topicsContainer.style.display = '';
      if (qotdContainer) qotdContainer.style.display = '';
      const oldFeedback = document.getElementById('amt-feedback-section');
      if (oldFeedback) oldFeedback.remove();
      const oldShare = document.getElementById('amt-share-section');
      if (oldShare) oldShare.remove();
      const oldEmail = document.getElementById('amt-email-section');
      if (oldEmail) oldEmail.remove();
      const oldRelated = document.getElementById('amt-related-section');
      if (oldRelated) oldRelated.remove();
      if (questionCoach) {
        questionCoach.innerHTML = '';
        questionCoach.style.display = 'none';
      }
      conversationContext = []; // reset conversation thread
    }
  });

  // ========================================
  // Session Persistence — restore last Q&A for returning visitors
  // ========================================

  // Save session after successful answer — MutationObserver watches output for new content
  const sessionObserver = new MutationObserver(() => {
    const q = input.value.trim();
    const a = output.textContent.trim();
    if (q && a && a.length > 50 && !output.querySelector('.amt-loading')) {
      saveLastSession(q, a);
    }
  });
  sessionObserver.observe(output, { childList: true, subtree: true, characterData: true });

  // ========================================
  // PWA Install Prompt — "Add to Home Screen"
  // ========================================

  let deferredInstallPrompt = null;

  window.addEventListener('beforeinstallprompt', (e) => {
    // Prevent the mini-infobar from appearing on mobile
    e.preventDefault();
    deferredInstallPrompt = e;
    console.log('[PWA] Install prompt captured');
    showInstallBanner();
  });

  function showInstallBanner() {
    // Don't show if already dismissed this session
    try {
      if (sessionStorage.getItem('amt_install_dismissed')) return;
    } catch (e) { /* storage not available */ }

    // Don't show if already installed (standalone mode)
    if (window.matchMedia('(display-mode: standalone)').matches) return;

    // Remove any existing banner
    const existing = document.getElementById('amt-install-banner');
    if (existing) existing.remove();

    const banner = document.createElement('div');
    banner.id = 'amt-install-banner';
    banner.className = 'amt-install-banner';
    banner.innerHTML = `
      <div class="amt-install-inner">
        <div class="amt-install-text">
          <strong>📲 Add Mirror Talk to your home screen</strong>
          <span>Instant access, no app store needed</span>
        </div>
        <div class="amt-install-actions">
          <button class="amt-install-btn" type="button">Install</button>
          <button class="amt-install-dismiss" type="button" aria-label="Dismiss">✕</button>
        </div>
      </div>
    `;

    // Insert at the top of the widget
    const widget = document.querySelector('.ask-mirror-talk');
    if (widget) {
      widget.insertBefore(banner, widget.firstChild);
    } else {
      document.body.appendChild(banner);
    }

    banner.querySelector('.amt-install-btn').addEventListener('click', async () => {
      if (!deferredInstallPrompt) return;
      deferredInstallPrompt.prompt();
      const result = await deferredInstallPrompt.userChoice;
      console.log('[PWA] User choice:', result.outcome);
      deferredInstallPrompt = null;
      banner.remove();
    });

    banner.querySelector('.amt-install-dismiss').addEventListener('click', () => {
      banner.classList.add('amt-install-hiding');
      setTimeout(() => banner.remove(), 300);
      try { sessionStorage.setItem('amt_install_dismissed', '1'); } catch (e) {}
    });

    // Auto-dismiss after 15 seconds to avoid annoyance
    setTimeout(() => {
      if (banner.parentNode) {
        banner.classList.add('amt-install-hiding');
        setTimeout(() => banner.remove(), 300);
      }
    }, 15000);
  }

  // Listen for successful install
  window.addEventListener('appinstalled', () => {
    log('[PWA] App installed successfully');
    deferredInstallPrompt = null;
    const banner = document.getElementById('amt-install-banner');
    if (banner) banner.remove();

    // Mark onboarding as complete immediately to prevent double-show on reload
    try { 
      localStorage.setItem('amt_onboarded', '1');
      localStorage.removeItem('amt_onboarding_started');
    } catch (e) {}

    // After install, prompt for notifications after a short delay
    setTimeout(() => showNotificationOptIn(), 2000);
  });

  // ── iOS install hint ──
  // Safari doesn't fire 'beforeinstallprompt', so show a manual instruction banner.
  // Other iOS browsers (Edge, Chrome, Firefox) can't install PWAs at all — guide them to Safari.
  (function showIOSInstallHint() {
    const isIOS = /iP(hone|ad|od)/.test(navigator.userAgent) && !window.MSStream;
    const isSafari = /Safari/.test(navigator.userAgent) && !/CriOS|FxiOS|OPiOS|EdgiOS/.test(navigator.userAgent);
    const isStandalone = window.matchMedia('(display-mode: standalone)').matches ||
                         window.navigator.standalone === true;

    if (!isIOS || isStandalone) return;

    // Non-Safari iOS browser (Edge, Chrome, Firefox on iOS): show a switch-to-Safari nudge.
    if (!isSafari) {
      try {
        if (sessionStorage.getItem('amt_install_dismissed')) return;
        if (localStorage.getItem('amt_ios_install_dismissed')) return;
      } catch (e) {}
      setTimeout(() => {
        const widget = document.querySelector('.ask-mirror-talk');
        if (!widget) return;
        const existing = document.getElementById('amt-install-banner');
        if (existing) return; // don't stack on top of another banner
        const banner = document.createElement('div');
        banner.id = 'amt-install-banner';
        banner.className = 'amt-install-banner amt-ios-install';
        banner.innerHTML = `
          <div class="amt-install-inner">
            <div class="amt-install-text">
              <strong>📲 Install Mirror Talk for the best experience</strong>
              <span>Open this page in <strong>Safari</strong> to add it to your home screen and enable notifications — your current browser doesn't support PWA installation on iOS.</span>
            </div>
            <div class="amt-install-actions">
              <button class="amt-install-dismiss" type="button" aria-label="Dismiss">✕</button>
            </div>
          </div>
        `;
        widget.insertBefore(banner, widget.firstChild);
        banner.querySelector('.amt-install-dismiss').addEventListener('click', () => {
          banner.classList.add('amt-install-hiding');
          setTimeout(() => banner.remove(), 300);
          try {
            sessionStorage.setItem('amt_install_dismissed', '1');
            localStorage.setItem('amt_ios_install_dismissed', '1');
          } catch (e) {}
        });
        setTimeout(() => {
          if (banner.parentNode) {
            banner.classList.add('amt-install-hiding');
            setTimeout(() => banner.remove(), 300);
          }
        }, 20000);
      }, 3000);
      return; // don't fall through to the Safari instructions
    }

    // Don't show if dismissed
    try {
      if (sessionStorage.getItem('amt_install_dismissed')) return;
      if (localStorage.getItem('amt_ios_install_dismissed')) return;
    } catch (e) {}

    // Show after a short delay
    setTimeout(() => {
      const widget = document.querySelector('.ask-mirror-talk');
      if (!widget) return;

      const banner = document.createElement('div');
      banner.id = 'amt-install-banner';
      banner.className = 'amt-install-banner amt-ios-install';
      banner.innerHTML = `
        <div class="amt-install-inner">
          <div class="amt-install-text">
            <strong>📲 Add Mirror Talk to your home screen</strong>
            <span>Tap <strong>Share</strong> <span style="font-size:1.2em">⎋</span> then <strong>"Add to Home Screen"</strong></span>
          </div>
          <div class="amt-install-actions">
            <button class="amt-install-dismiss" type="button" aria-label="Dismiss">✕</button>
          </div>
        </div>
      `;
      widget.insertBefore(banner, widget.firstChild);

      banner.querySelector('.amt-install-dismiss').addEventListener('click', () => {
        banner.classList.add('amt-install-hiding');
        setTimeout(() => banner.remove(), 300);
        try {
          sessionStorage.setItem('amt_install_dismissed', '1');
          localStorage.setItem('amt_ios_install_dismissed', '1');
        } catch (e) {}
      });

      // Auto-dismiss after 20 seconds
      setTimeout(() => {
        if (banner.parentNode) {
          banner.classList.add('amt-install-hiding');
          setTimeout(() => banner.remove(), 300);
        }
      }, 20000);
    }, 3000);
  })();

  // ========================================
  // Push Notifications — Daily question, reflections, and episode alerts
  // ========================================

  /**
   * Show a friendly notification opt-in banner.
   * Only shown if: Push API is available, permission not already decided,
   * and user hasn't dismissed it this session.
   */
  function showNotificationOptIn(fromBell) {
    console.log('[NotifOptIn] Called with args:', arguments);
    const isIOS = /iP(hone|ad|od)/.test(navigator.userAgent) && !window.MSStream;
    const isSafari = /Safari/.test(navigator.userAgent) && !/CriOS|FxiOS|OPiOS|EdgiOS/.test(navigator.userAgent);
    const isStandalone = window.matchMedia('(display-mode: standalone)').matches ||
                         window.navigator.standalone === true;

    console.log('[NotifOptIn] Environment:', { isIOS, isSafari, isStandalone, 
                 hasPushManager: 'PushManager' in window, 
                 hasNotification: 'Notification' in window,
                 permission: typeof Notification !== 'undefined' ? Notification.permission : 'N/A' });

    // Non-Safari iOS browser (Edge, Chrome, Firefox on iOS) not in standalone:
    // PWA installation — and therefore push notifications — requires Safari on iOS.
    // Show a targeted message so users aren't shown wrong instructions.
    if (isIOS && !isSafari && !isStandalone) {
      try {
        // Skip dismissal checks when called from bell button
        if (!fromBell && sessionStorage.getItem('amt_notif_dismissed')) return;
        if (!fromBell && localStorage.getItem('amt_notif_dismissed_permanent')) return;
      } catch (e) {}

      const existing = document.getElementById('amt-notif-optin');
      if (existing) existing.remove();

      const banner = document.createElement('div');
      banner.id = 'amt-notif-optin';
      banner.className = 'amt-notif-optin';
      banner.innerHTML = `
        <div class="amt-notif-inner">
          <div class="amt-notif-text">
            <strong>🔔 Use Safari to turn on reminders</strong>
            <span>On iPhone and iPad, notification support works through the Safari home-screen app. Open this page in <strong>Safari</strong>, then tap <strong>Share ⎋ → Add to Home Screen</strong>.</span>
          </div>
          <div class="amt-notif-actions">
            <button class="amt-notif-dismiss" type="button" aria-label="Got it">Got it</button>
          </div>
        </div>
      `;

      const widget = document.querySelector('.ask-mirror-talk');
      if (widget) {
        const headingRow = widget.querySelector('.amt-heading-row');
        if (headingRow) {
          headingRow.insertAdjacentElement('afterend', banner);
        } else {
          widget.insertBefore(banner, widget.firstChild);
        }
      }

      banner.querySelector('.amt-notif-dismiss').addEventListener('click', () => {
        banner.classList.add('amt-notif-hiding');
        setTimeout(() => banner.remove(), 300);
        try {
          sessionStorage.setItem('amt_notif_dismissed', '1');
          const count = parseInt(localStorage.getItem('amt_notif_dismiss_count') || '0', 10) + 1;
          localStorage.setItem('amt_notif_dismiss_count', String(count));
          if (count >= 2) localStorage.setItem('amt_notif_dismissed_permanent', '1');
        } catch (e) {}
      });

      setTimeout(() => {
        if (banner.parentNode) {
          banner.classList.add('amt-notif-hiding');
          setTimeout(() => banner.remove(), 300);
        }
      }, 20000);

      return;
    }

    // iOS Safari (not added to home screen): Push API is not available.
    // Show a banner explaining they need to install the PWA first.
    if (isIOS && !isStandalone) {
      // Don't show if dismissed (unless called from bell button)
      try {
        if (!fromBell && sessionStorage.getItem('amt_notif_dismissed')) return;
        if (!fromBell && localStorage.getItem('amt_notif_dismissed_permanent')) return;
      } catch (e) {}

      const existing = document.getElementById('amt-notif-optin');
      if (existing) existing.remove();

      const banner = document.createElement('div');
      banner.id = 'amt-notif-optin';
      banner.className = 'amt-notif-optin';
      banner.innerHTML = `
        <div class="amt-notif-inner">
          <div class="amt-notif-text">
            <strong>🔔 Add Mirror Talk to your home screen first</strong>
            <span>On iPhone and iPad, reminders work after the app is installed. Tap <strong>Share</strong> <span style="font-size:1.2em">⎋</span>, choose <strong>Add to Home Screen</strong>, then open Mirror Talk from there to enable alerts.</span>
          </div>
          <div class="amt-notif-actions">
            <button class="amt-notif-dismiss" type="button" aria-label="Got it">Got it</button>
          </div>
        </div>
      `;

      const widget = document.querySelector('.ask-mirror-talk');
      if (widget) {
        const headingRow = widget.querySelector('.amt-heading-row');
        if (headingRow) {
          headingRow.insertAdjacentElement('afterend', banner);
        } else {
          widget.insertBefore(banner, widget.firstChild);
        }
      }

      banner.querySelector('.amt-notif-dismiss').addEventListener('click', () => {
        banner.classList.add('amt-notif-hiding');
        setTimeout(() => banner.remove(), 300);
        try { sessionStorage.setItem('amt_notif_dismissed', '1'); } catch (e) {}
      });

      setTimeout(() => {
        if (banner.parentNode) {
          banner.classList.add('amt-notif-hiding');
          setTimeout(() => banner.remove(), 300);
        }
      }, 20000);

      return;
    }

    // iOS standalone (home screen PWA) but Push API unavailable:
    // This means iOS version is below 16.4. Show a helpful message.
    if (isIOS && isStandalone && (!('PushManager' in window) || !('Notification' in window))) {
      try {
        if (!fromBell && sessionStorage.getItem('amt_notif_dismissed')) return;
      } catch (e) {}

      const existing = document.getElementById('amt-notif-optin');
      if (existing) existing.remove();

      const banner = document.createElement('div');
      banner.id = 'amt-notif-optin';
      banner.className = 'amt-notif-optin';
      banner.innerHTML = `
        <div class="amt-notif-inner">
          <div class="amt-notif-text">
            <strong>🔔 Reminders need iOS 16.4 or newer</strong>
            <span>Your current iOS version does not support web-app notifications yet. Update in <strong>Settings → General → Software Update</strong> to enable them.</span>
          </div>
          <div class="amt-notif-actions">
            <button class="amt-notif-dismiss" type="button" aria-label="OK">OK</button>
          </div>
        </div>
      `;

      const widget = document.querySelector('.ask-mirror-talk');
      if (widget) {
        const headingRow = widget.querySelector('.amt-heading-row');
        if (headingRow) {
          headingRow.insertAdjacentElement('afterend', banner);
        } else {
          widget.insertBefore(banner, widget.firstChild);
        }
      }

      banner.querySelector('.amt-notif-dismiss').addEventListener('click', () => {
        banner.classList.add('amt-notif-hiding');
        setTimeout(() => banner.remove(), 300);
        try { sessionStorage.setItem('amt_notif_dismissed', '1'); } catch (e) {}
      });

      setTimeout(() => {
        if (banner.parentNode) {
          banner.classList.add('amt-notif-hiding');
          setTimeout(() => banner.remove(), 300);
        }
      }, 20000);

      return;
    }

    // Guard: Push API must be available (non-iOS browsers without support)
    if (!('PushManager' in window) || !('Notification' in window)) {
      console.log('[NotifOptIn] Push API not available, returning early');
      return;
    }

    // If permission already denied, show browser settings instructions
    if (Notification.permission === 'denied') {
      console.log('[NotifOptIn] Permission denied, showing instructions');
      // Don't show if dismissed this session (unless called from bell button)
      try {
        if (!fromBell && sessionStorage.getItem('amt_notif_dismissed')) return;
      } catch (e) {}

      const existing = document.getElementById('amt-notif-optin');
      if (existing) existing.remove();

      const banner = document.createElement('div');
      banner.id = 'amt-notif-optin';
      banner.className = 'amt-notif-optin';
      banner.innerHTML = `
        <div class="amt-notif-inner">
          <div class="amt-notif-text">
            <strong>🔔 Reminders are currently blocked</strong>
            <span>Open your browser's site settings from the address bar, then change notifications to <strong>Allow</strong> for Mirror Talk.</span>
          </div>
          <div class="amt-notif-actions">
            <button class="amt-notif-dismiss" type="button" aria-label="Got it">Got it</button>
          </div>
        </div>
      `;

      const widget = document.querySelector('.ask-mirror-talk');
      if (widget) {
        const headingRow = widget.querySelector('.amt-heading-row');
        if (headingRow) {
          headingRow.insertAdjacentElement('afterend', banner);
        } else {
          widget.insertBefore(banner, widget.firstChild);
        }
      }

      banner.querySelector('.amt-notif-dismiss').addEventListener('click', () => {
        banner.classList.add('amt-notif-hiding');
        setTimeout(() => banner.remove(), 300);
        try { sessionStorage.setItem('amt_notif_dismissed', '1'); } catch (e) {}
      });

      setTimeout(() => {
        if (banner.parentNode) {
          banner.classList.add('amt-notif-hiding');
          setTimeout(() => banner.remove(), 300);
        }
      }, 15000);

      return;
    }

    // If permission already granted but not subscribed, allow them to subscribe
    // (Don't nag if they explicitly dismissed, but let bell button trigger this)
    const clickedBell = arguments[0] === 'fromBell';
    console.log('[NotifOptIn] clickedBell:', clickedBell, 'permission:', Notification.permission);
    if (Notification.permission === 'granted' && !clickedBell) {
      // Permission already granted - they can subscribe via bell button
      console.log('[NotifOptIn] Permission granted but not from bell, returning');
      return;
    }

    // Don't show if dismissed this session (unless clicked bell)
    if (!clickedBell) {
      console.log('[NotifOptIn] Not from bell, checking dismissal status');
      try {
        if (sessionStorage.getItem('amt_notif_dismissed')) {
          console.log('[NotifOptIn] Dismissed this session, returning');
          return;
        }
      } catch (e) {}

      // Don't show if they dismissed permanently
      try {
        if (localStorage.getItem('amt_notif_dismissed_permanent')) {
          console.log('[NotifOptIn] Dismissed permanently, returning');
          return;
        }
      } catch (e) {}
    } else {
      console.log('[NotifOptIn] From bell click, bypassing dismissal checks');
    }

    console.log('[NotifOptIn] Creating notification banner');

    // Remove any existing banner
    const existing = document.getElementById('amt-notif-optin');
    if (existing) existing.remove();

    const banner = document.createElement('div');
    banner.id = 'amt-notif-optin';
    banner.className = 'amt-notif-optin';
    banner.innerHTML = `
      <div class="amt-notif-inner">
        <div class="amt-notif-text">
          <strong>🔔 Stay gently connected</strong>
          <span>Choose the kinds of reminders you want from Mirror Talk.</span>
        </div>
        <div class="amt-notif-actions">
          <button class="amt-notif-enable" type="button">Choose reminders</button>
          <button class="amt-notif-dismiss" type="button" aria-label="Not now">Not now</button>
        </div>
      </div>
      <div class="amt-notif-prefs" style="display:none;">
        <button class="amt-notif-back" type="button" aria-label="Go back">← Back</button>
        <p class="amt-notif-prefs-intro">Pick the reminders that would actually be helpful. You can change these later.</p>
        <label class="amt-notif-pref">
          <input type="checkbox" id="amt-notif-qotd" checked>
          <span>Daily reflection question</span>
        </label>
        <label class="amt-notif-pref">
          <input type="checkbox" id="amt-notif-midday" checked>
          <span>Midday and nightly reflections</span>
        </label>
        <label class="amt-notif-pref">
          <input type="checkbox" id="amt-notif-episodes" checked>
          <span>🎙️ New podcast episode alerts</span>
        </label>
        <button class="amt-notif-save" type="button">Enable selected reminders</button>
      </div>
    `;

    // Insert after the widget heading or at top of widget
    const widget = document.querySelector('.ask-mirror-talk');
    if (widget) {
      const headingRow = widget.querySelector('.amt-heading-row');
      if (headingRow) {
        headingRow.insertAdjacentElement('afterend', banner);
      } else {
        widget.insertBefore(banner, widget.firstChild);
      }
    } else {
      document.body.appendChild(banner);
    }

    // Show preferences on "Enable" click
    banner.querySelector('.amt-notif-enable').addEventListener('click', () => {
      banner.querySelector('.amt-notif-actions').style.display = 'none';
      banner.querySelector('.amt-notif-prefs').style.display = '';
    });

    // "Back" — return to the initial enable/dismiss view
    banner.querySelector('.amt-notif-back').addEventListener('click', () => {
      banner.querySelector('.amt-notif-prefs').style.display = 'none';
      banner.querySelector('.amt-notif-actions').style.display = '';
    });

    // "Save & Enable" — request permission and subscribe
    banner.querySelector('.amt-notif-save').addEventListener('click', async () => {
      const qotd = document.getElementById('amt-notif-qotd').checked;
      const midday = document.getElementById('amt-notif-midday').checked;
      const episodes = document.getElementById('amt-notif-episodes').checked;

      banner.querySelector('.amt-notif-save').textContent = 'Enabling…';
      banner.querySelector('.amt-notif-save').disabled = true;

      const result = await subscribeToPush(qotd, episodes, midday);
      if (result.success) {
        banner.innerHTML = `
          <div class="amt-notif-inner amt-notif-success">
            <span>✅ Reminders enabled. Mirror Talk will reach out only in the ways you chose.</span>
          </div>
        `;
        setTimeout(() => {
          banner.classList.add('amt-notif-hiding');
          setTimeout(() => banner.remove(), 300);
        }, 3000);
      } else {
        let errorMsg;
        if (result.reason === 'private') {
          errorMsg = 'Notifications are not available in private/incognito mode. Please open Mirror Talk in a regular browser window to subscribe.';
        } else if (result.reason === 'denied') {
          errorMsg = 'Notification permission was blocked. To enable, tap the 🔒 icon in your address bar → Site settings → Notifications → Allow.';
        } else if (result.reason === 'not_configured') {
          errorMsg = 'Notifications are still being set up on this app and should be available soon. Please check back a little later.';
        } else {
          errorMsg = 'We could not enable reminders right now. Please try again in a moment.';
        }
        banner.innerHTML = `
          <div class="amt-notif-inner amt-notif-error">
            <span>${errorMsg}</span>
          </div>
        `;
        setTimeout(() => banner.remove(), 6000);
      }
    });

    // Dismiss
    banner.querySelector('.amt-notif-dismiss').addEventListener('click', () => {
      banner.classList.add('amt-notif-hiding');
      setTimeout(() => banner.remove(), 300);
      try {
        sessionStorage.setItem('amt_notif_dismissed', '1');
        // After 2 dismissals, stop showing the banner permanently
        const count = parseInt(localStorage.getItem('amt_notif_dismiss_count') || '0', 10) + 1;
        localStorage.setItem('amt_notif_dismiss_count', String(count));
        if (count >= 2) {
          localStorage.setItem('amt_notif_dismissed_permanent', '1');
        }
      } catch (e) {}
    });

    // Auto-dismiss after 20 seconds, but not while the prefs panel is visible
    setTimeout(() => {
      const prefs = banner.querySelector('.amt-notif-prefs');
      const prefsVisible = prefs && prefs.style.display !== 'none';
      if (banner.parentNode && !prefsVisible) {
        banner.classList.add('amt-notif-hiding');
        setTimeout(() => banner.remove(), 300);
      }
    }, 20000);
  }

  /**
   * Detect if the browser is in private/incognito mode.
   */
  function isPrivateBrowsing() {
    // Check if storage is restricted (common in private mode)
    try {
      localStorage.setItem('__amt_private_test', '1');
      localStorage.removeItem('__amt_private_test');
    } catch (e) {
      return true;
    }
    // Safari private mode: serviceWorker may exist but registration always fails
    // Firefox private: serviceWorker is undefined
    if (!('serviceWorker' in navigator)) return true;
    return false;
  }

  async function refreshPushHeartbeat(force = false) {
    try {
      if (!('serviceWorker' in navigator)) return false;
      const todayKey = todayStr();
      if (!force && _readStorage(PUSH_HEARTBEAT_DAY_KEY) === todayKey) return true;

      const isSubscribed = _loadMirroredFlag('amt_push_subscribed', PUSH_SUBSCRIBED_COOKIE_KEY);
      if (!isSubscribed) return false;

      const registration = await navigator.serviceWorker.ready;
      const subscription = await registration.pushManager.getSubscription();
      if (!subscription || !subscription.endpoint) return false;

      const res = await fetch(`${API_BASE}/api/push/heartbeat`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ endpoint: subscription.endpoint }),
      });
      if (!res.ok) return false;

      _writeStorage(PUSH_HEARTBEAT_DAY_KEY, todayKey);
      return true;
    } catch (err) {
      console.warn('[Push] Heartbeat refresh error:', err);
      return false;
    }
  }

  /**
   * Subscribe the browser to push notifications.
   * Returns { success: boolean, reason?: string }
   */
  async function subscribeToPush(notifyQotd = true, notifyEpisodes = true, notifyMidday = true) {
    try {
      // Check for private browsing early
      if (isPrivateBrowsing()) {
        console.warn('[Push] Private/incognito mode detected');
        return { success: false, reason: 'private' };
      }

      // Request notification permission
      const permission = await Notification.requestPermission();
      if (permission !== 'granted') {
        console.warn('[Push] Permission denied');
        return { success: false, reason: 'denied' };
      }

      // Get the VAPID public key from the API
      const vapidRes = await fetch(`${API_BASE}/api/push/vapid-key`);
      if (!vapidRes.ok) {
        console.warn('[Push] VAPID key not available — server returned', vapidRes.status);
        return { success: false, reason: 'not_configured' };
      }
      const { public_key } = await vapidRes.json();

      // Convert base64url to Uint8Array
      const applicationServerKey = urlBase64ToUint8Array(public_key);

      // Get the service worker registration
      const registration = await navigator.serviceWorker.ready;

      // Reuse an existing browser subscription when it still belongs to the
      // current VAPID key. If the VAPID key changed, old subscriptions receive
      // server-side 401/403 failures forever until the browser resubscribes.
      let subscription = await registration.pushManager.getSubscription();
      if (subscription && !pushSubscriptionMatchesVapidKey(subscription, applicationServerKey, public_key)) {
        console.warn('[Push] Existing subscription uses an older VAPID key; resubscribing');
        try { await subscription.unsubscribe(); } catch (e) {}
        subscription = null;
        _writeStorage(PUSH_HEARTBEAT_DAY_KEY, '');
      }

      subscription = subscription || await registration.pushManager.subscribe({
          userVisibleOnly: true,
          applicationServerKey: applicationServerKey,
        });

      const subJson = subscription.toJSON();

      // Capture the browser's IANA timezone so the server can deliver
      // notifications at the right local time (e.g. 8 AM in the user's city).
      const userTimezone = Intl.DateTimeFormat().resolvedOptions().timeZone || 'UTC';

      // Send subscription to our API
      const res = await fetch(`${API_BASE}/api/push/subscribe`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          endpoint: subJson.endpoint,
          keys: subJson.keys,
          notify_qotd: notifyQotd,
          notify_new_episodes: notifyEpisodes,
          notify_midday: notifyMidday,
          timezone: userTimezone,
          preferred_qotd_hour: 8,
        }),
      });

      if (res.ok) {
        console.log('[Push] Subscription registered successfully');
        try {
          _saveMirroredFlag('amt_push_subscribed', PUSH_SUBSCRIBED_COOKIE_KEY, true, 365);
          _writeStorage(PUSH_VAPID_KEY_STORAGE_KEY, public_key);
          _writeStorage(PUSH_HEARTBEAT_DAY_KEY, '');
          // Bell is already shown by initNotifManageBtn, just ensure it's visible
          const bellBtn = document.getElementById('amt-notif-manage-btn');
          if (bellBtn) bellBtn.style.display = '';
        } catch (e) {}
        refreshPushHeartbeat(true);
        return { success: true };
      } else {
        console.warn('[Push] Server rejected subscription:', res.status);
        return { success: false, reason: 'server' };
      }
    } catch (err) {
      console.error('[Push] Subscription failed:', err);
      // Common in private mode: DOMException about storage or AbortError
      if (err.name === 'NotAllowedError' || err.name === 'AbortError' ||
          (err.message && err.message.includes('storage'))) {
        return { success: false, reason: 'private' };
      }
      return { success: false, reason: 'error' };
    }
  }

  /**
   * Convert a base64url-encoded string to a Uint8Array (for applicationServerKey).
   */
  function urlBase64ToUint8Array(base64String) {
    const padding = '='.repeat((4 - base64String.length % 4) % 4);
    const base64 = (base64String + padding).replace(/-/g, '+').replace(/_/g, '/');
    const rawData = window.atob(base64);
    const outputArray = new Uint8Array(rawData.length);
    for (let i = 0; i < rawData.length; ++i) {
      outputArray[i] = rawData.charCodeAt(i);
    }
    return outputArray;
  }

  function pushSubscriptionMatchesVapidKey(subscription, applicationServerKey, publicKey) {
    try {
      const storedPublicKey = _readStorage(PUSH_VAPID_KEY_STORAGE_KEY);
      if (storedPublicKey && storedPublicKey !== publicKey) return false;

      const existingKey = subscription?.options?.applicationServerKey;
      if (!existingKey) return true;

      const current = new Uint8Array(applicationServerKey);
      const existing = new Uint8Array(existingKey);
      if (current.length !== existing.length) return false;
      for (let i = 0; i < current.length; i += 1) {
        if (current[i] !== existing[i]) return false;
      }
      return true;
    } catch (err) {
      console.warn('[Push] Could not verify VAPID key for existing subscription:', err);
      return true;
    }
  }

  async function ensurePushSubscriptionHealthy() {
    try {
      if (!('serviceWorker' in navigator) || !('PushManager' in window) || !('Notification' in window)) return false;
      if (Notification.permission !== 'granted') return false;

      const vapidRes = await fetch(`${API_BASE}/api/push/vapid-key`);
      if (!vapidRes.ok) return false;
      const { public_key } = await vapidRes.json();
      const applicationServerKey = urlBase64ToUint8Array(public_key);

      const registration = await navigator.serviceWorker.ready;
      const subscription = await registration.pushManager.getSubscription();
      const hasLocalSubscription = _loadMirroredFlag('amt_push_subscribed', PUSH_SUBSCRIBED_COOKIE_KEY);

      if (!subscription) {
        if (hasLocalSubscription) {
          _saveMirroredFlag('amt_push_subscribed', PUSH_SUBSCRIBED_COOKIE_KEY, false, 365);
          _writeStorage(PUSH_HEARTBEAT_DAY_KEY, '');
          return !!(await subscribeToPush(true, true, true)).success;
        }
        return false;
      }

      if (!pushSubscriptionMatchesVapidKey(subscription, applicationServerKey, public_key)) {
        try { await subscription.unsubscribe(); } catch (e) {}
        _saveMirroredFlag('amt_push_subscribed', PUSH_SUBSCRIBED_COOKIE_KEY, false, 365);
        _writeStorage(PUSH_HEARTBEAT_DAY_KEY, '');
        return !!(await subscribeToPush(true, true, true)).success;
      }

      const heartbeatOk = await refreshPushHeartbeat(true);
      if (heartbeatOk) {
        _saveMirroredFlag('amt_push_subscribed', PUSH_SUBSCRIBED_COOKIE_KEY, true, 365);
        _writeStorage(PUSH_VAPID_KEY_STORAGE_KEY, public_key);
        return true;
      }

      // The browser still has permission/subscription, but the server row was
      // lost or deactivated. Re-register it without asking the user again.
      return !!(await subscribeToPush(true, true, true)).success;
    } catch (err) {
      console.warn('[Push] Subscription health check failed:', err);
      return false;
    }
  }

  /**
   * Unsubscribe the current browser from push notifications.
   * Calls the backend and clears the local subscription flag.
   */
  async function unsubscribeFromPush() {
    try {
      const registration = await navigator.serviceWorker.ready;
      const subscription = await registration.pushManager.getSubscription();
      if (subscription) {
        await fetch(`${API_BASE}/api/push/unsubscribe`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ endpoint: subscription.endpoint }),
        });
        await subscription.unsubscribe();
      }
    } catch (err) {
      console.warn('[Push] Unsubscribe error:', err);
    } finally {
      try {
        _saveMirroredFlag('amt_push_subscribed', PUSH_SUBSCRIBED_COOKIE_KEY, false, 365);
        localStorage.removeItem(PUSH_HEARTBEAT_DAY_KEY);
        localStorage.removeItem(PUSH_VAPID_KEY_STORAGE_KEY);
        localStorage.removeItem('amt_notif_dismiss_count');
        localStorage.removeItem('amt_notif_dismissed_permanent');
      } catch (e) {}
    }
  }

  /**
   * Update push preferences on the server.
   * Returns true on success.
   */
  async function updatePushPreferences(qotd, midday, episodes) {
    try {
      const registration = await navigator.serviceWorker.ready;
      const subscription = await registration.pushManager.getSubscription();
      if (!subscription) {
        const created = await subscribeToPush(qotd, episodes, midday);
        return !!created.success;
      }
      const res = await fetch(`${API_BASE}/api/push/preferences`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          endpoint: subscription.endpoint,
          notify_qotd: qotd,
          notify_midday: midday,
          notify_new_episodes: episodes,
        }),
      });
      if (res.ok) {
        refreshPushHeartbeat(true);
        return true;
      }
      if (res.status === 404) {
        const recreated = await subscribeToPush(qotd, episodes, midday);
        return !!recreated.success;
      }
      return false;
    } catch (err) {
      console.warn('[Push] Preference update error:', err);
      return false;
    }
  }

  /**
   * Toggle the notification management panel open/closed.
   */
  function toggleNotificationManagePanel() {
    const btn = document.getElementById('amt-notif-manage-btn');
    const panel = document.getElementById('amt-notif-manage-panel');
    if (!btn || !panel) return;

    const isOpen = panel.style.display !== 'none';
    if (isOpen) {
      panel.style.display = 'none';
      btn.setAttribute('aria-expanded', 'false');
      return;
    }

    btn.setAttribute('aria-expanded', 'true');
    renderNotificationPrefsPanel(panel);
    panel.style.display = '';
    scrollToElementSafely(panel, 'center');
  }

  function renderNotificationPrefsPanel(panel) {
    panel.innerHTML = `
      <p class="amt-nmp-heading">🔔 Notification settings</p>
      <div class="amt-nmp-prefs">
        <label class="amt-nmp-pref">
          <input type="checkbox" id="amt-nmp-qotd" checked>
          <span>Question of the Day <em class="amt-nmp-pref-desc">Daily morning nudge at 8 AM</em></span>
        </label>
        <label class="amt-nmp-pref">
          <input type="checkbox" id="amt-nmp-midday" checked>
          <span>Reflection nudges <em class="amt-nmp-pref-desc">Midday encouragement and a calm nightly reflection</em></span>
        </label>
        <label class="amt-nmp-pref">
          <input type="checkbox" id="amt-nmp-episodes" checked>
          <span>New podcast episodes <em class="amt-nmp-pref-desc">Only when a fresh Mirror Talk episode is published</em></span>
        </label>
      </div>
      <div class="amt-nmp-actions">
        <button type="button" class="amt-nmp-save" id="amt-nmp-save-btn">Save preferences</button>
        <button type="button" class="amt-nmp-unsub" id="amt-nmp-unsub-btn">Unsubscribe</button>
      </div>
    `;

    const saveBtn = panel.querySelector('#amt-nmp-save-btn');
    const unsubBtn = panel.querySelector('#amt-nmp-unsub-btn');

    saveBtn.addEventListener('click', async () => {
      const qotd     = panel.querySelector('#amt-nmp-qotd').checked;
      const midday   = panel.querySelector('#amt-nmp-midday').checked;
      const episodes = panel.querySelector('#amt-nmp-episodes').checked;
      
      saveBtn.disabled = true;
      saveBtn.textContent = 'Saving…';
      const ok = await updatePushPreferences(qotd, midday, episodes);
      if (ok) {
        saveBtn.textContent = '✅ Saved';
        setTimeout(() => {
          panel.style.display = 'none';
          document.getElementById('amt-notif-manage-btn').setAttribute('aria-expanded', 'false');
        }, 1200);
      } else {
        saveBtn.disabled = false;
        saveBtn.textContent = 'Save preferences';
        const actions = panel.querySelector('.amt-nmp-actions');
        actions.querySelector('.amt-nmp-error')?.remove();
        const err = document.createElement('span');
        err.className = 'amt-nmp-error';
        err.style.cssText = 'font-size:13px;color:#c0392b;';
        err.textContent = 'Could not save — please try again.';
        actions.appendChild(err);
        setTimeout(() => err.remove(), 4000);
      }
    });

    unsubBtn.addEventListener('click', () => {
      // Show the soft-retain step
      panel.innerHTML = `
        <div class="amt-nmp-retain">
          <p class="amt-nmp-retain-heading">Before you go…</p>
          <p class="amt-nmp-retain-body">Your daily morning question is a gentle nudge — one notification a day, no spam ever. Want to keep just that?</p>
          <div class="amt-nmp-retain-actions">
            <button type="button" class="amt-nmp-keep-qotd" id="amt-nmp-keep-qotd-btn">Keep just the daily question</button>
            <button type="button" class="amt-nmp-confirm-unsub" id="amt-nmp-confirm-unsub-btn">No thanks, unsubscribe</button>
          </div>
        </div>
      `;

      panel.querySelector('#amt-nmp-keep-qotd-btn').addEventListener('click', async () => {
        const ok = await updatePushPreferences(true, false, false);
        const retain = panel.querySelector('.amt-nmp-retain');
        retain.innerHTML = ok
          ? '<p class="amt-nmp-success-msg">✅ Done — you\'ll only get your daily question.</p>'
          : '<p class="amt-nmp-unsub-msg">Something went wrong. Please try again later.</p>';
        setTimeout(() => {
          panel.style.display = 'none';
          document.getElementById('amt-notif-manage-btn').setAttribute('aria-expanded', 'false');
        }, 2500);
      });

      panel.querySelector('#amt-nmp-confirm-unsub-btn').addEventListener('click', async () => {
        const btn = panel.querySelector('#amt-nmp-confirm-unsub-btn');
        btn.disabled = true;
        btn.textContent = 'Unsubscribing…';
        await unsubscribeFromPush();
        const retain = panel.querySelector('.amt-nmp-retain');
        retain.innerHTML = '<p class="amt-nmp-unsub-msg">You\'ve been unsubscribed. You can re-enable reminders here anytime.</p>';
        // Keep the bell visible so users can opt back in later.
        const bellBtn = document.getElementById('amt-notif-manage-btn');
        setTimeout(() => {
          panel.style.display = 'none';
          if (bellBtn) {
            bellBtn.setAttribute('aria-expanded', 'false');
          }
        }, 3000);
      });
    });
  }

  // ─── Wire up the notification management bell button ──────────────────────
  (function initNotifManageBtn() {
    const btn = document.getElementById('amt-notif-manage-btn');
    if (!btn) return;
    
    // Show bell for all users on notification-capable platforms. The bell is a
    // stable entry point into notification settings; saving preferences can
    // subscribe or update the user as needed.
    const isStandalone = window.matchMedia('(display-mode: standalone)').matches ||
                         window.navigator.standalone === true;
    const isIOS = /iP(hone|ad|od)/.test(navigator.userAgent) && !window.MSStream;
    const hasNotificationSurface = ('Notification' in window) || isIOS;
    
    if (hasNotificationSurface || isStandalone) {
      btn.style.display = '';
    }
    
    btn.addEventListener('click', () => {
      console.log('[Bell] Notification bell clicked');
      toggleNotificationManagePanel();
    });
  })();

  // Show notification opt-in after a delay.
  // For returning visitors: show after 5 seconds.
  // For new visitors: show after 15 seconds (give them time to explore first).
  // The install banner is separate and handled by 'beforeinstallprompt'.
  setTimeout(() => {
    try {
      const alreadySubscribed = _loadMirroredFlag('amt_push_subscribed', PUSH_SUBSCRIBED_COOKIE_KEY);

      ensurePushSubscriptionHealthy().then((healthy) => {
        if (!healthy && !alreadySubscribed) showNotificationOptIn();
      });
    } catch (e) {}
  }, (() => {
    try {
      const lastSession = loadLastSession();
      const isReturning = (lastSession && lastSession.question) ||
                          window.matchMedia('(display-mode: standalone)').matches;
      return isReturning ? 5000 : 15000;
    } catch (e) { return 10000; }
  })());

  // ========================================
  // Gamification — Streak, Badges, Explorer
  // ========================================

  const ACTIVITY_LOG_KEY = 'amt_activity_log';

  const AMT_BADGES = [
    { id: 'first_step',   emoji: '🌱', name: 'First Step',         desc: 'Asked your first question',              check: s => s.totalQuestions >= 1 },
    { id: 'curious',      emoji: '🔍', name: 'Curious Mind',        desc: 'Asked 10 questions',                     check: s => s.totalQuestions >= 10 },
    { id: 'streak_3',     emoji: '🔥', name: 'On Fire',             desc: 'Kept a 3-day streak',                    check: s => s.maxStreak >= 3 },
    { id: 'streak_7',     emoji: '💫', name: 'Week Warrior',        desc: 'Kept a 7-day streak',                    check: s => s.maxStreak >= 7 },
    { id: 'streak_14',    emoji: '🌟', name: 'Steady Heart',        desc: 'Kept a 14-day streak',                   check: s => s.maxStreak >= 14 },
    { id: 'streak_30',    emoji: '💎', name: 'Devoted',             desc: 'Kept a 30-day streak',                   check: s => s.maxStreak >= 30 },
    { id: 'explorer',     emoji: '🗺️', name: 'Explorer',            desc: 'Explored 5 different topics',            check: s => s.themesExplored.size >= 5 },
    { id: 'deep_diver',   emoji: '⚡', name: 'Deep Diver',          desc: 'Clicked a podcast citation',             check: s => s.citationsClicked >= 1 },
    { id: 'sharer',       emoji: '📤', name: 'Sharer',              desc: 'Shared an insight',                      check: s => s.sharesCount >= 1 },
    { id: 'guide',        emoji: '🫶', name: 'Guide',               desc: 'Shared 3 reflections',                   check: s => s.sharesCount >= 3 },
    { id: 'collector',    emoji: '🔖', name: 'Collector',           desc: 'Saved 5 insights',                       check: s => s.insightsSaved >= 5 },
    { id: 'night_owl',    emoji: '🌙', name: 'Night Owl',           desc: 'Asked a question after 10pm',            check: s => s.nightOwl },
    { id: 'wisdom_seeker',emoji: '📖', name: 'Wisdom Seeker',       desc: 'Asked 25 questions',                     check: s => s.totalQuestions >= 25 },
    { id: 'deep_session', emoji: '🌊', name: 'Deep Session',        desc: 'Asked 3 questions in a single day',      check: s => (s.dailyQuestions || 0) >= 3 },
    { id: 'completionist',emoji: '🏆', name: 'Completionist',       desc: 'Explored all 20 topics',                 check: s => s.themesExplored.size >= 20 },
  ];

  // Themes the backend already uses in the QOTD pool
  const AMT_THEMES = [
    'Self-worth','Forgiveness','Inner peace','Purpose','Surrender',
    'Leadership','Relationships','Gratitude','Boundaries','Healing',
    'Grief','Fear','Parenting','Growth','Communication',
    'Faith','Identity','Empowerment','Transition','Community',
  ];

  const LAST_SESSION_KEY = 'amt_last_session';
  const LAST_SESSION_COOKIE_KEY = 'amt_ls';
  const INSIGHTS_COOKIE_KEY = 'amt_ix';
  const REFLECTION_NOTES_COOKIE_KEY = 'amt_rn';
  const ACTIVITY_LOG_COOKIE_KEY = 'amt_ax';
  const PUSH_SUBSCRIBED_COOKIE_KEY = 'amt_ps';
  const PUSH_HEARTBEAT_DAY_KEY = 'amt_push_heartbeat_day';
  const PUSH_VAPID_KEY_STORAGE_KEY = 'amt_push_vapid_public_key';

  // ── Cookie helpers for cross-PWA-reinstall backup ────────────────────────
  // localStorage is wiped on iOS when the user deletes the PWA from homescreen.
  // Cookies survive because they live at the browser/domain level, not the PWA
  // context. We dual-write gamification state to both so data is recoverable.
  function _cookieSet(name, value, days) {
    try {
      const exp = new Date(Date.now() + days * 864e5).toUTCString();
      document.cookie = name + '=' + encodeURIComponent(value) +
        '; expires=' + exp + '; path=/; SameSite=Lax';
    } catch (e) {}
  }
  function _cookieGet(name) {
    try {
      const re = new RegExp('(?:^|; )' + name.replace(/[.*+?^${}()|[\]\\]/g, '\\$&') + '=([^;]*)');
      const m = document.cookie.match(re);
      return m ? decodeURIComponent(m[1]) : null;
    } catch (e) { return null; }
  }
  function _cookieDelete(name) {
    try {
      document.cookie = name + '=; expires=Thu, 01 Jan 1970 00:00:00 GMT; path=/; SameSite=Lax';
    } catch (e) {}
  }
  function _loadMirroredJson(localKey, cookieKey, fallback) {
    try {
      const raw = localStorage.getItem(localKey);
      if (raw) return JSON.parse(raw);
    } catch (e) {}
    try {
      const cookieRaw = _cookieGet(cookieKey);
      if (!cookieRaw) return fallback;
      const parsed = JSON.parse(cookieRaw);
      try { localStorage.setItem(localKey, cookieRaw); } catch (e) {}
      return parsed;
    } catch (e) {
      return fallback;
    }
  }
  function _loadMirroredFlag(localKey, cookieKey) {
    try {
      if (localStorage.getItem(localKey)) return true;
    } catch (e) {}
    try {
      const cookieValue = _cookieGet(cookieKey);
      if (!cookieValue) return false;
      try { localStorage.setItem(localKey, cookieValue); } catch (e) {}
      return cookieValue === '1';
    } catch (e) {
      return false;
    }
  }
  function _saveMirroredFlag(localKey, cookieKey, enabled, days) {
    try {
      if (enabled) {
        localStorage.setItem(localKey, '1');
        _cookieSet(cookieKey, '1', days || 365);
      } else {
        localStorage.removeItem(localKey);
        _cookieDelete(cookieKey);
      }
    } catch (e) {}
  }
  function clampText(text, maxLen) {
    return String(text || '').trim().slice(0, maxLen);
  }
  function compactLastSessionRecord(record) {
    if (!record) return null;
    return {
      question: clampText(record.question, 180),
      answer: clampText(record.answer, 600),
      excerpt: clampText(record.excerpt, 220),
      theme: clampText(record.theme, 60),
      time: Number(record.time || Date.now()),
    };
  }
  function loadLastSession() {
    return _loadMirroredJson(LAST_SESSION_KEY, LAST_SESSION_COOKIE_KEY, null);
  }
  function saveLastSessionRecord(record) {
    const compact = compactLastSessionRecord(record);
    if (!compact) return;
    try { localStorage.setItem(LAST_SESSION_KEY, JSON.stringify(compact)); } catch (e) {}
    try { _cookieSet(LAST_SESSION_COOKIE_KEY, JSON.stringify(compact), 365); } catch (e) {}
    try {
      localStorage.setItem('amt_last_question', compact.question);
      localStorage.setItem('amt_last_answer', compact.answer);
      localStorage.setItem('amt_last_excerpt', compact.excerpt);
      localStorage.setItem('amt_last_time', String(compact.time));
      if (compact.theme) localStorage.setItem('amt_last_theme', compact.theme);
    } catch (e) {}
  }
  function compactInsightRecordForBackup(insight) {
    const normalized = normalizeInsightRecord(insight);
    return {
      question: clampText(normalized.question, 120),
      answer: '',
      excerpt: clampText(normalized.excerpt, 180),
      theme: clampText(normalized.theme, 40),
      savedAt: normalized.savedAt,
    };
  }
  function loadReflectionNotes() {
    return _loadMirroredJson('amt_reflect_notes', REFLECTION_NOTES_COOKIE_KEY, []);
  }
  function saveReflectionNotes(notes) {
    const allNotes = Array.isArray(notes) ? notes.slice(0, 50) : [];
    const backup = allNotes.slice(0, 8).map(entry => ({
      prompt: clampText(entry && entry.prompt, 120),
      note: clampText(entry && entry.note, 280),
      theme: clampText(entry && entry.theme, 40),
      sourceQuestion: clampText(entry && entry.sourceQuestion, 120),
      sourceExcerpt: clampText(entry && entry.sourceExcerpt, 180),
      savedAt: Number((entry && entry.savedAt) || Date.now()),
    }));
    try { localStorage.setItem('amt_reflect_notes', JSON.stringify(allNotes)); } catch (e) {}
    try { _cookieSet(REFLECTION_NOTES_COOKIE_KEY, JSON.stringify(backup), 365); } catch (e) {}
  }

  // These depend on gamification/session constants being initialized first.
  renderJourneyCard();

  function normalizeStats(raw) {
    const parsed = raw && typeof raw === 'object' ? raw : {};
    const themes = parsed.themesExplored instanceof Set
      ? [...parsed.themesExplored]
      : (Array.isArray(parsed.themesExplored) ? parsed.themesExplored : []);
    const badges = parsed.earnedBadges instanceof Set
      ? [...parsed.earnedBadges]
      : (Array.isArray(parsed.earnedBadges) ? parsed.earnedBadges : []);
    return {
      totalQuestions:   Number(parsed.totalQuestions || 0),
      currentStreak:    Number(parsed.currentStreak || 0),
      maxStreak:        Number(parsed.maxStreak || 0),
      lastActiveDate:   parsed.lastActiveDate || null,
      themesExplored:   new Set(themes),
      earnedBadges:     new Set(badges),
      citationsClicked: Number(parsed.citationsClicked || 0),
      sharesCount:      Number(parsed.sharesCount || 0),
      insightsSaved:    Number(parsed.insightsSaved || 0),
      lastReviveDate:   parsed.lastReviveDate || null,
      nightOwl:         !!parsed.nightOwl,
      dailyQuestions:   Number(parsed.dailyQuestions || 0),
      lastSessionDate:  parsed.lastSessionDate || null,
    };
  }

  function loadStats() {
    try {
      const raw = localStorage.getItem('amt_gamification') || _cookieGet('amt_gx');
      if (raw) {
        const parsed = normalizeStats(JSON.parse(raw));
        // Cookie recovery: re-hydrate localStorage so future writes work normally
        if (!localStorage.getItem('amt_gamification')) {
          try { localStorage.setItem('amt_gamification', raw); } catch (e) {}
        }
        return parsed;
      }
    } catch (e) {}
    return normalizeStats({});
  }

  function saveStats(s) {
    try {
      const serialisable = Object.assign({}, s, {
        themesExplored: [...s.themesExplored],
        earnedBadges:   [...s.earnedBadges],
      });
      const json = JSON.stringify(serialisable);
      localStorage.setItem('amt_gamification', json);
      _cookieSet('amt_gx', json, 365); // backup — survives iOS PWA reinstall
    } catch (e) {}
  }

  function todayStr() {
    return formatLocalDate(new Date());
  }

  function formatLocalDate(date) {
    const year = date.getFullYear();
    const month = String(date.getMonth() + 1).padStart(2, '0');
    const day = String(date.getDate()).padStart(2, '0');
    return `${year}-${month}-${day}`;
  }

  function addLocalDays(dayStr, deltaDays) {
    const base = parseDayStamp(dayStr);
    if (base == null) return null;
    const date = new Date(base);
    date.setUTCDate(date.getUTCDate() + deltaDays);
    const year = date.getUTCFullYear();
    const month = String(date.getUTCMonth() + 1).padStart(2, '0');
    const day = String(date.getUTCDate()).padStart(2, '0');
    return `${year}-${month}-${day}`;
  }

  function parseDayStamp(dayStr) {
    if (!dayStr) return null;
    const parts = String(dayStr).split('-').map(Number);
    if (parts.length !== 3 || parts.some(Number.isNaN)) return null;
    return Date.UTC(parts[0], parts[1] - 1, parts[2]);
  }

  function dayDiff(fromDay, toDay) {
    const fromMs = parseDayStamp(fromDay);
    const toMs = parseDayStamp(toDay);
    if (fromMs == null || toMs == null) return null;
    return Math.round((toMs - fromMs) / 86400000);
  }

  function loadActivityLog() {
    return _loadMirroredJson(ACTIVITY_LOG_KEY, ACTIVITY_LOG_COOKIE_KEY, []);
  }

  function saveActivityLog(entries) {
    const fullEntries = Array.isArray(entries) ? entries.slice(-180) : [];
    const backupEntries = fullEntries.slice(-21).map(entry => ({
      type: clampText(entry.type, 24),
      day: clampText(entry.day, 10),
      ts: Number(entry.ts || Date.now()),
      theme: clampText(entry.theme, 40),
    }));
    try { localStorage.setItem(ACTIVITY_LOG_KEY, JSON.stringify(fullEntries)); } catch (e) {}
    try { _cookieSet(ACTIVITY_LOG_COOKIE_KEY, JSON.stringify(backupEntries), 365); } catch (e) {}
  }

  function logActivity(type, payload) {
    try {
      const entries = loadActivityLog();
      entries.push(Object.assign({
        type,
        ts: Date.now(),
        day: todayStr()
      }, payload || {}));
      saveActivityLog(entries);
    } catch (e) {}
  }

  function canOfferStreakRevive(stats) {
    if (!stats || !stats.currentStreak || stats.currentStreak < 3 || !stats.lastActiveDate) return false;
    if (stats.lastActiveDate === todayStr()) return false;
    if (dayDiff(stats.lastActiveDate, todayStr()) !== 2) return false;
    if (stats.lastReviveDate && dayDiff(stats.lastReviveDate, todayStr()) !== null && dayDiff(stats.lastReviveDate, todayStr()) < 14) return false;
    return true;
  }

  function shouldConsumeStreakRevive(stats) {
    if (!canOfferStreakRevive(stats)) return false;
    try {
      return sessionStorage.getItem('amt_pending_streak_revive') === '1';
    } catch (e) {
      return false;
    }
  }

  function recordQuestion(stats, themeHint, questionText) {
    const today = todayStr();
    const last  = stats.lastActiveDate;

    if (last !== today) {
      if (shouldConsumeStreakRevive(stats)) {
        stats.currentStreak += 1;
        stats.maxStreak = Math.max(stats.maxStreak, stats.currentStreak);
        stats.lastActiveDate = today;
        stats.lastReviveDate = today;
        try { sessionStorage.removeItem('amt_pending_streak_revive'); } catch (e) {}
      } else {
      // Check streak continuity
        const yStr = addLocalDays(today, -1);

        if (last === yStr) {
          stats.currentStreak += 1;
        } else if (last === null) {
          stats.currentStreak = 1;
        } else {
          // Streak broken
          stats.currentStreak = 1;
        }
        stats.maxStreak = Math.max(stats.maxStreak, stats.currentStreak);
        stats.lastActiveDate = today;
      }
    }

    stats.totalQuestions += 1;

    // Per-day question count — resets when the date changes
    if (stats.lastSessionDate !== today) {
      stats.dailyQuestions  = 1;
      stats.lastSessionDate = today;
    } else {
      stats.dailyQuestions = (stats.dailyQuestions || 0) + 1;
    }

    // Night owl check (22:00–23:59)
    const hour = new Date().getHours();
    if (hour >= 22) stats.nightOwl = true;

    // Theme tracking — prefer the server-supplied hint, then keyword-scan the
    // actual question text (bug fix: was scanning themeHint instead of questionText)
    if (themeHint) {
      stats.themesExplored.add(themeHint);
    } else {
      const q = (questionText || '').toLowerCase();
      for (const theme of AMT_THEMES) {
        if (q.includes(theme.toLowerCase())) {
          stats.themesExplored.add(theme);
          break;
        }
      }
    }

    return stats;
  }

  function checkAndAwardBadges(stats) {
    const newBadges = [];
    for (const badge of AMT_BADGES) {
      if (!stats.earnedBadges.has(badge.id) && badge.check(stats)) {
        stats.earnedBadges.add(badge.id);
        newBadges.push(badge);
      }
    }
    return newBadges;
  }

  function getNextUnlocks(stats) {
    const candidates = [];

    const streakGoals = [3, 7, 14, 30];
    const nextStreakGoal = streakGoals.find(goal => stats.maxStreak < goal);
    if (nextStreakGoal) {
      candidates.push({
        id: 'streak',
        label: `${nextStreakGoal - stats.maxStreak} more day${nextStreakGoal - stats.maxStreak === 1 ? '' : 's'} for your next streak badge`,
        detail: `Next streak reward at ${nextStreakGoal} days`,
        current: stats.maxStreak,
        target: nextStreakGoal,
        accent: 'gold'
      });
    }

    if (stats.totalQuestions < 25) {
      const target = stats.totalQuestions < 10 ? 10 : 25;
      candidates.push({
        id: 'questions',
        label: `${target - stats.totalQuestions} more question${target - stats.totalQuestions === 1 ? '' : 's'} to reach ${target}`,
        detail: target === 10 ? 'Unlock Curious Mind' : 'Unlock Wisdom Seeker',
        current: stats.totalQuestions,
        target,
        accent: 'rose'
      });
    }

    if (stats.themesExplored.size < 20) {
      const target = stats.themesExplored.size < 5 ? 5 : 20;
      candidates.push({
        id: 'themes',
        label: `${target - stats.themesExplored.size} more theme${target - stats.themesExplored.size === 1 ? '' : 's'} to explore`,
        detail: target === 5 ? 'Unlock Explorer' : 'Unlock Completionist',
        current: stats.themesExplored.size,
        target,
        accent: 'teal'
      });
    }

    if (stats.insightsSaved < 5) {
      candidates.push({
        id: 'insights',
        label: `${5 - stats.insightsSaved} more saved insight${5 - stats.insightsSaved === 1 ? '' : 's'} for Collector`,
        detail: 'Build your private reflection vault',
        current: stats.insightsSaved,
        target: 5,
        accent: 'ink'
      });
    }

    return candidates.slice(0, 3);
  }

  function getDailyMomentumText(stats) {
    const askedToday = stats.lastSessionDate === todayStr() ? (stats.dailyQuestions || 0) : 0;
    if (askedToday === 0) {
      return stats.currentStreak > 0
        ? `Ask one question today to protect your ${stats.currentStreak}-day streak.`
        : 'Ask one thoughtful question to begin your rhythm.';
    }
    if (askedToday < 3) {
      return `${3 - askedToday} more question${3 - askedToday === 1 ? '' : 's'} today unlocks a Deep Session celebration.`;
    }
    return `Today already counts as a deep session with ${askedToday} question${askedToday === 1 ? '' : 's'}.`;
  }

  function trackRewardEvent(kind) {
    try {
      const s = loadStats();
      if (kind === 'share') {
        s.sharesCount = (s.sharesCount || 0) + 1;
        logActivity('share');
      } else if (kind === 'insight_save') {
        s.insightsSaved = (s.insightsSaved || 0) + 1;
        logActivity('insight_save');
      } else {
        return;
      }

      const newBadges = checkAndAwardBadges(s);
      saveStats(s);
      renderStatsBar(s);
      renderMomentumCard(s);
      renderWeeklyRecap();
      newBadges.forEach(badge => showMilestoneToast(badge.emoji, `Badge unlocked: ${badge.name}`, badge.desc, badge));
    } catch (e) {}
  }

  function renderStreakRevivalCard(stats) {
    if (!streakRevivalCard) return;

    try {
      if (sessionStorage.getItem('amt_streak_revive_dismissed') === todayStr()) {
        streakRevivalCard.innerHTML = '';
        streakRevivalCard.style.display = 'none';
        return;
      }
    } catch (e) {}

    if (!canOfferStreakRevive(stats)) {
      streakRevivalCard.innerHTML = '';
      streakRevivalCard.style.display = 'none';
      return;
    }

    streakRevivalCard.innerHTML = `
      <div class="amt-streak-revival-inner">
        <div class="amt-streak-revival-copy">
          <span class="amt-streak-revival-kicker">Reflection Pass</span>
          <h3 class="amt-streak-revival-title">Your ${stats.currentStreak}-day streak can still be restored.</h3>
          <p class="amt-streak-revival-text">Ask one question today and we’ll treat it as a graceful return, not a reset. This recovery pass refreshes every 14 days.</p>
        </div>
        <div class="amt-streak-revival-actions">
          <button type="button" class="amt-streak-revival-btn amt-streak-revival-btn-primary">Restore my streak</button>
          <button type="button" class="amt-streak-revival-btn amt-streak-revival-btn-secondary">Not today</button>
        </div>
      </div>
    `;
    streakRevivalCard.style.display = '';

    streakRevivalCard.querySelector('.amt-streak-revival-btn-primary').addEventListener('click', () => {
      try { sessionStorage.setItem('amt_pending_streak_revive', '1'); } catch (e) {}
      submitRhythmQuestion(
        getRhythmReflectionQuestion('', { preferQotd: true }),
        'streak_revival',
        { feature: 'reflection_pass' }
      );
    });

    streakRevivalCard.querySelector('.amt-streak-revival-btn-secondary').addEventListener('click', () => {
      streakRevivalCard.style.display = 'none';
      try { sessionStorage.setItem('amt_streak_revive_dismissed', todayStr()); } catch (e) {}
    });
  }

  function getWeeklyRecapData() {
    const recentEntries = loadActivityLog().filter(entry => entry && entry.ts && entry.ts >= (Date.now() - (7 * 86400000)));
    if (!recentEntries.length) {
      return null;
    }

    const questionEntries = recentEntries.filter(entry => entry.type === 'question');
    const savedEntries = recentEntries.filter(entry => entry.type === 'insight_save');
    const shareEntries = recentEntries.filter(entry => entry.type === 'share');
    const themeCounts = {};
    questionEntries.forEach(entry => {
      if (entry.theme) themeCounts[entry.theme] = (themeCounts[entry.theme] || 0) + 1;
    });
    const topTheme = Object.entries(themeCounts).sort((a, b) => b[1] - a[1])[0]?.[0] || null;
    const dayCounts = {};
    recentEntries.forEach(entry => {
      if (entry.day) dayCounts[entry.day] = (dayCounts[entry.day] || 0) + 1;
    });
    const strongestDayCount = Math.max(0, ...Object.values(dayCounts));

    const latestSavedInsight = loadInsights()
      .map(normalizeInsightRecord)
      .filter(ins => ins.savedAt >= (Date.now() - (7 * 86400000)))
      .sort((a, b) => b.savedAt - a.savedAt)[0];

    const recapPrompt = topTheme
      ? getThemeStarter(topTheme)
      : 'What do I need most in this season of my life?';

    if (questionEntries.length < 2 && savedEntries.length === 0 && shareEntries.length === 0) {
      return null;
    }

    return {
      questionCount: questionEntries.length,
      savedCount: savedEntries.length,
      shareCount: shareEntries.length,
      topTheme,
      strongestDayCount,
      latestSavedInsight,
      recapPrompt
    };
  }

  // Get weekly recap template style (rotates between vibrant styles)
  function getWeeklyRecapTemplate() {
    const now = new Date();
    const weekNumber = Math.floor((now - new Date(now.getFullYear(), 0, 1)) / (7 * 24 * 60 * 60 * 1000));
    const templates = [
      'gradient_vibrant',
      'prismatic_rainbow', 
      'neon_modern', 
      'sunset_warmth',
      'ocean_depths',
      'purple_dream',
      'forest_vitality',
      'golden_hour'
    ];
    return templates[weekNumber % templates.length];
  }

  function buildWeeklyRecapShareCard(recap, scale) {
    const data = recap || getWeeklyRecapData();
    if (!data) return null;

    // Use standard reflection card dimensions (1080x1350) for consistency with our card template system
    const scaleFactor = scale || 1.0;
    const W = Math.round(1080 * scaleFactor);
    const H = Math.round(1350 * scaleFactor);
    const canvas = document.createElement('canvas');
    canvas.width = W;
    canvas.height = H;
    const ctx = canvas.getContext('2d');

    // Scale all drawing operations
    if (scaleFactor !== 1.0) {
      ctx.scale(scaleFactor, scaleFactor);
    }

    // Get the template for this week
    const template = getWeeklyRecapTemplate();

    // Apply template-specific background
    if (template === 'gradient_vibrant') {
      // Bold multi-color gradient (courage/energy theme)
      const vibrantGrad = ctx.createLinearGradient(0, 0, 1080, 1350);
      vibrantGrad.addColorStop(0, '#ff3366');
      vibrantGrad.addColorStop(0.3, '#ff6b4a');
      vibrantGrad.addColorStop(0.7, '#ffaa00');
      vibrantGrad.addColorStop(1, '#ffd700');
      ctx.fillStyle = vibrantGrad;
      ctx.fillRect(0, 0, 1080, 1350);
      
      // Subtle overlay for depth
      const overlay = ctx.createRadialGradient(540, 675, 0, 540, 675, 800);
      overlay.addColorStop(0, 'rgba(0,0,0,0)');
      overlay.addColorStop(1, 'rgba(0,0,0,0.20)');
      ctx.fillStyle = overlay;
      ctx.fillRect(0, 0, 1080, 1350);
      
      // Decorative elements
      ctx.fillStyle = 'rgba(255,255,255,0.08)';
      ctx.beginPath();
      ctx.arc(160, 270, 120, 0, Math.PI * 2);
      ctx.fill();
      ctx.beginPath();
      ctx.arc(950, 1010, 160, 0, Math.PI * 2);
      ctx.fill();
    } else if (template === 'prismatic_rainbow') {
      // Rainbow gradient like the example card
      const prismatic = ctx.createLinearGradient(0, 0, 1080, 1350);
      prismatic.addColorStop(0, '#ff0080');
      prismatic.addColorStop(0.15, '#ff4500');
      prismatic.addColorStop(0.3, '#ff8c00');
      prismatic.addColorStop(0.45, '#40e0d0');
      prismatic.addColorStop(0.6, '#7b68ee');
      prismatic.addColorStop(0.75, '#ff1493');
      prismatic.addColorStop(0.9, '#ff6b9d');
      prismatic.addColorStop(1, '#4169e1');
      ctx.fillStyle = prismatic;
      ctx.fillRect(0, 0, 1080, 1350);
      
      // Soften with overlay
      const softener = ctx.createLinearGradient(0, 0, 0, 1350);
      softener.addColorStop(0, 'rgba(0,0,0,0.12)');
      softener.addColorStop(0.5, 'rgba(0,0,0,0.05)');
      softener.addColorStop(1, 'rgba(0,0,0,0.18)');
      ctx.fillStyle = softener;
      ctx.fillRect(0, 0, 1080, 1350);
      
      // Radial light source
      const spotlight = ctx.createRadialGradient(540, 550, 0, 540, 550, 700);
      spotlight.addColorStop(0, 'rgba(255,255,255,0.15)');
      spotlight.addColorStop(0.6, 'rgba(255,255,255,0.05)');
      spotlight.addColorStop(1, 'rgba(255,255,255,0)');
      ctx.fillStyle = spotlight;
      ctx.fillRect(0, 0, 1080, 1350);
    } else if (template === 'neon_modern') {
      // Dark gradient base
      const darkGrad = ctx.createLinearGradient(0, 0, 1080, 1350);
      darkGrad.addColorStop(0, '#0a0a0f');
      darkGrad.addColorStop(0.5, '#1a1a2e');
      darkGrad.addColorStop(1, '#16213e');
      ctx.fillStyle = darkGrad;
      ctx.fillRect(0, 0, 1080, 1350);
      
      // Neon glow orbs
      const neonColor = '#00d9ff';
      const glow1 = ctx.createRadialGradient(270, 470, 0, 270, 470, 280);
      glow1.addColorStop(0, neonColor + '40');
      glow1.addColorStop(0.5, neonColor + '20');
      glow1.addColorStop(1, 'transparent');
      ctx.fillStyle = glow1;
      ctx.fillRect(0, 0, 1080, 1350);
      
      const glow2 = ctx.createRadialGradient(840, 920, 0, 840, 920, 320);
      glow2.addColorStop(0, '#ff0080' + '35');
      glow2.addColorStop(0.5, '#ff0080' + '18');
      glow2.addColorStop(1, 'transparent');
      ctx.fillStyle = glow2;
      ctx.fillRect(0, 0, 1080, 1350);
    } else if (template === 'sunset_warmth') {
      // Warm sunset gradient
      const sunsetGrad = ctx.createLinearGradient(0, 0, 1080, 1350);
      sunsetGrad.addColorStop(0, '#ff6b9d');
      sunsetGrad.addColorStop(0.3, '#ffa07a');
      sunsetGrad.addColorStop(0.6, '#ffb347');
      sunsetGrad.addColorStop(1, '#87ceeb');
      ctx.fillStyle = sunsetGrad;
      ctx.fillRect(0, 0, 1080, 1350);
      
      // Overlay for warmth
      const warmOverlay = ctx.createRadialGradient(540, 400, 0, 540, 400, 900);
      warmOverlay.addColorStop(0, 'rgba(255,140,0,0.10)');
      warmOverlay.addColorStop(0.7, 'rgba(255,69,0,0.05)');
      warmOverlay.addColorStop(1, 'rgba(0,0,0,0.15)');
      ctx.fillStyle = warmOverlay;
      ctx.fillRect(0, 0, 1080, 1350);
      
      // Decorative sun circle
      ctx.fillStyle = 'rgba(255,255,255,0.12)';
      ctx.beginPath();
      ctx.arc(200, 200, 140, 0, Math.PI * 2);
      ctx.fill();
    } else if (template === 'ocean_depths') {
      // Deep ocean blue gradient
      const oceanGrad = ctx.createLinearGradient(0, 0, 1080, 1350);
      oceanGrad.addColorStop(0, '#006994');
      oceanGrad.addColorStop(0.3, '#0088cc');
      oceanGrad.addColorStop(0.6, '#00bcd4');
      oceanGrad.addColorStop(1, '#26c6da');
      ctx.fillStyle = oceanGrad;
      ctx.fillRect(0, 0, 1080, 1350);
      
      // Wave overlay effect
      const waveOverlay = ctx.createRadialGradient(540, 300, 0, 540, 300, 800);
      waveOverlay.addColorStop(0, 'rgba(255,255,255,0.10)');
      waveOverlay.addColorStop(0.5, 'rgba(0,188,212,0.15)');
      waveOverlay.addColorStop(1, 'rgba(0,0,50,0.20)');
      ctx.fillStyle = waveOverlay;
      ctx.fillRect(0, 0, 1080, 1350);
      
      // Decorative bubbles
      ctx.fillStyle = 'rgba(255,255,255,0.10)';
      ctx.beginPath();
      ctx.arc(850, 280, 100, 0, Math.PI * 2);
      ctx.fill();
      ctx.beginPath();
      ctx.arc(220, 950, 130, 0, Math.PI * 2);
      ctx.fill();
      ctx.beginPath();
      ctx.arc(950, 1100, 80, 0, Math.PI * 2);
      ctx.fill();
    } else if (template === 'purple_dream') {
      // Dreamy purple to pink gradient
      const purpleGrad = ctx.createLinearGradient(0, 0, 1080, 1350);
      purpleGrad.addColorStop(0, '#6a1b9a');
      purpleGrad.addColorStop(0.25, '#8e24aa');
      purpleGrad.addColorStop(0.5, '#ab47bc');
      purpleGrad.addColorStop(0.75, '#ce93d8');
      purpleGrad.addColorStop(1, '#f48fb1');
      ctx.fillStyle = purpleGrad;
      ctx.fillRect(0, 0, 1080, 1350);
      
      // Dreamy overlay with soft light
      const dreamOverlay = ctx.createRadialGradient(400, 500, 0, 400, 500, 900);
      dreamOverlay.addColorStop(0, 'rgba(255,255,255,0.15)');
      dreamOverlay.addColorStop(0.6, 'rgba(171,71,188,0.10)');
      dreamOverlay.addColorStop(1, 'rgba(106,27,154,0.10)');
      ctx.fillStyle = dreamOverlay;
      ctx.fillRect(0, 0, 1080, 1350);
      
      // Floating orbs
      ctx.fillStyle = 'rgba(255,255,255,0.09)';
      ctx.beginPath();
      ctx.arc(180, 250, 110, 0, Math.PI * 2);
      ctx.fill();
      ctx.beginPath();
      ctx.arc(900, 850, 140, 0, Math.PI * 2);
      ctx.fill();
    } else if (template === 'forest_vitality') {
      // Fresh forest green gradient
      const forestGrad = ctx.createLinearGradient(0, 0, 1080, 1350);
      forestGrad.addColorStop(0, '#1b5e20');
      forestGrad.addColorStop(0.3, '#2e7d32');
      forestGrad.addColorStop(0.6, '#43a047');
      forestGrad.addColorStop(0.85, '#66bb6a');
      forestGrad.addColorStop(1, '#81c784');
      ctx.fillStyle = forestGrad;
      ctx.fillRect(0, 0, 1080, 1350);
      
      // Nature light filtering through
      const forestLight = ctx.createRadialGradient(540, 200, 0, 540, 200, 700);
      forestLight.addColorStop(0, 'rgba(200,230,201,0.18)');
      forestLight.addColorStop(0.5, 'rgba(129,199,132,0.10)');
      forestLight.addColorStop(1, 'rgba(27,94,32,0.05)');
      ctx.fillStyle = forestLight;
      ctx.fillRect(0, 0, 1080, 1350);
      
      // Subtle leaf shapes
      ctx.fillStyle = 'rgba(255,255,255,0.08)';
      ctx.beginPath();
      ctx.arc(150, 350, 95, 0, Math.PI * 2);
      ctx.fill();
      ctx.beginPath();
      ctx.arc(930, 1000, 120, 0, Math.PI * 2);
      ctx.fill();
    } else if (template === 'golden_hour') {
      // Golden hour amber to peach gradient
      const goldenGrad = ctx.createLinearGradient(0, 0, 1080, 1350);
      goldenGrad.addColorStop(0, '#ff6f00');
      goldenGrad.addColorStop(0.25, '#ff8f00');
      goldenGrad.addColorStop(0.5, '#ffa726');
      goldenGrad.addColorStop(0.75, '#ffb74d');
      goldenGrad.addColorStop(1, '#ffcc80');
      ctx.fillStyle = goldenGrad;
      ctx.fillRect(0, 0, 1080, 1350);
      
      // Golden glow overlay
      const goldenGlow = ctx.createRadialGradient(540, 450, 0, 540, 450, 850);
      goldenGlow.addColorStop(0, 'rgba(255,193,7,0.20)');
      goldenGlow.addColorStop(0.5, 'rgba(255,152,0,0.12)');
      goldenGlow.addColorStop(1, 'rgba(230,74,25,0.10)');
      ctx.fillStyle = goldenGlow;
      ctx.fillRect(0, 0, 1080, 1350);
      
      // Warm light circles
      ctx.fillStyle = 'rgba(255,255,255,0.12)';
      ctx.beginPath();
      ctx.arc(220, 220, 130, 0, Math.PI * 2);
      ctx.fill();
      ctx.beginPath();
      ctx.arc(860, 1050, 150, 0, Math.PI * 2);
      ctx.fill();
    }

    // Define style colors based on template (all use white text on colorful backgrounds)
    const style = {
      bg: ['#ffffff', '#ffffff', '#ffffff'],
      orbA: 'rgba(255,255,255,0.08)',
      orbB: 'rgba(255,255,255,0.08)',
      accent: '#ffffff',
      text: '#ffffff',
      textSoft: 'rgba(255,255,255,0.92)',
      cardText: '#2e3a38', // Dark text for white panels
      panelEdge: 'rgba(255,255,255,0.40)'
    };
    
    // Header with shadow for visibility on colorful backgrounds
    ctx.textAlign = 'left';
    ctx.shadowColor = 'rgba(0,0,0,0.35)';
    ctx.shadowBlur = 16;
    ctx.shadowOffsetY = 4;
    ctx.fillStyle = style.accent;
    ctx.font = '600 22px Georgia, serif';
    ctx.fillText('ASK MIRROR TALK', 96, 114);

    ctx.fillStyle = style.textSoft;
    ctx.font = '600 17px -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif';
    ctx.fillText('Your weekly reflection recap', 96, 156);
    ctx.shadowColor = 'transparent';

    // Theme pill (if available) - enhanced for colorful backgrounds
    if (data.topTheme) {
      const themeLabel = truncateText(data.topTheme, 24);
      ctx.font = '600 21px -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif';
      const pillWidth = Math.max(216, Math.ceil(ctx.measureText(themeLabel).width + 92));
      const pillX = 1080 - pillWidth - 96;
      const pillY = 96;
      
      // Enhanced pill with better visibility
      ctx.shadowColor = 'rgba(0,0,0,0.25)';
      ctx.shadowBlur = 20;
      ctx.shadowOffsetY = 6;
      const themeGrad = ctx.createLinearGradient(pillX, pillY, pillX + pillWidth, pillY + 54);
      themeGrad.addColorStop(0, 'rgba(255,255,255,0.32)');
      themeGrad.addColorStop(1, 'rgba(255,255,255,0.18)');
      ctx.fillStyle = themeGrad;
      _roundRect(ctx, pillX, pillY, pillWidth, 54, 27);
      ctx.fill();
      ctx.shadowColor = 'transparent';
      
      ctx.strokeStyle = 'rgba(255,255,255,0.40)';
      ctx.lineWidth = 1.8;
      _roundRect(ctx, pillX, pillY, pillWidth, 54, 27);
      ctx.stroke();
      
      ctx.shadowColor = 'rgba(0,0,0,0.30)';
      ctx.shadowBlur = 12;
      ctx.shadowOffsetY = 3;
      ctx.fillStyle = '#ffffff';
      ctx.textAlign = 'center';
      ctx.textBaseline = 'middle';
      ctx.fillText(themeLabel, pillX + (pillWidth / 2), pillY + 27);
      ctx.textBaseline = 'alphabetic';
      ctx.shadowColor = 'transparent';
    }

    // Headline with shadow for better visibility
    ctx.shadowColor = 'rgba(0,0,0,0.40)';
    ctx.shadowBlur = 20;
    ctx.shadowOffsetY = 6;
    ctx.fillStyle = style.text;
    ctx.font = '700 64px Georgia, serif';
    ctx.textAlign = 'left';
    const headline = data.topTheme
      ? `This week I kept returning to ${data.topTheme}.`
      : 'This week I kept returning to reflection.';
    wrapCanvasText(ctx, headline, 110, 278, 860, 76, 3, 'left');
    ctx.shadowColor = 'transparent';

    // Metrics panel - enhanced white glass panel
    const metrics = [
      { label: 'QUESTIONS', value: data.questionCount },
      { label: 'SAVED', value: data.savedCount },
      { label: 'SHARED', value: data.shareCount }
    ];
    
    const panelY = 520;
    const panelWidth = 860;
    const panelHeight = 190;
    const panelX = 110;
    
    // White glass panel with enhanced shadow
    ctx.shadowColor = 'rgba(0,0,0,0.30)';
    ctx.shadowBlur = 40;
    ctx.shadowOffsetY = 18;
    const panelGrad = ctx.createLinearGradient(panelX, panelY, panelX + panelWidth, panelY + panelHeight);
    panelGrad.addColorStop(0, 'rgba(255,255,255,0.96)');
    panelGrad.addColorStop(1, 'rgba(255,255,255,0.92)');
    ctx.fillStyle = panelGrad;
    _roundRect(ctx, panelX, panelY, panelWidth, panelHeight, 30);
    ctx.fill();
    ctx.shadowColor = 'transparent';
    
    ctx.strokeStyle = 'rgba(255,255,255,0.50)';
    ctx.lineWidth = 1.5;
    _roundRect(ctx, panelX, panelY, panelWidth, panelHeight, 30);
    ctx.stroke();
    
    // Metrics grid - dark text on white panel
    const metricWidth = panelWidth / 3;
    const metricTextColor = '#2a2a2a';
    const metricAccentColor = '#666666';
    
    metrics.forEach((metric, index) => {
      const x = panelX + (index * metricWidth) + (metricWidth / 2);
      
      ctx.fillStyle = metricAccentColor;
      ctx.font = '700 15px -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif';
      ctx.textAlign = 'center';
      ctx.fillText(metric.label, x, panelY + 62);
      
      ctx.fillStyle = metricTextColor;
      ctx.font = '700 54px Georgia, serif';
      ctx.fillText(String(metric.value), x, panelY + 128);
    });

    // Supporting text with shadow
    const subtextY = panelY + panelHeight + 52;
    const subline = data.strongestDayCount >= 3
      ? `Strongest day: ${data.strongestDayCount} moments of reflection`
      : 'Small consistent returns are building momentum';
    
    ctx.shadowColor = 'rgba(0,0,0,0.35)';
    ctx.shadowBlur = 16;
    ctx.shadowOffsetY = 4;
    ctx.fillStyle = style.textSoft;
    ctx.font = '600 23px -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif';
    ctx.textAlign = 'center';
    ctx.fillText(subline, 1080 / 2, subtextY);
    ctx.shadowColor = 'transparent';

    // Saved insight — open-air pull-quote directly on gradient.
    // Per-template contrast: lighter-background templates (golden_hour, sunset_warmth)
    // switch to dark text so white-on-light readability issues are avoided entirely.
    // All other (dark/vibrant) templates keep white text with a strong drop-shadow.
    if (data.latestSavedInsight && data.latestSavedInsight.excerpt) {
      const useDarkQuote   = template === 'golden_hour' || template === 'sunset_warmth';
      const quoteTextColor   = useDarkQuote ? 'rgba(30,20,10,0.92)'  : 'rgba(255,255,255,0.97)';
      const quoteShadowColor = useDarkQuote ? 'rgba(255,255,255,0.60)' : 'rgba(0,0,0,0.55)';
      const quoteMarkColor   = useDarkQuote ? 'rgba(30,20,10,0.30)'  : 'rgba(255,255,255,0.45)';
      const separatorColor   = useDarkQuote ? 'rgba(30,20,10,0.22)'  : 'rgba(255,255,255,0.28)';

      const quoteY = subtextY + 58;

      // Thin decorative separator
      ctx.strokeStyle = separatorColor;
      ctx.lineWidth = 1.2;
      ctx.beginPath();
      ctx.moveTo(200, quoteY);
      ctx.lineTo(880, quoteY);
      ctx.stroke();

      // Pre-process excerpt to a meaningful boundary so the visible text always
      // ends on a complete sentence or clause, not mid-word.
      const _raw = String(data.latestSavedInsight.excerpt || '').trim();
      const MAX_CHARS = 165;
      let excerpt = _raw;
      if (_raw.length > MAX_CHARS) {
        const chunk = _raw.slice(0, MAX_CHARS);
        const sentEnd = Math.max(
          chunk.lastIndexOf('. '), chunk.lastIndexOf('! '), chunk.lastIndexOf('? ')
        );
        if (sentEnd > MAX_CHARS * 0.45) {
          excerpt = _raw.slice(0, sentEnd + 1);
        } else {
          const clauseEnd = chunk.lastIndexOf(', ');
          excerpt = clauseEnd > MAX_CHARS * 0.45
            ? _raw.slice(0, clauseEnd) + '\u2026'
            : chunk.trimEnd().replace(/[.,;:-]+$/, '') + '\u2026';
        }
      }

      // Strong shadow for both quote mark and text — guarantees legibility on
      // all gradient hues without needing a background panel.
      ctx.shadowColor    = quoteShadowColor;
      ctx.shadowBlur     = 22;
      ctx.shadowOffsetY  = 4;

      // Large decorative open-quote mark
      ctx.fillStyle  = quoteMarkColor;
      ctx.font       = '700 80px Georgia, serif';
      ctx.textAlign  = 'left';
      ctx.fillText('\u201C', 110, quoteY + 96);

      // Quote text — 3 lines max (more complete than 2), italic serif, colour-safe per template
      ctx.fillStyle = quoteTextColor;
      ctx.font      = 'italic 400 29px Georgia, serif';
      ctx.textAlign = 'left';
      wrapCanvasText(ctx, excerpt, 168, quoteY + 58, 800, 44, 3, 'left');
      ctx.shadowColor = 'transparent';
    }

    // Footer with QR code and "Scan to reflect" (uses our new card template system)
    const footerY = 1350 - 188;
    drawShareFooter(ctx, style, 1080, footerY, 'center', {
      qrModuleSize: 4,
      qrQuiet: 4,
      chipWidth: 484,
      chipHeight: 188
    });

    return canvas.toDataURL('image/png');
  }

  function shareWeeklyRecapArtifact(recap) {
    const data = recap || getWeeklyRecapData();
    if (!data) return;

    // Use full size (scale=1.0) for sharing
    const dataUrl = buildWeeklyRecapShareCard(data, 1.0);
    const caption = data.topTheme
      ? `My Ask Mirror Talk weekly recap: ${data.questionCount} questions, ${data.savedCount} saved insights, and a week centered on ${data.topTheme}.`
      : `My Ask Mirror Talk weekly recap: ${data.questionCount} questions, ${data.savedCount} saved insights, and a stronger reflection rhythm.`;
    showShareModal(dataUrl, `${caption}\n\nhttps://mirrortalkpodcast.com/ask-mirror-talk`, {
      title: 'Share your weekly recap',
      hint: 'Turn your week of reflection into a premium card that invites others into the experience.',
      filename: 'mirror-talk-weekly-recap.png'
    });
  }

  function renderWeeklyRecap() {
    if (!weeklyRecapCard) return;

    const recap = getWeeklyRecapData();
    if (!recap) {
      weeklyRecapCard.innerHTML = '';
      weeklyRecapCard.style.display = 'none';
      return;
    }

    // Generate smaller preview version (0.35 scale) for inline display using card templates
    const cardImageUrl = buildWeeklyRecapShareCard(recap, 0.35);

    weeklyRecapCard.innerHTML = `
      <div class="amt-weekly-recap-inner">
        <div class="amt-weekly-recap-card-container">
          <img src="${cardImageUrl}" alt="Weekly Recap Card" class="amt-weekly-recap-card-image" />
        </div>
        <div class="amt-weekly-recap-actions">
          <button type="button" class="amt-weekly-recap-btn amt-weekly-recap-btn-primary" data-q="${escapeHtml(recap.recapPrompt)}">${recap.topTheme ? `Continue with ${escapeHtml(recap.topTheme)}` : 'Continue reflecting'}</button>
          <button type="button" class="amt-weekly-recap-btn amt-weekly-recap-btn-secondary">Open saved insights</button>
          <button type="button" class="amt-weekly-recap-btn amt-weekly-recap-btn-share">Share this week</button>
        </div>
      </div>
    `;
    weeklyRecapCard.style.display = '';

    const primaryBtn = weeklyRecapCard.querySelector('.amt-weekly-recap-btn-primary');
    if (primaryBtn) {
      primaryBtn.addEventListener('click', () => {
        submitRhythmQuestion(primaryBtn.dataset.q || recap.recapPrompt, 'weekly_recap', {
          theme: recap.topTheme || null
        });
      });
    }

    const secondaryBtn = weeklyRecapCard.querySelector('.amt-weekly-recap-btn-secondary');
    if (secondaryBtn) {
      secondaryBtn.addEventListener('click', () => {
        const btn = document.getElementById('amt-insights-btn');
        if (btn) btn.click();
      });
    }

    const shareBtn = weeklyRecapCard.querySelector('.amt-weekly-recap-btn-share');
    if (shareBtn) {
      shareBtn.addEventListener('click', () => {
        shareWeeklyRecapArtifact(recap);
      });
    }
  }

  function renderMomentumCard(stats) {
    if (!momentumCard) return;
    const s = stats || loadStats();
    const themesCount = s.themesExplored && typeof s.themesExplored.size === 'number' ? s.themesExplored.size : 0;
    const badgesCount = s.earnedBadges && typeof s.earnedBadges.size === 'number' ? s.earnedBadges.size : 0;
    const savedCount = Number(s.insightsSaved || 0);
    const sharedCount = Number(s.sharesCount || 0);
    const questions = Number(s.totalQuestions || 0);
    const streak = Number(s.currentStreak || 0);
    const askedToday = s.lastSessionDate === todayStr() ? Number(s.dailyQuestions || 0) : 0;
    const title = streak >= 3
      ? `${streak} days of returning.`
      : questions > 0
        ? 'Your rhythm is beginning to take shape.'
        : 'Your reflection rhythm can begin today.';
    const text = questions > 0
      ? `You have asked ${questions} question${questions === 1 ? '' : 's'}, explored ${themesCount} topic${themesCount === 1 ? '' : 's'}, saved ${savedCount} insight${savedCount === 1 ? '' : 's'}, and shared ${sharedCount} reflection${sharedCount === 1 ? '' : 's'}.`
      : 'Start with one honest question, then let your rhythm grow through small, steady returns.';
    const todayText = askedToday > 0
      ? `${askedToday} reflection${askedToday === 1 ? '' : 's'} today.`
      : 'No question asked yet today.';

    momentumCard.innerHTML = `
      <div class="amt-momentum-card-inner">
        <div class="amt-momentum-copy">
          <span class="amt-momentum-kicker">Your Momentum</span>
          <h3 class="amt-momentum-title">${escapeHtml(title)}</h3>
          <p class="amt-momentum-text">${escapeHtml(text)}</p>
        </div>
        <div class="amt-momentum-grid" aria-label="Reflection progress">
          <span class="amt-momentum-pill"><strong>${streak}</strong><em>day streak</em></span>
          <span class="amt-momentum-pill"><strong>${questions}</strong><em>questions</em></span>
          <span class="amt-momentum-pill"><strong>${themesCount}</strong><em>topics</em></span>
          <span class="amt-momentum-pill"><strong>${badgesCount}</strong><em>badges</em></span>
        </div>
        <div class="amt-momentum-next">
          <span>${escapeHtml(todayText)}</span>
          <button type="button" class="amt-momentum-ask-btn">${askedToday > 0 ? 'Ask another reflection' : 'Ask today’s reflection'}</button>
        </div>
      </div>
    `;
    momentumCard.style.display = '';

    const askBtn = momentumCard.querySelector('.amt-momentum-ask-btn');
    if (askBtn) {
      askBtn.addEventListener('click', () => {
        submitRhythmQuestion(
          getRhythmReflectionQuestion('', { preferQotd: askedToday === 0 }),
          'rhythm_momentum',
          { asked_today: askedToday }
        );
      });
    }
  }

  function renderStatsBar(stats) {
    const bar = document.getElementById('amt-stats-bar');
    if (!bar) return;
    const safeStats = stats || loadStats();
    const themesExplored = safeStats.themesExplored && typeof safeStats.themesExplored.size === 'number'
      ? safeStats.themesExplored
      : new Set(safeStats.themesExplored || []);
    const earnedBadges = safeStats.earnedBadges && typeof safeStats.earnedBadges.size === 'number'
      ? safeStats.earnedBadges
      : new Set(safeStats.earnedBadges || []);
    const hasProgress = Number(safeStats.totalQuestions || 0) > 0 ||
                        Number(safeStats.currentStreak || 0) > 0 ||
                        themesExplored.size > 0 ||
                        earnedBadges.size > 0;

    bar.classList.toggle('amt-stats-bar-empty', !hasProgress);
    document.getElementById('amt-streak-value').textContent   = Number(safeStats.currentStreak || 0);
    document.getElementById('amt-questions-value').textContent = Number(safeStats.totalQuestions || 0);
    document.getElementById('amt-themes-value').textContent   = themesExplored.size;
    document.getElementById('amt-badge-count').textContent    = earnedBadges.size;

    // Update streak count inside the dark-mode toggle pill
    const toggleStreak = document.getElementById('amt-toggle-streak');
    if (toggleStreak) {
      if (safeStats.currentStreak >= 1) {
        toggleStreak.textContent = '\uD83D\uDD25' + safeStats.currentStreak;
        toggleStreak.style.display = '';
      } else {
        toggleStreak.style.display = 'none';
      }
    }

    // Pulse the streak icon when streak > 0
    const streakIcon = bar.querySelector('.amt-stat-streak .amt-stat-icon');
    if (streakIcon) {
      streakIcon.classList.toggle('amt-streak-active', safeStats.currentStreak >= 3);
    }

    bar.style.display = '';

    // First-time hint: wobble the badge button so users discover it's tappable
    const btn = document.getElementById('amt-badges-btn');
    if (btn && !btn.dataset.hinted) {
      btn.dataset.hinted = '1';
      btn.classList.add('amt-badges-btn-hint');
      btn.addEventListener('animationend', () => btn.classList.remove('amt-badges-btn-hint'), { once: true });
    }

    let prompt = bar.querySelector('.amt-stats-prompt');
    if (!prompt) {
      prompt = document.createElement('div');
      prompt.className = 'amt-stats-prompt';
      bar.appendChild(prompt);
    }
    prompt.innerHTML = `
      <span class="amt-stats-prompt-kicker">${hasProgress ? 'Next up' : 'Start here'}</span>
      <span class="amt-stats-prompt-text">${escapeHtml(hasProgress ? getDailyMomentumText(safeStats) : 'Your reflection rhythm can begin with one honest question.')}</span>
      <span class="amt-stats-prompt-subtext">${safeStats.currentStreak >= 3 ? 'Your streak is active and your return rhythm is building.' : 'Small consistent returns matter more than intensity.'}</span>
    `;
    updateWorkflowBarState();
  }

  function renderBadgeShelf(stats) {
    const shelf = document.getElementById('amt-badge-shelf');
    if (!shelf) return;
    shelf.innerHTML = '';

    const nextUnlocks = getNextUnlocks(stats);
    const overview = document.createElement('div');
    overview.className = 'amt-badge-overview';
    overview.innerHTML = `
      <div class="amt-badge-overview-copy">
        <span class="amt-badge-overview-kicker">Your momentum</span>
        <h4 class="amt-badge-overview-title">${escapeHtml(getDailyMomentumText(stats))}</h4>
        <p class="amt-badge-overview-subtitle">${stats.currentStreak >= 1
          ? `You are on a ${stats.currentStreak}-day streak with ${stats.earnedBadges.size} badge${stats.earnedBadges.size === 1 ? '' : 's'} earned.`
          : `Your first streak starts the moment you ask today.`}</p>
      </div>
      <div class="amt-badge-overview-actions">
        <button type="button" class="amt-share-progress-btn amt-share-progress-btn-primary">📊 Share my progress</button>
        ${stats.currentStreak >= 3 ? `<button type="button" class="amt-share-progress-btn amt-share-progress-btn-secondary">🔥 Share my ${stats.currentStreak}-day streak</button>` : ''}
      </div>
    `;
    shelf.appendChild(overview);

    const unlockGrid = document.createElement('div');
    unlockGrid.className = 'amt-next-unlocks';
    unlockGrid.innerHTML = nextUnlocks.map(item => {
      const pct = Math.max(0, Math.min(100, Math.round((item.current / item.target) * 100)));
      return `
        <div class="amt-next-unlock-card amt-next-unlock-${item.accent}">
          <span class="amt-next-unlock-label">${escapeHtml(item.detail)}</span>
          <strong class="amt-next-unlock-title">${escapeHtml(item.label)}</strong>
          <div class="amt-next-unlock-meter"><span style="width:${pct}%"></span></div>
        </div>
      `;
    }).join('');
    if (nextUnlocks.length) shelf.appendChild(unlockGrid);

    const badgeGrid = document.createElement('div');
    badgeGrid.className = 'amt-badge-grid';

    for (const badge of AMT_BADGES) {
      const earned = stats.earnedBadges.has(badge.id);
      const el = document.createElement('div');
      el.className = 'amt-badge' + (earned ? ' amt-badge-earned' : ' amt-badge-locked');
      el.title = earned ? badge.name + ': ' + badge.desc : badge.desc + ' (locked)';
      el.innerHTML = `<span class="amt-badge-emoji">${badge.emoji}</span><span class="amt-badge-name">${badge.name}</span>`;
      if (earned) {
        const shareBtn = document.createElement('button');
        shareBtn.className = 'amt-badge-share-btn';
        shareBtn.title = 'Share this badge';
        shareBtn.textContent = '📤';
        shareBtn.addEventListener('click', (e) => {
          e.stopPropagation();
          shareMilestone(badge, 'badge');
        });
        el.appendChild(shareBtn);
      }
      badgeGrid.appendChild(el);
    }
    shelf.appendChild(badgeGrid);

    const progressBtn = overview.querySelector('.amt-share-progress-btn-primary');
    if (progressBtn) progressBtn.addEventListener('click', () => shareMilestone(null, 'progress'));

    const streakBtn = overview.querySelector('.amt-share-progress-btn-secondary');
    if (streakBtn) streakBtn.addEventListener('click', () => shareMilestone(null, 'streak'));
  }

  // Confetti burst (lightweight, no library)
  function launchConfetti() {
    const canvas = document.createElement('canvas');
    canvas.style.cssText = 'position:fixed;top:0;left:0;width:100%;height:100%;pointer-events:none;z-index:99999';
    document.body.appendChild(canvas);
    const ctx = canvas.getContext('2d');
    canvas.width  = window.innerWidth;
    canvas.height = window.innerHeight;

    const colours = ['#f7c948','#e84393','#3ecf8e','#7c5cbf','#ff6b35','#4ecdc4'];
    const pieces  = Array.from({ length: 80 }, () => ({
      x: Math.random() * canvas.width,
      y: -10 - Math.random() * 40,
      r: 4 + Math.random() * 5,
      c: colours[Math.floor(Math.random() * colours.length)],
      vx: (Math.random() - 0.5) * 4,
      vy: 2 + Math.random() * 3,
      rot: Math.random() * Math.PI * 2,
      vr: (Math.random() - 0.5) * 0.2,
    }));

    let frame = 0;
    function draw() {
      ctx.clearRect(0, 0, canvas.width, canvas.height);
      pieces.forEach(p => {
        p.x  += p.vx;
        p.y  += p.vy;
        p.rot += p.vr;
        ctx.save();
        ctx.translate(p.x, p.y);
        ctx.rotate(p.rot);
        ctx.fillStyle = p.c;
        ctx.globalAlpha = Math.max(0, 1 - frame / 90);
        ctx.fillRect(-p.r, -p.r / 2, p.r * 2, p.r);
        ctx.restore();
      });
      frame++;
      if (frame < 100) requestAnimationFrame(draw);
      else canvas.remove();
    }
    requestAnimationFrame(draw);
  }

  function showMilestoneToast(emoji, headline, sub, badge) {
    const toast = document.getElementById('amt-milestone-toast');
    if (!toast) return;
    toast.innerHTML = `<span class="amt-toast-emoji">${emoji}</span><div><strong>${headline}</strong><span>${sub}</span></div>`;
    toast.style.display = '';
    toast.classList.add('amt-toast-in');
    launchConfetti();

    // Add share button for badge toasts after a short delay
    if (badge) {
      setTimeout(() => {
        if (!toast.querySelector('.amt-toast-share-btn')) {
          const shareBtn = document.createElement('button');
          shareBtn.className = 'amt-toast-share-btn';
          shareBtn.textContent = '📤 Share';
          shareBtn.addEventListener('click', (e) => {
            e.stopPropagation();
            shareMilestone(badge, 'badge');
          });
          toast.appendChild(shareBtn);
        }
      }, 800);
    }

    setTimeout(() => {
      toast.classList.remove('amt-toast-in');
      toast.classList.add('amt-toast-out');
      setTimeout(() => {
        toast.style.display = 'none';
        toast.classList.remove('amt-toast-out');
      }, 500);
    }, 3500);
  }

  const STREAK_MILESTONES    = new Set([3, 7, 14, 30, 60, 100]);
  const DAILY_DEPTH_MILESTONES = new Set([3, 5, 10]); // questions-per-day celebrations

  // Map daily question count to a celebratory message
  function dailyDepthToast(count) {
    if (count === 3)  return { emoji: '🌊', headline: 'Deep session!',      sub: '3 questions today — you\'re really exploring.' };
    if (count === 5)  return { emoji: '🔮', headline: 'On a roll!',          sub: '5 questions in one sitting — incredible focus.' };
    if (count === 10) return { emoji: '🚀', headline: 'Unstoppable today!', sub: '10 questions in a day — that\'s dedication.' };
    return null;
  }

  function onQuestionAnswered(questionText, themeHint) {
    let stats = loadStats();
    const prevStreak       = stats.currentStreak;
    const prevDailyCount   = stats.dailyQuestions || 0;
    const reviveUsed       = shouldConsumeStreakRevive(stats);

    stats = recordQuestion(stats, themeHint, questionText);
    logActivity('question', { theme: themeHint || inferTheme(questionText, '') || null });
    const newBadges = checkAndAwardBadges(stats);
    saveStats(stats);
    renderStatsBar(stats);
    renderMomentumCard(stats);
    renderStreakRevivalCard(stats);
    renderWeeklyRecap();

    // Toggle the questions-active glow when ≥ 3 questions asked today
    const questionsIcon = document.querySelector('.amt-stat-questions .amt-stat-value');
    if (questionsIcon) {
      questionsIcon.classList.toggle('amt-questions-active', stats.dailyQuestions >= 3);
    }

    const reviveDelay = reviveUsed ? 4200 : 0;
    if (reviveUsed) {
      showMilestoneToast('✨', 'Streak restored', `Your reflection pass kept your ${stats.currentStreak}-day streak alive.`);
    }

    // Streak milestone toast
    if (stats.currentStreak !== prevStreak && STREAK_MILESTONES.has(stats.currentStreak)) {
      setTimeout(() => {
        showMilestoneToast('🔥', `${stats.currentStreak}-day streak!`, 'Keep the wisdom flowing.');
      }, reviveDelay);
    }

    // Daily-depth milestone toast (fires only on the exact crossing, not every question after)
    if (
      stats.dailyQuestions !== prevDailyCount &&
      DAILY_DEPTH_MILESTONES.has(stats.dailyQuestions)
    ) {
      const toastData = dailyDepthToast(stats.dailyQuestions);
      if (toastData) {
        const delay = reviveDelay + (STREAK_MILESTONES.has(stats.currentStreak) ? 4200 : 0);
        setTimeout(() => showMilestoneToast(toastData.emoji, toastData.headline, toastData.sub), delay);
      }
    }

    // New badge toasts (queue sequentially after any other toasts)
    const baseDelay = (
      reviveDelay +
      (STREAK_MILESTONES.has(stats.currentStreak) && stats.currentStreak !== prevStreak ? 4200 : 0) +
      (DAILY_DEPTH_MILESTONES.has(stats.dailyQuestions) && stats.dailyQuestions !== prevDailyCount ? 4200 : 0)
    );
    newBadges.forEach((badge, i) => {
      setTimeout(() => {
        showMilestoneToast(badge.emoji, `Badge unlocked: ${badge.name}`, badge.desc, badge);
      }, baseDelay + i * 4200);
    });
  }

  // Badge shelf toggle
  const badgesBtn = document.getElementById('amt-badges-btn');
  const badgeShelf = document.getElementById('amt-badge-shelf');
  if (badgesBtn && badgeShelf) {
    badgesBtn.addEventListener('click', () => {
      runWorkflowAction('progress', { persist: true, scroll: true });
      badgeShelf.style.display = '';
      renderBadgeShelf(loadStats());
    });
  }

  // Track citation clicks for the Deep Diver badge
  document.addEventListener('click', (e) => {
    if (e.target.closest('.citation-link')) {
      try {
        const s = loadStats();
        s.citationsClicked = (s.citationsClicked || 0) + 1;
        const newBadges = checkAndAwardBadges(s);
        saveStats(s);
        newBadges.forEach(badge => showMilestoneToast(badge.emoji, `Badge unlocked: ${badge.name}`, badge.desc, badge));
      } catch (e2) {}
    }
  });

  // ========================================
  // Onboarding Flow (first-visit 3-step guide)
  // ========================================
  (function initOnboarding() {
    // Early exit conditions - check these first before any UI work
    let resumeOnboarding = false;
    try {
      if (localStorage.getItem('amt_onboarded')) return;
      
      // Skip onboarding if page was just reloaded by service worker
      if (sessionStorage.getItem('amt_sw_reloaded')) {
        if (localStorage.getItem('amt_onboarding_started')) {
          resumeOnboarding = true;
        } else {
          return;
        }
      }
      
      // Skip onboarding if we're in standalone mode (already installed)
      const isStandalone = window.matchMedia('(display-mode: standalone)').matches ||
                           window.navigator.standalone === true;
      if (isStandalone) {
        localStorage.setItem('amt_onboarded', '1');
        localStorage.removeItem('amt_onboarding_started');
        return;
      }
      
      // Mark as started to prevent double-show on SW reload
      localStorage.setItem('amt_onboarding_started', '1');
    } catch (e) { 
      return; 
    }

    const overlay = document.getElementById('amt-onboarding-overlay');
    if (!overlay) return;

    const steps = [
      {
        emoji: '🎙️',
        heading: 'Welcome to Ask Mirror Talk',
        body: 'Explore the wisdom in over 100 Mirror Talk podcast episodes — just ask a question in plain English.',
        btnLabel: 'What can I ask? →',
      },
      {
        emoji: '💡',
        heading: 'Try questions like these',
        body: 'Click any example to ask it right now:',
        examples: [
          'How do I deal with grief and loss?',
          'What does Mirror Talk say about forgiveness?',
          'How can I overcome fear and self-doubt?',
        ],
        btnLabel: 'Got it! →',
      },
      {
        emoji: '🔥',
        heading: 'Build your streak',
        body: 'Come back daily to keep your streak alive, explore themes, and earn badges as you grow.',
        btnLabel: 'Start exploring',
      },
    ];

    let currentStep = 0;

    function renderStep(idx) {
      const step = steps[idx];
      const dotsHtml = steps.map((_, i) =>
        `<div class="amt-onboarding-dot${i === idx ? ' active' : ''}"></div>`
      ).join('');

      const examplesHtml = step.examples
        ? `<div class="amt-onboarding-examples">${step.examples.map(q =>
            `<button type="button" class="amt-onboarding-example" data-q="${q.replace(/"/g,'&quot;')}">${q}</button>`
          ).join('')}</div>`
        : '';

      overlay.innerHTML = `
        <div class="amt-onboarding-overlay">
          <div class="amt-onboarding-card">
            <div class="amt-onboarding-dots">${dotsHtml}</div>
            <div style="font-size:2.5rem;margin-bottom:10px;">${step.emoji}</div>
            <h2>${step.heading}</h2>
            <p>${step.body}</p>
            ${examplesHtml}
            <button type="button" class="amt-onboarding-next">${step.btnLabel}</button>
            <button type="button" class="amt-onboarding-skip">Skip intro</button>
          </div>
        </div>
      `;
      overlay.style.display = '';

      overlay.querySelector('.amt-onboarding-next').addEventListener('click', () => {
        if (currentStep < steps.length - 1) {
          currentStep++;
          renderStep(currentStep);
        } else {
          closeOnboarding();
        }
      });

      overlay.querySelector('.amt-onboarding-skip').addEventListener('click', closeOnboarding);

      overlay.querySelectorAll('.amt-onboarding-example').forEach(btn => {
        btn.addEventListener('click', () => {
          closeOnboarding();
          input.value = btn.dataset.q;
          input.focus();
          form.dispatchEvent(new Event('submit', { cancelable: true }));
        });
      });
    }

    function closeOnboarding() {
      overlay.style.display = 'none';
      try { 
        localStorage.setItem('amt_onboarded', '1');
        localStorage.removeItem('amt_onboarding_started');
      } catch (e) {}
    }

    // Show after a short delay so the page renders first.
    // If we are resuming after an SW-triggered reload, render immediately so
    // the intro doesn't feel like it flashed and vanished.
    setTimeout(() => renderStep(0), resumeOnboarding ? 0 : 800);
  })();

  // ========================================
  // Dark Mode Toggle
  // ========================================
  (function initDarkMode() {
    const toggleBtn = document.getElementById('amt-dark-mode-toggle');
    if (!toggleBtn) return;

    function applyMode(lightMode) {
      document.body.classList.toggle('amt-light-mode', lightMode);
      toggleBtn.textContent = lightMode ? '🌙' : '☀️';
      toggleBtn.title = lightMode ? 'Switch to dark mode' : 'Switch to light mode';
      try { localStorage.setItem('amt_light_mode', lightMode ? '1' : '0'); } catch (e) {}
    }

    // Restore saved preference
    try {
      const saved = localStorage.getItem('amt_light_mode');
      if (saved === '1') applyMode(true);
    } catch (e) {}

    toggleBtn.addEventListener('click', () => {
      applyMode(!document.body.classList.contains('amt-light-mode'));
    });
  })();

  // Initialise stats bar on page load
  try {
    const initStats = loadStats();
    // Keep the progress summary stable above the workflow bar on every load.
    // PWA display-mode detection can vary across refreshes, so the anchor should
    // not depend on standalone mode or prior activity.
    renderStatsBar(initStats);
    renderMomentumCard(initStats);
    // Restore daily-depth glow if the user already hit >= 3 questions today.
    const questionsIcon = document.querySelector('.amt-stat-questions .amt-stat-value');
    const isToday = initStats.lastSessionDate === todayStr();
    if (questionsIcon && isToday && (initStats.dailyQuestions || 0) >= 3) {
      questionsIcon.classList.add('amt-questions-active');
    }
    renderStreakRevivalCard(initStats);
    renderWeeklyRecap();
  } catch (e) {}

  // ========================================
  // Social Share Card (Canvas → PNG)
  // ========================================

  /**
   * Draw a branded 1200×630 share card on a canvas and return it as a PNG dataURL.
   * @param {Object} badge  — one entry from AMT_BADGES (may be null for a streak card)
   * @param {Object} stats  — current gamification stats
   * @param {string} type   — 'badge' | 'streak' | 'progress'
   */
  function getAchievementTheme(type, badge) {
    if (type === 'streak') {
      return {
        label: 'Daily rhythm',
        bg: ['#28140f', '#8a3d20', '#f0a63a'],
        ink: '#fff7e8',
        accent: '#ffd180',
        glow: 'rgba(255,178,78,0.34)'
      };
    }
    if (type === 'progress') {
      return {
        label: 'Growth journey',
        bg: ['#102821', '#246859', '#c4a766'],
        ink: '#f8fff9',
        accent: '#dff5be',
        glow: 'rgba(194,238,187,0.28)'
      };
    }
    const badgeThemes = {
      first_step: ['#17342c', '#3f8a6d', '#e5c588'],
      curious: ['#111f3a', '#375e9d', '#d8b86a'],
      streak_3: ['#27120e', '#9b4327', '#ffc061'],
      streak_7: ['#18213d', '#6a5aad', '#e2c879'],
      streak_14: ['#142e2b', '#4a9a82', '#f2d590'],
      streak_30: ['#151526', '#5c6fb4', '#d7ecff'],
      explorer: ['#16241b', '#3d7553', '#d9b76d'],
      deep_diver: ['#101b2f', '#286b85', '#a7efff'],
      sharer: ['#2d1830', '#9e5273', '#ffd1bc'],
      guide: ['#22172e', '#684c8f', '#ffc9a8'],
      collector: ['#2a2517', '#81713a', '#f1db92'],
      night_owl: ['#10111f', '#38406f', '#d7d3ff'],
      wisdom_seeker: ['#211725', '#70456f', '#f4c6d8'],
      deep_session: ['#102635', '#317b95', '#b5ebf2'],
      completionist: ['#1b1710', '#876529', '#ffe3a1']
    };
    const palette = badgeThemes[badge && badge.id] || ['#171f2b', '#536376', '#d8be77'];
    return {
      label: 'Badge unlocked',
      bg: palette,
      ink: '#fff8ee',
      accent: '#ffe0a3',
      glow: 'rgba(255,224,163,0.26)'
    };
  }

  function completeAchievementSentence(text) {
    const clean = normalizeReflectionText(text).replace(/[,:;]+$/g, '').trim();
    if (!clean) return '';
    return /[.!?]$/.test(clean) ? clean : `${clean}.`;
  }

  function getAchievementShareCopy(badge, stats, type) {
    const safeStats = stats || {};
    if (type === 'streak') {
      const days = Math.max(1, Number(safeStats.currentStreak || safeStats.maxStreak || 1));
      return {
        theme: 'Streak',
        eyebrow: 'Ask Mirror Talk',
        metric: String(days),
        metricLabel: days === 1 ? 'Day streak' : 'Day streak',
        headline: completeAchievementSentence(`${days} day${days === 1 ? '' : 's'} of returning to reflection is becoming a rhythm worth honoring`),
        supporting: completeAchievementSentence('Small daily returns can become a steadier inner life'),
        badgeLabel: 'Daily rhythm'
      };
    }
    if (type === 'progress') {
      const questions = Math.max(0, Number(safeStats.totalQuestions || 0));
      const streak = Math.max(0, Number(safeStats.currentStreak || 0));
      const badges = safeStats.earnedBadges && safeStats.earnedBadges.size ? safeStats.earnedBadges.size : 0;
      return {
        theme: 'Progress',
        eyebrow: 'Ask Mirror Talk',
        metric: String(questions),
        metricLabel: questions === 1 ? 'Question asked' : 'Questions asked',
        headline: completeAchievementSentence('Every honest question is part of a larger journey toward wisdom'),
        supporting: completeAchievementSentence(`${streak} day${streak === 1 ? '' : 's'} in rhythm and ${badges} badge${badges === 1 ? '' : 's'} earned so far`),
        badgeLabel: 'Growth journey'
      };
    }
    const cleanBadge = badge || {};
    const badgeCopy = {
      first_step: 'The first honest question has opened the door to a deeper journey.',
      curious: 'Curiosity is becoming a practice, not just a passing moment.',
      streak_3: 'Three steady returns show that reflection is becoming part of your rhythm.',
      streak_7: 'A full week of reflection is a quiet kind of devotion.',
      streak_14: 'Two weeks of returning shows a heart learning steadiness.',
      streak_30: 'Thirty days of reflection is a rhythm worth honoring and protecting.',
      explorer: 'You are exploring more of your inner world with courage and curiosity.',
      deep_diver: 'You followed the source deeper and let wisdom have more room to speak.',
      sharer: 'You passed a reflection forward and invited someone else to pause.',
      guide: 'Your reflections are becoming invitations for others to slow down and listen.',
      collector: 'You are gathering insight with care and returning to what matters.',
      night_owl: 'Even late in the day, you made room for an honest question.',
      wisdom_seeker: 'Your questions are becoming a meaningful path of wisdom.',
      deep_session: 'You stayed with the reflection long enough for something deeper to open.',
      completionist: 'You explored the whole landscape and made curiosity a practice.'
    };
    const name = String(cleanBadge.name || 'Reflection Badge').trim();
    return {
      theme: name,
      eyebrow: 'Ask Mirror Talk',
      metric: String(cleanBadge.emoji || '✦'),
      metricLabel: 'Badge earned',
      headline: completeAchievementSentence(badgeCopy[cleanBadge.id] || `The ${name} badge marks a meaningful step in your reflection journey`),
      supporting: completeAchievementSentence('A small moment of progress is still progress worth celebrating'),
      badgeLabel: 'Badge unlocked'
    };
  }

  function drawAchievementStatPill(ctx, x, y, w, h, text, accent) {
    ctx.fillStyle = 'rgba(255,255,255,0.14)';
    _roundRect(ctx, x, y, w, h, h / 2);
    ctx.fill();
    ctx.strokeStyle = 'rgba(255,255,255,0.28)';
    ctx.lineWidth = 1.4;
    _roundRect(ctx, x, y, w, h, h / 2);
    ctx.stroke();
    ctx.fillStyle = accent || '#ffe0a3';
    ctx.font = '800 23px -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif';
    ctx.textAlign = 'center';
    ctx.fillText(text, x + w / 2, y + Math.round(h / 2) + 8);
  }

  function buildShareCard(badge, stats, type) {
    const W = 1080, H = 1350;
    const canvas = document.createElement('canvas');
    canvas.width  = W;
    canvas.height = H;
    const ctx = canvas.getContext('2d');
    const cardType = type || 'progress';
    const theme = getAchievementTheme(cardType, badge);
    const copy = getAchievementShareCopy(badge, stats, cardType);

    const grad = ctx.createLinearGradient(0, 0, W, H);
    grad.addColorStop(0, theme.bg[0]);
    grad.addColorStop(0.56, theme.bg[1]);
    grad.addColorStop(1, theme.bg[2]);
    ctx.fillStyle = grad;
    ctx.fillRect(0, 0, W, H);

    const glowOne = ctx.createRadialGradient(W * 0.18, H * 0.18, 0, W * 0.18, H * 0.18, 470);
    glowOne.addColorStop(0, theme.glow);
    glowOne.addColorStop(0.62, 'rgba(255,255,255,0.05)');
    glowOne.addColorStop(1, 'rgba(255,255,255,0)');
    ctx.fillStyle = glowOne;
    ctx.fillRect(0, 0, W, H);

    const glowTwo = ctx.createRadialGradient(W * 0.82, H * 0.78, 0, W * 0.82, H * 0.78, 520);
    glowTwo.addColorStop(0, 'rgba(255,255,255,0.24)');
    glowTwo.addColorStop(0.5, 'rgba(255,255,255,0.08)');
    glowTwo.addColorStop(1, 'rgba(255,255,255,0)');
    ctx.fillStyle = glowTwo;
    ctx.fillRect(0, 0, W, H);

    ctx.strokeStyle = 'rgba(255,255,255,0.20)';
    ctx.lineWidth = 3;
    _roundRect(ctx, 34, 34, W - 68, H - 68, 46);
    ctx.stroke();
    ctx.strokeStyle = 'rgba(255,255,255,0.10)';
    ctx.lineWidth = 1.5;
    _roundRect(ctx, 56, 56, W - 112, H - 112, 36);
    ctx.stroke();

    ctx.strokeStyle = 'rgba(255,255,255,0.13)';
    ctx.lineWidth = 1.2;
    for (let i = 0; i < 7; i++) {
      const y = 160 + i * 116;
      ctx.beginPath();
      ctx.moveTo(96, y);
      ctx.lineTo(W - 96, y - 12);
      ctx.stroke();
    }

    ctx.textAlign = 'center';
    ctx.fillStyle = theme.ink;
    ctx.font = '800 26px Georgia, "Times New Roman", serif';
    ctx.fillText(copy.eyebrow.toUpperCase(), W / 2, 114);

    ctx.fillStyle = 'rgba(255,255,255,0.74)';
    ctx.font = '700 17px -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif';
    ctx.fillText(copy.badgeLabel.toUpperCase(), W / 2, 152);

    if (cardType === 'badge') {
      ctx.font = '112px serif';
      ctx.fillText(copy.metric, W / 2, 304);
    } else {
      ctx.fillStyle = theme.accent;
      ctx.font = '900 152px Georgia, "Times New Roman", serif';
      ctx.fillText(copy.metric, W / 2, 330);
    }

    ctx.fillStyle = 'rgba(255,255,255,0.76)';
    ctx.font = '800 24px -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif';
    ctx.fillText(copy.metricLabel.toUpperCase(), W / 2, 382);

    const pillText = String(copy.theme || 'Progress');
    ctx.font = '800 23px -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif';
    drawAchievementStatPill(ctx, W / 2 - 150, 420, 300, 58, pillText, theme.accent);

    ctx.shadowColor = 'rgba(0,0,0,0.30)';
    ctx.shadowBlur = 28;
    ctx.shadowOffsetY = 10;
    ctx.fillStyle = theme.ink;
    drawFittedCanvasText(ctx, {
      text: copy.headline,
      x: W / 2,
      y: 570,
      maxWidth: W - 196,
      maxHeight: 360,
      maxLines: 4,
      align: 'center',
      fontTemplate: '800 __SIZE__px Georgia, "Times New Roman", serif',
      maxSize: 76,
      minSize: 44,
      lineHeightRatio: 1.12
    });
    ctx.shadowColor = 'transparent';
    ctx.shadowBlur = 0;
    ctx.shadowOffsetY = 0;

    ctx.fillStyle = 'rgba(255,255,255,0.14)';
    _roundRect(ctx, 132, 930, W - 264, 112, 34);
    ctx.fill();
    ctx.strokeStyle = 'rgba(255,255,255,0.20)';
    ctx.lineWidth = 1.2;
    _roundRect(ctx, 132, 930, W - 264, 112, 34);
    ctx.stroke();

    ctx.fillStyle = 'rgba(255,255,255,0.86)';
    drawFittedCanvasText(ctx, {
      text: copy.supporting,
      x: W / 2,
      y: 970,
      maxWidth: W - 340,
      maxHeight: 58,
      maxLines: 2,
      align: 'center',
      fontTemplate: '650 __SIZE__px -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif',
      maxSize: 26,
      minSize: 20,
      lineHeightRatio: 1.22
    });

    drawShareFooter(ctx, { accent: theme.accent }, W, 1098, 'center', {
      qrModuleSize: 4,
      chipWidth: 500,
      chipHeight: 174
    });

    if (ENABLE_TEST_EXPORTS) {
      window.__AMT_LAST_ACHIEVEMENT_RENDER_DEBUG__ = {
        type: cardType,
        headline: copy.headline,
        supporting: copy.supporting,
        theme: copy.theme
      };
    }

    return canvas.toDataURL('image/png');
  }

  /** Helper: draw a rounded rectangle path (no fill/stroke — caller does that). */
  function _roundRect(ctx, x, y, w, h, r) {
    ctx.beginPath();
    ctx.moveTo(x + r, y);
    ctx.lineTo(x + w - r, y);
    ctx.quadraticCurveTo(x + w, y, x + w, y + r);
    ctx.lineTo(x + w, y + h - r);
    ctx.quadraticCurveTo(x + w, y + h, x + w - r, y + h);
    ctx.lineTo(x + r, y + h);
    ctx.quadraticCurveTo(x, y + h, x, y + h - r);
    ctx.lineTo(x, y + r);
    ctx.quadraticCurveTo(x, y, x + r, y);
    ctx.closePath();
  }

  /**
   * Show the share-card modal with platform buttons.
   * @param {string} dataUrl  — PNG data URL from buildShareCard()
   * @param {string} caption  — short text caption for text-based shares
   */
  /**
   * Convert a data URL to a File object (for Web Share API).
   */
  async function _dataUrlToFile(dataUrl, filename) {
    const res = await fetch(dataUrl);
    const blob = await res.blob();
    return new File([blob], filename, { type: 'image/png' });
  }

  async function _loadImage(dataUrl) {
    return new Promise((resolve, reject) => {
      const img = new Image();
      img.onload = () => resolve(img);
      img.onerror = reject;
      img.src = dataUrl;
    });
  }

  function _downloadBlob(blob, filename) {
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = filename || 'mirror-talk-motion.webm';
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    setTimeout(() => URL.revokeObjectURL(url), 1000);
  }

  async function _recordTheatricalMotionClip(dataUrl, options) {
    const opts = options || {};
    const durationMs = Number(opts.durationMs || 4200);
    const fps = Number(opts.fps || 30);
    const width = Number(opts.width || 1080);
    const height = Number(opts.height || 1350);
    const image = await _loadImage(dataUrl);
    const canvas = document.createElement('canvas');
    canvas.width = width;
    canvas.height = height;
    const ctx = canvas.getContext('2d');

    if (!ctx || typeof canvas.captureStream !== 'function' || typeof MediaRecorder === 'undefined') {
      throw new Error('Animated export is not supported in this browser.');
    }

    const stream = canvas.captureStream(fps);
    const mimeTypes = [
      'video/webm;codecs=vp9',
      'video/webm;codecs=vp8',
      'video/webm'
    ];
    const recorderOptions = {};
    const supportedMimeType = mimeTypes.find(type => MediaRecorder.isTypeSupported(type));
    if (supportedMimeType) {
      recorderOptions.mimeType = supportedMimeType;
    }

    const recorder = new MediaRecorder(stream, recorderOptions);
    const chunks = [];
    recorder.ondataavailable = event => {
      if (event.data && event.data.size > 0) chunks.push(event.data);
    };

    const scene = {
      titleBars: ['static', 'theatrical'],
      glowX: width * 0.18,
      glowY: height * 0.2,
      sweep: -0.35
    };

    const start = performance.now();
    let rafId = 0;

    const drawFrame = (now) => {
      const elapsed = Math.max(0, now - start);
      const progress = Math.min(1, elapsed / durationMs);
      const phase = progress * Math.PI * 2;
      const slowPhase = progress * Math.PI * 2 * 0.55;

      ctx.clearRect(0, 0, width, height);
      const bg = ctx.createLinearGradient(0, 0, width, height);
      bg.addColorStop(0, '#0b0806');
      bg.addColorStop(0.42, '#15100d');
      bg.addColorStop(1, '#090705');
      ctx.fillStyle = bg;
      ctx.fillRect(0, 0, width, height);

      const bloomA = ctx.createRadialGradient(width * 0.14, height * 0.18, 0, width * 0.14, height * 0.18, 300);
      bloomA.addColorStop(0, 'rgba(255,208,144,0.22)');
      bloomA.addColorStop(0.5, 'rgba(255,208,144,0.10)');
      bloomA.addColorStop(1, 'rgba(255,214,156,0)');
      ctx.save();
      ctx.globalCompositeOperation = 'screen';
      ctx.fillStyle = bloomA;
      ctx.fillRect(0, 0, width, height);
      ctx.restore();

      const bloomB = ctx.createRadialGradient(width * 0.86, height * 0.76, 0, width * 0.86, height * 0.76, 320);
      bloomB.addColorStop(0, 'rgba(122,206,255,0.16)');
      bloomB.addColorStop(0.5, 'rgba(122,206,255,0.07)');
      bloomB.addColorStop(1, 'rgba(122,206,255,0)');
      ctx.save();
      ctx.globalCompositeOperation = 'screen';
      ctx.fillStyle = bloomB;
      ctx.fillRect(0, 0, width, height);
      ctx.restore();

      const backGlow = ctx.createRadialGradient(width / 2, height * 0.55, 0, width / 2, height * 0.55, height * 0.82);
      backGlow.addColorStop(0, 'rgba(255,255,255,0.01)');
      backGlow.addColorStop(0.64, 'rgba(0,0,0,0.04)');
      backGlow.addColorStop(1, 'rgba(0,0,0,0.26)');
      ctx.fillStyle = backGlow;
      ctx.fillRect(0, 0, width, height);

      const cardScale = 1.0;
      const cardX = 0;
      const cardY = 0;
      ctx.save();
      ctx.globalAlpha = 0.94;
      ctx.drawImage(image, cardX, cardY, width * cardScale, height * cardScale);
      ctx.restore();

      const sweepX = ((elapsed / durationMs) * (width + 700)) - 350;
      const sweepGrad = ctx.createLinearGradient(sweepX - 320, 0, sweepX + 260, height);
      sweepGrad.addColorStop(0, 'rgba(255,255,255,0)');
      sweepGrad.addColorStop(0.42, 'rgba(255,255,255,0.01)');
      sweepGrad.addColorStop(0.5, 'rgba(255,240,210,0.14)');
      sweepGrad.addColorStop(0.58, 'rgba(255,255,255,0.01)');
      sweepGrad.addColorStop(1, 'rgba(255,255,255,0)');
      ctx.save();
      ctx.globalCompositeOperation = 'screen';
      ctx.fillStyle = sweepGrad;
      ctx.fillRect(0, 0, width, height);
      ctx.restore();

      const haloRadius = 160 + Math.sin(slowPhase) * 20;
      const haloGrad = ctx.createRadialGradient(scene.glowX, scene.glowY, 0, scene.glowX, scene.glowY, haloRadius);
      haloGrad.addColorStop(0, 'rgba(255,246,224,0.18)');
      haloGrad.addColorStop(0.44, 'rgba(255,206,122,0.10)');
      haloGrad.addColorStop(1, 'rgba(255,206,122,0)');
      ctx.save();
      ctx.globalCompositeOperation = 'screen';
      ctx.fillStyle = haloGrad;
      ctx.fillRect(0, 0, width, height);
      ctx.restore();

      const orbRadius = 104 + Math.sin(phase * 0.95) * 10;
      const orbX = width * 0.78 + Math.sin(slowPhase * 0.8) * 22;
      const orbY = height * 0.22 + Math.cos(slowPhase * 0.75) * 18;
      const orbGrad = ctx.createRadialGradient(orbX, orbY, 0, orbX, orbY, orbRadius);
      orbGrad.addColorStop(0, 'rgba(118,226,255,0.18)');
      orbGrad.addColorStop(0.55, 'rgba(118,226,255,0.07)');
      orbGrad.addColorStop(1, 'rgba(118,226,255,0)');
      ctx.save();
      ctx.globalCompositeOperation = 'screen';
      ctx.fillStyle = orbGrad;
      ctx.fillRect(0, 0, width, height);
      ctx.restore();

      const emberX = width * 0.18 + Math.cos(slowPhase * 0.9) * 18;
      const emberY = height * 0.78 + Math.sin(slowPhase * 0.7) * 16;
      const emberGrad = ctx.createRadialGradient(emberX, emberY, 0, emberX, emberY, 90);
      emberGrad.addColorStop(0, 'rgba(255,178,96,0.16)');
      emberGrad.addColorStop(0.58, 'rgba(255,178,96,0.06)');
      emberGrad.addColorStop(1, 'rgba(255,178,96,0)');
      ctx.save();
      ctx.globalCompositeOperation = 'screen';
      ctx.fillStyle = emberGrad;
      ctx.fillRect(0, 0, width, height);
      ctx.restore();

      const fineGrain = ctx.createLinearGradient(0, 0, width, 0);
      fineGrain.addColorStop(0, 'rgba(255,255,255,0.018)');
      fineGrain.addColorStop(0.5, 'rgba(255,255,255,0)');
      fineGrain.addColorStop(1, 'rgba(255,255,255,0.012)');
      ctx.fillStyle = fineGrain;
      ctx.fillRect(0, 0, width, height);

      const dustCount = 24;
      for (let i = 0; i < dustCount; i += 1) {
        const seed = i * 97.13;
        const px = (width * (0.08 + ((seed % 73) / 100))) + Math.sin(phase * (0.35 + (i % 5) * 0.06) + seed) * 22;
        const py = (height * (0.12 + ((seed % 61) / 100))) + Math.cos(phase * (0.28 + (i % 7) * 0.05) + seed) * 18;
        const size = 0.8 + ((i % 4) * 0.25);
        const alpha = 0.04 + ((Math.sin(phase * 1.1 + seed) + 1) * 0.018);
        ctx.fillStyle = `rgba(255,255,255,${alpha})`;
        ctx.fillRect(px, py, size, size);
      }

      const vignette = ctx.createRadialGradient(width / 2, height / 2, height * 0.28, width / 2, height / 2, height * 0.78);
      vignette.addColorStop(0, 'rgba(0,0,0,0)');
      vignette.addColorStop(0.68, 'rgba(0,0,0,0.08)');
      vignette.addColorStop(1, 'rgba(0,0,0,0.36)');
      ctx.fillStyle = vignette;
      ctx.fillRect(0, 0, width, height);

      ctx.strokeStyle = 'rgba(255,255,255,0.05)';
      ctx.lineWidth = 1;
      ctx.strokeRect(56, 56, width - 112, height - 112);

      ctx.save();
      ctx.globalCompositeOperation = 'screen';
      ctx.strokeStyle = 'rgba(255,239,212,0.08)';
      ctx.lineWidth = 2;
      ctx.beginPath();
      ctx.arc(width * 0.5, height * 0.52, height * 0.34 + Math.sin(slowPhase) * 8, Math.PI * 1.08, Math.PI * 1.92);
      ctx.stroke();
      ctx.restore();

      if (progress < 1) {
        rafId = requestAnimationFrame(drawFrame);
      } else {
        try { recorder.stop(); } catch (e) {}
      }
    };

    const finished = new Promise((resolve, reject) => {
      recorder.onerror = () => reject(new Error('Animated export recording failed.'));
      recorder.onstop = () => {
        const blob = new Blob(chunks, { type: recorder.mimeType || 'video/webm' });
        resolve(blob);
      };
    });

    recorder.start();
    rafId = requestAnimationFrame(drawFrame);

    const blob = await finished;
    cancelAnimationFrame(rafId);
    return blob;
  }

  /**
   * Trigger image download programmatically.
   */
  function _downloadImage(dataUrl, filename) {
    const a = document.createElement('a');
    a.href = dataUrl;
    a.download = filename || 'mirror-talk-achievement.png';
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
  }

  function buildJournalReflectionInsight(entry) {
    const note = String((entry && entry.note) || '').trim();
    const prompt = String((entry && entry.prompt) || '').trim();
    const sourceQuestion = String((entry && entry.sourceQuestion) || '').trim();
    const sourceExcerpt = String((entry && entry.sourceExcerpt) || '').trim();
    const answerBody = joinReflectionTextParts([note, sourceExcerpt]);
    const theme = inferReflectionArtifactTheme(
      `${sourceQuestion} ${prompt}`,
      answerBody || note || sourceExcerpt,
      (entry && entry.theme) || ''
    );

    return normalizeInsightRecord({
      question: sourceQuestion || prompt || 'What stayed with me from this reflection?',
      answer: answerBody || note || prompt,
      excerpt: note || sourceExcerpt || prompt,
      theme,
      shareSource: 'journal_note',
      sourceQuestion,
      sourceExcerpt,
      savedAt: Number((entry && entry.savedAt) || Date.now())
    });
  }

  function showShareModal(dataUrl, caption, options) {
    const modalOptions = options || {};
    const modalTitle = modalOptions.title || 'Share your reflection';
    const modalHint = modalOptions.hint || 'This card is ready to share. On supported phones, open the system share sheet and send it straight into your message or social app.';
    const downloadName = modalOptions.filename || 'mirror-talk-achievement.png';
    const shareContextLabel = modalOptions.contextLabel || 'Reflection card';
    const invitePrompt = modalOptions.invitePrompt || 'Start with one person who may need this reflection today, or save it to keep close.';
    const previewText = String(modalOptions.previewText || '').trim();
    const nativeShareLabel = modalOptions.nativeShareLabel || 'Share card now';
    const animatedShareLabel = modalOptions.animatedShareLabel || 'Share animated clip';
    const animatedDownloadLabel = modalOptions.animatedDownloadLabel || 'Download animated clip';
    const copyTextLabel = modalOptions.copyTextLabel || 'Copy ready caption';
    const copyLinkLabel = modalOptions.copyLinkLabel || 'Copy reflection link';
    const animationPrefKey = 'amt_share_card_animation_preview';
    const prefersReducedMotion = !!(window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches);
    const animationAllowed = modalOptions.animation !== false;
    let animationEnabled = false;

    try {
      const storedPreference = localStorage.getItem(animationPrefKey);
      if (storedPreference === '1') animationEnabled = true;
      if (storedPreference === '0') animationEnabled = false;
    } catch (e) {}

    if (prefersReducedMotion) {
      animationEnabled = false;
    }

    const animationToggleLabel = () => animationEnabled
      ? '↩ Static preview'
      : '✨ Animated preview';

    const animatedShareSupported = !!(window.MediaRecorder && HTMLCanvasElement.prototype.captureStream);

    // Remove any existing modal
    const existing = document.getElementById('amt-share-card-modal');
    if (existing) existing.remove();

    const pageUrl = buildTrackedPageUrl({
      source: 'share_card',
      medium: 'social',
      campaign: 'organic_reflection_share',
      ref: 'share_modal'
    });
    const shareText = caption + '\n\n' + pageUrl;
    const encodedText = encodeURIComponent(shareText);
    const encodedUrl  = encodeURIComponent(pageUrl);

    // Detect Web Share API with file support (best path — native OS share sheet)
    const canNativeShare = !!navigator.share;
    const canNativeShareFiles = !!navigator.canShare;

    const nativeShareBtn = canNativeShare
      ? `<button class="amt-scm-btn amt-scm-native" id="amt-scm-native-btn">
           📲 ${escapeHtml(nativeShareLabel)}
         </button>`
      : '';

    const modal = document.createElement('div');
    modal.id = 'amt-share-card-modal';
    modal.className = 'amt-share-card-modal';
    modal.setAttribute('role', 'dialog');
    modal.setAttribute('aria-modal', 'true');
    modal.setAttribute('aria-label', modalTitle);

    modal.innerHTML = `
      <div class="amt-scm-backdrop"></div>
      <div class="amt-scm-panel">
        <button class="amt-scm-close" aria-label="Close">&times;</button>
        <h3 class="amt-scm-title">${escapeHtml(modalTitle)}</h3>
        <p class="amt-scm-context">${escapeHtml(shareContextLabel)}</p>
        <div class="amt-scm-preview-shell" aria-hidden="true">
          <span class="amt-scm-preview-orb amt-scm-preview-orb-a"></span>
          <span class="amt-scm-preview-orb amt-scm-preview-orb-b"></span>
          <div class="amt-scm-preview-stage">
            <img class="amt-scm-preview" src="${dataUrl}" alt="Share card preview" />
            <span class="amt-scm-preview-shine"></span>
          </div>
        </div>
        ${previewText ? `<p class="amt-scm-preview-line">“${escapeHtml(previewText)}”</p>` : ''}
        <p class="amt-scm-hint">${escapeHtml(modalHint)}</p>
        <p class="amt-scm-invite">${escapeHtml(invitePrompt)}</p>
        <div class="amt-scm-buttons">
          ${nativeShareBtn}
          ${animationAllowed ? `<button class="amt-scm-btn amt-scm-toggle-animation" type="button" aria-pressed="${animationEnabled ? 'true' : 'false'}">${escapeHtml(animationToggleLabel())}</button>` : ''}
          ${animatedShareSupported ? `<button class="amt-scm-btn amt-scm-animated-share" type="button">🎬 ${escapeHtml(animatedShareLabel)}</button>` : ''}
          ${animatedShareSupported ? `<button class="amt-scm-btn amt-scm-animated-download" type="button">⬇️ ${escapeHtml(animatedDownloadLabel)}</button>` : ''}
          <button class="amt-scm-btn amt-scm-copy-link">
            🔗 ${escapeHtml(copyLinkLabel)}
          </button>
          <a class="amt-scm-btn amt-scm-download" href="${dataUrl}" download="${escapeHtml(downloadName)}">⬇️ Download image</a>
          <button class="amt-scm-btn amt-scm-copy">📋 ${escapeHtml(copyTextLabel)}</button>
        </div>
        <p class="amt-scm-platform-note" style="display:none;"></p>
      </div>
    `;

    document.body.appendChild(modal);
    requestAnimationFrame(() => modal.classList.add('amt-scm-visible'));

    const note = modal.querySelector('.amt-scm-platform-note');
    const toggleAnimationBtn = modal.querySelector('.amt-scm-toggle-animation');
    const animatedShareBtn = modal.querySelector('.amt-scm-animated-share');
    const animatedDownloadBtn = modal.querySelector('.amt-scm-animated-download');
    let hasTrackedShare = false;

    function syncAnimationState() {
      const active = animationAllowed && animationEnabled && !prefersReducedMotion;
      modal.classList.toggle('amt-scm-animated', active);
      if (toggleAnimationBtn) {
        toggleAnimationBtn.setAttribute('aria-pressed', active ? 'true' : 'false');
        toggleAnimationBtn.textContent = active ? '↩ Static preview' : '✨ Animated preview';
        toggleAnimationBtn.title = active
          ? 'Return to the static share preview'
          : (prefersReducedMotion ? 'Your system prefers reduced motion' : 'Animate the preview without changing the downloadable image');
        toggleAnimationBtn.disabled = prefersReducedMotion;
      }
    }

    syncAnimationState();

    if (toggleAnimationBtn) {
      toggleAnimationBtn.addEventListener('click', () => {
        if (prefersReducedMotion) return;
        animationEnabled = !animationEnabled;
        try {
          localStorage.setItem(animationPrefKey, animationEnabled ? '1' : '0');
        } catch (e) {}
        syncAnimationState();
      });
    }

    function markShareComplete() {
      if (hasTrackedShare) return;
      hasTrackedShare = true;
      trackRewardEvent('share');
    }

    async function shareViaSystemSheet(platformName) {
      const file = await _dataUrlToFile(dataUrl, downloadName);
      const sharePayload = canNativeShareFiles && navigator.canShare({ files: [file] })
        ? { files: [file] }
        : { title: modalTitle, text: shareText, url: pageUrl };

      await navigator.share(sharePayload);
      markShareComplete();
      if (platformName) {
        note.textContent = `✅ Share sheet opened. Choose ${platformName} if it appears in your available apps.`;
        note.style.display = '';
      }
    }

    async function createAnimatedShareAsset() {
      const motionFilename = downloadName.replace(/\.png$/i, '.webm');
      const blob = await _recordTheatricalMotionClip(dataUrl, {
        width: 1080,
        height: 1350,
        durationMs: 4200,
        fps: 30
      });
      return { blob, motionFilename };
    }

    async function handleAnimatedExport(mode) {
      try {
        note.textContent = '🎬 Creating animated share clip…';
        note.style.display = '';
        const { blob, motionFilename } = await createAnimatedShareAsset();
        const file = new File([blob], motionFilename, { type: blob.type || 'video/webm' });
        const sharePayload = canNativeShareFiles && navigator.canShare && navigator.canShare({ files: [file] })
          ? { files: [file], title: modalTitle, text: shareText, url: pageUrl }
          : null;

        if (mode === 'share' && sharePayload) {
          await navigator.share(sharePayload);
          markShareComplete();
          note.textContent = '✅ Animated share sheet opened.';
          note.style.display = '';
          return;
        }

        if (mode === 'share' && !sharePayload) {
          _downloadBlob(blob, motionFilename);
          markShareComplete();
          note.textContent = '📥 Animated clip downloaded — attach it to your social app or stories composer.';
          note.style.display = '';
          return;
        }

        _downloadBlob(blob, motionFilename);
        note.textContent = '📥 Animated clip downloaded.';
        note.style.display = '';
      } catch (err) {
        warn('Animated export failed, falling back to static image:', err);
        note.textContent = '⚠️ Animated export is unavailable here, so the static image download remains available.';
        note.style.display = '';
      }
    }

    // ── Helper: download image then open platform URL ──────────────────
    function downloadThenOpen(platformUrl, platformNote) {
      _downloadImage(dataUrl, downloadName);
      markShareComplete();
      note.textContent = platformNote;
      note.style.display = '';
      setTimeout(() => window.open(platformUrl, '_blank', 'noopener,noreferrer'), 400);
    }

    // ── Close handlers ──────────────────────────────────────────────────
    const close = () => {
      modal.classList.remove('amt-scm-visible');
      setTimeout(() => modal.remove(), 300);
    };
    modal.querySelector('.amt-scm-close').addEventListener('click', close);
    modal.querySelector('.amt-scm-backdrop').addEventListener('click', close);
    document.addEventListener('keydown', function escHandler(e) {
      if (e.key === 'Escape') { close(); document.removeEventListener('keydown', escHandler); }
    });

    // ── Native share (Web Share API with file) ───────────────────────────
    if (canNativeShare) {
      modal.querySelector('#amt-scm-native-btn').addEventListener('click', async function() {
        try {
          await shareViaSystemSheet();
        } catch (err) {
          if (err.name !== 'AbortError') {
            // Fallback to download
            _downloadImage(dataUrl, downloadName);
            markShareComplete();
            note.textContent = '📥 Image saved — paste it into your app of choice.';
            note.style.display = '';
          }
        }
      });
    }

    if (animatedShareBtn) {
      animatedShareBtn.addEventListener('click', () => handleAnimatedExport('share'));
    }

    if (animatedDownloadBtn) {
      animatedDownloadBtn.addEventListener('click', () => handleAnimatedExport('download'));
    }

    const copyLinkBtn = modal.querySelector('.amt-scm-copy-link');
    if (copyLinkBtn) {
      copyLinkBtn.addEventListener('click', async function() {
        try {
          await navigator.clipboard.writeText(pageUrl);
          markShareComplete();
          this.textContent = '✅ Link copied';
          setTimeout(() => { this.textContent = `🔗 ${copyLinkLabel}`; }, 2500);
        } catch (e) {
          this.textContent = '⚠️ Copy failed';
        }
      });
    }

    // ── Copy text ─────────────────────────────────────────────────────────
    modal.querySelector('.amt-scm-copy').addEventListener('click', async function() {
      try {
        await navigator.clipboard.writeText(shareText);
        markShareComplete();
        this.textContent = '✅ Copied!';
        setTimeout(() => { this.textContent = `📋 ${copyTextLabel}`; }, 2500);
      } catch (e) {
        this.textContent = '⚠️ Copy failed';
      }
    });
  }

  /**
   * Public entry-point: build card and open modal.
   * @param {Object|null} badge  — from AMT_BADGES, or null
   * @param {'badge'|'streak'|'progress'} type
   */
  function shareMilestone(badge, type) {
    const stats = loadStats();
    const dataUrl = buildShareCard(badge, stats, type);
    const shareCopy = getAchievementShareCopy(badge, stats, type);
    const caption = type === 'badge'
      ? `I just unlocked the "${badge.name}" badge on Ask Mirror Talk. ${shareCopy.headline}`
      : type === 'streak'
      ? `${stats.currentStreak}-day streak on Ask Mirror Talk. Small daily returns can become a steadier inner life.`
      : `My Ask Mirror Talk journey: ${stats.totalQuestions} questions, ${stats.currentStreak}-day streak, and ${stats.earnedBadges.size} badges earned.`;
    showShareModal(dataUrl, caption, {
      title: type === 'badge' ? 'Share this badge' : type === 'streak' ? 'Share your streak' : 'Share your progress',
      hint: 'This card is polished and ready to share as a quiet celebration of your reflection rhythm.',
      filename: type === 'badge' ? 'mirror-talk-badge.png' : type === 'streak' ? 'mirror-talk-streak.png' : 'mirror-talk-progress.png',
      contextLabel: type === 'badge' ? (badge && badge.name ? badge.name : 'Badge unlocked') : type === 'streak' ? `${stats.currentStreak}-day streak` : 'Reflection progress',
      invitePrompt: 'Share the progress without pressure. The card celebrates consistency and invites someone else to reflect too.',
      previewText: shareCopy.headline || '',
      nativeShareLabel: 'Open share sheet',
      copyTextLabel: 'Copy share caption',
      copyLinkLabel: 'Copy Ask Mirror Talk link'
    });
  }

  // ── Wire share button into milestone toast ──
  // The toast now sprouts a "Share" button 1 s after appearing.
  const _origShowMilestoneToast = showMilestoneToast;
  // Override to attach a share button for badge toasts
  window._amtShareMilestone = shareMilestone; // expose for badge shelf buttons

  function normalizeInsightRecord(insight) {
    const question = String((insight && insight.question) || '').trim();
    const answer = String((insight && insight.answer) || '').trim();
    const rawExcerpt = String((insight && insight.excerpt) || '').trim();
    const shareableHeadline = String((insight && insight.shareable_headline) || '').trim();
    const theme = inferReflectionArtifactTheme(
      question,
      `${answer} ${rawExcerpt}`,
      (insight && insight.theme) || ''
    );
    const excerpt = ensureReflectionSentence(rawExcerpt) ||
      extractInsightExcerpt(answer, theme) ||
      buildThemeReflectionFallback(theme);

    return {
      question,
      answer,
      theme,
      excerpt,
      shareable_headline: shareableHeadline,
      shareSource: String((insight && insight.shareSource) || '').trim(),
      sourceQuestion: String((insight && insight.sourceQuestion) || '').trim(),
      sourceExcerpt: String((insight && insight.sourceExcerpt) || '').trim(),
      savedAt: (insight && insight.savedAt) || Date.now()
    };
  }

  function hashInsightShareSeed(text) {
    const source = String(text || '');
    let hash = 0;
    for (let i = 0; i < source.length; i++) {
      hash = ((hash << 5) - hash) + source.charCodeAt(i);
      hash |= 0;
    }
    return Math.abs(hash);
  }

  function getInsightShareVariant(insight) {
    const seed = hashInsightShareSeed(`${insight.theme}|${insight.question}|${insight.excerpt}`);
    const variants = [
      {
        questionAlign: 'center',
        questionX: 540,
        questionWidth: 904,
        themeAlign: 'center',
        footerAlign: 'center',
        orbA: { x: 0.84, y: 0.15, inner: 30, outer: 460 },
        orbB: { x: 0.14, y: 0.82, inner: 40, outer: 380 },
        glossCurve: { lineX: 210, bendX: 92, bendY: 174, tailY: 318 },
        panelInset: 72,
        accentWidth: 284,
        excerptX: 118
      },
      {
        questionAlign: 'left',
        questionX: 102,
        questionWidth: 836,
        themeAlign: 'left',
        footerAlign: 'left',
        orbA: { x: 0.76, y: 0.16, inner: 28, outer: 420 },
        orbB: { x: 0.20, y: 0.74, inner: 46, outer: 340 },
        glossCurve: { lineX: 260, bendX: 138, bendY: 204, tailY: 346 },
        panelInset: 88,
        accentWidth: 236,
        excerptX: 134
      },
      {
        questionAlign: 'center',
        questionX: 540,
        questionWidth: 876,
        themeAlign: 'center',
        footerAlign: 'center',
        orbA: { x: 0.20, y: 0.20, inner: 30, outer: 390 },
        orbB: { x: 0.84, y: 0.80, inner: 40, outer: 360 },
        glossCurve: { lineX: 170, bendX: 132, bendY: 196, tailY: 360 },
        panelInset: 80,
        accentWidth: 320,
        excerptX: 126
      },
      {
        questionAlign: 'left',
        questionX: 108,
        questionWidth: 824,
        themeAlign: 'center',
        footerAlign: 'center',
        orbA: { x: 0.88, y: 0.22, inner: 30, outer: 420 },
        orbB: { x: 0.10, y: 0.84, inner: 34, outer: 330 },
        glossCurve: { lineX: 226, bendX: 104, bendY: 182, tailY: 328 },
        panelInset: 84,
        accentWidth: 268,
        excerptX: 130
      }
    ];
    return variants[seed % variants.length];
  }

  function getInsightShareThemeStyle(theme) {
    const key = String(theme || '').toLowerCase();
    const palettes = {
      gratitude: {
        bg: ['#1f1510', '#75462d', '#ebb483'],
        orbA: 'rgba(235, 180, 131, 0.42)',
        orbB: 'rgba(255, 235, 215, 0.17)',
        accent: '#f5d4b3',
        accentSoft: 'rgba(245,212,179,0.22)',
        text: '#fff6ed',
        textSoft: 'rgba(255,246,237,0.78)',
        panelEdge: 'rgba(250,225,200,0.28)',
        frameGlow: 'rgba(245,212,179,0.16)',
        card: 'rgba(255,250,244,0.97)',
        cardText: '#32271c',
        kicker: 'A reflection worth keeping close',
        motif: 'rays'
      },
      faith: {
        bg: ['#130f1f', '#422448', '#d39d42'],
        orbA: 'rgba(224, 178, 82, 0.48)',
        orbB: 'rgba(255, 237, 198, 0.18)',
        accent: '#f0c678',
        accentSoft: 'rgba(240,198,120,0.22)',
        text: '#fff7ea',
        textSoft: 'rgba(255,247,234,0.78)',
        panelEdge: 'rgba(255,244,220,0.30)',
        frameGlow: 'rgba(240,198,120,0.18)',
        card: 'rgba(255,250,243,0.965)',
        cardText: '#2f261e',
        kicker: 'A quiet return to what still feels sacred',
        motif: 'halo'
      },
      fear: {
        bg: ['#1c0d14', '#6f1a38', '#d65a5a'],
        orbA: 'rgba(214, 90, 90, 0.42)',
        orbB: 'rgba(250, 205, 205, 0.16)',
        accent: '#f5a8a8',
        accentSoft: 'rgba(245,168,168,0.22)',
        text: '#ffeef0',
        textSoft: 'rgba(255,238,240,0.75)',
        panelEdge: 'rgba(248,195,195,0.26)',
        frameGlow: 'rgba(245,168,168,0.14)',
        card: 'rgba(255,246,247,0.965)',
        cardText: '#341e22',
        kicker: 'A reflection for what fear guards and what it costs',
        motif: 'ember'
      },
      healing: {
        bg: ['#0c1f24', '#15616f', '#5dc7ab'],
        orbA: 'rgba(93, 199, 171, 0.46)',
        orbB: 'rgba(210, 255, 239, 0.18)',
        accent: '#b8f0d6',
        accentSoft: 'rgba(184,240,214,0.22)',
        text: '#f2fffb',
        textSoft: 'rgba(242,255,251,0.78)',
        panelEdge: 'rgba(214,255,241,0.26)',
        frameGlow: 'rgba(184,240,214,0.16)',
        card: 'rgba(247,255,251,0.97)',
        cardText: '#20312a',
        kicker: 'A reflection for gentler repair and steadier ground',
        motif: 'tide'
      },
      grief: {
        bg: ['#1a1520', '#3d2c52', '#7a6b9e'],
        orbA: 'rgba(122, 107, 158, 0.38)',
        orbB: 'rgba(215, 210, 230, 0.14)',
        accent: '#c4b8e0',
        accentSoft: 'rgba(196,184,224,0.20)',
        text: '#f0ecf8',
        textSoft: 'rgba(240,236,248,0.76)',
        panelEdge: 'rgba(210,203,228,0.26)',
        frameGlow: 'rgba(196,184,224,0.15)',
        card: 'rgba(248,246,252,0.965)',
        cardText: '#2a2535',
        kicker: 'A reflection that holds space for what cannot be rushed',
        motif: 'veil'
      },
      relationships: {
        bg: ['#1b111d', '#6d2f52', '#ef8a84'],
        orbA: 'rgba(239, 138, 132, 0.44)',
        orbB: 'rgba(255, 226, 222, 0.18)',
        accent: '#ffc6bf',
        accentSoft: 'rgba(255,198,191,0.22)',
        text: '#fff1f0',
        textSoft: 'rgba(255,241,240,0.78)',
        panelEdge: 'rgba(255,223,218,0.28)',
        frameGlow: 'rgba(255,198,191,0.16)',
        card: 'rgba(255,248,247,0.965)',
        cardText: '#342425',
        kicker: 'A reflection shaped for honest connection',
        motif: 'threads'
      },
      'self-worth': {
        bg: ['#1d1510', '#6b4520', '#c8924d'],
        orbA: 'rgba(200, 146, 77, 0.40)',
        orbB: 'rgba(240, 220, 188, 0.16)',
        accent: '#e8c895',
        accentSoft: 'rgba(232,200,149,0.22)',
        text: '#fff3e6',
        textSoft: 'rgba(255,243,230,0.75)',
        panelEdge: 'rgba(235,210,175,0.25)',
        frameGlow: 'rgba(232,200,149,0.15)',
        card: 'rgba(254,249,242,0.97)',
        cardText: '#342618',
        kicker: 'A reflection that brings you home to your own ground',
        motif: 'orbit'
      },
      leadership: {
        bg: ['#0f1a28', '#1e3a5f', '#4a7ba7'],
        orbA: 'rgba(74, 123, 167, 0.36)',
        orbB: 'rgba(200, 225, 245, 0.14)',
        accent: '#a8d1f0',
        accentSoft: 'rgba(168,209,240,0.18)',
        text: '#f0f7fc',
        textSoft: 'rgba(240,247,252,0.76)',
        panelEdge: 'rgba(185,220,242,0.22)',
        frameGlow: 'rgba(148,199,235,0.12)',
        card: 'rgba(246,251,255,0.97)',
        cardText: '#1d2d3a',
        kicker: 'A reflection for those who carry others forward with integrity',
        motif: 'beacon'
      },
      boundaries: {
        bg: ['#16181f', '#35506f', '#b8d1e8'],
        orbA: 'rgba(184, 209, 232, 0.38)',
        orbB: 'rgba(245, 249, 255, 0.15)',
        accent: '#e7f2ff',
        accentSoft: 'rgba(231,242,255,0.20)',
        text: '#f7fbff',
        textSoft: 'rgba(247,251,255,0.78)',
        panelEdge: 'rgba(230,240,250,0.24)',
        frameGlow: 'rgba(201,226,246,0.14)',
        card: 'rgba(249,252,255,0.97)',
        cardText: '#20313c',
        kicker: 'A reflection for steadier yeses and kinder noes',
        motif: 'lattice'
      },
      courage: {
        bg: ['#1a1010', '#7f2f1d', '#f2a35b'],
        orbA: 'rgba(242, 163, 91, 0.42)',
        orbB: 'rgba(255, 236, 206, 0.16)',
        accent: '#ffd2a6',
        accentSoft: 'rgba(255,210,166,0.22)',
        text: '#fff6ee',
        textSoft: 'rgba(255,246,238,0.78)',
        panelEdge: 'rgba(255,224,195,0.26)',
        frameGlow: 'rgba(255,210,166,0.15)',
        card: 'rgba(255,249,244,0.97)',
        cardText: '#34251d',
        kicker: 'A reflection for the brave next step, not the perfect one',
        motif: 'ember'
      },
      purpose: {
        bg: ['#14151e', '#2f4a68', '#f0bf73'],
        orbA: 'rgba(240, 191, 115, 0.40)',
        orbB: 'rgba(255, 242, 212, 0.15)',
        accent: '#ffe0a7',
        accentSoft: 'rgba(255,224,167,0.20)',
        text: '#fff8ee',
        textSoft: 'rgba(255,248,238,0.77)',
        panelEdge: 'rgba(255,231,193,0.25)',
        frameGlow: 'rgba(255,224,167,0.14)',
        card: 'rgba(255,251,245,0.97)',
        cardText: '#32261d',
        kicker: 'A reflection for listening to what keeps calling you forward',
        motif: 'path'
      },
      forgiveness: {
        bg: ['#161722', '#4f4878', '#cdb4ff'],
        orbA: 'rgba(205, 180, 255, 0.40)',
        orbB: 'rgba(243, 236, 255, 0.16)',
        accent: '#e6d7ff',
        accentSoft: 'rgba(230,215,255,0.20)',
        text: '#f7f2ff',
        textSoft: 'rgba(247,242,255,0.78)',
        panelEdge: 'rgba(232,224,255,0.24)',
        frameGlow: 'rgba(224,208,255,0.15)',
        card: 'rgba(252,249,255,0.97)',
        cardText: '#28243a',
        kicker: 'A reflection for what softens when you release your grip',
        motif: 'halo'
      },
      'inner peace': {
        bg: ['#102128', '#1d5a64', '#9ed7db'],
        orbA: 'rgba(158, 215, 219, 0.38)',
        orbB: 'rgba(231, 251, 255, 0.16)',
        accent: '#d8f5f6',
        accentSoft: 'rgba(216,245,246,0.20)',
        text: '#f1ffff',
        textSoft: 'rgba(241,255,255,0.77)',
        panelEdge: 'rgba(217,245,245,0.24)',
        frameGlow: 'rgba(199,240,242,0.14)',
        card: 'rgba(247,255,255,0.97)',
        cardText: '#203033',
        kicker: 'A reflection for coming back to a steadier inner weather',
        motif: 'horizon'
      }
    };

    return palettes[key] || {
      bg: ['#171312', '#6a4730', '#e0a261'],
      orbA: 'rgba(224, 162, 97, 0.44)',
      orbB: 'rgba(255, 233, 204, 0.18)',
      accent: '#f5cf98',
      accentSoft: 'rgba(245,207,152,0.24)',
      text: '#fff7ed',
      textSoft: 'rgba(255,247,237,0.77)',
      panelEdge: 'rgba(255,229,191,0.26)',
      frameGlow: 'rgba(245,207,152,0.16)',
      card: 'rgba(255,249,242,0.97)',
      cardText: '#31251c',
      kicker: 'A reflection worth keeping close',
      motif: 'orbit'
    };
  }

  function drawThemeArtDirection(ctx, style, W, H, variant) {
    const motif = String(style.motif || 'orbit');
    ctx.save();

    if (motif === 'halo') {
      ctx.strokeStyle = 'rgba(255,255,255,0.09)';
      ctx.lineWidth = 2;
      ctx.beginPath();
      ctx.arc(W * 0.72, H * 0.25, 168, 0, Math.PI * 2);
      ctx.stroke();
      ctx.beginPath();
      ctx.arc(W * 0.72, H * 0.25, 118, 0, Math.PI * 2);
      ctx.stroke();
    } else if (motif === 'ember') {
      ctx.fillStyle = 'rgba(255,255,255,0.05)';
      for (let i = 0; i < 6; i++) {
        ctx.beginPath();
        ctx.arc(150 + (i * 120), H - 150 - (i % 2 === 0 ? 10 : 28), 4 + (i % 3), 0, Math.PI * 2);
        ctx.fill();
      }
    } else if (motif === 'tide') {
      ctx.strokeStyle = 'rgba(255,255,255,0.07)';
      ctx.lineWidth = 2;
      for (let i = 0; i < 4; i++) {
        ctx.beginPath();
        ctx.moveTo(90, 900 + (i * 34));
        ctx.bezierCurveTo(260, 860 + (i * 24), 520, 960 + (i * 24), 940, 900 + (i * 34));
        ctx.stroke();
      }
    } else if (motif === 'veil') {
      ctx.fillStyle = 'rgba(255,255,255,0.045)';
      ctx.beginPath();
      ctx.moveTo(0, H * 0.58);
      ctx.bezierCurveTo(W * 0.24, H * 0.48, W * 0.48, H * 0.70, W, H * 0.58);
      ctx.lineTo(W, H);
      ctx.lineTo(0, H);
      ctx.closePath();
      ctx.fill();
    } else if (motif === 'threads') {
      ctx.strokeStyle = 'rgba(255,255,255,0.055)';
      ctx.lineWidth = 2;
      ctx.beginPath();
      ctx.moveTo(94, 260);
      ctx.bezierCurveTo(260, 180, 440, 190, 620, 300);
      ctx.stroke();
      ctx.beginPath();
      ctx.moveTo(420, 180);
      ctx.bezierCurveTo(620, 240, 760, 220, 948, 146);
      ctx.stroke();
    } else if (motif === 'orbit') {
      ctx.strokeStyle = 'rgba(255,255,255,0.06)';
      ctx.lineWidth = 1.6;
      ctx.beginPath();
      ctx.ellipse(W * 0.54, H * 0.32, 320, 118, -0.28, 0, Math.PI * 2);
      ctx.stroke();
      ctx.beginPath();
      ctx.ellipse(W * 0.5, H * 0.72, 370, 142, 0.18, 0, Math.PI * 2);
      ctx.stroke();
    } else if (motif === 'beacon') {
      ctx.strokeStyle = 'rgba(255,255,255,0.065)';
      ctx.lineWidth = 2;
      ctx.beginPath();
      ctx.moveTo(W * 0.62, 92);
      ctx.lineTo(W * 0.62, H - 190);
      ctx.stroke();
      ctx.beginPath();
      ctx.moveTo(W * 0.62, 210);
      ctx.lineTo(W - 92, 210);
      ctx.stroke();
    } else if (motif === 'rays') {
      ctx.strokeStyle = 'rgba(255,255,255,0.07)';
      ctx.lineWidth = 2;
      const centerX = W * 0.82;
      const centerY = H * 0.18;
      for (let i = 0; i < 5; i++) {
        const angle = (Math.PI / 3) + (i * Math.PI / 6);
        ctx.beginPath();
        ctx.moveTo(centerX, centerY);
        ctx.lineTo(
          centerX + Math.cos(angle) * 160,
          centerY + Math.sin(angle) * 160
        );
        ctx.stroke();
      }
      ctx.beginPath();
      ctx.moveTo(W * 0.62, 362);
      ctx.lineTo(W - 132, 362);
      ctx.stroke();
    } else if (motif === 'lattice') {
      ctx.strokeStyle = 'rgba(255,255,255,0.05)';
      ctx.lineWidth = 1.6;
      for (let i = 0; i < 4; i++) {
        ctx.beginPath();
        ctx.moveTo(120 + (i * 70), 160);
        ctx.lineTo(210 + (i * 70), H - 150);
        ctx.stroke();
      }
      for (let i = 0; i < 4; i++) {
        ctx.beginPath();
        ctx.moveTo(W - 120 - (i * 70), 160);
        ctx.lineTo(W - 210 - (i * 70), H - 150);
        ctx.stroke();
      }
    } else if (motif === 'path') {
      ctx.strokeStyle = 'rgba(255,255,255,0.06)';
      ctx.lineWidth = 2;
      ctx.beginPath();
      ctx.moveTo(W * 0.15, H - 180);
      ctx.bezierCurveTo(W * 0.34, H - 290, W * 0.50, H - 430, W * 0.82, 220);
      ctx.stroke();
    } else if (motif === 'horizon') {
      ctx.strokeStyle = 'rgba(255,255,255,0.06)';
      ctx.lineWidth = 2;
      ctx.beginPath();
      ctx.moveTo(92, H * 0.52);
      ctx.lineTo(W - 92, H * 0.52);
      ctx.stroke();
      ctx.beginPath();
      ctx.arc(W * 0.72, H * 0.52, 82, Math.PI, Math.PI * 2);
      ctx.stroke();
    }

    ctx.restore();
  }

  function splitHeadlineForSpotlight(line) {
    const words = String(line || '').split(/\s+/).filter(Boolean);
    if (words.length < 5) {
      return { lead: line, highlight: '', tail: '' };
    }
    const highlightStart = Math.max(1, Math.floor(words.length / 3));
    const highlightSize = Math.min(4, Math.max(2, Math.ceil(words.length / 3)));
    return {
      lead: words.slice(0, highlightStart).join(' '),
      highlight: words.slice(highlightStart, highlightStart + highlightSize).join(' '),
      tail: words.slice(highlightStart + highlightSize).join(' ')
    };
  }

  function canUsePosterFamily(insight, headline) {
    const text = String(headline || extractShareHeadline(insight) || '').trim();
    const words = text.split(/\s+/).filter(Boolean);
    const longestWord = words.reduce((max, word) => Math.max(max, word.length), 0);
    return words.length >= 6 && words.length <= 18 && text.length >= 44 && text.length <= 150 && longestWord <= 16;
  }

  function canUseSpotlightFamily(insight, headline) {
    const text = String(headline || extractShareHeadline(insight) || '').trim();
    const words = text.split(/\s+/).filter(Boolean);
    if (words.length < 7 || words.length > 20 || text.length > 160) return false;
    const split = splitHeadlineForSpotlight(text);
    return !!(split.lead && split.highlight && split.tail &&
      split.highlight.length >= 8 && split.highlight.length <= 34 &&
      split.tail.length >= 12 && split.tail.length <= 72);
  }

  function validateCompleteHeadline(text) {
    return isCompleteReflectionSentence(text);
  }

  function selectFittingShareHeadline(ctx, normalized, fitOptions) {
    const opts = fitOptions || {};
    const headlinePool = [];
    const themeKeywords = getThemeReflectionKeywords(normalized.theme || '');

    const addHeadlineCandidate = (value) => {
      const clean = ensureReflectionSentence(value);
      if (!clean) return;
      if (!headlinePool.some(existing => trimDanglingHeadlineTail(existing).toLowerCase() === trimDanglingHeadlineTail(clean).toLowerCase())) {
        headlinePool.push(clean);
      }
    };

    const scoreHeadlinePresentation = (text) => {
      return scoreShareHeadlineCandidate(text, themeKeywords);
    };

    const scoreInsightDepth = (text) => {
      const clean = ensureReflectionSentence(text);
      if (!clean) return -Infinity;
      const lower = clean.toLowerCase();
      const words = clean.split(/\s+/).filter(Boolean);
      let depth = 0;

      // Signals of reflective reasoning depth.
      if (/\b(because|so that|which means|this means|therefore|instead of|rather than|even when|even if|in the midst|without requiring|as you|when you)\b/i.test(lower)) depth += 5;
      if (/\b(pattern|habit|truth|clarity|healing|growth|connection|resilience|compassion|grace|wisdom|defensiveness|boundaries|vulnerability|integrity|alignment|agency|identity|belonging)\b/i.test(lower)) depth += 4;
      if (/\b(acknowledg|recogniz|discern|separate|release|repair|rebuild|transform|reconnect|honor|protect|choose|practice|cultivate|integrate|reflect)\w*\b/i.test(lower)) depth += 3;
      if (/\b(you|your|we|our)\b/i.test(lower)) depth += 1;
      if (words.length >= 10 && words.length <= 24) depth += 3;
      else if (words.length >= 8 && words.length <= 28) depth += 1;
      if (/^[A-Z][a-z]+(?:\s+[A-Z][a-z]+){0,2}\s+(says|shares|notes|explains|reminds|suggests|teaches)\b/.test(clean)) depth -= 6;

      return depth;
    };

    const scoreQuestionRelevance = (candidate) => {
      const question = String(normalized.question || '').toLowerCase();
      const candidateLower = String(candidate || '').toLowerCase();
      if (!question || !candidateLower) return 0;
      
      const stopwords = new Set([
        'a', 'an', 'and', 'are', 'as', 'at', 'be', 'but', 'by', 'for', 'from', 'has', 'he', 'in',
        'is', 'it', 'its', 'my', 'not', 'of', 'on', 'or', 'that', 'the', 'to', 'was', 'will', 'with'
      ]);
      
      const extractKeyTerms = (text) => {
        return text.split(/\s+/)
          .map(word => word.replace(/[^a-z0-9]/g, '').toLowerCase())
          .filter(word => word.length > 3 && !stopwords.has(word));
      };
      
      const questionTerms = new Set(extractKeyTerms(question));
      const candidateTerms = new Set(extractKeyTerms(candidateLower));
      
      let matches = 0;
      questionTerms.forEach(term => {
        if (candidateTerms.has(term)) matches += 1;
      });
      
      // Score is the overlap ratio, boosted by question importance
      const relevance = matches / Math.max(1, questionTerms.size);
      return relevance * 4; // Scale to 0-4 range
    };

    const fitsAnyProfile = (candidate, profiles) => profiles.some(profile => canRenderCanvasTextFully(
      ctx,
      candidate,
      profile.maxWidth,
      profile.maxHeight,
      profile.maxLines,
      profile.fontTemplate,
      profile.maxSize,
      profile.minSize,
      profile.lineHeightRatio
    ));

    const fitProfiles = [
      {
        maxWidth: opts.maxWidth,
        maxHeight: opts.maxHeight,
        maxLines: opts.maxLines,
        fontTemplate: opts.fontTemplate,
        maxSize: opts.maxSize,
        minSize: opts.minSize,
        lineHeightRatio: opts.lineHeightRatio
      },
      {
        maxWidth: opts.maxWidth,
        maxHeight: opts.maxHeight * 1.15,
        maxLines: Math.min(7, opts.maxLines + 1),
        fontTemplate: opts.fontTemplate,
        maxSize: opts.maxSize,
        minSize: Math.max(28, Math.floor(opts.minSize * 0.85)),
        lineHeightRatio: opts.lineHeightRatio
      }
    ];
    
    console.log('[selectFittingShareHeadline] normalized.shareable_headline:', normalized.shareable_headline);
    
    // API headline is useful, but do not let it dominate if answer-derived candidates are stronger.
    const apiHeadline = normalized.shareable_headline && typeof normalized.shareable_headline === 'string' 
      ? ensureReflectionSentence(normalized.shareable_headline) 
      : '';
    
    console.log('[selectFittingShareHeadline] apiHeadline after ensureReflectionSentence:', apiHeadline);

    const extractedCandidates = listCardHeadlineCandidates(
      joinReflectionTextParts([normalized.answer, normalized.excerpt]),
      normalized.theme || '',
      { includeFallback: (normalized.shareSource || '') === 'current_answer' || !(normalized.shareSource || '').trim() }
    );
    extractedCandidates.forEach(addHeadlineCandidate);

    if (apiHeadline && !isWeakShareHeadlineCandidate(apiHeadline)) {
      const bestExtractedScore = extractedCandidates.reduce((best, candidate) => {
        const score = scoreHeadlinePresentation(candidate);
        return Number.isFinite(score) ? Math.max(best, score) : best;
      }, -Infinity);
      const apiScore = scoreHeadlinePresentation(apiHeadline);

      if (!extractedCandidates.length || apiScore >= (bestExtractedScore + 1.5)) {
        addHeadlineCandidate(apiHeadline);
      }
    }

    const allowSyntheticFallback = (normalized.shareSource || '') === 'current_answer' || !(normalized.shareSource || '').trim();
    const sourceRescueCandidates = !allowSyntheticFallback
      ? listCompactSourceReflectionCandidates(joinReflectionTextParts([normalized.excerpt, normalized.answer]))
      : [];

    if (!headlinePool.length) {
      const sourceRescue = sourceRescueCandidates.find(candidate => fitsAnyProfile(candidate, fitProfiles));
      if (sourceRescue) {
        console.log('[Card] Recovered source-grounded headline candidate:', sourceRescue.substring(0, 80) + '...');
        return sourceRescue;
      }
      console.log('[Card] No usable headline candidates found, using fallback');
      return buildThemeReflectionFallback(normalized.theme || '');
    }

    const scoredCandidates = headlinePool
      .map(candidate => ({
        candidate,
        score: scoreHeadlinePresentation(candidate),
        depth: scoreInsightDepth(candidate),
        relevance: scoreQuestionRelevance(candidate),
        fits: fitsAnyProfile(candidate, fitProfiles)
      }))
      .filter(item => item.fits)
      .sort((a, b) => {
        // Primary sort: presentation score
        if (Math.abs(a.score - b.score) > 0.5) return b.score - a.score;
        // Tiebreak 1: question relevance (if close on score)
        if (Math.abs(a.relevance - b.relevance) > 0.3) return b.relevance - a.relevance;
        // Tiebreak 2: insight depth
        if (a.depth !== b.depth) return b.depth - a.depth;
        // Tiebreak 3: length (prefer mid-range)
        return b.candidate.length - a.candidate.length;
      });

    if (DEBUG) {
      const preview = scoredCandidates
        .slice(0, 5)
        .map(item => ({
          score: Number(item.score.toFixed(2)),
          depth: item.depth,
          relevance: Number(item.relevance.toFixed(2)),
          fits: item.fits,
          candidate: item.candidate.substring(0, 60)
        }));
      console.log('[ShareHeadlineSelector] Candidate ranking (top 5):', preview);
    }

    const top = scoredCandidates[0];
    const second = scoredCandidates[1];
    const closeScoreThreshold = 2.0;
    let chosen = top;

    if (top && second && Math.abs(top.score - second.score) <= closeScoreThreshold) {
      // If scores are close, prefer better question relevance
      if (second.relevance > top.relevance + 0.5) {
        chosen = second;
        if (DEBUG) {
          console.log('[ShareHeadlineSelector] Close score, prefer higher question relevance:', {
            topScore: Number(top.score.toFixed(2)),
            topRelevance: Number(top.relevance.toFixed(2)),
            secondScore: Number(second.score.toFixed(2)),
            secondRelevance: Number(second.relevance.toFixed(2)),
            chosen: second.candidate
          });
        }
      }
      // Otherwise tie-break by depth if relevance is similar
      else if (Math.abs(top.relevance - second.relevance) <= 0.3 && second.depth > top.depth) {
        chosen = second;
        if (DEBUG) {
          console.log('[ShareHeadlineSelector] Close score, tie-break by insight depth:', {
            topScore: Number(top.score.toFixed(2)),
            secondScore: Number(second.score.toFixed(2)),
            topDepth: top.depth,
            secondDepth: second.depth,
            chosen: second.candidate
          });
        }
      }
    }

    if (chosen) {
      console.log('[Card] Selected headline candidate:', chosen.candidate.substring(0, 80) + '...');
      return chosen.candidate;
    }

    const sourceRescue = sourceRescueCandidates.find(candidate => fitsAnyProfile(candidate, fitProfiles));
    if (sourceRescue) {
      console.log('[Card] Recovered source-grounded headline candidate:', sourceRescue.substring(0, 80) + '...');
      return sourceRescue;
    }

    console.log('[Card] Headline candidates available but none fit, using fallback');
    return buildThemeReflectionFallback(normalized.theme || '');
  }

  function getInsightShareFamily(insight) {
    if (TEST_FORCE_FAMILY) return TEST_FORCE_FAMILY;

    const headline = extractShareHeadline(insight);
    const apiHeadline = insight.shareable_headline && typeof insight.shareable_headline === 'string' 
      ? ensureReflectionSentence(insight.shareable_headline) 
      : '';
    
    // A/B test: Randomly assign some users to bold_vibrant variant for testing
    const seed = hashInsightShareSeed(`${insight.theme}|${insight.question}|${insight.excerpt}`);
    const boldVariantEnabled = window.__AMT_AB_TEST_BOLD_VARIANT || false;
    const boldVariantPct = window.__AMT_BOLD_VARIANT_PCT || 0;
    const shouldUseBoldVariant = boldVariantEnabled && (seed % 100) < boldVariantPct;
    
    // If bold variant A/B test is enabled, use it for a percentage of renders
    if (shouldUseBoldVariant) {
      return 'bold_vibrant';
    }
    
    // If we have an API headline, prefer card families with more generous height limits
    if (apiHeadline && !isWeakShareHeadlineCandidate(apiHeadline)) {
      const words = apiHeadline.split(/\s+/).filter(Boolean);
      const chars = apiHeadline.length;
      
      // For longer API headlines, prefer families with larger canvas limits
      // spotlight: 620px height, 6 lines; poster: 520px, 6 lines
      if (chars > 110 || words.length > 18) {
        console.log('[Card Family] API headline is long (' + chars + ' chars), choosing generous layout');
        // Alternate between spotlight and poster for variety
        return seed % 2 === 0 ? 'spotlight' : 'poster';
      }
      
      if (chars > 85 || words.length > 15) {
        console.log('[Card Family] API headline is medium-long (' + chars + ' chars), using poster layout');
        return 'poster';  // 520px height, 6 lines
      }
    }
    
    // Default logic for shorter headlines or fallback extractions
    const words = String(headline || '').split(/\s+/).filter(Boolean);
    if (words.length <= 20) {
      return 'aura_poster';
    }

    const families = ['aura_poster', 'gradient_immersive', 'aura_poster', 'prismatic_quote'];
    return families[seed % families.length];
  }

  function drawShareCardShell(ctx, style, W, H, variant) {
    const grad = ctx.createLinearGradient(0, 0, W, H);
    grad.addColorStop(0, style.bg[0]);
    grad.addColorStop(0.42, style.bg[1]);
    grad.addColorStop(1, style.bg[2]);
    ctx.fillStyle = grad;
    ctx.fillRect(0, 0, W, H);

    const orbA = ctx.createRadialGradient(
      W * variant.orbA.x,
      H * variant.orbA.y,
      variant.orbA.inner,
      W * variant.orbA.x,
      H * variant.orbA.y,
      variant.orbA.outer
    );
    orbA.addColorStop(0, style.orbA);
    orbA.addColorStop(1, 'rgba(255,255,255,0)');
    ctx.fillStyle = orbA;
    ctx.fillRect(0, 0, W, H);

    const orbB = ctx.createRadialGradient(
      W * variant.orbB.x,
      H * variant.orbB.y,
      variant.orbB.inner,
      W * variant.orbB.x,
      H * variant.orbB.y,
      variant.orbB.outer
    );
    orbB.addColorStop(0, style.orbB);
    orbB.addColorStop(1, 'rgba(255,255,255,0)');
    ctx.fillStyle = orbB;
    ctx.fillRect(0, 0, W, H);

    drawThemeArtDirection(ctx, style, W, H, variant);

    const gloss = ctx.createLinearGradient(0, 0, W, H * 0.52);
    gloss.addColorStop(0, 'rgba(255,255,255,0.42)');
    gloss.addColorStop(0.18, 'rgba(255,255,255,0.16)');
    gloss.addColorStop(0.46, 'rgba(255,255,255,0.03)');
    gloss.addColorStop(1, 'rgba(255,255,255,0)');
    ctx.fillStyle = gloss;
    ctx.beginPath();
    ctx.moveTo(48, 48);
    ctx.lineTo(W - variant.glossCurve.lineX, 48);
    ctx.quadraticCurveTo(W - variant.glossCurve.bendX, 76, W - 42, variant.glossCurve.bendY);
    ctx.lineTo(48, variant.glossCurve.tailY);
    ctx.closePath();
    ctx.fill();

    const verticalGlow = ctx.createLinearGradient(0, 0, 0, H);
    verticalGlow.addColorStop(0, 'rgba(255,255,255,0.10)');
    verticalGlow.addColorStop(0.32, 'rgba(255,255,255,0.03)');
    verticalGlow.addColorStop(1, 'rgba(0,0,0,0.16)');
    ctx.fillStyle = verticalGlow;
    ctx.fillRect(0, 0, W, H);

    const vignette = ctx.createRadialGradient(W * 0.5, H * 0.52, H * 0.16, W * 0.5, H * 0.52, H * 0.88);
    vignette.addColorStop(0, 'rgba(255,255,255,0)');
    vignette.addColorStop(0.62, 'rgba(0,0,0,0.03)');
    vignette.addColorStop(1, 'rgba(0,0,0,0.24)');
    ctx.fillStyle = vignette;
    ctx.fillRect(0, 0, W, H);

    ctx.fillStyle = 'rgba(255,255,255,0.045)';
    ctx.fillRect(54, 54, W - 108, H - 108);

    ctx.strokeStyle = 'rgba(255,255,255,0.035)';
    ctx.lineWidth = 1;
    for (let y = 76; y < H - 76; y += 84) {
      ctx.beginPath();
      ctx.moveTo(70, y);
      ctx.lineTo(W - 70, y);
      ctx.stroke();
    }

    for (let i = 0; i < 1200; i++) {
      ctx.fillStyle = i % 2 === 0 ? 'rgba(255,255,255,0.018)' : 'rgba(0,0,0,0.012)';
      ctx.fillRect(Math.random() * W, Math.random() * H, 1.2, 1.2);
    }

    ctx.strokeStyle = style.frameGlow || 'rgba(255,255,255,0.14)';
    ctx.lineWidth = 8;
    _roundRect(ctx, 32, 32, W - 64, H - 64, 42);
    ctx.stroke();

    ctx.strokeStyle = 'rgba(255,255,255,0.16)';
    ctx.lineWidth = 1.8;
    _roundRect(ctx, 30, 30, W - 60, H - 60, 40);
    ctx.stroke();

    ctx.strokeStyle = 'rgba(255,255,255,0.07)';
    ctx.lineWidth = 1;
    _roundRect(ctx, 52, 52, W - 104, H - 104, 34);
    ctx.stroke();
  }

  let reflectionCardQrMatrix = null;
  const REFLECTION_CARD_QR_ROWS = [
    '111111100011100000111011001111111',
    '100000100100000111100000001000001',
    '101110101110101110101111001011101',
    '101110101001100001001001101011101',
    '101110101011011110111111001011101',
    '100000101001111001101000101000001',
    '111111101010101010101010101111111',
    '000000001110101010000100000000000',
    '101111100011111001000011101111100',
    '011101010011010010111011001101101',
    '011001110011011110001010111010100',
    '011110001111110010111111111011111',
    '011110110111101010010010110111001',
    '100001000100110100011111011001011',
    '000100110110101110101110011111110',
    '110100010001000100010100111101100',
    '111010100010000101000010010110001',
    '000101010000011011011101001101101',
    '010001111011001111000000100110110',
    '001111010001011000000101101111111',
    '110111111111110101000010100011000',
    '111101011010100110011101001001001',
    '101100101000100001101100111111110',
    '100000011001111010001110010101110',
    '100111101000100001011010111110001',
    '000000001010100010011101100010111',
    '111111100001100100101111101010110',
    '100000101011111010010111100011110',
    '101110101100101001011010111111000',
    '101110101101100100010001110010011',
    '101110101110011100000110001101100',
    '100000100010001000111101011011100',
    '111111101001010101100011110101010'
  ];

  function getReflectionCardQrPayload() {
    return REFLECTION_CARD_QR_URL.length <= 64 ? REFLECTION_CARD_QR_URL : BASE_PAGE_URL;
  }

  function createReflectionCardQrMatrix() {
    const qrSize = REFLECTION_CARD_QR_ROWS.length;
    return {
      size: qrSize,
      modules: REFLECTION_CARD_QR_ROWS.map(row => row.split('').map(bit => bit === '1')),
      payload: getReflectionCardQrPayload(),
      mask: 'qrcode-8.2-m'
    };
  }

  function getReflectionCardQrMatrix() {
    if (!reflectionCardQrMatrix) {
      reflectionCardQrMatrix = createReflectionCardQrMatrix();
    }
    return reflectionCardQrMatrix;
  }

  function drawReflectionQrCode(ctx, x, y, moduleSize, options) {
    const opts = options || {};
    const qr = getReflectionCardQrMatrix();
    const quiet = Number(opts.quiet || 4);
    const boxSize = (qr.size + quiet * 2) * moduleSize;
    ctx.fillStyle = opts.bg || '#fffaf2';
    ctx.fillRect(x, y, boxSize, boxSize);
    ctx.fillStyle = opts.fg || '#211b16';
    qr.modules.forEach((row, rowIndex) => {
      row.forEach((dark, colIndex) => {
        if (!dark) return;
        ctx.fillRect(
          x + (quiet + colIndex) * moduleSize,
          y + (quiet + rowIndex) * moduleSize,
          moduleSize,
          moduleSize
        );
      });
    });
    return boxSize;
  }

  function drawShareFooter(ctx, style, W, y, align, options) {
    const opts = options || {};
    const qrModuleSize = Number(opts.qrModuleSize || 4);
    const qrQuiet = Number(opts.qrQuiet || 4);
    const qr = getReflectionCardQrMatrix();
    const qrOuter = (qr.size + qrQuiet * 2) * qrModuleSize;
    const chipW = opts.chipWidth || 484;
    const chipH = opts.chipHeight || Math.max(188, qrOuter + 20);
    const chipX = align === 'left' ? 80 : Math.round((W - chipW) / 2);
    const chipY = Math.min(y + 28, 1350 - chipH - 42);

    const glassGrad = ctx.createLinearGradient(chipX, chipY, chipX + chipW, chipY + chipH);
    glassGrad.addColorStop(0, 'rgba(255,255,255,0.26)');
    glassGrad.addColorStop(0.52, 'rgba(255,255,255,0.13)');
    glassGrad.addColorStop(1, 'rgba(255,255,255,0.06)');

    ctx.shadowColor = 'rgba(0,0,0,0.14)';
    ctx.shadowBlur = 14;
    ctx.shadowOffsetY = 6;
    ctx.fillStyle = glassGrad;
    _roundRect(ctx, chipX, chipY, chipW, chipH, 30);
    ctx.fill();
    ctx.shadowColor = 'transparent';
    ctx.shadowBlur = 0;
    ctx.shadowOffsetY = 0;
    ctx.strokeStyle = 'rgba(255,255,255,0.28)';
    ctx.lineWidth = 1.4;
    _roundRect(ctx, chipX, chipY, chipW, chipH, 30);
    ctx.stroke();

    const qrX = chipX + 16;
    const qrY = chipY + Math.round((chipH - qrOuter) / 2);
    ctx.shadowColor = 'rgba(0,0,0,0.12)';
    ctx.shadowBlur = 10;
    ctx.shadowOffsetY = 4;
    ctx.fillStyle = '#ffffff';
    _roundRect(ctx, qrX, qrY, qrOuter, qrOuter, 14);
    ctx.fill();
    ctx.shadowColor = 'transparent';
    ctx.shadowBlur = 0;
    ctx.shadowOffsetY = 0;
    drawReflectionQrCode(ctx, qrX, qrY, qrModuleSize, { quiet: qrQuiet, bg: '#ffffff', fg: '#000000' });

    const textX = qrX + qrOuter + 20;
    const textTop = chipY + Math.round(chipH / 2) - 8;
    ctx.textAlign = 'left';

    ctx.strokeStyle = style.accent || 'rgba(255,226,166,0.90)';
    ctx.lineWidth = 2;
    ctx.beginPath();
    ctx.moveTo(textX, textTop - 28);
    ctx.lineTo(Math.min(chipX + chipW - 26, textX + 112), textTop - 26);
    ctx.stroke();

    ctx.fillStyle = '#fffaf4';
    ctx.font = '800 21px -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif';
    ctx.fillText('ASK MIRROR TALK', textX, textTop - 12);

    ctx.font = '600 13px -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif';
    ctx.fillStyle = '#fffaf4';
    ctx.fillText('Scan to reflect', textX, textTop + 20);

    ctx.font = '600 12px -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif';
    ctx.fillStyle = 'rgba(255,250,244,0.78)';
    ctx.fillText(REFLECTION_CARD_URL_LABEL, textX, textTop + 49);

    if (ENABLE_TEST_EXPORTS) {
      window.__AMT_LAST_FOOTER_DEBUG__ = {
        label: 'Scan to reflect',
        qrPayload: getReflectionCardQrPayload(),
        qrMatrixSize: qr.size,
        qrModuleSize,
        qrQuiet,
        qrRenderedSize: qrOuter,
        urlLabel: REFLECTION_CARD_URL_LABEL
      };
    }
  }

  function buildBoldVibrantShareCard(ctx, normalized, style, W, H, variant) {
    // High-contrast bold variant for A/B testing
    // More vibrant colors, stronger accents, higher engagement appeal
    const headline = selectFittingShareHeadline(ctx, normalized, {
      maxWidth: W - 160,
      maxHeight: 500,
      maxLines: 5,
      fontTemplate: '800 __SIZE__px -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif',
      maxSize: 92,
      minSize: 50,
      lineHeightRatio: 1.1
    });

    const theme = String(normalized.theme || '').toLowerCase();
    
    // VIBRANT COLOR PALETTES - designed for high engagement and shareability
    let bgGrad, accentColor, textColor;
    
    if (theme === 'courage' || theme === 'fear') {
      bgGrad = { stops: ['#ff3d5a', '#ff6b4a', '#ffaa00'] };
      accentColor = '#ffff00';
      textColor = '#ffffff';
    } else if (theme === 'healing' || theme === 'grief') {
      bgGrad = { stops: ['#00d4aa', '#00b8ff', '#0088ff'] };
      accentColor = '#ffffff';
      textColor = '#ffffff';
    } else if (theme === 'faith' || theme === 'forgiveness' || theme === 'inner peace') {
      bgGrad = { stops: ['#9b59b6', '#8e44ad', '#c471ed'] };
      accentColor = '#ffe066';
      textColor = '#ffffff';
    } else if (theme === 'leadership' || theme === 'boundaries') {
      bgGrad = { stops: ['#2c3e50', '#3498db', '#00d9ff'] };
      accentColor = '#00ff99';
      textColor = '#ffffff';
    } else if (theme === 'gratitude' || theme === 'empowerment') {
      bgGrad = { stops: ['#ff6b35', '#ff8c42', '#ffa500'] };
      accentColor = '#ffffff';
      textColor = '#ffffff';
    } else {
      bgGrad = { stops: [style.bg[0] || '#2c3e50', style.bg[1] || '#3498db', style.bg[2] || '#00d9ff'] };
      accentColor = '#ffff00';
      textColor = '#ffffff';
    }
    
    // Strong background gradient
    const grad = ctx.createLinearGradient(0, 0, W, H);
    grad.addColorStop(0, bgGrad.stops[0]);
    grad.addColorStop(0.5, bgGrad.stops[1]);
    grad.addColorStop(1, bgGrad.stops[2]);
    ctx.fillStyle = grad;
    ctx.fillRect(0, 0, W, H);
    
    // Add bold geometric elements for visual interest
    const overlay = ctx.createRadialGradient(W / 2, H / 2, 0, W / 2, H / 2, W * 0.9);
    overlay.addColorStop(0, 'rgba(0,0,0,0)');
    overlay.addColorStop(1, 'rgba(0,0,0,0.15)');
    ctx.fillStyle = overlay;
    ctx.fillRect(0, 0, W, H);
    
    // Bold decorative circles - high contrast
    ctx.fillStyle = 'rgba(255,255,255,0.12)';
    ctx.beginPath();
    ctx.arc(W * 0.1, H * 0.15, 140, 0, Math.PI * 2);
    ctx.fill();
    ctx.beginPath();
    ctx.arc(W * 0.9, H * 0.8, 180, 0, Math.PI * 2);
    ctx.fill();
    
    // TOP ACCENT BAR - bold and eye-catching
    ctx.fillStyle = accentColor;
    ctx.fillRect(0, 0, W, 8);
    
    // Theme label - bold, high-contrast
    ctx.fillStyle = 'rgba(255,255,255,0.95)';
    ctx.font = '800 20px -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif';
    ctx.textAlign = 'center';
    ctx.fillText(String(normalized.theme || 'REFLECTION').toUpperCase(), W / 2, 90);
    
    // DIVIDER LINE - accent color
    ctx.strokeStyle = accentColor;
    ctx.lineWidth = 4;
    ctx.beginPath();
    ctx.moveTo(W * 0.25, 110);
    ctx.lineTo(W * 0.75, 110);
    ctx.stroke();
    
    // Main quote - BOLD, LARGE, HIGH CONTRAST
    ctx.fillStyle = textColor;
    ctx.shadowColor = 'rgba(0,0,0,0.4)';
    ctx.shadowBlur = 32;
    ctx.shadowOffsetY = 12;
    
    const quoteMetrics = drawFittedCanvasText(ctx, {
      text: headline,
      x: W / 2,
      y: H / 2 - 80,
      maxWidth: W - 160,
      maxHeight: 500,
      maxLines: 5,
      align: 'center',
      fontTemplate: '800 __SIZE__px -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif',
      maxSize: 92,
      minSize: 50,
      lineHeightRatio: 1.1
    });
    
    ctx.shadowColor = 'transparent';
    
    // Bottom accent bar
    ctx.fillStyle = accentColor;
    ctx.fillRect(0, H - 8, W, 8);
    
    // Footer with branding and QR
    const footerStyle = { ...style, text: textColor, accent: accentColor };
    drawShareFooter(ctx, footerStyle, W, H - 180, 'center');
    
    if (ENABLE_TEST_EXPORTS) {
      window.__AMT_LAST_RENDER_DEBUG__ = { family: 'bold_vibrant', headline };
    }
  }

  function buildPosterInsightShareCard(ctx, normalized, style, W, H, variant) {
    let headline = selectFittingShareHeadline(ctx, normalized, {
      maxWidth: W - 160,
      maxHeight: 520,
      maxLines: 6,
      fontTemplate: '500 __SIZE__px Georgia, serif',
      maxSize: 78,
      minSize: 44,
      lineHeightRatio: 1.14
    });
    headline = ensureReflectionSentence(headline);
    
    // Enhanced gradient background
    const richGrad = ctx.createLinearGradient(0, 0, W, H);
    richGrad.addColorStop(0, style.bg[0]);
    richGrad.addColorStop(0.42, style.bg[1]);
    richGrad.addColorStop(1, style.bg[2]);
    ctx.fillStyle = richGrad;
    ctx.fillRect(0, 0, W, H);
    
    // Add depth with orbs
    const orbA = ctx.createRadialGradient(W * 0.18, H * 0.22, 0, W * 0.18, H * 0.22, 440);
    orbA.addColorStop(0, 'rgba(255,255,255,0.14)');
    orbA.addColorStop(0.55, 'rgba(255,255,255,0.05)');
    orbA.addColorStop(1, 'transparent');
    ctx.fillStyle = orbA;
    ctx.fillRect(0, 0, W, H);
    
    const orbB = ctx.createRadialGradient(W * 0.86, H * 0.72, 0, W * 0.86, H * 0.72, 400);
    orbB.addColorStop(0, style.accentSoft || 'rgba(255,255,255,0.12)');
    orbB.addColorStop(0.6, 'rgba(255,255,255,0.04)');
    orbB.addColorStop(1, 'transparent');
    ctx.fillStyle = orbB;
    ctx.fillRect(0, 0, W, H);
    
    // Frame
    ctx.strokeStyle = 'rgba(255,255,255,0.16)';
    ctx.lineWidth = 2.5;
    _roundRect(ctx, 28, 28, W - 56, H - 56, 38);
    ctx.stroke();

    ctx.textAlign = 'left';
    ctx.fillStyle = style.accent;
    ctx.font = '600 21px -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif';
    ctx.fillText(String(normalized.theme || 'Reflection').toUpperCase(), 80, 105);
    
    // Subtle decorative line under theme
    ctx.strokeStyle = style.accent;
    ctx.lineWidth = 2;
    ctx.beginPath();
    ctx.moveTo(80, 125);
    ctx.lineTo(280, 125);
    ctx.stroke();

    // Render headline as unified text block - clean design without blue box
    ctx.fillStyle = style.text;
    const headlineMetrics = drawFittedCanvasText(ctx, {
      text: headline,
      x: 80,
      y: 300,
      maxWidth: W - 160,
      maxHeight: 520,
      maxLines: 6,
      align: 'left',
      fontTemplate: '500 __SIZE__px Georgia, serif',
      maxSize: 78,
      minSize: 44,
      lineHeightRatio: 1.14
    });

    drawShareFooter(ctx, style, W, H - 135, 'left');
    if (ENABLE_TEST_EXPORTS) {
      window.__AMT_LAST_RENDER_DEBUG__ = { family: 'poster', headline };
    }
  }

  function buildSpotlightInsightShareCard(ctx, normalized, style, W, H, variant) {
    let headline = selectFittingShareHeadline(ctx, normalized, {
      maxWidth: W - 160,
      maxHeight: 620,
      maxLines: 6,
      fontTemplate: '500 __SIZE__px Georgia, serif',
      maxSize: 68,
      minSize: 42,
      lineHeightRatio: 1.15
    });
    headline = ensureReflectionSentence(headline);
    
    // Enhanced gradient background with more depth
    const richGrad = ctx.createLinearGradient(0, 0, W, H);
    richGrad.addColorStop(0, style.bg[0]);
    richGrad.addColorStop(0.35, style.bg[1]);
    richGrad.addColorStop(1, style.bg[2]);
    ctx.fillStyle = richGrad;
    ctx.fillRect(0, 0, W, H);
    
    // Add atmospheric orbs for depth
    const orbA = ctx.createRadialGradient(W * 0.82, H * 0.18, 0, W * 0.82, H * 0.18, 420);
    orbA.addColorStop(0, 'rgba(255,255,255,0.12)');
    orbA.addColorStop(0.5, 'rgba(255,255,255,0.04)');
    orbA.addColorStop(1, 'transparent');
    ctx.fillStyle = orbA;
    ctx.fillRect(0, 0, W, H);
    
    const orbB = ctx.createRadialGradient(W * 0.15, H * 0.78, 0, W * 0.15, H * 0.78, 380);
    orbB.addColorStop(0, style.accentSoft || 'rgba(255,255,255,0.10)');
    orbB.addColorStop(0.6, 'rgba(255,255,255,0.03)');
    orbB.addColorStop(1, 'transparent');
    ctx.fillStyle = orbB;
    ctx.fillRect(0, 0, W, H);
    
    // Frame border
    ctx.strokeStyle = 'rgba(255,255,255,0.15)';
    ctx.lineWidth = 2.5;
    _roundRect(ctx, 28, 28, W - 56, H - 56, 40);
    ctx.stroke();

    ctx.textAlign = 'center';
    ctx.fillStyle = style.accent;
    ctx.font = '700 23px -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif';
    ctx.fillText(String(normalized.theme || 'Reflection').toUpperCase(), W / 2, 105);

    // Subtle decorative line under theme
    ctx.strokeStyle = style.accent;
    ctx.lineWidth = 2;
    ctx.beginPath();
    ctx.moveTo(W / 2 - 40, 125);
    ctx.lineTo(W / 2 + 40, 125);
    ctx.stroke();

    // Render headline as unified text block with consistent typography
    ctx.fillStyle = style.text;
    const headlineMetrics = drawFittedCanvasText(ctx, {
      text: headline,
      x: W / 2,
      y: 300,
      maxWidth: W - 160,
      maxHeight: 620,
      maxLines: 6,
      align: 'center',
      fontTemplate: '500 __SIZE__px Georgia, serif',
      maxSize: 68,
      minSize: 42,
      lineHeightRatio: 1.15
    });

    drawShareFooter(ctx, style, W, H - 135, 'center');
    if (ENABLE_TEST_EXPORTS) {
      window.__AMT_LAST_RENDER_DEBUG__ = { family: 'spotlight', headline };
    }
  }

  function buildAuraPosterShareCard(ctx, normalized, style, W, H, variant) {
    const headlineOptions = {
      maxWidth: W - 190,
      maxHeight: 470,
      maxLines: 4,
      fontTemplate: '700 __SIZE__px Georgia, serif',
      maxSize: 88,
      minSize: 44,
      lineHeightRatio: 1.12
    };
    const headline = selectFittingShareHeadline(ctx, normalized, headlineOptions);

    const theme = String(normalized.theme || 'Reflection');
    const grad = ctx.createLinearGradient(0, 0, W, H);
    grad.addColorStop(0, style.bg[0]);
    grad.addColorStop(0.46, style.bg[1]);
    grad.addColorStop(1, style.bg[2]);
    ctx.fillStyle = grad;
    ctx.fillRect(0, 0, W, H);

    const bloomA = ctx.createRadialGradient(W * 0.24, H * 0.22, 0, W * 0.24, H * 0.22, 390);
    bloomA.addColorStop(0, 'rgba(255,255,255,0.24)');
    bloomA.addColorStop(1, 'rgba(255,255,255,0)');
    ctx.fillStyle = bloomA;
    ctx.fillRect(0, 0, W, H);

    const bloomB = ctx.createRadialGradient(W * 0.82, H * 0.76, 0, W * 0.82, H * 0.76, 420);
    bloomB.addColorStop(0, style.orbA || 'rgba(255,255,255,0.18)');
    bloomB.addColorStop(1, 'rgba(255,255,255,0)');
    ctx.fillStyle = bloomB;
    ctx.fillRect(0, 0, W, H);

    const depth = ctx.createLinearGradient(0, 0, 0, H);
    depth.addColorStop(0, 'rgba(0,0,0,0.08)');
    depth.addColorStop(0.52, 'rgba(0,0,0,0.00)');
    depth.addColorStop(1, 'rgba(0,0,0,0.28)');
    ctx.fillStyle = depth;
    ctx.fillRect(0, 0, W, H);

    drawThemeArtDirection(ctx, style, W, H, variant);

    ctx.strokeStyle = 'rgba(255,255,255,0.18)';
    ctx.lineWidth = 1.4;
    ctx.beginPath();
    ctx.moveTo(132, 164);
    ctx.lineTo(W - 132, 164);
    ctx.stroke();

    ctx.fillStyle = 'rgba(255,255,255,0.86)';
    ctx.font = '700 18px -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif';
    ctx.textAlign = 'left';
    ctx.fillText(theme.toUpperCase(), 98, 118);

    ctx.textAlign = 'right';
    ctx.font = '600 15px -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif';
    ctx.fillStyle = 'rgba(255,255,255,0.72)';
    ctx.fillText('ASK MIRROR TALK', W - 98, 118);

    ctx.shadowColor = 'rgba(0,0,0,0.24)';
    ctx.shadowBlur = 28;
    ctx.shadowOffsetY = 8;
    ctx.fillStyle = '#fffaf4';
    ctx.textAlign = 'center';
    const metrics = drawFittedCanvasText(ctx, {
      text: headline,
      x: W / 2,
      y: 445,
      maxWidth: headlineOptions.maxWidth,
      maxHeight: headlineOptions.maxHeight,
      maxLines: headlineOptions.maxLines,
      align: 'center',
      fontTemplate: headlineOptions.fontTemplate,
      maxSize: headlineOptions.maxSize,
      minSize: headlineOptions.minSize,
      lineHeightRatio: headlineOptions.lineHeightRatio
    });
    ctx.shadowColor = 'transparent';

    drawShareFooter(ctx, style, W, H - 206, 'center', { chipWidth: 472 });
    if (ENABLE_TEST_EXPORTS) {
      window.__AMT_LAST_RENDER_DEBUG__ = { family: 'aura_poster', headline };
    }
  }

  function buildMinimalInsightShareCard(ctx, normalized, style, W, H, variant) {
    drawShareCardShell(ctx, style, W, H, variant);
    const headlineOptions = {
      maxWidth: W - 184,
      maxHeight: 430,
      maxLines: 4,
      fontTemplate: '600 __SIZE__px Georgia, serif',
      maxSize: 74,
      minSize: 34,
      lineHeightRatio: 1.12
    };
    const headline = selectFittingShareHeadline(ctx, normalized, headlineOptions);
    const supportingCandidates = listSupportingReflectionCandidates(
      joinReflectionTextParts([normalized.answer, normalized.excerpt]),
      normalized.theme || '',
      headline
    );
    const excerptFitOptions = {
      maxWidth: W - 276,
      maxHeight: 216,
      maxLines: 4,
      fontTemplate: '500 __SIZE__px Georgia, serif',
      maxSize: 40,
      minSize: 28,
      lineHeightRatio: 1.35
    };
    const supportingExcerpt = selectFittingReflectionLine(ctx, supportingCandidates, excerptFitOptions);
    const showExcerpt = !!supportingExcerpt && !isDuplicateReflectionLine(headline, supportingExcerpt);

    ctx.fillStyle = 'rgba(255,255,255,0.9)';
    ctx.fillRect(82, 86, W - 164, 2);

    ctx.fillStyle = style.accent;
    ctx.font = '600 19px -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif';
    ctx.textAlign = 'left';
    ctx.fillText(String(normalized.theme || 'Reflection').toUpperCase(), 92, 126);
    ctx.textAlign = 'right';
    ctx.fillText('ASK MIRROR TALK', W - 92, 126);

    ctx.fillStyle = style.textSoft || 'rgba(255,255,255,0.78)';
    ctx.font = '500 28px -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif';
    wrapCanvasText(ctx, style.kicker, 92, 204, 520, 34, 2, 'left');

    ctx.fillStyle = style.text;
    const headlineMetrics = drawFittedCanvasText(ctx, {
      text: headline,
      x: 92,
      y: 388,
      maxWidth: headlineOptions.maxWidth,
      maxHeight: showExcerpt ? 260 : 430,
      maxLines: headlineOptions.maxLines,
      align: 'left',
      fontTemplate: headlineOptions.fontTemplate,
      maxSize: showExcerpt ? 68 : 74,
      minSize: headlineOptions.minSize,
      lineHeightRatio: headlineOptions.lineHeightRatio
    });

    if (!showExcerpt) {
      drawShareFooter(ctx, style, W, H - 154, 'left');
      if (ENABLE_TEST_EXPORTS) {
        window.__AMT_LAST_RENDER_DEBUG__ = { family: 'minimal', headline, showExcerpt: false };
      }
      return;
    }

    const excerptBoxY = 510;
    const excerptBoxH = 360;
    ctx.fillStyle = 'rgba(255,255,255,0.09)';
    _roundRect(ctx, 92, excerptBoxY, W - 184, excerptBoxH, 26);
    ctx.fill();
    ctx.strokeStyle = style.panelEdge || 'rgba(255,255,255,0.18)';
    ctx.lineWidth = 1.1;
    _roundRect(ctx, 92, excerptBoxY, W - 184, excerptBoxH, 26);
    ctx.stroke();

    ctx.fillStyle = style.accent;
    ctx.font = '70px Georgia, serif';
    ctx.fillText('“', 116, excerptBoxY + 92);

    ctx.fillStyle = style.cardText || style.text;
    const excerptMetrics = getFittedCanvasTextMetrics(ctx, {
      text: supportingExcerpt,
      ...excerptFitOptions
    });
    ctx.font = `500 ${excerptMetrics.size}px Georgia, serif`;
    wrapCanvasText(ctx, supportingExcerpt, 146, excerptBoxY + 132, W - 276, excerptMetrics.lineHeight, excerptFitOptions.maxLines, 'left');

    drawShareFooter(ctx, style, W, H - 154, 'left');
    if (ENABLE_TEST_EXPORTS) {
      window.__AMT_LAST_RENDER_DEBUG__ = { family: 'minimal', headline, supportingExcerpt, showExcerpt: true };
    }
  }

  function buildAtmosphericInsightShareCard(ctx, normalized, style, W, H, variant) {
    drawShareCardShell(ctx, style, W, H, variant);
    const headlineOptions = {
      maxWidth: W - 220,
      maxHeight: 410,
      maxLines: 4,
      fontTemplate: '600 __SIZE__px Georgia, serif',
      maxSize: 74,
      minSize: 34,
      lineHeightRatio: 1.12
    };
    const headline = selectFittingShareHeadline(ctx, normalized, headlineOptions);
    const supportingCandidates = listSupportingReflectionCandidates(
      joinReflectionTextParts([normalized.answer, normalized.excerpt]),
      normalized.theme || '',
      headline
    );
    const excerptFitOptions = {
      maxWidth: W - 300,
      maxHeight: 138,
      maxLines: 3,
      fontTemplate: '500 __SIZE__px Georgia, serif',
      maxSize: 34,
      minSize: 24,
      lineHeightRatio: 1.35
    };
    const supportingExcerpt = selectFittingReflectionLine(ctx, supportingCandidates, excerptFitOptions);
    const showExcerpt = !!supportingExcerpt && !isDuplicateReflectionLine(headline, supportingExcerpt);

    const veil = ctx.createLinearGradient(0, H * 0.18, 0, H);
    veil.addColorStop(0, 'rgba(8,8,8,0.00)');
    veil.addColorStop(0.34, 'rgba(8,8,8,0.10)');
    veil.addColorStop(1, 'rgba(8,8,8,0.28)');
    ctx.fillStyle = veil;
    ctx.fillRect(0, 0, W, H);

    ctx.fillStyle = 'rgba(255,255,255,0.08)';
    ctx.beginPath();
    ctx.arc(W * 0.78, H * 0.24, 160, 0, Math.PI * 2);
    ctx.fill();

    ctx.fillStyle = style.accent;
    ctx.font = '600 20px -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif';
    ctx.textAlign = 'left';
    ctx.fillText(String(normalized.theme || 'Reflection').toUpperCase(), 94, 112);
    ctx.textAlign = 'right';
    ctx.fillText('ASK MIRROR TALK', W - 94, 112);

    ctx.fillStyle = style.textSoft || 'rgba(255,255,255,0.78)';
    ctx.font = '500 28px -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif';
    wrapCanvasText(ctx, style.kicker, 96, 226, 420, 34, 3, 'left');

    ctx.fillStyle = 'rgba(255,255,255,0.94)';
    const headlineMetrics = drawFittedCanvasText(ctx, {
      text: headline,
      x: 96,
      y: 664,
      maxWidth: headlineOptions.maxWidth,
      maxHeight: showExcerpt ? 280 : 410,
      maxLines: headlineOptions.maxLines,
      align: 'left',
      fontTemplate: headlineOptions.fontTemplate,
      maxSize: showExcerpt ? 68 : 74,
      minSize: headlineOptions.minSize,
      lineHeightRatio: headlineOptions.lineHeightRatio
    });

    if (!showExcerpt) {
      drawShareFooter(ctx, style, W, H - 154, 'left');
      if (ENABLE_TEST_EXPORTS) {
        window.__AMT_LAST_RENDER_DEBUG__ = { family: 'atmospheric', headline, showExcerpt: false };
      }
      return;
    }

    const excerptBoxY = 810;
    const excerptBoxH = 250;
    ctx.fillStyle = 'rgba(255,255,255,0.08)';
    _roundRect(ctx, 92, excerptBoxY, W - 184, excerptBoxH, 30);
    ctx.fill();
    ctx.strokeStyle = style.panelEdge || 'rgba(255,255,255,0.18)';
    ctx.lineWidth = 1.1;
    _roundRect(ctx, 92, excerptBoxY, W - 184, excerptBoxH, 30);
    ctx.stroke();

    ctx.fillStyle = style.accent;
    ctx.font = '60px Georgia, serif';
    ctx.textAlign = 'left';
    ctx.fillText('“', 124, excerptBoxY + 86);

    ctx.fillStyle = style.cardText || style.text;
    const excerptMetrics = getFittedCanvasTextMetrics(ctx, {
      text: supportingExcerpt,
      ...excerptFitOptions
    });
    ctx.font = `500 ${excerptMetrics.size}px Georgia, serif`;
    wrapCanvasText(ctx, supportingExcerpt, 154, excerptBoxY + 118, W - 300, excerptMetrics.lineHeight, excerptFitOptions.maxLines, 'left');

    drawShareFooter(ctx, style, W, H - 154, 'left');
    if (ENABLE_TEST_EXPORTS) {
      window.__AMT_LAST_RENDER_DEBUG__ = { family: 'atmospheric', headline, supportingExcerpt, showExcerpt: true };
    }
  }

  function calculateBalancedShareBaseline(metrics, options) {
    const opts = options || {};
    const contentTop = Number(opts.contentTop || 0);
    const contentBottom = Number(opts.contentBottom || contentTop);
    const groupHeight = Math.max(1, Number(opts.groupHeight || (metrics && metrics.height) || 1));
    const size = Math.max(1, Number((metrics && metrics.size) || 1));
    const available = Math.max(0, contentBottom - contentTop);
    const groupTop = contentTop + Math.max(0, available - groupHeight) / 2;
    const minBaseline = Number(opts.minBaseline || contentTop);
    const maxBaseline = Number(opts.maxBaseline || contentBottom);
    return Math.round(Math.max(minBaseline, Math.min(maxBaseline, groupTop + size)));
  }

  function buildEditorialInsightShareCard(ctx, normalized, style, W, H, variant) {
    drawShareCardShell(ctx, style, W, H, variant);
    const headlineOptions = {
      maxWidth: variant.questionWidth,
      maxHeightWithExcerpt: 390,
      maxHeightWithoutExcerpt: 560,
      maxLines: 4,
      fontTemplate: '700 __SIZE__px Georgia, serif',
      maxSizeWithExcerpt: 76,
      maxSizeWithoutExcerpt: 82,
      minSize: 34,
      lineHeightRatio: 1.1
    };
    
    // Prioritize API-generated shareable_headline if available and fits rendering constraints
    const apiHeadline = normalized.shareable_headline && typeof normalized.shareable_headline === 'string' 
      ? ensureReflectionSentence(normalized.shareable_headline) 
      : '';
    
    let headline = '';
    
    // Try API headline first if it's not weak and fits the canvas
    if (apiHeadline && !isWeakShareHeadlineCandidate(apiHeadline)) {
      // First try: standard constraints
      if (canRenderCanvasTextFully(
        ctx,
        apiHeadline,
        headlineOptions.maxWidth,
        headlineOptions.maxHeightWithExcerpt,
        headlineOptions.maxLines,
        headlineOptions.fontTemplate,
        headlineOptions.maxSizeWithExcerpt,
        headlineOptions.minSize,
        headlineOptions.lineHeightRatio
      ) || canRenderCanvasTextFully(
        ctx,
        apiHeadline,
        headlineOptions.maxWidth,
        headlineOptions.maxHeightWithoutExcerpt,
        headlineOptions.maxLines,
        headlineOptions.fontTemplate,
        headlineOptions.maxSizeWithoutExcerpt,
        headlineOptions.minSize,
        headlineOptions.lineHeightRatio
      )) {
        headline = apiHeadline;
        console.log('[Editorial Card] Using API-generated headline:', apiHeadline.substring(0, 60) + '...');
      }
      // Second try: allow smaller font (reduce minSize by 20%)
      else {
        const flexibleMinSize = Math.max(28, Math.floor(headlineOptions.minSize * 0.8));
        if (canRenderCanvasTextFully(
          ctx,
          apiHeadline,
          headlineOptions.maxWidth,
          headlineOptions.maxHeightWithExcerpt,
          headlineOptions.maxLines,
          headlineOptions.fontTemplate,
          headlineOptions.maxSizeWithExcerpt,
          flexibleMinSize,
          headlineOptions.lineHeightRatio
        ) || canRenderCanvasTextFully(
          ctx,
          apiHeadline,
          headlineOptions.maxWidth,
          headlineOptions.maxHeightWithoutExcerpt,
          headlineOptions.maxLines,
          headlineOptions.fontTemplate,
          headlineOptions.maxSizeWithoutExcerpt,
          flexibleMinSize,
          headlineOptions.lineHeightRatio
        )) {
          headline = apiHeadline;
          console.log('[Editorial Card] Using API headline with reduced font size');
        } else {
          console.log('[Editorial Card] API headline exists but doesn\'t fit canvas constraints, using fallback');
        }
      }
    } else if (!apiHeadline) {
      console.log('[Editorial Card] No API headline available, extracting from answer text');
    } else {
      console.log('[Editorial Card] API headline is weak/generic, using fallback');
    }
    
    // Fallback to extraction from answer text if API headline not usable
    if (!headline) {
      const headlineCandidates = listCardHeadlineCandidates(
        joinReflectionTextParts([normalized.answer, normalized.excerpt]),
        normalized.theme || ''
      );

      headline = headlineCandidates.find(candidate =>
        canRenderCanvasTextFully(
          ctx,
          candidate,
          headlineOptions.maxWidth,
          headlineOptions.maxHeightWithExcerpt,
          headlineOptions.maxLines,
          headlineOptions.fontTemplate,
          headlineOptions.maxSizeWithExcerpt,
          headlineOptions.minSize,
          headlineOptions.lineHeightRatio
        )
      ) || headlineCandidates.find(candidate =>
        canRenderCanvasTextFully(
          ctx,
          candidate,
          headlineOptions.maxWidth,
          headlineOptions.maxHeightWithoutExcerpt,
          headlineOptions.maxLines,
          headlineOptions.fontTemplate,
          headlineOptions.maxSizeWithoutExcerpt,
          headlineOptions.minSize,
          headlineOptions.lineHeightRatio
        )
      ) || buildThemeReflectionFallback(normalized.theme || '');
    }

    const supportingCandidates = listSupportingReflectionCandidates(
      joinReflectionTextParts([normalized.answer, normalized.excerpt]),
      normalized.theme || '',
      headline
    );
    const headlineCanShareSpace = canRenderCanvasTextFully(
        ctx,
        headline,
        headlineOptions.maxWidth,
        headlineOptions.maxHeightWithExcerpt,
        headlineOptions.maxLines,
        headlineOptions.fontTemplate,
        headlineOptions.maxSizeWithExcerpt,
        headlineOptions.minSize,
        headlineOptions.lineHeightRatio
      );
    const panelInset = variant.panelInset;
    const panelWidth = W - (panelInset * 2);
    const excerptTextWidth = panelWidth - ((variant.excerptX - panelInset) * 2);
    const excerptFitOptions = {
      maxWidth: excerptTextWidth,
      maxHeight: 238,
      maxLines: 5,
      fontTemplate: '500 __SIZE__px Georgia, serif',
      maxSize: 43,
      minSize: 26,
      lineHeightRatio: 1.16
    };
    const supportingExcerpt = headlineCanShareSpace
      ? selectFittingReflectionLine(ctx, supportingCandidates, excerptFitOptions)
      : '';
    const showExcerpt = !!supportingExcerpt && !isDuplicateReflectionLine(headline, supportingExcerpt);
    const headlineMetrics = getFittedCanvasTextMetrics(ctx, {
      text: headline,
      maxWidth: headlineOptions.maxWidth,
      maxHeight: showExcerpt ? headlineOptions.maxHeightWithExcerpt : headlineOptions.maxHeightWithoutExcerpt,
      maxLines: headlineOptions.maxLines,
      fontTemplate: headlineOptions.fontTemplate,
      maxSize: showExcerpt ? headlineOptions.maxSizeWithExcerpt : headlineOptions.maxSizeWithoutExcerpt,
      minSize: headlineOptions.minSize,
      lineHeightRatio: headlineOptions.lineHeightRatio
    });
    const excerptMetrics = showExcerpt ? getFittedCanvasTextMetrics(ctx, {
      text: supportingExcerpt,
      maxWidth: excerptTextWidth,
      maxHeight: excerptFitOptions.maxHeight,
      maxLines: excerptFitOptions.maxLines,
      fontTemplate: excerptFitOptions.fontTemplate,
      maxSize: excerptFitOptions.maxSize,
      minSize: excerptFitOptions.minSize,
      lineHeightRatio: excerptFitOptions.lineHeightRatio
    }) : null;
    const excerptBoxH = showExcerpt
      ? Math.max(224, Math.min(380, 128 + excerptMetrics.height + 70))
      : 0;
    const footerY = H - 188;
    const themeGap = showExcerpt ? 38 : 44;
    const panelGap = 106;
    const groupHeight = headlineMetrics.height + themeGap + (showExcerpt ? panelGap + excerptBoxH : 54);
    const headlineStartY = calculateBalancedShareBaseline(headlineMetrics, {
      contentTop: showExcerpt ? 218 : 270,
      contentBottom: footerY - 112,
      groupHeight,
      minBaseline: showExcerpt ? 238 : 340,
      maxBaseline: showExcerpt ? 344 : 540
    });

    ctx.fillStyle = style.accent;
    ctx.font = '600 22px Georgia, serif';
    ctx.textAlign = variant.questionAlign === 'left' ? 'left' : 'center';
    ctx.fillText('ASK MIRROR TALK', variant.questionAlign === 'left' ? 98 : W / 2, 114);

    ctx.font = '600 17px -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif';
    ctx.fillStyle = style.textSoft || 'rgba(255,255,255,0.76)';
    ctx.fillText(style.kicker, variant.questionAlign === 'left' ? 98 : W / 2, 150);

    ctx.fillStyle = style.text;
    drawFittedCanvasText(ctx, {
      text: headline,
      x: variant.questionX,
      y: headlineStartY,
      maxWidth: headlineOptions.maxWidth,
      maxHeight: showExcerpt ? headlineOptions.maxHeightWithExcerpt : headlineOptions.maxHeightWithoutExcerpt,
      maxLines: headlineOptions.maxLines,
      align: variant.questionAlign,
      fontTemplate: headlineOptions.fontTemplate,
      maxSize: showExcerpt ? headlineOptions.maxSizeWithExcerpt : headlineOptions.maxSizeWithoutExcerpt,
      minSize: headlineOptions.minSize,
      lineHeightRatio: headlineOptions.lineHeightRatio
    });
    const questionBottom = headlineStartY + Math.max(headlineMetrics.height - headlineMetrics.size, 0);

    const themeLabel = truncateText(normalized.theme || 'Reflection', 24);
    ctx.font = '600 22px -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif';
    const themeWidth = Math.max(228, Math.ceil(ctx.measureText(themeLabel).width + 92));
    const themeX = variant.themeAlign === 'left' ? 94 : Math.round((W - themeWidth) / 2);
    const themeY = questionBottom + themeGap;

    const pillGrad = ctx.createLinearGradient(themeX, themeY, themeX + themeWidth, themeY);
    pillGrad.addColorStop(0, 'rgba(255,255,255,0.30)');
    pillGrad.addColorStop(1, 'rgba(255,255,255,0.12)');
    ctx.fillStyle = pillGrad;
    _roundRect(ctx, themeX, themeY, themeWidth, 54, 27);
    ctx.fill();
    ctx.strokeStyle = 'rgba(255,255,255,0.22)';
    ctx.lineWidth = 1.5;
    _roundRect(ctx, themeX, themeY, themeWidth, 54, 27);
    ctx.stroke();
    ctx.fillStyle = style.accent;
    ctx.textAlign = variant.themeAlign === 'left' ? 'left' : 'center';
    ctx.textBaseline = 'middle';
    ctx.fillText(themeLabel, variant.themeAlign === 'left' ? themeX + 46 : themeX + (themeWidth / 2), themeY + 27);
    ctx.textBaseline = 'alphabetic';

    const excerptBoxY = themeY + panelGap;

    if (!showExcerpt) {
      drawShareFooter(ctx, style, W, footerY, variant.footerAlign);
      if (ENABLE_TEST_EXPORTS) {
        window.__AMT_LAST_RENDER_DEBUG__ = {
          family: 'editorial',
          headline,
          supportingExcerpt: supportingCandidates[0] || '',
          showExcerpt: false,
          panelMode: 'none',
          excerptRejected: supportingCandidates.length ? 'does_not_fit' : 'none_available',
          layout: { headlineStartY, footerY, groupHeight }
        };
      }
      return;
    }

    const panelMode = excerptMetrics.lineCount <= 2 ? 'compact' : excerptMetrics.lineCount === 3 ? 'balanced' : 'full';

    ctx.shadowColor = 'rgba(0,0,0,0.18)';
    ctx.shadowBlur = 40;
    ctx.shadowOffsetY = 16;
    ctx.fillStyle = style.card;
    _roundRect(ctx, panelInset, excerptBoxY, panelWidth, excerptBoxH, 34);
    ctx.fill();
    ctx.shadowColor = 'transparent';
    ctx.strokeStyle = style.panelEdge || 'rgba(255,255,255,0.40)';
    ctx.lineWidth = 1.5;
    _roundRect(ctx, panelInset, excerptBoxY, panelWidth, excerptBoxH, 34);
    ctx.stroke();

    const accentBar = ctx.createLinearGradient(panelInset, excerptBoxY, W - panelInset, excerptBoxY);
    accentBar.addColorStop(0, style.accent);
    accentBar.addColorStop(1, 'rgba(255,255,255,0)');
    ctx.fillStyle = accentBar;
    _roundRect(ctx, panelInset + 24, excerptBoxY + 26, variant.accentWidth, 8, 4);
    ctx.fill();

    ctx.fillStyle = style.accent;
    ctx.font = '82px Georgia, serif';
    ctx.textAlign = 'left';
    ctx.fillText('“', variant.excerptX - 10, excerptBoxY + 106);

    ctx.fillStyle = style.cardText;
    ctx.font = `500 ${excerptMetrics.size}px Georgia, serif`;
    wrapCanvasText(ctx, supportingExcerpt, variant.excerptX, excerptBoxY + 158, excerptTextWidth, excerptMetrics.lineHeight, excerptFitOptions.maxLines, 'left');

    drawShareFooter(ctx, style, W, footerY, variant.footerAlign);
    if (ENABLE_TEST_EXPORTS) {
      window.__AMT_LAST_RENDER_DEBUG__ = {
        family: 'editorial',
        headline,
        supportingExcerpt,
        showExcerpt: true,
        panelMode,
        excerptLineCount: excerptMetrics.lineCount,
        excerptPanelHeight: excerptBoxH,
        layout: { headlineStartY, footerY, groupHeight }
      };
    }
  }

  function buildEditorialSereneInsightShareCard(ctx, normalized, style, W, H, variant) {
    drawShareCardShell(ctx, style, W, H, variant);
    const headlineOptions = {
      maxWidth: 848,
      maxHeightWithExcerpt: 360,
      maxHeightWithoutExcerpt: 500,
      maxLines: 4,
      fontTemplate: '700 __SIZE__px Georgia, serif',
      maxSizeWithExcerpt: 72,
      maxSizeWithoutExcerpt: 78,
      minSize: 34,
      lineHeightRatio: 1.1
    };
    
    // Prioritize API-generated shareable_headline if available and fits rendering constraints
    const apiHeadline = normalized.shareable_headline && typeof normalized.shareable_headline === 'string' 
      ? ensureReflectionSentence(normalized.shareable_headline) 
      : '';
    
    let headline = '';
    
    // Try API headline first if it's not weak and fits the canvas
    if (apiHeadline && !isWeakShareHeadlineCandidate(apiHeadline)) {
      // First try: standard constraints
      if (canRenderCanvasTextFully(
        ctx,
        apiHeadline,
        headlineOptions.maxWidth,
        headlineOptions.maxHeightWithExcerpt,
        headlineOptions.maxLines,
        headlineOptions.fontTemplate,
        headlineOptions.maxSizeWithExcerpt,
        headlineOptions.minSize,
        headlineOptions.lineHeightRatio
      ) || canRenderCanvasTextFully(
        ctx,
        apiHeadline,
        headlineOptions.maxWidth,
        headlineOptions.maxHeightWithoutExcerpt,
        headlineOptions.maxLines,
        headlineOptions.fontTemplate,
        headlineOptions.maxSizeWithoutExcerpt,
        headlineOptions.minSize,
        headlineOptions.lineHeightRatio
      )) {
        headline = apiHeadline;
        console.log('[Editorial Serene Card] Using API-generated headline:', apiHeadline.substring(0, 60) + '...');
      }
      // Second try: allow smaller font (reduce minSize by 20%)
      else {
        const flexibleMinSize = Math.max(28, Math.floor(headlineOptions.minSize * 0.8));
        if (canRenderCanvasTextFully(
          ctx,
          apiHeadline,
          headlineOptions.maxWidth,
          headlineOptions.maxHeightWithExcerpt,
          headlineOptions.maxLines,
          headlineOptions.fontTemplate,
          headlineOptions.maxSizeWithExcerpt,
          flexibleMinSize,
          headlineOptions.lineHeightRatio
        ) || canRenderCanvasTextFully(
          ctx,
          apiHeadline,
          headlineOptions.maxWidth,
          headlineOptions.maxHeightWithoutExcerpt,
          headlineOptions.maxLines,
          headlineOptions.fontTemplate,
          headlineOptions.maxSizeWithoutExcerpt,
          flexibleMinSize,
          headlineOptions.lineHeightRatio
        )) {
          headline = apiHeadline;
          console.log('[Editorial Serene Card] Using API headline with reduced font size');
        } else {
          console.log('[Editorial Serene Card] API headline exists but doesn\'t fit canvas constraints, using fallback');
        }
      }
    } else if (!apiHeadline) {
      console.log('[Editorial Serene Card] No API headline available, extracting from answer text');
    } else {
      console.log('[Editorial Serene Card] API headline is weak/generic, using fallback');
    }
    
    // Fallback to extraction from answer text if API headline not usable
    if (!headline) {
      const headlineCandidates = listCardHeadlineCandidates(
        joinReflectionTextParts([normalized.answer, normalized.excerpt]),
        normalized.theme || ''
      );

      headline = headlineCandidates.find(candidate =>
        canRenderCanvasTextFully(
          ctx,
          candidate,
          headlineOptions.maxWidth,
          headlineOptions.maxHeightWithExcerpt,
          headlineOptions.maxLines,
          headlineOptions.fontTemplate,
          headlineOptions.maxSizeWithExcerpt,
          headlineOptions.minSize,
          headlineOptions.lineHeightRatio
        )
      ) || headlineCandidates.find(candidate =>
        canRenderCanvasTextFully(
          ctx,
          candidate,
          headlineOptions.maxWidth,
          headlineOptions.maxHeightWithoutExcerpt,
          headlineOptions.maxLines,
          headlineOptions.fontTemplate,
          headlineOptions.maxSizeWithoutExcerpt,
          headlineOptions.minSize,
          headlineOptions.lineHeightRatio
        )
      ) || buildThemeReflectionFallback(normalized.theme || '');
    }

    const supportingCandidates = listSupportingReflectionCandidates(
      joinReflectionTextParts([normalized.answer, normalized.excerpt]),
      normalized.theme || '',
      headline
    );
    const headlineCanShareSpace = canRenderCanvasTextFully(
        ctx,
        headline,
        headlineOptions.maxWidth,
        headlineOptions.maxHeightWithExcerpt,
        headlineOptions.maxLines,
        headlineOptions.fontTemplate,
        headlineOptions.maxSizeWithExcerpt,
        headlineOptions.minSize,
        headlineOptions.lineHeightRatio
      );
    const panelInset = 110;
    const panelWidth = W - (panelInset * 2);
    const excerptX = 154;
    const excerptTextWidth = panelWidth - ((excerptX - panelInset) * 2);
    const excerptFitOptions = {
      maxWidth: excerptTextWidth,
      maxHeight: 210,
      maxLines: 5,
      fontTemplate: '500 __SIZE__px Georgia, serif',
      maxSize: 40,
      minSize: 25,
      lineHeightRatio: 1.16
    };
    const supportingExcerpt = headlineCanShareSpace
      ? selectFittingReflectionLine(ctx, supportingCandidates, excerptFitOptions)
      : '';
    const showExcerpt = !!supportingExcerpt && !isDuplicateReflectionLine(headline, supportingExcerpt);
    const headlineMetrics = getFittedCanvasTextMetrics(ctx, {
      text: headline,
      maxWidth: headlineOptions.maxWidth,
      maxHeight: showExcerpt ? headlineOptions.maxHeightWithExcerpt : headlineOptions.maxHeightWithoutExcerpt,
      maxLines: headlineOptions.maxLines,
      fontTemplate: headlineOptions.fontTemplate,
      maxSize: showExcerpt ? headlineOptions.maxSizeWithExcerpt : headlineOptions.maxSizeWithoutExcerpt,
      minSize: headlineOptions.minSize,
      lineHeightRatio: headlineOptions.lineHeightRatio
    });
    const excerptMetrics = showExcerpt ? getFittedCanvasTextMetrics(ctx, {
      text: supportingExcerpt,
      maxWidth: excerptTextWidth,
      maxHeight: excerptFitOptions.maxHeight,
      maxLines: excerptFitOptions.maxLines,
      fontTemplate: excerptFitOptions.fontTemplate,
      maxSize: excerptFitOptions.maxSize,
      minSize: excerptFitOptions.minSize,
      lineHeightRatio: excerptFitOptions.lineHeightRatio
    }) : null;
    const excerptBoxH = showExcerpt
      ? Math.max(210, Math.min(340, 120 + excerptMetrics.height + 56))
      : 0;
    const footerY = H - 188;
    const panelGap = 96;
    const groupHeight = headlineMetrics.height + (showExcerpt ? panelGap + excerptBoxH : 0);
    const headlineStartY = calculateBalancedShareBaseline(headlineMetrics, {
      contentTop: showExcerpt ? 238 : 330,
      contentBottom: footerY - 118,
      groupHeight,
      minBaseline: showExcerpt ? 278 : 390,
      maxBaseline: showExcerpt ? 390 : 610
    });

    ctx.textAlign = 'right';
    ctx.fillStyle = style.accent;
    ctx.font = '600 22px Georgia, serif';
    ctx.fillText('ASK MIRROR TALK', W - 96, 114);

    ctx.fillStyle = style.textSoft || 'rgba(255,255,255,0.76)';
    ctx.font = '600 17px -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif';
    wrapCanvasText(ctx, style.kicker, W - 516, 156, 420, 26, 2, 'right');

    const themeLabel = truncateText(normalized.theme || 'Reflection', 24);
    ctx.font = '600 21px -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif';
    const pillWidth = Math.max(216, Math.ceil(ctx.measureText(themeLabel).width + 92));
    const pillX = 96;
    const pillY = 96;
    const themeGrad = ctx.createLinearGradient(pillX, pillY, pillX + pillWidth, pillY + 54);
    themeGrad.addColorStop(0, 'rgba(255,255,255,0.24)');
    themeGrad.addColorStop(1, 'rgba(255,255,255,0.10)');
    ctx.fillStyle = themeGrad;
    _roundRect(ctx, pillX, pillY, pillWidth, 54, 27);
    ctx.fill();
    ctx.strokeStyle = 'rgba(255,255,255,0.18)';
    ctx.lineWidth = 1.4;
    _roundRect(ctx, pillX, pillY, pillWidth, 54, 27);
    ctx.stroke();
    ctx.fillStyle = style.accent;
    ctx.textAlign = 'center';
    ctx.textBaseline = 'middle';
    ctx.fillText(themeLabel, pillX + (pillWidth / 2), pillY + 27);
    ctx.textBaseline = 'alphabetic';

    ctx.fillStyle = style.text;
    drawFittedCanvasText(ctx, {
      text: headline,
      x: 110,
      y: headlineStartY,
      maxWidth: headlineOptions.maxWidth,
      maxHeight: showExcerpt ? headlineOptions.maxHeightWithExcerpt : headlineOptions.maxHeightWithoutExcerpt,
      maxLines: headlineOptions.maxLines,
      align: 'left',
      fontTemplate: headlineOptions.fontTemplate,
      maxSize: showExcerpt ? headlineOptions.maxSizeWithExcerpt : headlineOptions.maxSizeWithoutExcerpt,
      minSize: headlineOptions.minSize,
      lineHeightRatio: headlineOptions.lineHeightRatio
    });
    const questionBottom = headlineStartY + Math.max(headlineMetrics.height - headlineMetrics.size, 0);

    const excerptBoxY = questionBottom + panelGap;

    if (!showExcerpt) {
      drawShareFooter(ctx, style, W, footerY, 'center');
      if (ENABLE_TEST_EXPORTS) {
        window.__AMT_LAST_RENDER_DEBUG__ = {
          family: 'editorial_serene',
          headline,
          supportingExcerpt: supportingCandidates[0] || '',
          showExcerpt: false,
          panelMode: 'none',
          excerptRejected: supportingCandidates.length ? 'does_not_fit' : 'none_available',
          layout: { headlineStartY, footerY, groupHeight }
        };
      }
      return;
    }

    const panelMode = excerptMetrics.lineCount <= 2 ? 'compact' : excerptMetrics.lineCount === 3 ? 'balanced' : 'full';

    ctx.shadowColor = 'rgba(0,0,0,0.15)';
    ctx.shadowBlur = 34;
    ctx.shadowOffsetY = 14;
    ctx.fillStyle = 'rgba(255,255,255,0.93)';
    _roundRect(ctx, panelInset, excerptBoxY, panelWidth, excerptBoxH, 30);
    ctx.fill();
    ctx.shadowColor = 'transparent';
    ctx.strokeStyle = style.panelEdge || 'rgba(255,255,255,0.30)';
    ctx.lineWidth = 1.2;
    _roundRect(ctx, panelInset, excerptBoxY, panelWidth, excerptBoxH, 30);
    ctx.stroke();

    const accentBar = ctx.createLinearGradient(panelInset, excerptBoxY, panelInset + 300, excerptBoxY);
    accentBar.addColorStop(0, style.accent);
    accentBar.addColorStop(1, 'rgba(255,255,255,0)');
    ctx.fillStyle = accentBar;
    _roundRect(ctx, panelInset + 26, excerptBoxY + 24, 278, 8, 4);
    ctx.fill();

    ctx.fillStyle = style.accent;
    ctx.font = '78px Georgia, serif';
    ctx.textAlign = 'left';
    ctx.fillText('“', excerptX - 12, excerptBoxY + 102);

    ctx.fillStyle = style.cardText;
    ctx.font = `500 ${excerptMetrics.size}px Georgia, serif`;
    wrapCanvasText(ctx, supportingExcerpt, excerptX, excerptBoxY + 148, excerptTextWidth, excerptMetrics.lineHeight, excerptFitOptions.maxLines, 'left');

    drawShareFooter(ctx, style, W, footerY, 'center');
    if (ENABLE_TEST_EXPORTS) {
      window.__AMT_LAST_RENDER_DEBUG__ = {
        family: 'editorial_serene',
        headline,
        supportingExcerpt,
        showExcerpt: true,
        panelMode,
        excerptLineCount: excerptMetrics.lineCount,
        excerptPanelHeight: excerptBoxH,
        layout: { headlineStartY, footerY, groupHeight }
      };
    }
  }

  function buildGradientImmersiveShareCard(ctx, normalized, style, W, H, variant) {
    // Vibrant, full-bleed gradient with bold centered quote
    const headlineOptions = {
      maxWidth: W - 160,
      maxHeight: 420,
      maxLines: 4,
      fontTemplate: '700 __SIZE__px -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif',
      maxSize: 88,
      minSize: 46,
      lineHeightRatio: 1.18
    };
    const headline = selectFittingShareHeadline(ctx, normalized, headlineOptions);
    
    // Dynamic gradient based on theme - more vibrant and saturated
    const vibrantGrad = ctx.createLinearGradient(0, 0, W, H);
    const theme = String(normalized.theme || '').toLowerCase();
    
    // Enhanced color palettes for each theme - more saturated
    if (theme === 'courage' || theme === 'fear') {
      vibrantGrad.addColorStop(0, '#ff3366');
      vibrantGrad.addColorStop(0.5, '#ff6b4a');
      vibrantGrad.addColorStop(1, '#ffaa00');
    } else if (theme === 'healing') {
      vibrantGrad.addColorStop(0, '#00d4aa');
      vibrantGrad.addColorStop(0.5, '#00b8e6');
      vibrantGrad.addColorStop(1, '#0088ff');
    } else if (theme === 'faith' || theme === 'forgiveness') {
      vibrantGrad.addColorStop(0, '#9b59b6');
      vibrantGrad.addColorStop(0.5, '#8e44ad');
      vibrantGrad.addColorStop(1, '#c471ed');
    } else if (theme === 'leadership') {
      vibrantGrad.addColorStop(0, '#2c3e50');
      vibrantGrad.addColorStop(0.5, '#3498db');
      vibrantGrad.addColorStop(1, '#00d9ff');
    } else if (theme === 'grief' || theme === 'inner peace') {
      vibrantGrad.addColorStop(0, '#667eea');
      vibrantGrad.addColorStop(0.5, '#764ba2');
      vibrantGrad.addColorStop(1, '#f093fb');
    } else {
      vibrantGrad.addColorStop(0, style.bg[0]);
      vibrantGrad.addColorStop(0.5, style.bg[1]);
      vibrantGrad.addColorStop(1, style.bg[2]);
    }
    
    ctx.fillStyle = vibrantGrad;
    ctx.fillRect(0, 0, W, H);
    
    // Subtle overlay for depth
    const overlay = ctx.createRadialGradient(W / 2, H / 2, 0, W / 2, H / 2, W * 0.8);
    overlay.addColorStop(0, 'rgba(0,0,0,0)');
    overlay.addColorStop(1, 'rgba(0,0,0,0.25)');
    ctx.fillStyle = overlay;
    ctx.fillRect(0, 0, W, H);
    
    // Decorative elements - light geometric shapes
    ctx.fillStyle = 'rgba(255,255,255,0.08)';
    ctx.beginPath();
    ctx.arc(W * 0.15, H * 0.20, 120, 0, Math.PI * 2);
    ctx.fill();
    ctx.beginPath();
    ctx.arc(W * 0.88, H * 0.75, 160, 0, Math.PI * 2);
    ctx.fill();
    
    // Main quote - large, bold, centered
    ctx.fillStyle = '#ffffff';
    ctx.shadowColor = 'rgba(0,0,0,0.35)';
    ctx.shadowBlur = 24;
    ctx.shadowOffsetY = 8;
    
    const quoteMetrics = drawFittedCanvasText(ctx, {
      text: headline,
      x: W / 2,
      y: H / 2 - 60,
      maxWidth: headlineOptions.maxWidth,
      maxHeight: headlineOptions.maxHeight,
      maxLines: headlineOptions.maxLines,
      align: 'center',
      fontTemplate: headlineOptions.fontTemplate,
      maxSize: headlineOptions.maxSize,
      minSize: headlineOptions.minSize,
      lineHeightRatio: headlineOptions.lineHeightRatio
    });
    
    ctx.shadowColor = 'transparent';
    
    // Theme label - minimal, top
    ctx.fillStyle = 'rgba(255,255,255,0.95)';
    ctx.font = '600 16px -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif';
    ctx.textAlign = 'center';
    ctx.fillText(String(normalized.theme || 'REFLECTION').toUpperCase(), W / 2, 84);
    
    drawShareFooter(ctx, style, W, H - 206, 'center');
    if (ENABLE_TEST_EXPORTS) {
      window.__AMT_LAST_RENDER_DEBUG__ = { family: 'gradient_immersive', headline };
    }
  }

  function buildNeonContemplativeShareCard(ctx, normalized, style, W, H, variant) {
    // Futuristic glass-morphism with neon accents
    const headlineOptions = {
      maxWidth: W - 280,
      maxHeight: 460,
      maxLines: 4,
      fontTemplate: '600 __SIZE__px Georgia, serif',
      maxSize: 72,
      minSize: 42,
      lineHeightRatio: 1.22
    };
    const headline = selectFittingShareHeadline(ctx, normalized, headlineOptions);
    
    // Dark gradient base
    const darkGrad = ctx.createLinearGradient(0, 0, W, H);
    darkGrad.addColorStop(0, '#0a0a0f');
    darkGrad.addColorStop(0.5, '#1a1a2e');
    darkGrad.addColorStop(1, '#16213e');
    ctx.fillStyle = darkGrad;
    ctx.fillRect(0, 0, W, H);
    
    // Neon glow orbs in background
    const neonColor = style.accent.includes('#') ? style.accent : '#00d9ff';
    
    const glow1 = ctx.createRadialGradient(W * 0.25, H * 0.35, 0, W * 0.25, H * 0.35, 280);
    glow1.addColorStop(0, neonColor + '40');
    glow1.addColorStop(0.5, neonColor + '20');
    glow1.addColorStop(1, 'transparent');
    ctx.fillStyle = glow1;
    ctx.fillRect(0, 0, W, H);
    
    const glow2 = ctx.createRadialGradient(W * 0.78, H * 0.68, 0, W * 0.78, H * 0.68, 320);
    glow2.addColorStop(0, neonColor + '35');
    glow2.addColorStop(0.5, neonColor + '18');
    glow2.addColorStop(1, 'transparent');
    ctx.fillStyle = glow2;
    ctx.fillRect(0, 0, W, H);
    
    // Glass-morphism panel
    const panelY = 240;
    const panelH = 780;
    
    ctx.fillStyle = 'rgba(255,255,255,0.06)';
    ctx.filter = 'blur(1px)';
    _roundRect(ctx, 80, panelY, W - 160, panelH, 36);
    ctx.fill();
    ctx.filter = 'none';
    
    // Panel border with neon glow
    ctx.strokeStyle = neonColor + 'cc';
    ctx.lineWidth = 2.5;
    ctx.shadowColor = neonColor;
    ctx.shadowBlur = 18;
    _roundRect(ctx, 80, panelY, W - 160, panelH, 36);
    ctx.stroke();
    ctx.shadowColor = 'transparent';
    
    // Secondary inner glow
    ctx.strokeStyle = 'rgba(255,255,255,0.25)';
    ctx.lineWidth = 1;
    _roundRect(ctx, 82, panelY + 2, W - 164, panelH - 4, 35);
    ctx.stroke();
    
    // Theme indicator - neon accent
    ctx.fillStyle = neonColor;
    ctx.font = '700 18px -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif';
    ctx.textAlign = 'center';
    ctx.fillText(String(normalized.theme || 'REFLECTION').toUpperCase(), W / 2, panelY + 68);
    
    // Main quote
    ctx.fillStyle = '#ffffff';
    const quoteMetrics = drawFittedCanvasText(ctx, {
      text: headline,
      x: W / 2,
      y: panelY + 240,
      maxWidth: headlineOptions.maxWidth,
      maxHeight: headlineOptions.maxHeight,
      maxLines: headlineOptions.maxLines,
      align: 'center',
      fontTemplate: headlineOptions.fontTemplate,
      maxSize: headlineOptions.maxSize,
      minSize: headlineOptions.minSize,
      lineHeightRatio: headlineOptions.lineHeightRatio
    });
    
    // Accent line - neon
    ctx.strokeStyle = neonColor;
    ctx.lineWidth = 3;
    ctx.beginPath();
    ctx.moveTo(W / 2 - 80, panelY + panelH - 86);
    ctx.lineTo(W / 2 + 80, panelY + panelH - 86);
    ctx.stroke();
    
    drawShareFooter(ctx, style, W, H - 206, 'center');
    if (ENABLE_TEST_EXPORTS) {
      window.__AMT_LAST_RENDER_DEBUG__ = { family: 'neon_contemplative', headline };
    }
  }

  function buildPrismaticQuoteShareCard(ctx, normalized, style, W, H, variant) {
    // Iridescent gradient with bold centered statement
    const headlineOptions = {
      maxWidth: W - 360,
      maxHeight: 420,
      maxLines: 4,
      fontTemplate: '700 __SIZE__px Georgia, serif',
      maxSize: 76,
      minSize: 44,
      lineHeightRatio: 1.20
    };
    const headline = selectFittingShareHeadline(ctx, normalized, headlineOptions);
    
    // Multi-color prismatic gradient
    const prismatic = ctx.createLinearGradient(0, 0, W, H);
    prismatic.addColorStop(0, '#ff0080');
    prismatic.addColorStop(0.2, '#ff8c00');
    prismatic.addColorStop(0.4, '#40e0d0');
    prismatic.addColorStop(0.6, '#7b68ee');
    prismatic.addColorStop(0.8, '#ff1493');
    prismatic.addColorStop(1, '#ff6347');
    ctx.fillStyle = prismatic;
    ctx.fillRect(0, 0, W, H);
    
    // Soften with overlay
    const softener = ctx.createLinearGradient(0, 0, 0, H);
    softener.addColorStop(0, 'rgba(0,0,0,0.15)');
    softener.addColorStop(0.5, 'rgba(0,0,0,0.05)');
    softener.addColorStop(1, 'rgba(0,0,0,0.20)');
    ctx.fillStyle = softener;
    ctx.fillRect(0, 0, W, H);
    
    // Radial light source for depth
    const spotlight = ctx.createRadialGradient(W / 2, H * 0.42, 0, W / 2, H * 0.42, W * 0.65);
    spotlight.addColorStop(0, 'rgba(255,255,255,0.18)');
    spotlight.addColorStop(0.6, 'rgba(255,255,255,0.05)');
    spotlight.addColorStop(1, 'rgba(255,255,255,0)');
    ctx.fillStyle = spotlight;
    ctx.fillRect(0, 0, W, H);
    
    // Main quote container - floating white panel
    const containerY = 320;
    const containerH = 680;
    
    ctx.shadowColor = 'rgba(0,0,0,0.45)';
    ctx.shadowBlur = 48;
    ctx.shadowOffsetY = 16;
    ctx.fillStyle = '#ffffff';
    _roundRect(ctx, 110, containerY, W - 220, containerH, 32);
    ctx.fill();
    ctx.shadowColor = 'transparent';
    
    // Colorful accent bar at top
    const accentBar = ctx.createLinearGradient(130, containerY + 30, W - 130, containerY + 30);
    accentBar.addColorStop(0, '#ff0080');
    accentBar.addColorStop(0.33, '#40e0d0');
    accentBar.addColorStop(0.66, '#7b68ee');
    accentBar.addColorStop(1, '#ff6347');
    ctx.fillStyle = accentBar;
    _roundRect(ctx, 156, containerY + 44, W - 312, 6, 3);
    ctx.fill();
    
    // Theme label
    ctx.fillStyle = '#1a1a2e';
    ctx.font = '700 17px -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif';
    ctx.textAlign = 'center';
    ctx.fillText(String(normalized.theme || 'REFLECTION').toUpperCase(), W / 2, containerY + 110);
    
    // Main quote - dark text on white
    ctx.fillStyle = '#1a1a2e';
    const quoteMetrics = drawFittedCanvasText(ctx, {
      text: headline,
      x: W / 2,
      y: containerY + 260,
      maxWidth: headlineOptions.maxWidth,
      maxHeight: headlineOptions.maxHeight,
      maxLines: headlineOptions.maxLines,
      align: 'center',
      fontTemplate: headlineOptions.fontTemplate,
      maxSize: headlineOptions.maxSize,
      minSize: headlineOptions.minSize,
      lineHeightRatio: headlineOptions.lineHeightRatio
    });
    
    // Bottom accent
    ctx.fillStyle = accentBar;
    _roundRect(ctx, 156, containerY + containerH - 50, W - 312, 6, 3);
    ctx.fill();
    
    ctx.fillStyle = 'rgba(26,26,46,0.75)';
    ctx.font = '600 15px -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif';
    ctx.fillText('ASK MIRROR TALK', W / 2, containerY + containerH - 24);

    drawShareFooter(ctx, style, W, H - 206, 'center');
    if (ENABLE_TEST_EXPORTS) {
      window.__AMT_LAST_RENDER_DEBUG__ = { family: 'prismatic_quote', headline };
    }
  }

  function buildInsightShareCard(insight) {
    const normalized = normalizeInsightRecord(insight);
    const style = getInsightShareThemeStyle(normalized.theme);
    const variant = getInsightShareVariant(normalized);
    const family = getInsightShareFamily(normalized);
    const W = 1080;
    const H = 1350;
    const canvas = document.createElement('canvas');
    canvas.width = W;
    canvas.height = H;
    const ctx = canvas.getContext('2d');
    if (ENABLE_TEST_EXPORTS) {
      window.__AMT_LAST_RENDER_DEBUG__ = null;
      window.__AMT_LAST_FOOTER_DEBUG__ = null;
    }
    if (family === 'aura_poster') {
      buildAuraPosterShareCard(ctx, normalized, style, W, H, variant);
    } else if (family === 'bold_vibrant') {
      buildBoldVibrantShareCard(ctx, normalized, style, W, H, variant);
    } else if (family === 'poster') {
      buildPosterInsightShareCard(ctx, normalized, style, W, H, variant);
    } else if (family === 'gradient_immersive') {
      buildGradientImmersiveShareCard(ctx, normalized, style, W, H, variant);
    } else if (family === 'neon_contemplative') {
      buildNeonContemplativeShareCard(ctx, normalized, style, W, H, variant);
    } else if (family === 'prismatic_quote') {
      buildPrismaticQuoteShareCard(ctx, normalized, style, W, H, variant);
    } else if (family === 'spotlight') {
      buildSpotlightInsightShareCard(ctx, normalized, style, W, H, variant);
    } else if (family === 'minimal') {
      buildMinimalInsightShareCard(ctx, normalized, style, W, H, variant);
    } else if (family === 'atmospheric') {
      buildAtmosphericInsightShareCard(ctx, normalized, style, W, H, variant);
    } else if (family === 'editorial_serene') {
      buildEditorialSereneInsightShareCard(ctx, normalized, style, W, H, variant);
    } else {
      buildEditorialInsightShareCard(ctx, normalized, style, W, H, variant);
    }

    if (ENABLE_TEST_EXPORTS && !window.__AMT_LAST_RENDER_DEBUG__) {
      window.__AMT_LAST_RENDER_DEBUG__ = { family };
    }

    return canvas.toDataURL('image/png');
  }

  function wrapCanvasText(ctx, text, x, startY, maxWidth, lineHeight, maxLines, align) {
    const lines = splitCanvasLines(ctx, text, maxWidth);

    const finalLines = lines.slice(0, maxLines);
    if (lines.length > maxLines) {
      finalLines[maxLines - 1] = truncateCanvasTextToWidth(ctx, finalLines[maxLines - 1], maxWidth);
    }

    ctx.textAlign = align || 'left';
    finalLines.forEach((line, index) => {
      ctx.fillText(line, x, startY + (index * lineHeight));
    });
    return finalLines.length;
  }

  function countWrappedLines(ctx, text, maxWidth, maxLines) {
    const lines = splitCanvasLines(ctx, text, maxWidth);
    return Math.min(lines.length, maxLines);
  }

  function splitCanvasLines(ctx, text, maxWidth) {
    const words = String(text || '').split(/\s+/).filter(Boolean);
    const lines = [];
    let currentLine = '';

    words.forEach(word => {
      const testLine = currentLine ? `${currentLine} ${word}` : word;
      if (ctx.measureText(testLine).width > maxWidth && currentLine) {
        lines.push(currentLine);
        currentLine = word;
      } else {
        currentLine = testLine;
      }
    });
    if (currentLine) lines.push(currentLine);
    return lines;
  }

  function truncateCanvasTextToWidth(ctx, text, maxWidth) {
    const source = String(text || '').trim();
    if (!source) return '';
    const ellipsis = '…';
    if (ctx.measureText(source).width <= maxWidth) return source;

    let low = 0;
    let high = source.length;
    let best = '';
    while (low <= high) {
      const mid = Math.floor((low + high) / 2);
      const candidate = source.slice(0, mid).trim().replace(/[.,;:!?-]+$/g, '').trim() + ellipsis;
      if (ctx.measureText(candidate).width <= maxWidth) {
        best = candidate;
        low = mid + 1;
      } else {
        high = mid - 1;
      }
    }
    return best || ellipsis;
  }

  function fitCanvasText(ctx, text, maxWidth, maxLines, fontTemplate, maxSize, minSize) {
    for (let size = maxSize; size >= minSize; size -= 2) {
      ctx.font = fontTemplate.replace('__SIZE__', String(size));
      const lineCount = splitCanvasLines(ctx, text, maxWidth).length;
      if (lineCount <= maxLines) {
        return {
          size,
          lineCount,
          lineHeight: Math.round(size * 1.14)
        };
      }
    }
    return {
      size: minSize,
      lineCount: splitCanvasLines(ctx, text, maxWidth).length,
      lineHeight: Math.round(minSize * 1.14)
    };
  }

  function fitCanvasTextBox(ctx, text, maxWidth, maxHeight, maxLines, fontTemplate, maxSize, minSize, lineHeightRatio) {
    const ratio = lineHeightRatio || 1.14;
    for (let size = maxSize; size >= minSize; size -= 2) {
      ctx.font = fontTemplate.replace('__SIZE__', String(size));
      const lines = splitCanvasLines(ctx, text, maxWidth);
      const lineCount = Math.min(lines.length, maxLines);
      const lineHeight = Math.round(size * ratio);
      if (lineCount <= maxLines && (lineCount * lineHeight) <= maxHeight) {
        return { size, lineCount, lineHeight };
      }
    }
    return {
      size: minSize,
      lineCount: Math.min(splitCanvasLines(ctx, text, maxWidth).length, maxLines),
      lineHeight: Math.round(minSize * ratio)
    };
  }

  function canRenderCanvasTextFully(ctx, text, maxWidth, maxHeight, maxLines, fontTemplate, maxSize, minSize, lineHeightRatio) {
    const fit = fitCanvasTextBox(ctx, text, maxWidth, maxHeight, maxLines, fontTemplate, maxSize, minSize, lineHeightRatio);
    ctx.font = fontTemplate.replace('__SIZE__', String(fit.size));
    const lines = splitCanvasLines(ctx, text, maxWidth);
    const lineCount = lines.length;
    return lineCount <= maxLines && (lineCount * fit.lineHeight) <= maxHeight;
  }

  function drawFittedCanvasText(ctx, options) {
    const fit = options.maxHeight
      ? fitCanvasTextBox(
          ctx,
          options.text,
          options.maxWidth,
          options.maxHeight,
          options.maxLines,
          options.fontTemplate,
          options.maxSize,
          options.minSize,
          options.lineHeightRatio
        )
      : fitCanvasText(
          ctx,
          options.text,
          options.maxWidth,
          options.maxLines,
          options.fontTemplate,
          options.maxSize,
          options.minSize
        );
    const lineHeight = fit.lineHeight || Math.round(fit.size * (options.lineHeightRatio || 1.14));
    ctx.font = options.fontTemplate.replace('__SIZE__', String(fit.size));
    const renderedLines = wrapCanvasText(
      ctx,
      options.text,
      options.x,
      options.y,
      options.maxWidth,
      lineHeight,
      options.maxLines,
      options.align
    );
    return {
      lineCount: renderedLines,
      lineHeight,
      height: renderedLines * lineHeight,
      size: fit.size
    };
  }

  function getFittedCanvasTextMetrics(ctx, options) {
    const fit = options.maxHeight
      ? fitCanvasTextBox(
          ctx,
          options.text,
          options.maxWidth,
          options.maxHeight,
          options.maxLines,
          options.fontTemplate,
          options.maxSize,
          options.minSize,
          options.lineHeightRatio
        )
      : fitCanvasText(
          ctx,
          options.text,
          options.maxWidth,
          options.maxLines,
          options.fontTemplate,
          options.maxSize,
          options.minSize
        );
    const lineHeight = fit.lineHeight || Math.round(fit.size * (options.lineHeightRatio || 1.14));
    ctx.font = options.fontTemplate.replace('__SIZE__', String(fit.size));
    const lines = splitCanvasLines(ctx, options.text, options.maxWidth).slice(0, options.maxLines);
    return {
      lines,
      lineCount: lines.length,
      lineHeight,
      height: lines.length * lineHeight,
      size: fit.size
    };
  }

  function showShareHoldbackToast(message) {
    const toast = document.getElementById('amt-milestone-toast');
    if (!toast) return;
    toast.innerHTML = `
      <span class="amt-toast-emoji">✦</span>
      <div>
        <strong>Reflection card held back</strong>
        <span>${escapeHtml(message || 'This answer needs one more pass before it becomes a shareable card.')}</span>
      </div>
    `;
    toast.style.display = '';
    toast.classList.add('amt-toast-in');
    setTimeout(() => {
      toast.classList.remove('amt-toast-in');
      toast.classList.add('amt-toast-out');
      setTimeout(() => {
        toast.style.display = 'none';
        toast.classList.remove('amt-toast-out');
      }, 500);
    }, 4200);
  }

  function shareInsightArtifact(insight) {
    const normalized = {
      ...normalizeInsightRecord(insight),
      shareSource: (insight && insight.shareSource) || 'saved_insight'
    };
    const headline = extractShareHeadline(normalized);
    if (isFallbackAnswerMeta(insight && insight.answerMeta)) {
      showShareHoldbackToast('The answer is currently source moments only. Refine the question first, then share the complete reflection.');
      return;
    }
    if (!isShareableReflectionText(headline) || !isShareableReflectionText(normalized.excerpt)) {
      showShareHoldbackToast('The selected text is not complete or reflective enough for a polished card yet.');
      return;
    }
    const dataUrl = buildInsightShareCard(normalized);
    const caption = `A reflection I saved on Ask Mirror Talk: "${normalized.excerpt}"\n\nhttps://mirrortalkpodcast.com/ask-mirror-talk`;
    showShareModal(dataUrl, caption, {
      title: 'Share this reflection',
      hint: 'This card is polished and ready. Send it, save it, or pass the pause to someone who may need it.',
      filename: 'mirror-talk-reflection.png',
      contextLabel: normalized.theme || 'Saved reflection',
      invitePrompt: 'Lead with the reflection itself. The link is there only if they want to enter the experience too.',
      previewText: headline,
      nativeShareLabel: 'Open share sheet',
      copyTextLabel: 'Copy share caption',
      copyLinkLabel: 'Copy reflection link'
    });
  }

  // ========================================
  // FEATURE 1: Saved Answers — "My Insights"
  // ========================================

  const INSIGHTS_KEY = 'amt_saved_insights';

  function loadInsights() {
    return _loadMirroredJson(INSIGHTS_KEY, INSIGHTS_COOKIE_KEY, []);
  }

  function saveInsights(arr) {
    const insights = Array.isArray(arr) ? arr.slice(0, 30) : [];
    const backup = insights.slice(0, 5).map(compactInsightRecordForBackup);
    try { localStorage.setItem(INSIGHTS_KEY, JSON.stringify(insights)); } catch (e) {}
    try { _cookieSet(INSIGHTS_COOKIE_KEY, JSON.stringify(backup), 365); } catch (e) {}
  }

  function addSaveInsightButton(question, answerText, answerMeta) {
    const existing = document.getElementById('amt-save-insight-section');
    if (existing) existing.remove();
    if (!question || !answerText) return;

    const section = document.createElement('div');
    section.id = 'amt-save-insight-section';
    section.className = 'amt-save-insight-section';

    if (isFallbackAnswerMeta(answerMeta)) {
      section.innerHTML = `<button type="button" class="amt-save-insight-btn" disabled title="Refine this answer before saving it as an insight">
        🔖 Refine before saving insight
      </button>`;
      getAnswerUtilitiesRoot().appendChild(section);
      return;
    }

    const normalizedInsight = normalizeInsightRecord({
      question,
      answer: answerText.substring(0, 1500),
      theme: inferTheme(question, answerText),
      savedAt: Date.now()
    });
    const insights = loadInsights().map(normalizeInsightRecord);
    const alreadySaved = insights.some(i => i.question === question);

    section.innerHTML = `<button type="button" class="amt-save-insight-btn" title="${alreadySaved ? 'Already saved' : 'Save this insight'}">
      ${alreadySaved ? '🔖 Saved to your collection' : '🔖 Save to your collection'}
    </button>`;
    getAnswerUtilitiesRoot().appendChild(section);

    const btn = section.querySelector('.amt-save-insight-btn');
    if (alreadySaved) {
      btn.disabled = true;
      return;
    }

    btn.addEventListener('click', () => {
      const allInsights = loadInsights();
      allInsights.unshift(normalizedInsight);
      saveInsights(allInsights);
      btn.textContent = '🔖 Saved to your collection';
      btn.disabled = true;
      trackRewardEvent('insight_save');
      // Update the insights button badge
      updateInsightsBadge();
    });
  }

  function updateInsightsBadge() {
    const btn = document.getElementById('amt-insights-btn');
    if (!btn) return;
    btn.style.display = '';
  }

  function renderInsightsPanel() {
    const panel = document.getElementById('amt-insights-panel');
    if (!panel) return;
    const insights = loadInsights().map(normalizeInsightRecord);

    if (insights.length === 0) {
      // Hide the panel — empty state is not shown inline, it only appears when
      // the user explicitly opens the panel via the 🔖 button
      panel.style.display = 'none';
      panel.innerHTML = '';
      return;
    }

    panel.innerHTML = `
      <div class="amt-insights-header">
        <span class="amt-insights-title">🔖 My Insights <span class="amt-insights-count">(${insights.length})</span></span>
        <button type="button" class="amt-insights-close-btn" aria-label="Close insights">✕</button>
      </div>
      <div class="amt-insights-list">
        ${insights.map((ins, idx) => `
          <div class="amt-insight-item" data-idx="${idx}">
            <div class="amt-insight-topline">
              <span class="amt-insight-theme">${escapeHtml(ins.theme)}</span>
              <span class="amt-insight-date">${formatRelativeTime(ins.savedAt)}</span>
            </div>
            <p class="amt-insight-question">${escapeHtml(ins.question)}</p>
            <p class="amt-insight-answer">“${escapeHtml(ins.excerpt)}”</p>
            <div class="amt-insight-meta">
              <button type="button" class="amt-insight-ask-btn" data-q="${ins.question.replace(/"/g,'&quot;')}">Revisit</button>
              <button type="button" class="amt-insight-share-btn" data-idx="${idx}">Share card</button>
              <button type="button" class="amt-insight-delete-btn" data-idx="${idx}" aria-label="Delete">Remove</button>
            </div>
          </div>
        `).join('')}
      </div>
    `;
    panel.style.display = '';

    panel.querySelector('.amt-insights-close-btn').addEventListener('click', () => {
      panel.style.display = 'none';
    });

    panel.querySelectorAll('.amt-insight-ask-btn').forEach(btn => {
      btn.addEventListener('click', () => {
        panel.style.display = 'none';
        setQuestionOrigin('saved_insight_revisit');
        submitQuestionFromPrompt(btn.dataset.q);
      });
    });

    panel.querySelectorAll('.amt-insight-share-btn').forEach(btn => {
      btn.addEventListener('click', () => {
        const idx = parseInt(btn.dataset.idx, 10);
        shareInsightArtifact(insights[idx]);
      });
    });

    panel.querySelectorAll('.amt-insight-delete-btn').forEach(btn => {
      btn.addEventListener('click', () => {
        const idx = parseInt(btn.dataset.idx, 10);
        const all = loadInsights();
        all.splice(idx, 1);
        saveInsights(all);
        updateInsightsBadge();
        renderInsightsPanel();
      });
    });
  }

  function openInsightsPanel(options) {
    const opts = options || {};
    const panel = document.getElementById('amt-insights-panel');
    if (!panel) return false;
    const insights = loadInsights();

    if (insights.length === 0) {
      panel.innerHTML = '<div class="amt-insights-empty"><p>No saved insights yet.</p><p class="amt-insights-empty-hint">After an answer, tap 🔖 Save insight to keep it here.</p></div>';
      panel.style.display = '';
    } else {
      renderInsightsPanel();
    }

    panel.classList.add('amt-insights-panel-pulse');
    setTimeout(() => panel.classList.remove('amt-insights-panel-pulse'), 900);
    if (opts.scroll !== false) {
      panel.scrollIntoView({ behavior: 'smooth', block: 'center' });
    }
    return true;
  }

  // Wire insights button
  (function initInsightsBtn() {
    const btn = document.getElementById('amt-insights-btn');
    const panel = document.getElementById('amt-insights-panel');
    if (!btn || !panel) return;
    updateInsightsBadge();
    btn.addEventListener('click', () => {
      if (panel.style.display !== 'none') {
        panel.style.display = 'none';
        return;
      }
      runWorkflowAction('save_share', { persist: true, scroll: false });
      openInsightsPanel({ scroll: true });
    });
  })();

  // Hook into done event to show save button — patch post-answer flow
  const _origAddShareButton = addShareButton;

  // ========================================
  // FEATURE 2: Streak Protection In-App Alert
  // ========================================

  (function checkStreakProtection() {
    try {
      const stats = loadStats();
      if (stats.currentStreak < 1) return; // no streak to protect
      if (sessionStorage.getItem('amt_streak_protect_dismissed') === todayStr()) return;
      const today = todayStr();
      // Already asked today — no need to warn
      if (stats.lastActiveDate === today) return;

      const hour = new Date().getHours();
      // Only show the banner after 18:00 (6 PM) when the streak is at risk
      if (hour < 18) return;

      const banner = document.getElementById('amt-streak-protect-banner');
      if (!banner) return;

      banner.innerHTML = `
        <div class="amt-streak-protect-inner">
          <span class="amt-streak-protect-icon">🔥</span>
          <span class="amt-streak-protect-text">Your <strong>${stats.currentStreak}-day streak</strong> is still alive. Ask one question before midnight to protect it and keep your rhythm going.</span>
          <button type="button" class="amt-streak-protect-cta">Ask now</button>
          <button type="button" class="amt-streak-protect-dismiss" aria-label="Dismiss">✕</button>
        </div>
      `;
      banner.style.display = '';

      banner.querySelector('.amt-streak-protect-cta').addEventListener('click', () => {
        banner.style.display = 'none';
        submitRhythmQuestion(
          getRhythmReflectionQuestion('', { preferQotd: true }),
          'streak_protection',
          { feature: 'streak_protection_banner' }
        );
      });

      banner.querySelector('.amt-streak-protect-dismiss').addEventListener('click', () => {
        banner.style.display = 'none';
        try { sessionStorage.setItem('amt_streak_protect_dismissed', todayStr()); } catch (e) {}
      });
    } catch (e) {}
  })();

  // ========================================
  // FEATURE 3: Reflect Prompt After Answer
  // ========================================

  const REFLECT_PROMPTS = [
    'What part of this resonated most with you today?',
    'How might you apply this in your life this week?',
    'What emotion came up as you read this?',
    'Which line felt most true for where you are right now?',
    'What would change if you truly believed this?',
    'Is there someone in your life who needs to hear this too?',
    'What\u2019s one small step you could take today based on this?',
  ];

  function showReflectPrompt() {
    const section = document.getElementById('amt-reflect-section');
    if (!section) return;

    if (continuationStrip && continuationStrip.parentNode === responseContainer) {
      responseContainer.insertBefore(section, continuationStrip);
    } else if (answerUtilities && answerUtilities.parentNode === responseContainer) {
      responseContainer.insertBefore(section, answerUtilities);
    }

    const prompt = REFLECT_PROMPTS[Math.floor(Math.random() * REFLECT_PROMPTS.length)];
    const lastSession = loadLastSession() || {};
    const sourceTheme = String(lastSession.theme || inferTheme(lastSession.question || '', lastSession.answer || '') || '').trim();
    const sourceQuestion = String(lastSession.question || '').trim();
    const sourceExcerpt = String(lastSession.excerpt || extractInsightExcerpt(lastSession.answer || '', sourceTheme) || '').trim();

    section.innerHTML = `
      <div class="amt-reflect-inner">
        <p class="amt-reflect-label">✍️ Pause and jot what landed.</p>
        <p class="amt-reflect-question">${escapeHtml(prompt)}</p>
        <button type="button" class="amt-reflect-toggle">Jot a private note ↓</button>
        <div class="amt-reflect-note-wrap" style="display:none;">
          <textarea class="amt-reflect-textarea" rows="3" maxlength="500" placeholder="Write for yourself — this stays private on your device…" aria-label="Private reflection note"></textarea>
          <div class="amt-reflect-actions">
            <button type="button" class="amt-reflect-save-btn">Save note</button>
            <span class="amt-reflect-saved-msg" style="display:none;">✓ Saved</span>
          </div>
        </div>
      </div>
    `;
    section.style.display = '';

    section.querySelector('.amt-reflect-toggle').addEventListener('click', function() {
      const wrap = section.querySelector('.amt-reflect-note-wrap');
      const isOpen = wrap.style.display !== 'none';
      wrap.style.display = isOpen ? 'none' : '';
      this.textContent = isOpen ? 'Jot a private note ↓' : 'Hide note ↑';
      if (!isOpen) {
        emitProductEvent('reflection_note_opened', { prompt });
        section.querySelector('.amt-reflect-textarea').focus();
      }
    });

    section.querySelector('.amt-reflect-save-btn').addEventListener('click', () => {
      const textarea = section.querySelector('.amt-reflect-textarea');
      const note = textarea.value.trim();
      if (!note) return;
      emitProductEvent('reflection_note_saved', { prompt, length: note.length });
      try {
        const existing = loadReflectionNotes();
        existing.unshift({
          note,
          prompt,
          theme: sourceTheme || '',
          sourceQuestion,
          sourceExcerpt,
          savedAt: Date.now()
        });
        saveReflectionNotes(existing);
      } catch (e) {}
      // Clear the textarea and show brief confirmation so the user can add another note
      textarea.value = '';
      textarea.focus();
      const msg = section.querySelector('.amt-reflect-saved-msg');
      msg.style.display = '';
      setTimeout(() => { msg.style.display = 'none'; }, 2000);
    });
  }

  function openReflectNoteComposer() {
    let section = document.getElementById('amt-reflect-section');
    const lastSession = loadLastSession() || {};
    const hasReflectionContext = !!(lastSession.question || lastSession.answer || lastSession.excerpt);

    if (section && (!section.innerHTML.trim() || section.style.display === 'none') && hasReflectionContext) {
      showReflectPrompt();
      section = document.getElementById('amt-reflect-section');
    }

    if (section && section.innerHTML.trim()) {
      runWorkflowAction('save_share', { persist: true, scroll: false });
      section.style.display = '';
      const toggle = section.querySelector('.amt-reflect-toggle');
      const wrap = section.querySelector('.amt-reflect-note-wrap');
      if (toggle && wrap && wrap.style.display === 'none') {
        toggle.click();
      }
      scrollToElementSafely(section, 'center');
      return;
    }

    runWorkflowAction('ask', { persist: true, scroll: true });
    if (input) {
      input.focus();
    }
  }

  (function initQuickNoteButton() {
    const btn = document.getElementById('amt-note-btn');
    if (!btn) return;
    btn.addEventListener('click', openReflectNoteComposer);
  })();

  // ========================================
  // FEATURE 4: "Come Back Tomorrow" Teaser
  // ========================================

  function showComeBackTeaser() {
    // Pick a tomorrow theme (rotate by tomorrow's date for consistency)
    const tomorrow = new Date();
    tomorrow.setDate(tomorrow.getDate() + 1);
    const dayIdx = tomorrow.toISOString().slice(0, 10).split('').reduce((a, c) => a + c.charCodeAt(0), 0);
    const stats = loadStats();
    const exploredThemes = stats.themesExplored || new Set();
    const unexplored = AMT_THEMES.filter(t => !exploredThemes.has(t));
    const pool = unexplored.length > 0 ? unexplored : AMT_THEMES;
    const teaserTheme = pool[dayIdx % pool.length];

    // Show a brief teaser toast (reuse the milestone toast style)
    const toast = document.getElementById('amt-milestone-toast');
    if (!toast) return;
    toast.innerHTML = `
      <span class="amt-toast-emoji">🌅</span>
      <div>
        <strong>Come back tomorrow</strong>
        <span>Tomorrow's theme: <em>${escapeHtml(teaserTheme)}</em></span>
      </div>
    `;
    toast.style.display = '';
    toast.classList.add('amt-toast-in');

    setTimeout(() => {
      toast.classList.remove('amt-toast-in');
      toast.classList.add('amt-toast-out');
      setTimeout(() => {
        toast.style.display = 'none';
        toast.classList.remove('amt-toast-out');
      }, 500);
    }, 4500);
  }

  // ========================================
  // FEATURE 5: Clear Share Actions
  // ========================================
  // Keep the reflection share and invite flows separate so users don't need
  // to understand a mode switch before they act.

  function addShareButtonV2(question, answerText, themeHint, answerMeta) {
    const existing = document.getElementById('amt-share-section');
    if (existing) existing.remove();

    const shareSection = document.createElement('div');
    shareSection.id = 'amt-share-section';
    shareSection.className = 'amt-share-section amt-share-section-v2';
    const fallbackAnswer = isFallbackAnswerMeta(answerMeta);

    console.log('[addShareButtonV2] window._amtLastShareableHeadline:', window._amtLastShareableHeadline);
    
    const reflectionInsight = normalizeInsightRecord({
      question,
      answer: answerText,
      theme: themeHint || inferTheme(question, answerText),
      savedAt: Date.now(),
      shareable_headline: window._amtLastShareableHeadline || '',
      shareSource: 'current_answer'
    });
    reflectionInsight.answerMeta = answerMeta || {};
    const pageUrl = buildTrackedPageUrl({
      source: 'invite_friend',
      medium: 'share',
      campaign: 'growth_sprint',
      ref: 'invite_button',
      intent: 'shared_reflection',
      question: question,
      content: 'direct_prompt',
      inviteReflection: true,
      theme: reflectionInsight.theme || ''
    });
    const referralShare = `I just used Ask Mirror Talk for this question: "${question.substring(0, 80)}". You can start with the same reflection path or ask your own question here:\n${pageUrl}`;
    const reflectionLine = extractShareHeadline(reflectionInsight);
    const canShareReflection = !fallbackAnswer &&
      isShareableReflectionText(reflectionLine) &&
      isShareableReflectionText(reflectionInsight.excerpt);

    shareSection.innerHTML = `
      <div class="amt-share-intro">
        <span class="amt-share-kicker">${fallbackAnswer ? 'Refine before sharing' : 'Keep or pass on what mattered'}</span>
        <p class="amt-share-caption">${fallbackAnswer ? 'The app found source moments, but the full reflective answer did not complete. Refine this before creating a public card.' : 'Share a polished reflection card, or send someone a direct path into the Mirror Talk experience.'}</p>
        ${canShareReflection ? `<p class="amt-share-caption amt-share-line">${escapeHtml(reflectionLine)}</p>` : ''}
      </div>
      <div class="amt-share-actions-row">
        <button type="button" class="amt-share-btn amt-share-btn-primary" data-action="reflection"${canShareReflection ? '' : ' disabled aria-disabled="true"'}>${canShareReflection ? 'Share this reflection' : 'Card paused until answer is complete'}</button>
        <button type="button" class="amt-share-btn amt-share-btn-secondary" data-action="invite">Invite a friend</button>
      </div>
    `;

    getAnswerUtilitiesRoot().appendChild(shareSection);
    emitProductEvent('share_panel_shown', { mode: 'reflection_or_invite' });
    updateWorkflowBarState();

    shareSection.querySelectorAll('.amt-share-btn').forEach(btn => {
      btn.addEventListener('click', async function() {
        const action = this.dataset.action;
        if (action === 'reflection') {
          if (!canShareReflection) {
            showShareHoldbackToast('This answer needs a complete reflective line before it becomes a shareable card.');
            return;
          }
          emitProductEvent('share_cta_used', { action: 'reflection_card' });
          shareInsightArtifact(reflectionInsight);
          return;
        }

        const textToShare = referralShare;
        const titleToShare = 'Ask Mirror Talk';

        try {
          if (navigator.share) {
            await navigator.share({ title: titleToShare, text: textToShare });
            trackRewardEvent('share');
            emitProductEvent('share_cta_used', { action: 'invite_friend', method: 'native_share' });
            return;
          }
        } catch (e) {
          if (e.name !== 'AbortError') console.warn('Share failed:', e);
        }

        try {
          await navigator.clipboard.writeText(textToShare);
          trackRewardEvent('share');
          emitProductEvent('share_cta_used', { action: 'invite_friend', method: 'copy_link' });
          const originalText = this.textContent;
          this.textContent = 'Link copied';
          setTimeout(() => { this.textContent = originalText; }, 2500);
        } catch (e) {}
      });
    });

    // Also add the save insight button here
    addSaveInsightButton(question, answerText, answerMeta);
  }

  // ========================================
  // FEATURE 6: "About This App" Explainer Modal
  // ========================================

  (function initAboutModal() {
    const btn = document.getElementById('amt-about-btn');
    const modal = document.getElementById('amt-about-modal');
    if (!btn || !modal) return;

    btn.addEventListener('click', () => {
      modal.innerHTML = `
        <div class="amt-about-backdrop"></div>
        <div class="amt-about-panel">
          <button class="amt-about-close" aria-label="Close">✕</button>
          <div class="amt-about-logo" aria-hidden="true">🎙️</div>
          <h2 class="amt-about-title">Ask Mirror Talk</h2>
          <p class="amt-about-tagline">Your personal guide to the Mirror Talk podcast library</p>
          <ul class="amt-about-bullets">
            <li><span class="amt-about-bullet-icon">🔍</span><span>Ask any question and get AI-powered answers <strong>drawn directly from podcast episodes</strong> — with timestamps you can listen to.</span></li>
            <li><span class="amt-about-bullet-icon">🔥</span><span>Build a <strong>daily exploration habit</strong> with streaks, badges and a personalised Question of the Day.</span></li>
            <li><span class="amt-about-bullet-icon">📲</span><span><strong>Add to your home screen</strong> for instant access and daily wisdom delivered straight to your phone.</span></li>
          </ul>
          <div class="amt-about-stats-preview" id="amt-about-stats-preview"></div>
          <button type="button" class="amt-about-cta">Start asking →</button>
        </div>
      `;
      modal.style.display = '';
      requestAnimationFrame(() => modal.classList.add('amt-about-visible'));

      // Personalise with user stats if available
      try {
        const s = loadStats();
        if (s.totalQuestions > 0) {
          const preview = modal.querySelector('#amt-about-stats-preview');
          if (preview) preview.innerHTML = `<p class="amt-about-your-stats">Your journey so far: <strong>${s.totalQuestions} questions</strong> · <strong>${s.currentStreak}-day streak</strong> · <strong>${s.earnedBadges.size} badges</strong></p>`;
        }
      } catch (e) {}

      const close = () => {
        modal.classList.remove('amt-about-visible');
        setTimeout(() => { modal.style.display = 'none'; modal.innerHTML = ''; }, 300);
      };
      modal.querySelector('.amt-about-close').addEventListener('click', close);
      modal.querySelector('.amt-about-backdrop').addEventListener('click', close);
      modal.querySelector('.amt-about-cta').addEventListener('click', () => {
        close();
        input.focus();
        form.scrollIntoView({ behavior: 'smooth', block: 'center' });
      });
      document.addEventListener('keydown', function escHandler(e) {
        if (e.key === 'Escape') { close(); document.removeEventListener('keydown', escHandler); }
      }, { once: true });
    });
  })();

  // ========================================
  // FEATURE: Settings Modal (Audio & Sound)
  // ========================================

  // ========================================
  // FEATURE 7: Auto-Open Explore Panel on First Visit
  // ========================================

  // autoOpenExploreOnFirstVisit — disabled; expander is always collapsed by default.

  // ========================================
  // FEATURE: My Reflection Notes Journal
  // ========================================

  (function initJournalModal() {
    const btn   = document.getElementById('amt-journal-btn');
    const modal = document.getElementById('amt-journal-modal');
    if (!btn || !modal) return;

    function formatDate(ts) {
      try {
        return new Date(ts).toLocaleDateString(undefined, { day: 'numeric', month: 'short', year: 'numeric' });
      } catch (e) { return ''; }
    }

    function openJournal() {
      let notes = loadReflectionNotes();

      const pageUrl = window.location.href;

      const noteItems = notes.length === 0
        ? `<p class="amt-journal-empty">You haven't saved any reflection notes yet.<br>After reading an answer, tap <strong>✍️</strong> beside the journal to jot what landed.</p>`
        : notes.map((entry, i) => `
          <div class="amt-journal-entry" data-index="${i}">
            <div class="amt-insight-topline">
              <span class="amt-insight-theme">${escapeHtml(entry.theme || 'Reflection')}</span>
              <span class="amt-journal-date">${formatDate(entry.savedAt)}</span>
            </div>
            <p class="amt-journal-prompt">${escapeHtml(entry.prompt || '')}</p>
            <p class="amt-journal-note" data-index="${i}">${escapeHtml(entry.note || '')}</p>
            ${entry.sourceExcerpt ? `<p class="amt-insight-answer">“${escapeHtml(entry.sourceExcerpt)}”</p>` : ''}
            <div class="amt-journal-entry-footer">
              <div class="amt-journal-entry-actions">
                ${entry.sourceQuestion ? `<button type="button" class="amt-journal-revisit-btn" data-question="${escapeHtml(entry.sourceQuestion)}" title="Return to this reflection">↺ Revisit</button>` : ''}
                <button type="button" class="amt-journal-edit-btn" data-index="${i}" title="Edit this note">✏️ Edit</button>
                <button type="button" class="amt-journal-share-btn" data-index="${i}" title="Turn this note into a reflection card">📤 Share card</button>
                <button type="button" class="amt-journal-delete-btn" data-index="${i}" title="Delete this note">🗑</button>
              </div>
            </div>
          </div>
        `).join('');

      modal.innerHTML = `
        <div class="amt-journal-backdrop"></div>
        <div class="amt-journal-panel">
          <button class="amt-journal-close" aria-label="Close">✕</button>
          <div class="amt-journal-header-copy">
            <h2 class="amt-journal-title">📓 My Reflection Notes</h2>
            <p class="amt-journal-subtitle">${notes.length} note${notes.length !== 1 ? 's' : ''} — your reflections, saved insights, and shareable moments in one private place</p>
          </div>
          <div class="amt-journal-list">${noteItems}</div>
        </div>
      `;
      modal.style.display = '';
      requestAnimationFrame(() => modal.classList.add('amt-journal-visible'));

      const close = () => {
        modal.classList.remove('amt-journal-visible');
        setTimeout(() => { modal.style.display = 'none'; modal.innerHTML = ''; }, 300);
      };

      modal.querySelector('.amt-journal-backdrop').addEventListener('click', close);
      modal.querySelector('.amt-journal-close').addEventListener('click', close);
      document.addEventListener('keydown', function escHandler(e) {
        if (e.key === 'Escape') { close(); document.removeEventListener('keydown', escHandler); }
      }, { once: true });

      modal.querySelectorAll('.amt-journal-revisit-btn').forEach(revisitBtn => {
        revisitBtn.addEventListener('click', () => {
          const questionText = revisitBtn.dataset.question || '';
          if (!questionText) return;
          close();
          setQuestionOrigin('journal_revisit');
          submitQuestionFromPrompt(questionText);
        });
      });

      // Edit buttons — inline editing within the entry card
      modal.querySelectorAll('.amt-journal-edit-btn').forEach(editBtn => {
        editBtn.addEventListener('click', () => {
          const idx = parseInt(editBtn.dataset.index, 10);
          let notes = loadReflectionNotes();
          const entry = notes[idx];
          if (!entry) return;

          const noteEl = modal.querySelector(`.amt-journal-note[data-index="${idx}"]`);
          const footer = editBtn.closest('.amt-journal-entry-footer');
          if (!noteEl || !footer) return;

          // Replace static text with editable textarea
          noteEl.style.display = 'none';
          const editWrap = document.createElement('div');
          editWrap.className = 'amt-journal-edit-wrap';
          editWrap.innerHTML = `
            <textarea class="amt-journal-edit-textarea" maxlength="500" rows="4">${escapeHtml(entry.note || '')}</textarea>
            <div class="amt-journal-edit-actions">
              <button type="button" class="amt-journal-edit-save-btn">Save</button>
              <button type="button" class="amt-journal-edit-cancel-btn">Cancel</button>
            </div>
          `;
          noteEl.parentNode.insertBefore(editWrap, noteEl.nextSibling);
          footer.style.display = 'none';

          const textarea = editWrap.querySelector('.amt-journal-edit-textarea');
          // position cursor at end
          textarea.focus();
          textarea.setSelectionRange(textarea.value.length, textarea.value.length);

          editWrap.querySelector('.amt-journal-edit-save-btn').addEventListener('click', () => {
            const newText = textarea.value.trim();
            if (!newText) return;
            let notes = loadReflectionNotes();
            notes[idx] = { ...notes[idx], note: newText };
            saveReflectionNotes(notes);
            close();
            setTimeout(() => openJournal(), 310);
          });

          editWrap.querySelector('.amt-journal-edit-cancel-btn').addEventListener('click', () => {
            editWrap.remove();
            noteEl.style.display = '';
            footer.style.display = '';
          });
        });
      });

      // Share buttons
      modal.querySelectorAll('.amt-journal-share-btn').forEach(shareBtn => {
        shareBtn.addEventListener('click', async () => {
          const idx = parseInt(shareBtn.dataset.index, 10);
          let notes = loadReflectionNotes();
          const entry = notes[idx];
          if (!entry) return;
          shareInsightArtifact({
            ...buildJournalReflectionInsight(entry),
            shareSource: 'journal_note'
          });
        });
      });

      // Delete buttons
      modal.querySelectorAll('.amt-journal-delete-btn').forEach(delBtn => {
        delBtn.addEventListener('click', () => {
          const idx = parseInt(delBtn.dataset.index, 10);
          let notes = loadReflectionNotes();
          notes.splice(idx, 1);
          saveReflectionNotes(notes);
          // Re-render
          close();
          setTimeout(() => openJournal(), 310);
        });
      });
    }

    btn.addEventListener('click', openJournal);
  })();
  // ========================================

  const MOOD_REACTIONS = [
    { emoji: '😮', label: 'Surprising' },
    { emoji: '💡', label: 'Insightful' },
    { emoji: '😢', label: 'Moving' },
    { emoji: '🙏', label: 'Grateful' },
  ];

  function showMoodReactions() {
    const container = document.getElementById('amt-mood-reactions');
    if (!container) return;

    container.innerHTML = `
      <p class="amt-mood-label">How did this land?</p>
      <div class="amt-mood-buttons">
        ${MOOD_REACTIONS.map((r, i) => `
          <button type="button" class="amt-mood-btn" data-emoji="${r.emoji}" data-label="${r.label}" style="animation-delay:${i * 0.08}s" title="${r.label}">
            <span class="amt-mood-emoji">${r.emoji}</span>
            <span class="amt-mood-reaction-label">${r.label}</span>
          </button>
        `).join('')}
      </div>
    `;
    container.style.display = '';

    container.querySelectorAll('.amt-mood-btn').forEach(btn => {
      btn.addEventListener('click', function() {
        container.querySelectorAll('.amt-mood-btn').forEach(b => b.classList.remove('amt-mood-selected'));
        this.classList.add('amt-mood-selected');
        // Track in stats (lightweight — just store last reaction per session)
        try { sessionStorage.setItem('amt_last_reaction', this.dataset.label); } catch (e) {}
        // Brief thank-you
        setTimeout(() => {
          const label = container.querySelector('.amt-mood-label');
          if (label) {
            label.textContent = 'Thanks for sharing how you feel 🙏';
            label.style.fontStyle = 'italic';
          }
        }, 400);
      });
    });
  }

  // ========================================
  // FEATURE 9: Copy Answer Button
  // ========================================

  function initCopyAnswerButton(answerText) {
    const btn = document.getElementById('amt-copy-answer-btn');
    if (!btn) return;
    btn.style.display = '';
    // Detach any previous listener
    const freshBtn = btn.cloneNode(true);
    btn.parentNode.replaceChild(freshBtn, btn);
    freshBtn.style.display = '';

    freshBtn.addEventListener('click', async () => {
      try {
        await navigator.clipboard.writeText(answerText);
        freshBtn.textContent = '✓ Copied';
        freshBtn.classList.add('amt-copy-copied');
        setTimeout(() => {
          freshBtn.textContent = '⎘ Copy';
          freshBtn.classList.remove('amt-copy-copied');
        }, 2000);
      } catch (e) {
        freshBtn.textContent = '⚠️ Failed';
        setTimeout(() => { freshBtn.textContent = '⎘ Copy'; }, 2000);
      }
    });
  }

  // ========================================
  // FEATURE 10: Text Size Toggle
  // ========================================

  (function initTextSizeToggle() {
    const btn = document.getElementById('amt-text-size-btn');
    if (!btn) return;
    const sizes = ['amt-text-small', 'amt-text-default', 'amt-text-large'];
    const labels = ['Aa–', 'Aa', 'Aa+'];
    let current = 1; // default
    try {
      const saved = parseInt(localStorage.getItem('amt_text_size') || '1', 10);
      if (saved >= 0 && saved <= 2) current = saved;
    } catch (e) {}

    const sizeNames = ['Small', 'Default', 'Large'];

    function applySize(idx, flash) {
      const widget = document.querySelector('.ask-mirror-talk');
      if (!widget) return;
      sizes.forEach(cls => widget.classList.remove(cls));
      if (idx !== 1) widget.classList.add(sizes[idx]); // no class needed for default
      btn.textContent = labels[idx];
      btn.title = 'Text size: ' + sizeNames[idx] + ' \u2014 click to change';
      try { localStorage.setItem('amt_text_size', String(idx)); } catch (e) {}
      if (flash) {
        btn.classList.add('amt-size-changed');
        setTimeout(() => btn.classList.remove('amt-size-changed'), 350);
      }
    }

    applySize(current, false);

    btn.addEventListener('click', () => {
      current = (current + 1) % sizes.length;
      applySize(current, true);
    });
  })();

  // ========================================
  // FEATURE 11: Animated Topic Icon Parade
  // ========================================

  (function initIconParade() {
    if (!exploreIcons) return;

    let iconList = [];
    let paradeIdx = 0;
    let paradeTimer = null;

    // Called once topics load and populate exploreIcons
    const observer = new MutationObserver(() => {
      if (!exploreIcons.textContent.trim()) return;
      // Extract icons from the text content
      iconList = [...exploreIcons.textContent].filter(c => c.trim() && c !== ' ');
      if (iconList.length < 2) return;
      observer.disconnect();
      startParade();
    });
    observer.observe(exploreIcons, { childList: true, characterData: true, subtree: true });

    function startParade() {
      if (paradeTimer) return;
      paradeTimer = setInterval(() => {
        // Only animate when the panel is closed (chevron not expanded)
        if (exploreToggle && exploreToggle.getAttribute('aria-expanded') === 'true') return;
        paradeIdx = (paradeIdx + 1) % iconList.length;
        exploreIcons.classList.add('amt-icons-fade-out');
        setTimeout(() => {
          // Rotate the array display: show 5 icons starting from paradeIdx
          const visible = [];
          for (let i = 0; i < Math.min(5, iconList.length); i++) {
            visible.push(iconList[(paradeIdx + i) % iconList.length]);
          }
          exploreIcons.textContent = visible.join(' ');
          exploreIcons.classList.remove('amt-icons-fade-out');
          exploreIcons.classList.add('amt-icons-fade-in');
          setTimeout(() => exploreIcons.classList.remove('amt-icons-fade-in'), 400);
        }, 300);
      }, 2000);
    }
  })();

  // ========================================
  // FEATURE 12: Response Reading Progress Bar
  // ========================================

  (function initResponseProgressBar() {
    const progressBar = document.getElementById('amt-response-progress-bar');
    if (!progressBar) return;

    function updateProgress() {
      if (!responseContainer || responseContainer.style.display === 'none') return;
      const rect = responseContainer.getBoundingClientRect();
      const windowH = window.innerHeight;
      const totalH = responseContainer.offsetHeight;
      if (totalH <= windowH) {
        progressBar.style.width = '100%';
        return;
      }
      const scrolled = Math.max(0, -rect.top);
      const scrollable = totalH - windowH;
      const pct = Math.min(100, (scrolled / scrollable) * 100);
      progressBar.style.width = pct + '%';
    }

    window.addEventListener('scroll', updateProgress, { passive: true });
    // Reset on new answer
    const progressOutput = document.getElementById('ask-mirror-talk-output');
    if (progressOutput) {
      new MutationObserver(() => {
        progressBar.style.width = '0%';
      }).observe(progressOutput, { childList: true });
    }
  })();

  // ========================================
  // PATCH: Wire all new features into post-answer flow
  // ========================================

  // Intercept the 'done' event path by patching the SSE done block
  // We do this by overriding addShareButton to the V2 version everywhere
  // and calling the new functions at the right time.

  // ═══════════════════════════════════════════════════════════════
  // ██ PREMIUM FEATURES - UI HELPERS
  // ═══════════════════════════════════════════════════════════════

  /**
   * Show pattern insight card
   */
  function showPatternInsight(patterns) {
    if (!patterns || !patterns.topTheme) return;

    const existing = document.getElementById('amt-pattern-insight-card');
    if (existing) existing.remove();

    const card = document.createElement('div');
    card.id = 'amt-pattern-insight-card';
    card.className = 'amt-pattern-card';
    
    const themeEmojis = {
      relationships: '🫂',
      identity: '🪞',
      anxiety: '🌊',
      growth: '🌱',
      grief: '🕊️',
      confidence: '💪',
      boundaries: '🛡️',
      forgiveness: '🤝',
      vulnerability: '🦋',
      healing: '✨'
    };

    const icon = themeEmojis[patterns.topTheme] || '💭';
    
    card.innerHTML = `
      <div class="amt-pattern-header">
        <span class="amt-pattern-icon">${icon}</span>
        <h4 class="amt-pattern-title">Your Reflection Journey</h4>
      </div>
      <p class="amt-pattern-insight">
        You've asked <strong>${patterns.totalReflections} questions</strong>. 
        <span class="amt-pattern-stat">${patterns.topTheme}</span> keeps calling you back—
        there's wisdom here for you to uncover.
      </p>
    `;

    // Insert after response
    if (responseContainer && responseContainer.parentNode) {
      responseContainer.parentNode.insertBefore(card, responseContainer.nextSibling);
    }
  }

  /**
   * Show contextual greeting based on history
   */
  async function showContextualGreeting() {
    if (!window.AskMirrorTalkPremium) return;

    try {
      const greeting = await window.AskMirrorTalkPremium.generateContextualGreeting();
      if (!greeting || greeting.type === 'first_time') return;

      const existing = document.querySelector('.amt-contextual-greeting');
      if (existing) existing.remove();

      const greetingEl = document.createElement('div');
      greetingEl.className = 'amt-contextual-greeting';
      greetingEl.textContent = greeting.text;

      const formIntro = document.querySelector('.amt-form-intro');
      if (formIntro && formIntro.parentNode) {
        formIntro.parentNode.insertBefore(greetingEl, formIntro);
      }
    } catch (error) {
      console.warn('Failed to show contextual greeting:', error);
    }
  }

  /**
   * Show progress summary in Progress workflow panel
   */
  async function showProgressSummary() {
    if (!window.AskMirrorTalkPremium) return;

    try {
      const summary = await window.AskMirrorTalkPremium.generateProgressSummary();
      if (!summary) return;

      const progressPanel = document.querySelector('#amt-workflow-panel-progress');
      if (!progressPanel) return;

      const existing = progressPanel.querySelector('.amt-progress-summary');
      if (existing) existing.remove();

      const card = document.createElement('div');
      card.className = 'amt-progress-summary';
      
      card.innerHTML = `
        <p class="amt-progress-narrative">${summary.message}</p>
        <div class="amt-progress-stats">
          <div class="amt-progress-stat">
            <span class="amt-progress-stat-value">${summary.stats.total || 0}</span>
            <span class="amt-progress-stat-label">Reflections</span>
          </div>
          <div class="amt-progress-stat">
            <span class="amt-progress-stat-value">${summary.stats.weeklyAverage || '0'}</span>
            <span class="amt-progress-stat-label">Per Week</span>
          </div>
          <div class="amt-progress-stat">
            <span class="amt-progress-stat-value">${summary.stats.topTheme || 'general'}</span>
            <span class="amt-progress-stat-label">Top Theme</span>
          </div>
          <div class="amt-progress-stat">
            <span class="amt-progress-stat-value">${summary.stats.bestTime || 'evening'}</span>
            <span class="amt-progress-stat-label">Best Time</span>
          </div>
        </div>
      `;

      progressPanel.insertBefore(card, progressPanel.firstChild);
    } catch (error) {
      console.warn('Failed to show progress summary:', error);
    }
  }

  /**
   * Add export/import controls to Save & Share panel
   */
  function addDataControls() {
    if (!window.AskMirrorTalkPremium) return;

    const saveSharePanel = document.querySelector('#amt-workflow-panel-save-share');
    if (!saveSharePanel) return;

    const existing = saveSharePanel.querySelector('.amt-data-controls');
    if (existing) return; // Already added

    const controls = document.createElement('div');
    controls.className = 'amt-data-controls';
    controls.innerHTML = `
      <button type="button" class="amt-export-btn" title="Export all reflections">
        📤 Export Reflections
      </button>
      <button type="button" class="amt-import-btn" title="Import reflections">
        📥 Import Reflections
      </button>
      <input type="file" id="amt-import-file" accept=".json" style="display:none;">
    `;

    saveSharePanel.appendChild(controls);

    // Wire up export
    controls.querySelector('.amt-export-btn').addEventListener('click', async () => {
      const success = await window.AskMirrorTalkPremium.exportReflections();
      if (success) {
        alert('✅ Reflections exported successfully!');
      } else {
        alert('❌ Failed to export reflections. Please try again.');
      }
    });

    // Wire up import
    const importBtn = controls.querySelector('.amt-import-btn');
    const fileInput = controls.querySelector('#amt-import-file');
    
    importBtn.addEventListener('click', () => fileInput.click());
    
    fileInput.addEventListener('change', async (e) => {
      const file = e.target.files[0];
      if (!file) return;

      const result = await window.AskMirrorTalkPremium.importReflections(file);
      if (result.success) {
        alert(`✅ Imported ${result.imported} reflections successfully!`);
        fileInput.value = ''; // Reset
      } else {
        alert(`❌ Import failed: ${result.error}`);
      }
    });
  }

  /**
   * Handle offline mode
   */
  function handleOfflineMode() {
    if (!window.AskMirrorTalkPremium) return;

    // Listen for offline submit attempts
    document.addEventListener('amt:offline-submit', async (e) => {
      const { question, queueId } = e.detail;
      
      try {
        // Try to submit via normal flow
        input.value = question;
        const submitEvent = new Event('submit', { cancelable: true });
        const success = await form.dispatchEvent(submitEvent);
        
        if (success) {
          // Remove from queue on successful submission
          await window.AskMirrorTalkPremium.removeFromOfflineQueue(queueId);
        }
      } catch (error) {
        console.error('Failed to process offline submission:', error);
      }
    });

    // Show offline indicator when offline
    window.addEventListener('offline', () => {
      const existing = document.querySelector('.amt-offline-banner');
      if (existing) return;

      const banner = document.createElement('div');
      banner.className = 'amt-offline-banner';
      banner.textContent = 'You\'re offline. Reflections will sync when reconnected.';
      document.body.appendChild(banner);
    });

    window.addEventListener('online', () => {
      const banner = document.querySelector('.amt-offline-banner');
      if (banner) banner.remove();
    });
  }

  // Initialize premium features on page load
  if (window.AskMirrorTalkPremium) {
    // Show contextual greeting
    showContextualGreeting();
    
    // Initialize offline mode handlers
    handleOfflineMode();
    
    // Add data controls to Save & Share panel
    setTimeout(() => addDataControls(), 1000);
    
    // Update progress summary when switching to Progress panel
    document.querySelectorAll('[data-workflow-action="progress"]').forEach(btn => {
      btn.addEventListener('click', () => {
        setTimeout(() => showProgressSummary(), 300);
      });
    });
  }

  // ═══════════════════════════════════════════════════════════════
  // ██ END PREMIUM FEATURES
  // ═══════════════════════════════════════════════════════════════

  // Replace addShareButton globally within this scope
  // (The original is still bound in the SSE done handler — we override it here)
  function runPostAnswerExtras(question, ans) {
    if (!output) return;
    if (output.dataset.amtPostAnswerApplied === '1') return;
    output.dataset.amtPostAnswerApplied = '1';
    window._amtPostAnswerExtras(question, ans);
  }

  function safePostAnswerStep(fn) {
    try {
      fn();
    } catch (e) {
      console.warn('Post-answer extra failed:', e);
    }
  }

  window._amtPostAnswerExtras = function(question, ans) {
    safePostAnswerStep(() => addShareButtonV2(question, ans));
    setTimeout(() => safePostAnswerStep(() => showReflectPrompt()), 600);
    safePostAnswerStep(() => initCopyAnswerButton(ans));
    setTimeout(() => safePostAnswerStep(() => showMoodReactions()), 400);
  };

  // Hook into 'done' SSE event by patching the form submit handler
  // The safest approach: re-define addShareButton in this closure scope to V2
  // (original is only referenced internally; we reuse the same variable name)
  // Since we can't re-assign the already-declared const, we patch via the DOM event
  // by attaching a MutationObserver on #ask-mirror-talk-output for amt-complete class.

  const postAnswerObserver = new MutationObserver(() => {
    if (output.classList.contains('amt-complete')) {
      const question = input.value.trim();
      const ans = output.innerText || output.textContent || '';
      if (question && ans.length > 20) {
        // Remove old share section to let V2 replace it
        setTimeout(() => {
          runPostAnswerExtras(question, ans);
        }, 200);
      }
    }
  });
  if (output) postAnswerObserver.observe(output, { attributes: true, attributeFilter: ['class'] });

  // Hook into daily depth milestone for "Come Back Tomorrow" teaser (Feature 4)
  // Patch onQuestionAnswered post-processing to append the teaser at depth=3
  const _patchedOnQA = onQuestionAnswered;
  // We can't reassign a const but we can hook by decorating the DAILY_DEPTH_MILESTONES check
  // via the observable side-effect: watch for the '🌊 Deep session!' toast firing
  const _toastObserver = new MutationObserver(() => {
    const toast = document.getElementById('amt-milestone-toast');
    if (toast && toast.innerHTML.includes('Deep session')) {
      // Schedule come-back teaser to fire after the milestone toast finishes (3.5s + buffer)
      setTimeout(() => showComeBackTeaser(), 5000);
    }
  });
  const toastEl = document.getElementById('amt-milestone-toast');
  if (toastEl) _toastObserver.observe(toastEl, { childList: true });

  // ─── Keyboard Shortcuts ─────────────────────────────────────────
  document.addEventListener('keydown', (e) => {
    // Don't interfere with typing in input fields
    if (e.target.tagName === 'INPUT' || e.target.tagName === 'TEXTAREA') return;
    
    const shortcuts = {
      '/': () => { input.focus(); e.preventDefault(); },
      'n': () => { loadQuestionOfTheDay(); e.preventDefault(); },
      's': () => { document.querySelector('.amt-share-btn')?.click(); e.preventDefault(); },
      'c': () => { document.querySelector('.amt-copy-btn')?.click(); e.preventDefault(); },
      'b': () => { exploreToggle?.click(); e.preventDefault(); },
      '?': () => { showKeyboardHelp(); e.preventDefault(); }
    };
    
    // Cmd/Ctrl + K for quick focus
    if ((e.metaKey || e.ctrlKey) && e.key === 'k') {
      e.preventDefault();
      input.focus();
      input.select();
    }
    
    if (shortcuts[e.key]) {
      shortcuts[e.key]();
    }
  });
  
  function showKeyboardHelp() {
    const helpModal = document.createElement('div');
    helpModal.style.cssText = 'position:fixed;top:50%;left:50%;transform:translate(-50%,-50%);background:white;padding:2rem;border-radius:12px;box-shadow:0 10px 40px rgba(0,0,0,0.3);z-index:10000;max-width:400px;';
    helpModal.innerHTML = `
      <h3 style="margin:0 0 1rem;font-size:1.5rem;">Keyboard Shortcuts</h3>
      <div style="display:grid;gap:0.5rem;font-size:0.95rem;">
        <div><kbd style="padding:0.2rem 0.5rem;background:#f0f0f0;border-radius:4px;font-family:monospace;">/</kbd> Focus question input</div>
        <div><kbd style="padding:0.2rem 0.5rem;background:#f0f0f0;border-radius:4px;font-family:monospace;">n</kbd> Load new QOTD</div>
        <div><kbd style="padding:0.2rem 0.5rem;background:#f0f0f0;border-radius:4px;font-family:monospace;">s</kbd> Share answer</div>
        <div><kbd style="padding:0.2rem 0.5rem;background:#f0f0f0;border-radius:4px;font-family:monospace;">c</kbd> Copy answer</div>
        <div><kbd style="padding:0.2rem 0.5rem;background:#f0f0f0;border-radius:4px;font-family:monospace;">b</kbd> Browse topics</div>
        <div><kbd style="padding:0.2rem 0.5rem;background:#f0f0f0;border-radius:4px;font-family:monospace;">Cmd/Ctrl + K</kbd> Quick ask</div>
        <div><kbd style="padding:0.2rem 0.5rem;background:#f0f0f0;border-radius:4px;font-family:monospace;">?</kbd> Show this help</div>
      </div>
      <button onclick="this.parentElement.remove()" style="margin-top:1.5rem;padding:0.5rem 1.5rem;background:#943e08;color:white;border:none;border-radius:6px;cursor:pointer;width:100%;font-weight:600;">Got it</button>
    `;
    document.body.appendChild(helpModal);
    
    const overlay = document.createElement('div');
    overlay.style.cssText = 'position:fixed;top:0;left:0;right:0;bottom:0;background:rgba(0,0,0,0.5);z-index:9999;';
    overlay.onclick = () => { helpModal.remove(); overlay.remove(); };
    document.body.appendChild(overlay);
  }
  
  // ─── Voice Input ───────────────────────────────────────────────
  let voiceRecognition = null;
  let isRecognitionActive = false;
  let voiceBtn = null;

  function enableVoiceInput() {
    if (!('webkitSpeechRecognition' in window)) {
      log('Speech recognition not supported');
      return;
    }
    
    voiceRecognition = new webkitSpeechRecognition();
    voiceRecognition.continuous = false;
    voiceRecognition.interimResults = true;
    voiceRecognition.lang = 'en-US';
    
    voiceBtn = document.createElement('button');
    voiceBtn.type = 'button';
    voiceBtn.className = 'amt-voice-btn';
    voiceBtn.innerHTML = '🎤';
    voiceBtn.title = 'Ask with voice (click to start/stop)';
    voiceBtn.style.cssText = 'position:absolute;right:12px;bottom:12px;background:rgba(255,255,255,0.9);border:1px solid #d4cec6;border-radius:8px;font-size:1.3rem;cursor:pointer;padding:8px 10px;opacity:0.7;transition:all 0.2s;z-index:5;box-shadow:0 2px 4px rgba(0,0,0,0.08);';
    
    const updateButtonState = (disabled) => {
      if (disabled) {
        voiceBtn.style.opacity = '0.4';
        voiceBtn.style.cursor = 'not-allowed';
        voiceBtn.disabled = true;
      } else {
        voiceBtn.style.opacity = isRecognitionActive ? '1' : '0.7';
        voiceBtn.style.cursor = 'pointer';
        voiceBtn.disabled = false;
      }
    };
    
    voiceBtn.onmouseenter = () => {
      if (!voiceBtn.disabled) {
        voiceBtn.style.opacity = '1';
        voiceBtn.style.transform = 'scale(1.05)';
      }
    };
    voiceBtn.onmouseleave = () => {
      if (!voiceBtn.disabled) {
        voiceBtn.style.opacity = isRecognitionActive ? '1' : '0.7';
        voiceBtn.style.transform = 'scale(1)';
      }
    };
    
    const stopRecognition = () => {
      if (isRecognitionActive && voiceRecognition) {
        try {
          voiceRecognition.stop();
        } catch (e) {
          // Already stopped, ignore
        }
        isRecognitionActive = false;
        voiceBtn.innerHTML = '🎤';
        voiceBtn.title = 'Ask with voice (click to start/stop)';
        voiceBtn.style.opacity = '0.7';
        voiceBtn.style.background = 'rgba(255,255,255,0.9)';
        input.placeholder = 'Ask what you are carrying, questioning, or trying to understand...';
      }
    };
    
    const startRecognition = () => {
      // Don't allow voice input during response generation
      if (submitBtn && submitBtn.disabled) {
        return;
      }
      
      if (!isRecognitionActive && voiceRecognition) {
        try {
          voiceRecognition.start();
          isRecognitionActive = true;
          voiceBtn.innerHTML = '🔴';
          voiceBtn.title = 'Recording... (click to stop)';
          voiceBtn.style.opacity = '1';
          voiceBtn.style.background = 'rgba(255,255,255,1)';
          input.placeholder = '🎤 Listening...';
        } catch (e) {
          warn('Voice recognition error:', e);
          isRecognitionActive = false;
          voiceBtn.innerHTML = '🎤';
          voiceBtn.style.opacity = '0.7';
        }
      }
    };
    
    voiceBtn.onclick = () => {
      // Don't allow voice input during response generation
      if (submitBtn && submitBtn.disabled) {
        return;
      }
      
      if (isRecognitionActive) {
        stopRecognition();
      } else {
        startRecognition();
      }
    };
    
    voiceRecognition.onresult = (event) => {
      const transcript = Array.from(event.results)
        .map(result => result[0].transcript)
        .join('');
      input.value = transcript;
    };
    
    voiceRecognition.onend = () => {
      isRecognitionActive = false;
      voiceBtn.innerHTML = '🎤';
      voiceBtn.title = 'Ask with voice (click to start/stop)';
      voiceBtn.style.opacity = '0.7';
      voiceBtn.style.background = 'rgba(255,255,255,0.9)';
      input.placeholder = 'Ask what you are carrying, questioning, or trying to understand...';
    };
    
    voiceRecognition.onerror = (event) => {
      warn('Voice recognition error:', event.error);
      isRecognitionActive = false;
      voiceBtn.innerHTML = '🎤';
      voiceBtn.title = 'Ask with voice (click to start/stop)';
      voiceBtn.style.opacity = '0.7';
      voiceBtn.style.background = 'rgba(255,255,255,0.9)';
      input.placeholder = 'Ask what you are carrying, questioning, or trying to understand...';
    };
    
    // Create a wrapper for proper positioning
    // Wrap the textarea in a positioned container so the mic button has a proper anchor
    const textareaWrapper = document.createElement('div');
    textareaWrapper.style.cssText = 'position:relative;';
    
    // Insert wrapper before textarea, then move textarea into it
    input.parentNode.insertBefore(textareaWrapper, input);
    textareaWrapper.appendChild(input);
    textareaWrapper.appendChild(voiceBtn);
    
    // Monitor submitBtn disabled state to control voice button
    if (submitBtn) {
      const observer = new MutationObserver(() => {
        if (voiceBtn) {
          updateButtonState(submitBtn.disabled);
          if (submitBtn.disabled && isRecognitionActive) {
            stopRecognition();
          }
        }
      });
      observer.observe(submitBtn, { attributes: true, attributeFilter: ['disabled'] });
    }
    
    log('Voice input enabled');
  }
  
  // Stop voice recognition when form is submitted
  if (form) {
    form.addEventListener('submit', () => {
      if (isRecognitionActive && voiceRecognition) {
        try {
          voiceRecognition.stop();
        } catch (e) {
          // Already stopped
        }
        isRecognitionActive = false;
      }
    });
  }
  
  // Enable voice input on mobile devices
  if (/iPhone|iPad|Android/i.test(navigator.userAgent)) {
    setTimeout(enableVoiceInput, 1000);
  }
  
  // ─── Social Proof ──────────────────────────────────────────────
  function showSocialProof() {
    fetch(`${API_BASE}/api/stats/questions-today`)
      .then(res => res.json())
      .then(data => {
        if (!data.count || data.count < 10) return; // Only show if meaningful
        
        const badge = document.createElement('div');
        badge.className = 'amt-social-proof';
        badge.style.cssText = 'position:fixed;bottom:20px;right:20px;padding:0.75rem 1.25rem;background:rgba(148,62,8,0.95);color:white;border-radius:24px;font-size:0.85rem;font-weight:600;z-index:100;box-shadow:0 4px 12px rgba(0,0,0,0.15);display:flex;align-items:center;gap:0.5rem;animation:slideInRight 0.5s ease;';
        badge.innerHTML = `
          <span style="display:inline-block;width:8px;height:8px;background:#4ade80;border-radius:50%;animation:pulse 2s infinite;"></span>
          <span>${data.count} questions asked today</span>
        `;
        
        // Add CSS animation
        if (!document.getElementById('amt-social-proof-styles')) {
          const style = document.createElement('style');
          style.id = 'amt-social-proof-styles';
          style.textContent = `
            @keyframes slideInRight {
              from { transform: translateX(120%); opacity: 0; }
              to { transform: translateX(0); opacity: 1; }
            }
            @keyframes pulse {
              0%, 100% { opacity: 1; transform: scale(1); }
              50% { opacity: 0.5; transform: scale(1.2); }
            }
            @media (max-width: 640px) {
              .amt-social-proof {
                bottom: 80px !important;
                right: 10px !important;
                font-size: 0.8rem !important;
              }
            }
          `;
          document.head.appendChild(style);
        }
        
        widgetRoot.appendChild(badge);
        
        // Auto-hide after 8 seconds
        setTimeout(() => {
          badge.style.animation = 'slideInRight 0.5s ease reverse';
          setTimeout(() => badge.remove(), 500);
        }, 8000);
      })
      .catch(() => {}); // Silent fail
  }
  
  // Show social proof after a delay
  setTimeout(showSocialProof, 3000);
  
  // ─── Pull-to-Refresh ───────────────────────────────────────────
  let pullStartY = 0;
  let pullDistance = 0;
  let refreshIndicator = null;
  
  function showRefreshIndicator() {
    if (refreshIndicator) return;
    refreshIndicator = document.createElement('div');
    refreshIndicator.style.cssText = 'position:fixed;top:0;left:50%;transform:translateX(-50%);padding:1rem;background:rgba(148,62,8,0.95);color:white;border-radius:0 0 12px 12px;font-weight:600;z-index:1000;transition:transform 0.3s;';
    refreshIndicator.innerHTML = '⬆️ Release to refresh';
    document.body.appendChild(refreshIndicator);
  }
  
  function hideRefreshIndicator() {
    if (refreshIndicator) {
      refreshIndicator.style.transform = 'translateX(-50%) translateY(-100%)';
      setTimeout(() => {
        refreshIndicator?.remove();
        refreshIndicator = null;
      }, 300);
    }
  }
  
  document.addEventListener('touchstart', (e) => {
    if (window.scrollY === 0 && !submitBtn.disabled) {
      pullStartY = e.touches[0].clientY;
    }
  });
  
  document.addEventListener('touchmove', (e) => {
    if (pullStartY === 0) return;
    pullDistance = e.touches[0].clientY - pullStartY;
    if (pullDistance > 80 && !refreshIndicator) {
      showRefreshIndicator();
    } else if (pullDistance < 80 && refreshIndicator) {
      hideRefreshIndicator();
    }
  });
  
  document.addEventListener('touchend', () => {
    if (pullDistance > 80) {
      loadQuestionOfTheDay();
      // Haptic feedback if available
      if (navigator.vibrate) navigator.vibrate(10);
    }
    pullStartY = 0;
    pullDistance = 0;
    hideRefreshIndicator();
  });

  try {
    initWorkflowBar();
  } catch (e) {
    warn('[Workflow] Could not initialize reflection workflow:', e);
  }

  if (ENABLE_TEST_EXPORTS) {
    window.__AMT_TEST_EXPORTS__ = {
      normalizeInsightRecord,
      extractShareHeadline,
      extractInsightExcerpt,
      extractCardHeadline,
      listCardHeadlineCandidates,
      isCompleteReflectionSentence,
      ensureReflectionSentence,
      joinReflectionTextParts,
      buildThemeReflectionFallback,
      buildJournalReflectionInsight,
      buildInsightShareCard,
      buildShareCard,
      getAchievementShareCopy,
      getReflectionCardQrMatrix,
      getReflectionCardQrPayload,
      getInsightShareThemeStyle,
      getInsightShareVariant,
      getInsightShareFamily,
      buildWeeklyRecapShareCard,
      getWeeklyRecapTemplate
    };
  }

})();
