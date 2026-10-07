(() => {
  'use strict';
  const root = document.querySelector('[data-mt-player-window]');
  if (!root) return;
  const audio = root.querySelector('[data-mt-window-audio]');
  const title = root.querySelector('[data-mt-window-title]');
  const key = 'mt_audio_state_v1';

  const readState = () => {
    try { return JSON.parse(localStorage.getItem(key) || '{}'); } catch (_) { return {}; }
  };
  const saveState = () => {
    try {
      localStorage.setItem(key, JSON.stringify({
        audio: audio.currentSrc || audio.src,
        title: title.textContent,
        time: audio.currentTime || 0,
        playing: !audio.paused,
        updated: Date.now()
      }));
    } catch (_) {}
  };
  const select = (url, episodeTitle, time = 0, play = true) => {
    audio.src = url;
    title.textContent = episodeTitle;
    audio.addEventListener('loadedmetadata', () => { if (time > 0 && Number.isFinite(time)) audio.currentTime = Math.min(time, audio.duration || time); }, { once: true });
    if ('mediaSession' in navigator) navigator.mediaSession.metadata = new MediaMetadata({ title: episodeTitle, artist: 'Mirror Talk: Soulful Conversations' });
    if (play) audio.play().catch(() => {});
  };

  const state = readState();
  if (state.audio) select(state.audio, state.title || 'Mirror Talk: Soulful Conversations', Number(state.time) || 0, Boolean(state.playing));
  root.querySelectorAll('[data-mt-window-episode]').forEach((button) => button.addEventListener('click', () => select(button.dataset.audio, button.dataset.title)));
  ['play', 'pause', 'timeupdate', 'ended'].forEach((eventName) => audio.addEventListener(eventName, saveState));
  const returnLink = root.querySelector('[data-mt-return-site]');
  if (returnLink) returnLink.addEventListener('click', (event) => {
    const returnUrl = root.dataset.returnUrl || returnLink.href || '/';
    if (!window.opener || window.opener.closed) return; // The real link remains a reliable same-window fallback.
    event.preventDefault();
    try {
      window.opener.focus();
      window.opener.postMessage({ type: 'MT_PLAYER_RETURN', audioState: readState() }, window.location.origin);
      window.setTimeout(() => { if (!window.closed) window.location.assign(returnUrl); }, 180);
      window.close();
    } catch (_) {
      window.location.assign(returnUrl);
    }
  });
  window.addEventListener('beforeunload', saveState);
})();
