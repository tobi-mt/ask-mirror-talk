(() => {
  'use strict';
  const root = document.querySelector('[data-mt-youtube-studio]');
  if (!root) return;

  const consentKey = 'mt_external_media_consent_v1';
  const media = root.querySelector('[data-mt-youtube-media]');
  const poster = root.querySelector('[data-mt-youtube-poster]');
  const playerNode = root.querySelector('[data-mt-youtube-player]');
  const consentButton = root.querySelector('[data-mt-youtube-consent]');
  const soundButton = root.querySelector('[data-mt-youtube-sound]');
  const status = root.querySelector('[data-mt-youtube-status]');
  const reducedMotion = matchMedia('(prefers-reduced-motion: reduce)').matches;
  const saveData = Boolean(navigator.connection && navigator.connection.saveData);
  let player = null;
  let visible = false;
  let ready = false;
  let started = false;
  let soundCheck = null;
  let moduleReported = false;
  let playbackFallback = null;
  const progressReported = new Set();

  const report = (name, metadata = {}) => document.dispatchEvent(new CustomEvent('mt:intelligence-event', {
    detail: { name, metadata: { video_id: root.dataset.videoId, video_title: root.dataset.videoTitle, surface: root.className.match(/mt-youtube-studio--([\w-]+)/)?.[1] || '', ...metadata } }
  }));
  const hasConsent = () => {
    try { return localStorage.getItem(consentKey) === 'granted'; } catch (_) { return false; }
  };
  const podcastAudio = () => document.querySelector('[data-mt-audio],[data-mt-link-hub-audio]');
  const podcastIsPlaying = () => {
    const audio = podcastAudio();
    return audio && !audio.paused && !audio.ended;
  };
  const pausePodcast = () => {
    const audio = podcastAudio();
    if (audio && !audio.paused) audio.pause();
  };

  const loadYouTubeApi = () => new Promise((resolve, reject) => {
    if (window.YT && typeof window.YT.Player === 'function') return resolve(window.YT);
    const timeout = window.setTimeout(() => reject(new Error('YouTube player API timed out')), 8000);
    const prior = window.onYouTubeIframeAPIReady;
    window.onYouTubeIframeAPIReady = () => {
      if (typeof prior === 'function') prior();
      window.clearTimeout(timeout);
      resolve(window.YT);
    };
    if (!document.querySelector('script[data-mt-youtube-api]')) {
      const script = document.createElement('script');
      script.src = 'https://www.youtube.com/iframe_api';
      script.async = true;
      script.dataset.mtYoutubeApi = 'true';
      script.onerror = () => { window.clearTimeout(timeout); reject(new Error('YouTube player API failed to load')); };
      document.head.appendChild(script);
    }
  });

  const shouldAutoplay = () => visible && !document.hidden && !reducedMotion && !saveData && !podcastIsPlaying();
  const monitorSound = () => {
    window.clearInterval(soundCheck);
    soundCheck = window.setInterval(() => {
      if (!player || !ready || typeof player.isMuted !== 'function' || typeof player.getPlayerState !== 'function') return;
      if (!player.isMuted() && player.getPlayerState() === window.YT.PlayerState.PLAYING) pausePodcast();
      const duration = typeof player.getDuration === 'function' ? Number(player.getDuration()) || 0 : 0;
      const currentTime = typeof player.getCurrentTime === 'function' ? Number(player.getCurrentTime()) || 0 : 0;
      const progress = duration ? currentTime / duration * 100 : 0;
      [25, 50, 75].forEach((bucket) => {
        if (progress >= bucket && !progressReported.has(bucket)) {
          progressReported.add(bucket);
          report('youtube_video_progress', { progress_bucket: bucket });
        }
      });
    }, 1000);
  };
  const startMuted = () => {
    if (!ready || !shouldAutoplay() || !player || typeof player.mute !== 'function' || typeof player.playVideo !== 'function') return;
    player.mute();
    player.playVideo();
  };

  const showPreparingState = () => {
    root.classList.add('is-loading');
    consentButton.disabled = true;
    consentButton.textContent = 'Preparing video…';
    const heading = poster.querySelector('strong');
    const copy = poster.querySelector('p');
    if (heading) heading.textContent = 'Bringing the latest conversation into view';
    if (copy) copy.textContent = 'The video will begin quietly. If your browser pauses autoplay, the ordinary play controls will appear.';
  };

  const revealNativePlayer = (message) => {
    window.clearTimeout(playbackFallback);
    root.classList.remove('is-loading');
    root.classList.add('is-player-ready');
    poster.hidden = true;
    if (message) status.textContent = message;
  };

  const createPlayer = async (playImmediately = false) => {
    if (player || !hasConsent()) return;
    if (root.dataset.videoThumbnail) media.style.backgroundImage = `url("${root.dataset.videoThumbnail.replace(/"/g, '%22')}")`;
    media.style.backgroundSize = 'cover';
    media.style.backgroundPosition = 'center';
    showPreparingState();
    root.classList.add('is-media-enabled');
    status.textContent = saveData ? 'Data Saver is on. The video will wait for you.' : reducedMotion ? 'Automatic motion is paused by your device preference.' : 'Preparing the latest video…';
    let YT;
    try {
      YT = await loadYouTubeApi();
    } catch (_) {
      root.classList.remove('is-loading');
      consentButton.disabled = false;
      consentButton.textContent = 'Try loading video again';
      status.textContent = 'YouTube did not respond. Try again or use the Watch on YouTube link.';
      player = null;
      report('youtube_api_error');
      return;
    }
    player = new YT.Player(playerNode, {
      host: 'https://www.youtube-nocookie.com',
      videoId: root.dataset.videoId,
      playerVars: {
        autoplay: 0,
        controls: 1,
        playsinline: 1,
        rel: 0,
        origin: location.origin,
        enablejsapi: 1
      },
      events: {
        onReady: (event) => {
          // YouTube may emit state events before the Player constructor has
          // finished assigning its return value. The callback target is the
          // authoritative, fully initialized controller.
          player = event.target;
          ready = true;
          event.target.mute();
          soundButton.hidden = false;
          const mayAutoplay = playImmediately || shouldAutoplay();
          if (mayAutoplay && !reducedMotion && !saveData) event.target.playVideo();
          else revealNativePlayer(saveData ? 'Data Saver is on. Press play when you are ready.' : 'Press play whenever you are ready.');
          playbackFallback = window.setTimeout(() => {
            if (!player || typeof player.getPlayerState !== 'function' || player.getPlayerState() !== YT.PlayerState.PLAYING) {
              revealNativePlayer('Your browser paused automatic playback. Press play when you are ready.');
              report('youtube_autoplay_fallback');
            }
          }, 2800);
          monitorSound();
          report('youtube_video_ready');
        },
        onStateChange: (event) => {
          player = event.target || player;
          if (event.data === YT.PlayerState.PLAYING) {
            revealNativePlayer();
            root.classList.add('is-playing');
            const muted = !player || typeof player.isMuted !== 'function' ? true : player.isMuted();
            if (!started) { started = true; report('youtube_video_start', { muted }); }
            status.textContent = muted ? 'Playing quietly. Turn sound on whenever you are ready.' : 'Playing with sound.';
          }
          if (event.data === YT.PlayerState.ENDED) report('youtube_video_complete');
        },
        onAutoplayBlocked: () => {
          revealNativePlayer('Your browser paused automatic playback. Press play when you are ready.');
          report('youtube_autoplay_blocked');
        },
        onError: () => {
          window.clearTimeout(playbackFallback);
          root.classList.remove('is-loading');
          root.classList.remove('is-player-ready');
          poster.hidden = false;
          consentButton.disabled = true;
          consentButton.textContent = 'Watch on YouTube instead';
          status.textContent = 'This video cannot play here just now. You can still watch it on YouTube.';
          report('youtube_video_error');
        }
      }
    });
  };

  consentButton.addEventListener('click', () => {
    try { localStorage.setItem(consentKey, 'granted'); } catch (_) {}
    report('youtube_media_allowed');
    createPlayer(true);
  });

  soundButton.addEventListener('click', () => {
    if (!player || !ready || typeof player.isMuted !== 'function') return;
    if (player.isMuted()) {
      pausePodcast();
      if (typeof player.unMute === 'function') player.unMute();
      soundButton.textContent = 'Mute video';
      status.textContent = 'Playing with sound.';
      report('youtube_video_unmuted');
    } else {
      if (typeof player.mute === 'function') player.mute();
      soundButton.textContent = 'Turn sound on';
      status.textContent = 'Playing quietly.';
      report('youtube_video_muted');
    }
  });

  document.addEventListener('mt:podcast-play', () => {
    if (player && ready && typeof player.getPlayerState === 'function' && typeof player.pauseVideo === 'function' && player.getPlayerState() === window.YT.PlayerState.PLAYING) {
      player.pauseVideo();
      status.textContent = 'Video paused while you listen to the podcast.';
    }
  });
  document.addEventListener('visibilitychange', () => {
    if (document.hidden && player && ready && typeof player.pauseVideo === 'function') player.pauseVideo();
  });

  const observer = new IntersectionObserver((entries) => {
    visible = Boolean(entries[0] && entries[0].isIntersecting && entries[0].intersectionRatio >= 0.5);
    if (visible && !moduleReported) { moduleReported = true; report('youtube_module_viewable'); }
    if (visible && hasConsent()) {
      if (!player) createPlayer(false);
      else startMuted();
    } else if (player && ready && typeof player.pauseVideo === 'function') {
      player.pauseVideo();
    }
  }, { threshold: [0, 0.5, 0.75] });
  observer.observe(media);

  if (hasConsent()) showPreparingState();
})();
