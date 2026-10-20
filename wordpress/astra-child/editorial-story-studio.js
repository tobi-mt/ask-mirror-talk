(() => {
  'use strict';
  const externalMediaConsent = 'mt_external_media_consent_v1';
  const reducedMotion = matchMedia('(prefers-reduced-motion: reduce)').matches;
  const saveData = Boolean(navigator.connection && navigator.connection.saveData);
  const hasConsent = () => {
    try { return localStorage.getItem(externalMediaConsent) === 'granted'; } catch (_) { return false; }
  };
  const grantConsent = () => {
    try { localStorage.setItem(externalMediaConsent, 'granted'); } catch (_) {}
  };
  const report = (name, id, metadata = {}) => document.dispatchEvent(new CustomEvent('mt:intelligence-event', {
    detail: { name, metadata: { video_id: id, surface: 'story-studio', ...metadata } }
  }));

  document.querySelectorAll('[data-mt-story-video]').forEach((root) => {
    const button = root.querySelector('[data-mt-story-video-play]');
    const frame = root.querySelector('[data-mt-story-video-frame]');
    const id = root.dataset.videoId;
    if (!button || !frame || !/^[\w-]{11}$/.test(id || '')) return;
    let loaded = false;

    const load = (autoplay) => {
      if (loaded) return;
      loaded = true;
      const iframe = document.createElement('iframe');
      const startsMuted = autoplay && !reducedMotion && !saveData;
      const params = new URLSearchParams({
        autoplay: startsMuted ? '1' : '0', mute: '1', controls: '1', rel: '0',
        playsinline: '1', modestbranding: '1', origin: location.origin
      });
      iframe.src = `https://www.youtube-nocookie.com/embed/${id}?${params.toString()}`;
      iframe.title = button.getAttribute('aria-label') || 'Mirror Talk video';
      iframe.allow = 'accelerometer; autoplay; encrypted-media; gyroscope; picture-in-picture; web-share';
      iframe.allowFullscreen = true;
      iframe.setAttribute('playsinline', '');
      frame.replaceChildren(iframe);
      root.classList.add('is-playing');
      button.hidden = true;
      document.querySelectorAll('audio').forEach((audio) => { if (!audio.paused) audio.pause(); });
      report('youtube_video_ready', id, { muted: true, autoplay_requested: startsMuted });
      if (startsMuted) report('youtube_video_start', id, { muted: true, autoplay_requested: true });
    };

    button.addEventListener('click', () => {
      grantConsent();
      report('youtube_media_allowed', id, { source: 'inline-video' });
      load(true);
    }, { once: true });

    const observer = new IntersectionObserver((entries) => {
      const visible = Boolean(entries[0] && entries[0].isIntersecting && entries[0].intersectionRatio >= 0.5);
      if (visible && hasConsent()) load(true);
    }, { threshold: [0, 0.5] });
    observer.observe(root);
  });

  document.querySelectorAll('[data-mt-story-audio]').forEach((audio) => {
    let completed = false;
    audio.addEventListener('play', () => {
      document.dispatchEvent(new CustomEvent('mt:podcast-play'));
      document.dispatchEvent(new CustomEvent('mt:intelligence-event', { detail: { name: 'podcast_play', metadata: { episode_title: audio.dataset.episodeTitle || '' } } }));
    });
    audio.addEventListener('timeupdate', () => {
      if (!completed && audio.duration > 0 && audio.currentTime / audio.duration >= 0.95) {
        completed = true;
        document.dispatchEvent(new CustomEvent('mt:intelligence-event', { detail: { name: 'podcast_complete', metadata: { episode_title: audio.dataset.episodeTitle || '', progress_bucket: 100 } } }));
      }
    });
    audio.addEventListener('ended', () => {
      if (completed) return;
      completed = true;
      document.dispatchEvent(new CustomEvent('mt:intelligence-event', { detail: { name: 'podcast_complete', metadata: { episode_title: audio.dataset.episodeTitle || '', progress_bucket: 100 } } }));
    });
  });
  document.addEventListener('click', (event) => {
    const outline = event.target.closest('.mt-composer-outline a');
    const newsletter = event.target.closest('.mt-story-newsletter [data-mt-open-dialog]');
    const follow = event.target.closest('.mt-story-follow a');
    if (!outline && !newsletter && !follow) return;
    const target = outline ? 'outline' : (newsletter ? 'newsletter' : 'listening-platform');
    const label = (outline || newsletter || follow).textContent.trim().slice(0, 120);
    document.dispatchEvent(new CustomEvent('mt:intelligence-event', {
      detail: { name: outline ? 'composer_outline_click' : 'composer_cta_click', metadata: { target, label } }
    }));
  });
})();
