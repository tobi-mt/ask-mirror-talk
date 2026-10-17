(() => {
  'use strict';
  document.querySelectorAll('[data-mt-story-video]').forEach((root) => {
    const button = root.querySelector('[data-mt-story-video-play]');
    const frame = root.querySelector('[data-mt-story-video-frame]');
    const id = root.dataset.videoId;
    if (!button || !frame || !/^[\w-]{11}$/.test(id || '')) return;
    button.addEventListener('click', () => {
      const iframe = document.createElement('iframe');
      iframe.src = `https://www.youtube-nocookie.com/embed/${id}?autoplay=1&rel=0&playsinline=1`;
      iframe.title = button.getAttribute('aria-label') || 'Mirror Talk video';
      iframe.allow = 'accelerometer; autoplay; encrypted-media; gyroscope; picture-in-picture';
      iframe.allowFullscreen = true;
      frame.appendChild(iframe);
      root.classList.add('is-playing');
      button.hidden = true;
      document.querySelectorAll('audio').forEach((audio) => { if (!audio.paused) audio.pause(); });
      document.dispatchEvent(new CustomEvent('mt:intelligence-event', { detail: { name: 'youtube_video_start', metadata: { video_id: id, surface: 'story-studio' } } }));
    }, { once: true });
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
