(() => {
  'use strict';

  const openDialog = (dialog) => {
    if (!dialog || dialog.open) return;
    document.querySelectorAll('dialog[open]').forEach((open) => open.close());
    if (typeof dialog.showModal === 'function') dialog.showModal();
    else dialog.setAttribute('open', '');
  };

  document.addEventListener('click', (event) => {
    const opener = event.target.closest('[data-mt-open-dialog]');
    if (opener) {
      const dialog = document.getElementById(opener.dataset.mtOpenDialog);
      if (dialog) {
        event.preventDefault();
        openDialog(dialog);
      }
      return;
    }

    const closer = event.target.closest('[data-mt-dialog-close]');
    if (closer) {
      const dialog = closer.closest('dialog');
      if (dialog) dialog.close();
    }
    if (typeof HTMLDialogElement !== 'undefined' && event.target instanceof HTMLDialogElement) {
      const rect = event.target.getBoundingClientRect();
      const inside = event.clientX >= rect.left && event.clientX <= rect.right && event.clientY >= rect.top && event.clientY <= rect.bottom;
      if (!inside) event.target.close();
    }
  });

  const newsletterForm = document.querySelector('[data-mt-newsletter-form]');
  if (newsletterForm) newsletterForm.addEventListener('submit', async (event) => {
    event.preventDefault();
    const status = newsletterForm.querySelector('[data-mt-newsletter-status]');
    const submit = newsletterForm.querySelector('[type="submit"]');
    const config = window.MirrorTalkNewsletter || {};
    if (!newsletterForm.reportValidity() || !config.ajaxUrl) return;
    submit.disabled = true;
    status.textContent = 'Joining…';
    const payload = new FormData(newsletterForm);
    payload.append('action', 'mirrortalk_newsletter_signup');
    payload.append('nonce', config.nonce || '');
    payload.append('issued_at', String(config.issuedAt || ''));
    payload.append('proof', config.proof || '');
    try {
      const response = await fetch(config.ajaxUrl, { method: 'POST', body: payload, credentials: 'same-origin' });
      const result = await response.json();
      status.textContent = (result && result.data && result.data.message) || (result.success ? 'You are subscribed.' : 'Please check your details and try again.');
      status.classList.toggle('is-success', Boolean(result.success));
      if (result.success) {
        newsletterForm.reset();
        if (window.MirrorTalkTrack) window.MirrorTalkTrack('newsletter_subscribed', { path: location.pathname });
      }
    } catch (_) {
      status.textContent = 'We could not complete your subscription just now. Please try again.';
    } finally {
      submit.disabled = false;
    }
  });

  const player = document.querySelector('[data-mt-listen]');
  if (player) {
    const launcher = player.querySelector('[data-mt-listen-toggle]');
    const close = player.querySelector('[data-mt-listen-close]');
    const panel = player.querySelector('.mt-listen__panel');
    const queueToggle = player.querySelector('[data-mt-queue-toggle]');
    const queue = player.querySelector('.mt-listen__queue');
    const audio = player.querySelector('[data-mt-audio]');
    const title = player.querySelector('[data-mt-player-title]');
    const popout = player.querySelector('[data-mt-popout]');
    const saveMoment = player.querySelector('[data-mt-save-moment]');
    const reflectMoment = player.querySelector('[data-mt-reflect-moment]');
    const momentStatus = player.querySelector('[data-mt-moment-status]');
    const transcriptPanel = player.querySelector('[data-mt-transcript-panel]');
    const transcriptRoot = player.querySelector('[data-mt-transcript-cues]');
    const chapterLabel = player.querySelector('[data-mt-player-chapter]');
    const reflectionWorkspace = player.querySelector('[data-mt-reflection-workspace]');
    const reflectionContext = player.querySelector('[data-mt-reflection-context]');
    const reflectionAnswer = player.querySelector('[data-mt-reflection-answer]');
    const reflectionFollowups = player.querySelector('[data-mt-reflection-followups]');
    const reflectionForm = player.querySelector('[data-mt-reflection-form]');
    const reflectionInput = player.querySelector('[data-mt-reflection-input]');
    const reflectionSave = player.querySelector('[data-mt-reflection-save]');
    const audioStateKey = 'mt_audio_state_v1';
    const momentsKey = 'mt_saved_moments_v1';
    const reflectionsKey = 'amt_saved_insights';
    let progressReported = new Set();
    let transcriptCues = [];
    let chapters = [];
    let activeCueIndex = -1;
    let activeChapterIndex = -1;
    let reflectionState = null;
    let resumeAfterReflection = false;
    const report = (name, metadata = {}) => window.dispatchEvent(new CustomEvent('mt:intelligence-event', {
      detail: { name, metadata: { episode_title: title.textContent.trim(), ...metadata } }
    }));

    const saveAudioState = () => {
      try {
        localStorage.setItem(audioStateKey, JSON.stringify({
          audio: audio.currentSrc || audio.src,
          title: title.textContent,
          time: audio.currentTime || 0,
          playing: !audio.paused,
          updated: Date.now()
        }));
      } catch (_) {}
    };

    const formatTime = (seconds) => {
      const value = Math.max(0, Math.floor(Number(seconds) || 0));
      const hours = Math.floor(value / 3600);
      const minutes = Math.floor((value % 3600) / 60);
      const remainder = value % 60;
      return hours ? `${hours}:${String(minutes).padStart(2, '0')}:${String(remainder).padStart(2, '0')}` : `${minutes}:${String(remainder).padStart(2, '0')}`;
    };

    const selectedEpisode = () => player.querySelector('[data-mt-episode].is-current') || player.querySelector('[data-mt-episode]');
    const momentRecord = () => {
      const episode = selectedEpisode();
      return {
        title: title.textContent.trim(),
        audio: audio.currentSrc || audio.src,
        permalink: episode ? episode.dataset.permalink || '' : '',
        time: Math.floor(audio.currentTime || 0),
        timeLabel: formatTime(audio.currentTime || 0),
        savedAt: Date.now()
      };
    };

    const parseClock = (value) => {
      const parts = String(value || '').trim().replace(',', '.').split(':').map(Number);
      if (parts.some((part) => Number.isNaN(part))) return 0;
      if (parts.length === 3) return parts[0] * 3600 + parts[1] * 60 + parts[2];
      if (parts.length === 2) return parts[0] * 60 + parts[1];
      return parts[0] || 0;
    };

    const parseVtt = (source) => String(source || '').replace(/^WEBVTT[^\n]*\n/i, '').split(/\n\s*\n/).map((block) => {
      const lines = block.trim().split(/\r?\n/);
      const timingIndex = lines.findIndex((line) => line.indexOf('-->') !== -1);
      if (timingIndex < 0) return null;
      const timing = lines[timingIndex].split('-->');
      const clean = document.createElement('div');
      clean.innerHTML = lines.slice(timingIndex + 1).join(' ').replace(/<v\s+([^>]+)>/gi, '<strong>$1:</strong> ');
      return { start: parseClock(timing[0]), end: parseClock(timing[1].trim().split(/\s+/)[0]), text: clean.textContent.trim() };
    }).filter((cue) => cue && cue.text);

    const renderTranscript = () => {
      transcriptRoot.innerHTML = '';
      transcriptCues.forEach((cue, index) => {
        const button = document.createElement('button');
        button.type = 'button';
        button.className = 'mt-living-transcript__cue';
        button.dataset.cueIndex = String(index);
        button.innerHTML = `<small>${formatTime(cue.start)}</small><span></span>`;
        button.querySelector('span').textContent = cue.text;
        button.addEventListener('click', () => { audio.currentTime = cue.start; audio.play().catch(() => {}); });
        transcriptRoot.appendChild(button);
      });
      transcriptPanel.hidden = transcriptCues.length === 0;
    };

    const loadLivingData = async (episode) => {
      transcriptCues = []; chapters = []; activeCueIndex = -1; activeChapterIndex = -1;
      transcriptPanel.hidden = true;
      chapterLabel.textContent = 'Now selected';
      if (!episode) return;
      if (episode.dataset.transcript) {
        try {
          const response = await fetch(episode.dataset.transcript, { credentials: 'omit' });
          if (response.ok) { transcriptCues = parseVtt(await response.text()); renderTranscript(); }
        } catch (_) { /* Transcript support is an enhancement, never a blocker. */ }
      }
      if (episode.dataset.chapters) {
        try {
          const response = await fetch(episode.dataset.chapters, { credentials: 'omit' });
          if (response.ok) {
            const payload = await response.json();
            chapters = Array.isArray(payload.chapters) ? payload.chapters.map((chapter) => ({ start: Number(chapter.startTime) || 0, title: String(chapter.title || '') })) : [];
          }
        } catch (_) { /* Chapter support is optional. */ }
      }
    };

    const setPanel = (expanded) => {
      panel.hidden = !expanded;
      launcher.setAttribute('aria-expanded', String(expanded));
      player.classList.toggle('is-open', expanded);
      if (expanded) close.focus();
      else launcher.focus();
    };

    launcher.addEventListener('click', () => setPanel(panel.hidden));
    close.addEventListener('click', () => setPanel(false));
    queueToggle.addEventListener('click', () => {
      const expanded = queue.hidden;
      queue.hidden = !expanded;
      queueToggle.setAttribute('aria-expanded', String(expanded));
      player.classList.toggle('has-queue', expanded);
    });

    player.querySelectorAll('[data-mt-episode]').forEach((episode) => {
      episode.addEventListener('click', async () => {
        player.querySelectorAll('[data-mt-episode]').forEach((item) => item.classList.remove('is-current'));
        episode.classList.add('is-current');
        audio.src = episode.dataset.audio;
        title.textContent = episode.dataset.title;
        progressReported = new Set();
        loadLivingData(episode);
        report('episode_discovered', { episode_id: episode.dataset.episodeId || '' });
        if ('mediaSession' in navigator) {
          navigator.mediaSession.metadata = new MediaMetadata({ title: episode.dataset.title, artist: 'Mirror Talk: Soulful Conversations' });
        }
        try { await audio.play(); } catch (_) { /* Browser keeps the selected episode ready. */ }
      });
    });

    try {
      const stored = JSON.parse(localStorage.getItem(audioStateKey) || '{}');
      if (stored.audio) {
        audio.src = stored.audio;
        title.textContent = stored.title || title.textContent;
        audio.addEventListener('loadedmetadata', () => {
          const time = Number(stored.time) || 0;
          if (time > 0) audio.currentTime = Math.min(time, audio.duration || time);
        }, { once: true });
      }
    } catch (_) { /* Keep the RSS-selected latest episode. */ }

    loadLivingData(selectedEpisode());

    if (saveMoment) saveMoment.addEventListener('click', () => {
      const moment = momentRecord();
      let moments = [];
      try { moments = JSON.parse(localStorage.getItem(momentsKey) || '[]'); } catch (_) {}
      if (!Array.isArray(moments)) moments = [];
      moments = moments.filter((item) => !(item.audio === moment.audio && Math.abs(Number(item.time || 0) - moment.time) < 5));
      moments.unshift(moment);
      try { localStorage.setItem(momentsKey, JSON.stringify(moments.slice(0, 50))); } catch (_) {}
      momentStatus.textContent = `Saved ${moment.title} at ${moment.timeLabel} privately on this device.`;
      report('living_mirror_moment_saved', { progress_bucket: Math.round((audio.currentTime / (audio.duration || 1)) * 100) });
    });

    const setReflectionMode = (active) => {
      player.classList.toggle('is-reflecting', active);
      reflectionWorkspace.hidden = !active;
      if (!active) {
        if (resumeAfterReflection) audio.play().catch(() => {});
        resumeAfterReflection = false;
      }
    };

    const normalizeReflectionPayload = (payload) => {
      const wrapped = payload && payload.data ? payload.data : payload;
      const data = wrapped && wrapped.data ? wrapped.data : wrapped || {};
      return {
        answer: String(data.answer || data.response || data.message || ''),
        followups: data.follow_up_questions || data.followups || data.suggested_questions || []
      };
    };

    const requestReflection = async (question, retry = true) => {
      const config = window.MirrorTalkLiving || {};
      const body = new URLSearchParams({ action: 'ask_mirror_talk', nonce: config.nonce || '', question });
      const response = await fetch(config.ajaxUrl, {
        method: 'POST', credentials: 'same-origin',
        headers: { 'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8' },
        body: body.toString()
      });
      const result = await response.json();
      if (!response.ok || !result.success) {
        const code = result && result.data && result.data.code;
        if (retry && code === 'nonce_expired') {
          const refreshBody = new URLSearchParams({ action: 'ask_mirror_talk_refresh_nonce' });
          const refreshed = await fetch(config.ajaxUrl, { method: 'POST', credentials: 'same-origin', body: refreshBody }).then((item) => item.json());
          if (refreshed.success && refreshed.data && refreshed.data.nonce) {
            config.nonce = refreshed.data.nonce;
            return requestReflection(question, false);
          }
        }
        throw new Error((result && result.data && result.data.message) || 'The reflection could not be created just now.');
      }
      return normalizeReflectionPayload(result);
    };

    const renderFollowups = (questions) => {
      reflectionFollowups.innerHTML = '';
      const choices = Array.isArray(questions) ? questions.slice(0, 3) : [];
      choices.forEach((question) => {
        const button = document.createElement('button');
        button.type = 'button';
        button.textContent = String(question);
        button.addEventListener('click', () => submitReflection(String(question), true));
        reflectionFollowups.appendChild(button);
      });
      reflectionFollowups.hidden = choices.length === 0;
    };

    const submitReflection = async (question, followup = false) => {
      reflectionAnswer.classList.add('is-loading');
      reflectionAnswer.textContent = followup ? 'Continuing your reflection…' : 'Listening to this moment and gathering a reflection…';
      reflectionFollowups.hidden = true;
      reflectionForm.hidden = true;
      reflectionSave.hidden = true;
      try {
        const result = await requestReflection(question);
        if (!result.answer) throw new Error('The reflection returned without an answer.');
        reflectionState = Object.assign({}, reflectionState || {}, { question, answer: result.answer, updatedAt: Date.now() });
        reflectionAnswer.textContent = result.answer;
        renderFollowups(result.followups);
        reflectionForm.hidden = false;
        reflectionSave.hidden = false;
        report(followup ? 'living_mirror_followup_answered' : 'living_mirror_reflection_answered');
      } catch (error) {
        reflectionAnswer.textContent = `${error.message} You can try again or return to listening.`;
        reflectionForm.hidden = false;
      } finally {
        reflectionAnswer.classList.remove('is-loading');
      }
    };

    if (reflectMoment) reflectMoment.addEventListener('click', () => {
      const moment = momentRecord();
      resumeAfterReflection = !audio.paused;
      audio.pause();
      reflectionState = { moment, createdAt: Date.now() };
      reflectionContext.textContent = `${moment.title} · ${moment.timeLabel}`;
      reflectionInput.value = '';
      reflectionSave.textContent = 'Save reflection';
      reflectionSave.disabled = false;
      setReflectionMode(true);
      const question = `I am listening to “${moment.title}” at ${moment.timeLabel}. What might this moment help me notice about my life and my next step?`;
      report('living_mirror_reflection_started', { progress_bucket: Math.round((audio.currentTime / (audio.duration || 1)) * 100) });
      submitReflection(question);
    });

    player.querySelectorAll('[data-mt-reflection-back]').forEach((button) => button.addEventListener('click', () => setReflectionMode(false)));

    if (reflectionForm) reflectionForm.addEventListener('submit', (event) => {
      event.preventDefault();
      const followup = reflectionInput.value.trim();
      if (!followup) return;
      const contextualQuestion = reflectionState && reflectionState.answer
        ? `A previous reflection said: “${reflectionState.answer.slice(0, 260)}” My follow-up question is: ${followup.slice(0, 180)}`
        : followup;
      reflectionInput.value = '';
      submitReflection(contextualQuestion, true);
    });

    if (reflectionSave) reflectionSave.addEventListener('click', () => {
      if (!reflectionState || !reflectionState.answer) return;
      let saved = [];
      try { saved = JSON.parse(localStorage.getItem(reflectionsKey) || '[]'); } catch (_) {}
      if (!Array.isArray(saved)) saved = [];
      saved.unshift(reflectionState);
      try { localStorage.setItem(reflectionsKey, JSON.stringify(saved.slice(0, 50))); } catch (_) {}
      reflectionSave.textContent = 'Saved privately';
      reflectionSave.disabled = true;
      report('living_mirror_reflection_saved');
    });

    document.addEventListener('mt:resume-moment', (event) => {
      const moment = event.detail || {};
      if (!moment.audio) return;
      audio.src = moment.audio;
      title.textContent = moment.title || 'Saved Mirror Talk moment';
      audio.addEventListener('loadedmetadata', () => {
        audio.currentTime = Math.min(Number(moment.time) || 0, audio.duration || Number(moment.time) || 0);
        audio.play().catch(() => {});
      }, { once: true });
      setPanel(true);
    });

    ['play', 'pause', 'timeupdate', 'ended'].forEach((eventName) => audio.addEventListener(eventName, saveAudioState));
    audio.addEventListener('play', () => {
      report('podcast_play');
      document.dispatchEvent(new CustomEvent('mt:podcast-play'));
    });
    audio.addEventListener('pause', () => { if (!audio.ended && audio.currentTime > 0) report('podcast_pause', { progress_bucket: Math.round((audio.currentTime / (audio.duration || 1)) * 100) }); });
    audio.addEventListener('timeupdate', () => {
      if (!audio.duration) return;
      const percent = audio.currentTime / audio.duration * 100;
      [25, 50, 75].forEach((bucket) => {
        if (percent >= bucket && !progressReported.has(bucket)) { progressReported.add(bucket); report('podcast_progress', { progress_bucket: bucket }); }
      });
      const cueIndex = transcriptCues.findIndex((cue) => audio.currentTime >= cue.start && audio.currentTime < cue.end);
      if (cueIndex !== activeCueIndex) {
        const previousCue = transcriptRoot.querySelector('.is-active');
        if (previousCue) previousCue.classList.remove('is-active');
        const cue = transcriptRoot.querySelector(`[data-cue-index="${cueIndex}"]`);
        if (cue) { cue.classList.add('is-active'); cue.scrollIntoView({ block: 'nearest', behavior: 'smooth' }); }
        activeCueIndex = cueIndex;
      }
      let chapterIndex = -1;
      chapters.forEach((chapter, index) => { if (audio.currentTime >= chapter.start) chapterIndex = index; });
      if (chapterIndex !== activeChapterIndex) {
        chapterLabel.textContent = chapterIndex >= 0 && chapters[chapterIndex].title ? chapters[chapterIndex].title : 'Now selected';
        activeChapterIndex = chapterIndex;
      }
    });
    audio.addEventListener('ended', () => report('podcast_complete', { progress_bucket: 100 }));
    if ('mediaSession' in navigator && typeof navigator.mediaSession.setActionHandler === 'function') {
      try {
        navigator.mediaSession.setActionHandler('play', () => audio.play());
        navigator.mediaSession.setActionHandler('pause', () => audio.pause());
        navigator.mediaSession.setActionHandler('seekbackward', (details) => { audio.currentTime = Math.max(0, audio.currentTime - (details.seekOffset || 15)); });
        navigator.mediaSession.setActionHandler('seekforward', (details) => { audio.currentTime = Math.min(audio.duration || Infinity, audio.currentTime + (details.seekOffset || 30)); });
      } catch (_) { /* Some browsers expose Media Session without all actions. */ }
    }
    if (popout) popout.addEventListener('click', () => {
      const shouldContinue = !audio.paused;
      saveAudioState();
      const windowPlayer = window.open(popout.dataset.playerUrl, 'mirrorTalkPlayer', 'popup,width=480,height=760,resizable=yes');
      if (windowPlayer) {
        audio.pause();
        const transferred = JSON.parse(localStorage.getItem(audioStateKey) || '{}');
        transferred.playing = shouldContinue;
        localStorage.setItem(audioStateKey, JSON.stringify(transferred));
        windowPlayer.focus();
      }
    });

    document.addEventListener('keydown', (event) => {
      if (event.key === 'Escape' && !panel.hidden) setPanel(false);
    });
  }

  // One contextual invitation, only after a reader has shown real engagement.
  const newsletter = document.querySelector('[data-mt-newsletter-dialog]');
  if (newsletter && document.body.classList.contains('single-post')) {
    const storageKey = 'mt_newsletter_invited_at_v1';
    const lastShown = Number(localStorage.getItem(storageKey) || 0);
    const cooldown = 21 * 24 * 60 * 60 * 1000;
    let timeReady = false;
    let depthReady = false;
    let shown = false;

    const consider = () => {
      if (shown || !timeReady || !depthReady || Date.now() - lastShown < cooldown) return;
      if (document.querySelector('dialog[open]') || (player && player.classList.contains('is-open'))) return;
      shown = true;
      localStorage.setItem(storageKey, String(Date.now()));
      openDialog(newsletter);
    };

    window.setTimeout(() => { timeReady = true; consider(); }, 45000);
    window.addEventListener('scroll', () => {
      const available = document.documentElement.scrollHeight - window.innerHeight;
      depthReady = available > 0 && window.scrollY / available >= 0.55;
      consider();
    }, { passive: true });
  }
})();
