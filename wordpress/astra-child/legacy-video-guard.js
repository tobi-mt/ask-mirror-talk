(() => {
  'use strict';
  const videoId = (value = '') => {
    const match = String(value).match(/(?:youtu\.be\/|youtube(?:-nocookie)?\.com\/(?:watch\?(?:.*&)?v=|embed\/|shorts\/))([A-Za-z0-9_-]{11})/i);
    return match ? match[1] : '';
  };
  const upgrade = () => {
    document.querySelectorAll('.elementor-widget-video[data-settings]').forEach((widget) => {
      let settings = {};
      try { settings = JSON.parse(widget.dataset.settings || '{}'); } catch (_) { return; }
      const id = videoId(settings.youtube_url);
      if (!id || widget.dataset.mtGuarded === 'true') return;
      widget.dataset.mtGuarded = 'true';
      widget.classList.remove('elementor-widget-video');
      widget.removeAttribute('data-widget_type');
      const container = widget.querySelector('.elementor-widget-container') || widget;
      container.innerHTML = '';
      const facade = document.createElement('div');
      facade.className = 'mt-legacy-video-facade';
      facade.style.backgroundImage = `linear-gradient(rgba(16,12,20,.24),rgba(16,12,20,.68)),url(https://i.ytimg.com/vi/${id}/hqdefault.jpg)`;
      const button = document.createElement('button');
      button.type = 'button';
      button.className = 'mt-legacy-video-facade__button';
      button.setAttribute('aria-label', 'Play this Mirror Talk video');
      button.innerHTML = '<span aria-hidden="true">▶</span><strong>Play video</strong><small>YouTube privacy-enhanced mode</small>';
      button.addEventListener('click', () => {
        const frame = document.createElement('iframe');
        frame.src = `https://www.youtube-nocookie.com/embed/${id}?autoplay=1&rel=0`;
        frame.title = 'Mirror Talk video';
        frame.allow = 'accelerometer; autoplay; encrypted-media; gyroscope; picture-in-picture; web-share';
        frame.allowFullscreen = true;
        frame.loading = 'lazy';
        facade.replaceChildren(frame);
      }, { once: true });
      facade.appendChild(button);
      container.appendChild(facade);
    });
  };
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', upgrade, { once: true });
  else upgrade();
})();
