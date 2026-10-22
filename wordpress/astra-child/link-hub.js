(() => {
  'use strict';
  const hub = document.querySelector('[data-mt-link-hub]');
  if (!hub) return;
  const emit = (action, destination = '') => {
    window.dispatchEvent(new CustomEvent('mt:intelligence-event', { detail: { name: 'link_hub_action', metadata: { path: location.pathname, status: action, target: destination } } }));
  };
  const share = hub.querySelector('[data-mt-link-hub-share]');
  const shareStatus = hub.querySelector('[data-mt-link-hub-share-status]');
  const hubAudio = hub.querySelector('[data-mt-link-hub-audio]');
  hubAudio?.addEventListener('play', () => {
    document.dispatchEvent(new CustomEvent('mt:podcast-play', { detail: { title: hubAudio.dataset.episodeTitle || '' } }));
  });
  share?.addEventListener('click', async () => {
    const payload = { title: document.title, text: 'Listen, reflect and connect with Mirror Talk.', url: location.href };
    try {
      if (navigator.share) await navigator.share(payload);
      else { await navigator.clipboard.writeText(location.href); if (shareStatus) shareStatus.textContent = 'Official link copied.'; }
      emit('share', location.href);
    } catch (error) {
      if (error?.name !== 'AbortError' && shareStatus) shareStatus.textContent = 'Copy the address from your browser to share this page.';
    }
  });
  hub.addEventListener('click', (event) => {
    const episode = event.target.closest('[data-mt-link-hub-episode]');
    if (episode) {
      const audio = hub.querySelector('[data-mt-link-hub-audio]');
      const title = hub.querySelector('[data-mt-link-hub-title]');
      if (!audio) return;
      audio.src = episode.dataset.audio || '';
      audio.dataset.episodeTitle = episode.dataset.title || '';
      if (title) title.textContent = episode.dataset.title || '';
      hub.querySelectorAll('[data-mt-link-hub-episode]').forEach((item) => item.classList.toggle('is-current', item === episode));
      audio.play().catch(() => {});
      emit('episode_selected', episode.dataset.title || '');
      return;
    }
    const action = event.target.closest('[data-mt-link-hub-action]');
    if (action) emit(action.dataset.mtLinkHubAction || 'unknown', action.href || 'dialog');
  });
})();

