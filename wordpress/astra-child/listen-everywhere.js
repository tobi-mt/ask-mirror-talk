(() => {
  'use strict';
  const root = document.documentElement;
  const ua = navigator.userAgent || '';
  const device = /Android/i.test(ua) ? 'android' : /iPhone|iPad|iPod|Macintosh/i.test(ua) ? 'apple' : 'desktop';
  let preferred = '';
  try { preferred = localStorage.getItem('mt_preferred_listen_platform') || ''; } catch (_) {}

  document.querySelectorAll('[data-mt-platform-directory]').forEach((directory) => {
    const cards = [...directory.querySelectorAll('[data-mt-platform-card]')];
    cards.sort((a, b) => {
      const score = (card) => (card.dataset.platform === preferred ? 0 : (card.dataset.devices || '').split(' ').includes(device) ? 1 : 2);
      return score(a) - score(b);
    }).forEach((card) => directory.append(card));
    if (preferred) directory.querySelector(`[data-platform="${CSS.escape(preferred)}"]`)?.classList.add('is-preferred');
  });

  document.addEventListener('click', async (event) => {
    const platform = event.target.closest('[data-mt-platform-link]');
    if (platform) {
      try { localStorage.setItem('mt_preferred_listen_platform', platform.dataset.mtPlatformLink); } catch (_) {}
      document.dispatchEvent(new CustomEvent('mt:intelligence-event', { detail: { name: 'listen_platform_selected', metadata: { platform: platform.dataset.mtPlatformLink, path: location.pathname } } }));
    }
    const copy = event.target.closest('[data-mt-copy-rss]');
    if (copy) {
      try { await navigator.clipboard.writeText(copy.dataset.mtCopyRss); copy.textContent = 'Feed URL copied'; }
      catch (_) { window.prompt('Copy the podcast feed URL:', copy.dataset.mtCopyRss); }
    }
    const episode = event.target.closest('[data-mt-listen-page-episode]');
    if (episode) {
      const audio = document.querySelector('[data-mt-listen-page-audio]');
      const title = document.querySelector('[data-mt-listen-page-title]');
      if (!audio) return;
      audio.src = episode.dataset.audio;
      audio.dataset.episodeTitle = episode.dataset.title || '';
      if (title) title.textContent = episode.dataset.title;
      document.querySelectorAll('[data-mt-listen-page-episode]').forEach((item) => item.classList.toggle('is-current', item === episode));
      audio.play().catch(() => {});
    }
  });
  root.dataset.mtListenDevice = device;
})();
