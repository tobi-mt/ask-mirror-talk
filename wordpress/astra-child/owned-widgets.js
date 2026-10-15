(() => {
  'use strict';
  const reduced = matchMedia('(prefers-reduced-motion: reduce)').matches;
  document.querySelectorAll('[data-mt-owned-slider]').forEach((slider) => {
    const track = slider.querySelector('.mt-owned-slider__track');
    const slides = [...(track?.children || [])];
    const pause = slider.querySelector('[data-mt-slider-pause]');
    if (!track || slides.length < 2) { if (pause) pause.hidden = true; return; }
    let index = 0; let timer = 0; let paused = reduced;
    slides.forEach((slide, i) => { slide.setAttribute('aria-roledescription', 'slide'); slide.setAttribute('aria-label', `${i + 1} of ${slides.length}`); });
    const show = (next) => { index = (next + slides.length) % slides.length; track.scrollTo({ left: slides[index].offsetLeft, behavior: reduced ? 'auto' : 'smooth' }); };
    const stop = () => { clearInterval(timer); timer = 0; };
    const start = () => { stop(); if (!paused && document.visibilityState === 'visible') timer = setInterval(() => show(index + 1), 7500); };
    pause?.addEventListener('click', () => { paused = !paused; pause.textContent = paused ? 'Play' : 'Pause'; paused ? stop() : start(); });
    slider.addEventListener('mouseenter', stop); slider.addEventListener('mouseleave', start);
    slider.addEventListener('focusin', stop); slider.addEventListener('focusout', start);
    document.addEventListener('visibilitychange', () => document.visibilityState === 'hidden' ? stop() : start());
    if (!reduced) start();
  });
})();
