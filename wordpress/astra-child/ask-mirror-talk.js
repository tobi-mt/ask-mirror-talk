(function() {
  'use strict';

  console.log('Ask Mirror Talk Widget v5.4.1 loaded');

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
  const exploreExpander = document.querySelector('#amt-explore-expander');
  const exploreToggle = document.querySelector('#amt-explore-toggle');
  const explorePanel = document.querySelector('#amt-explore-panel');
  const exploreIcons = document.querySelector('#amt-explore-icons');
  const journeyCard = document.querySelector('#amt-journey-card');
  const weeklyRecapCard = document.querySelector('#amt-weekly-recap');
  const streakRevivalCard = document.querySelector('#amt-streak-revival-card');
  const answerContext = document.querySelector('#amt-answer-context');
  const answerUtilities = document.querySelector('#amt-answer-utilities');
  const citationTrustNote = document.querySelector('#amt-citation-trust-note');

  if (!form) {
    console.warn('⚠️ Ask Mirror Talk form not found on this page');
    return;
  }

  // ─── API URL ────────────────────────────────────────────────
  const API_BASE = (AskMirrorTalk.apiUrl || 'https://ask-mirror-talk-production.up.railway.app');
  let lastShownCitations = [];

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
        console.log('✓ Nonce refreshed');
        return true;
      }
    } catch (e) {
      console.warn('Nonce refresh error:', e);
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
  function loadQuestionOfTheDay() {
    if (!qotdContainer) return;

    fetch(`${API_BASE}/api/question-of-the-day`)
      .then(res => res.json())
      .then(data => {
        if (!data.question) {
          qotdContainer.style.display = 'none';
          return;
        }

        qotdContainer.innerHTML = `
          <div class="amt-qotd-inner">
            <div class="amt-qotd-header">
              <span class="amt-qotd-badge">✨ Question of the Day</span>
              <span class="amt-qotd-theme">${escapeHtml(data.theme || '')}</span>
            </div>
            <p class="amt-qotd-text">"${escapeHtml(data.question)}"</p>
            <button type="button" class="amt-qotd-ask">Ask this →</button>
          </div>
        `;

        qotdContainer.querySelector('.amt-qotd-ask').addEventListener('click', () => {
          input.value = data.question;
          input.focus();
          qotdContainer.style.display = 'none';
          form.dispatchEvent(new Event('submit', { cancelable: true }));
        });

        qotdContainer.style.display = '';
      })
      .catch(err => {
        console.warn('Could not load Question of the Day:', err);
        qotdContainer.style.display = 'none';
      });
  }

  // ─── Auto-submit helper ──────────────────────────────────────
  // Used by both the URL ?autoask= path and the SW postMessage path.
  function autoSubmitQuestion(question) {
    if (!question || !form) return;
    // Don't fire a second concurrent request if one is already in-flight
    // (guards the postMessage fallback path for old iOS Safari < 15.4).
    if (submitBtn && submitBtn.disabled) return;
    input.value = question;
    // Hide the QOTD card so the answer takes centre stage
    if (qotdContainer) qotdContainer.style.display = 'none';
    // Scroll the form into view smoothly before firing
    form.scrollIntoView({ behavior: 'smooth', block: 'center' });
    // Short delay so the scroll completes and the page paint is visible
    setTimeout(() => {
      form.dispatchEvent(new Event('submit', { cancelable: true }));
    }, 300);
  }

  // ─── Handle ?autoask= URL param (notification click → new tab) ─
  (function checkAutoAsk() {
    const params = new URLSearchParams(window.location.search);
    const raw = params.get('autoask');
    // Cap length before any processing to prevent oversized input
    const question = raw ? raw.slice(0, 500) : null;
    if (question) {
      // Remove the param from the browser URL so sharing/refreshing doesn't re-fire
      const remainingParams = params.toString()
        .replace(/autoask=[^&]*&?/, '')
        .replace(/&$/, '');
      const cleanUrl = window.location.pathname +
        (remainingParams ? `?${remainingParams}` : '') +
        window.location.hash;
      history.replaceState(null, '', cleanUrl || window.location.pathname);

      // Wait for DOM to be fully ready then auto-submit
      if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', () => autoSubmitQuestion(question));
      } else {
        // Tiny delay to let the widget's own init finish
        setTimeout(() => autoSubmitQuestion(question), 100);
      }
    }
  })();

  // ─── Handle messages from service worker (already-open tab) ───
  if ('serviceWorker' in navigator) {
    // controllerchange fires natively when a new SW takes control — works on
    // iOS Safari PWA where client.navigate() and postMessage may be unreliable.
    // Guard: only reload if there was ALREADY a controller (i.e. an SW update
    // happened), not on the very first install.
    var _hadController = !!navigator.serviceWorker.controller;
    navigator.serviceWorker.addEventListener('controllerchange', function() {
      if (!_hadController) { _hadController = true; return; }
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
      } else if (event.data && event.data.type === 'NAVIGATE_TO_FORM') {
        // Midday motivation notification clicked while app was open — scroll
        // to the form and focus the input so the user can start typing.
        if (form) form.scrollIntoView({ behavior: 'smooth', block: 'center' });
        if (input) input.focus();
      } else if (event.data && event.data.type === 'SW_UPDATED') {
        // New service worker just activated and claimed this tab.
        // Reload so the page picks up freshly-cached JS/CSS instead of old
        // in-memory assets. Guard with sessionStorage to prevent reload loops.
        try {
          if (!sessionStorage.getItem('amt_sw_reloaded')) {
            sessionStorage.setItem('amt_sw_reloaded', '1');
            window.location.reload();
          }
        } catch (e) { window.location.reload(); }
      }
    });
  }

  loadQuestionOfTheDay();

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
            input.value = q;
            input.focus();
            form.dispatchEvent(new Event('submit', { cancelable: true }));
          });
          suggestionsList.appendChild(btn);
        });
        suggestionsContainer.style.display = '';
        updateExploreExpander();
      })
      .catch(err => {
        console.warn('Could not load suggested questions:', err);
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
              input.value = btn.dataset.q;
              input.focus();
              topicsContainer.style.display = 'none';
              form.dispatchEvent(new Event('submit', { cancelable: true }));
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
        console.warn('Could not load topics:', err);
        topicsContainer.style.display = 'none';
      });
  }

  loadTopics();

  // ─── Explore Expander ──────────────────────────────────────
  function updateExploreExpander() {
    if (!exploreExpander) return;
    const hasContent = (topicsContainer && topicsContainer.style.display !== 'none') ||
                       (suggestionsContainer && suggestionsContainer.style.display !== 'none');
    exploreExpander.style.display = hasContent ? '' : 'none';
  }

  if (exploreToggle && explorePanel) {
    exploreToggle.addEventListener('click', () => {
      const isOpen = exploreToggle.getAttribute('aria-expanded') === 'true';
      exploreToggle.setAttribute('aria-expanded', String(!isOpen));
      explorePanel.classList.toggle('amt-explore-panel--open', !isOpen);
    });
  }

  // ─── Follow-up Questions ────────────────────────────────────
  function showFollowUpQuestions(questions) {
    if (!followupsContainer || !followupsList || !questions || questions.length === 0) {
      if (followupsContainer) followupsContainer.style.display = 'none';
      return;
    }

    followupsList.innerHTML = '';
    questions.forEach(q => {
      const btn = document.createElement('button');
      btn.type = 'button';
      btn.className = 'amt-followup-btn';
      btn.textContent = q;
      btn.addEventListener('click', () => {
        input.value = q;
        input.focus();
        followupsContainer.style.display = 'none';
        form.dispatchEvent(new Event('submit', { cancelable: true }));
      });
      followupsList.appendChild(btn);
    });
    followupsContainer.style.display = '';
    // No auto-scroll to follow-ups — user is reading the answer from top to bottom.
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
  let lastDepthMessage = ''; // Track episode depth for display

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
          <div class="amt-shimmer-group">
            <div class="amt-shimmer"></div>
            <div class="amt-shimmer"></div>
            <div class="amt-shimmer"></div>
            <div class="amt-shimmer"></div>
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

  // Show error message with shake animation
  function showError(message) {
    responseContainer.style.display = '';
    requestAnimationFrame(() => responseContainer.classList.add('amt-visible'));
    responseContainer.classList.remove('amt-streaming', 'amt-loading-state');
    responseContainer.classList.add('error');
    output.innerHTML = `<p><strong>⚠️ ${message}</strong></p>`;
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
  function showInlinePlayer(citationItem, audioUrl, startSeconds, endSeconds, episodeTitle) {
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
          <a href="${audioUrl}#t=${startSeconds}" target="_blank" rel="noopener noreferrer" class="amt-player-external" title="Open in new tab">↗ Open</a>
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
    if (endSeconds && endSeconds > startSeconds) {
      audio.addEventListener('timeupdate', function checkEnd() {
        if (audio.currentTime >= endSeconds) {
          audio.pause();
          audio.removeEventListener('timeupdate', checkEnd);
        }
      });
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
        const matchBadgeHtml = index === 0
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
            if (url) {
              showInlinePlayer(li, url, start, end, title);
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
            previewBtn.title = 'Preview 30 seconds';
            previewBtn.innerHTML = '⏯ Preview 30s';
            previewBtn.addEventListener('click', (e) => {
              e.stopPropagation();
              const existingPreview = li.querySelector('.amt-preview-audio');
              if (existingPreview) {
                existingPreview.pause();
                existingPreview.remove();
                previewBtn.innerHTML = '⏯ Preview 30s';
                return;
              }
              // Stop any preview playing in another citation item
              document.querySelectorAll('.amt-preview-audio').forEach(otherAudio => {
                otherAudio.pause();
                const otherBtn = otherAudio.closest('.citation-item')?.querySelector('.citation-preview-btn');
                if (otherBtn) otherBtn.innerHTML = '⏯ Preview 30s';
                otherAudio.remove();
              });
              const previewAudio = document.createElement('audio');
              previewAudio.className = 'amt-preview-audio';
              previewAudio.style.display = 'none';
              previewAudio.src = audioUrl;
              li.appendChild(previewAudio);
              previewBtn.innerHTML = '⏹ Stop preview';
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
                  previewBtn.innerHTML = '⏯ Preview 30s';
                  previewAudio.removeEventListener('timeupdate', stopAt);
                }
              });
              previewAudio.addEventListener('ended', () => {
                previewAudio.remove();
                previewBtn.innerHTML = '⏯ Preview 30s';
              });
            });
            li.appendChild(previewBtn);
          }

          // "Explore this episode" button — links to full episode page
          if (podcastUrl) {
            const exploreBtn = document.createElement("a");
            exploreBtn.href = podcastUrl;
            exploreBtn.target = "_blank";
            exploreBtn.rel = "noopener noreferrer";
            exploreBtn.className = "citation-explore";
            exploreBtn.textContent = "Explore this episode ↗";
            li.appendChild(exploreBtn);
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
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), 60000);
    let response;
    try {
      response = await fetch(`${API_BASE}/ask/stream`, {
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
    lastDepthMessage = '';

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
            // Only capture the final depth message (e.g. "Drawing from 6 episodes…")
            // — not the initial "Searching episodes…" loading message.
            if (event.message && event.message.startsWith('Drawing from')) {
              lastDepthMessage = event.message;
            }
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

          if (event.type === 'done') {
            // Expose qa_log_id for analytics addon
            window._amtLastQALogId = event.qa_log_id;
            // Remove streaming class and add completion class for CSS animations
            responseContainer.classList.remove('amt-streaming');
            output.classList.add('amt-complete');

            // Show depth indicator (e.g. "Drawing from 6 episodes…")
            if (lastDepthMessage) {
              const depthEl = document.createElement('div');
              depthEl.className = 'amt-depth-indicator';
              depthEl.textContent = lastDepthMessage.replace('…', '');
              // Append after the response text, before share button
              output.appendChild(depthEl);
            }

            console.log('✅ Stream complete', {
              qa_log_id: event.qa_log_id,
              latency_ms: event.latency_ms,
              cached: event.cached || false
            });
            // Add share button, related questions, and SEO schema after answer is complete
            addShareButton(question, answerText);
            addSaveToEmailButton(question, answerText);
            showRelatedQuestions(event.qa_log_id);
            injectFAQSchema(question, answerText);
            finalizeAnswerPresentation(question, answerText, lastShownCitations, window._amtLastTheme || null);

            // Gamification: record the answered question
            onQuestionAnswered(question, window._amtLastTheme || null);
            window._amtLastTheme = null;

            // Conversation memory: append this turn
            appendConversationTurn(question, answerText);

            // Scroll response into view only if it's not already visible.
            // Using 'nearest' avoids yanking the user back if they've already scrolled down.
            setTimeout(() => {
              responseContainer.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
            }, 100);
          }
        } catch (parseErr) {
          console.warn('SSE parse error:', parseErr, jsonStr);
        }
      }
    }
    clearTimeout(timeoutId);
    return answerText;
  }

  // Show answer (used for non-streaming fallback)
  function showAnswer(answer, citationsList, followUpQuestions) {
    responseContainer.classList.remove('error', 'amt-streaming');
    
    let formattedAnswer = formatMarkdownToHtml(answer);
    const paragraphs = formattedAnswer.split('\n\n').filter(p => p.trim());
    const htmlParagraphs = paragraphs.map(p => {
      const trimmed = p.trim();
      if (trimmed.startsWith('<ol>') || trimmed.startsWith('<ul>')) return trimmed;
      return '<p>' + trimmed.replace(/\n/g, '<br>') + '</p>';
    });
    output.innerHTML = htmlParagraphs.join('');

    showCitations(citationsList);
    showFollowUpQuestions(followUpQuestions);

    // Add share button and SEO schema
    const questionText = input.value.trim();
    addShareButton(questionText, answer);
    addSaveToEmailButton(questionText, answer);
    injectFAQSchema(questionText, answer);
    finalizeAnswerPresentation(questionText, answer, citationsList);

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

  function truncateText(text, maxLen) {
    const value = String(text || '').trim();
    if (value.length <= maxLen) return value;
    return value.slice(0, Math.max(0, maxLen - 1)).trimEnd() + '…';
  }

  function getThemeStarter(theme) {
    return THEME_STARTERS[theme] || `What does Mirror Talk say about ${String(theme || 'this theme').toLowerCase()}?`;
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
      ['Inner peace', ['peace', 'calm', 'stillness']],
      ['Communication', ['conversation', 'communicate', 'conflict', 'hard talk']],
      ['Empowerment', ['voice', 'speak up', 'confidence', 'empower']],
      ['Transition', ['transition', 'change', 'new season', 'move on']],
      ['Self-worth', ['worthy', 'worth', 'comparison', 'confidence']],
      ['Faith', ['faith', 'god', 'spiritual']],
      ['Community', ['community', 'belonging', 'support system']]
    ];

    for (const [theme, keywords] of themeKeywords) {
      if (keywords.some(keyword => haystack.includes(keyword))) return theme;
    }

    return null;
  }

  function extractInsightExcerpt(answerText) {
    const clean = String(answerText || '')
      .replace(/\s+/g, ' ')
      .replace(/^\s+|\s+$/g, '');
    if (!clean) return '';

    const sentences = clean.match(/[^.!?]+[.!?]+/g) || [];
    const candidate = sentences.find(sentence => sentence.trim().length >= 70) || sentences[0] || clean;
    return truncateText(candidate.trim(), 210);
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

  function updateCitationTrustNote(citationsList) {
    if (!citationTrustNote) return;
    const count = Array.isArray(citationsList) ? citationsList.length : 0;

    if (!count) {
      citationTrustNote.innerHTML = '';
      citationTrustNote.style.display = 'none';
      return;
    }

    citationTrustNote.innerHTML = `
      <div class="amt-citation-trust-copy">
        <strong>${count} referenced episode${count === 1 ? '' : 's'}</strong>
        <span>The strongest match appears first. Tap <em>Preview 30s</em> to hear the exact moment behind the answer.</span>
      </div>
    `;
    citationTrustNote.style.display = '';
  }

  function renderAnswerContext(question, answerText, citationsList) {
    if (!answerContext) return;

    const theme = inferTheme(question, answerText);
    const citationCount = Array.isArray(citationsList) ? citationsList.length : 0;
    const trustSummary = citationCount > 0
      ? `${citationCount} episode reference${citationCount === 1 ? '' : 's'} anchored this reflection`
      : 'Reflective answer drawn from the Mirror Talk library';
    const contextSummary = lastDepthMessage
      ? lastDepthMessage.replace('…', '')
      : (citationCount > 0
          ? 'Use the references below to preview the exact moments behind this answer.'
          : 'Ask a follow-up if you want us to explore a narrower angle.');

    answerContext.innerHTML = `
      <div class="amt-answer-context-copy">
        <span class="amt-answer-context-kicker">Grounded Reflection</span>
        <p class="amt-answer-context-summary">${escapeHtml(trustSummary)}.</p>
        <p class="amt-answer-context-detail">${escapeHtml(contextSummary)}</p>
      </div>
      <div class="amt-answer-context-pills">
        ${theme ? `<span class="amt-answer-pill">${escapeHtml(theme)}</span>` : ''}
        <span class="amt-answer-pill">${citationCount > 0 ? 'Timestamped cues' : 'Reflective guidance'}</span>
      </div>
    `;
    answerContext.style.display = '';
  }

  function saveLastSession(question, answer, themeHint) {
    const theme = themeHint || inferTheme(question, answer) || '';
    const excerpt = extractInsightExcerpt(answer);
    saveLastSessionRecord({
      question,
      answer: answer.substring(0, 2000),
      excerpt,
      theme,
      time: Date.now(),
    });
  }

  function finalizeAnswerPresentation(question, answerText, citationsList, themeHint) {
    const theme = themeHint || inferTheme(question, answerText);
    saveLastSession(question, answerText, theme);
    renderAnswerContext(question, answerText, citationsList);
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
    const nextTheme = unexploredThemes[0] || lastTheme || AMT_THEMES[0];
    const continueQuestion = lastQ || getThemeStarter(lastTheme || nextTheme);
    const continueLabel = lastQ ? 'Continue where you left off' : 'Pick up your reflection';
    const continueExcerpt = extractInsightExcerpt(lastA);
    const nextPrompt = getThemeStarter(nextTheme);
    const continuityLine = lastTheme
      ? `Last time you explored ${lastTheme}.`
      : `You have explored ${stats.themesExplored.size} theme${stats.themesExplored.size === 1 ? '' : 's'} so far.`;
    const timeLine = lastTime ? `Last visit ${formatRelativeTime(lastTime)}.` : '';

    journeyCard.innerHTML = `
      <div class="amt-journey-card-inner">
        <div class="amt-journey-card-copy">
          <span class="amt-journey-kicker">Continue your reflection</span>
          <h3 class="amt-journey-title">${escapeHtml(continueLabel)}</h3>
          <p class="amt-journey-text">${escapeHtml(continuityLine)} ${escapeHtml(timeLine)}</p>
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
        input.value = btn.dataset.q || '';
        input.focus();
        form.scrollIntoView({ behavior: 'smooth', block: 'center' });
        setTimeout(() => form.dispatchEvent(new Event('submit', { cancelable: true })), 180);
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

  // ========================================
  // Rating (Thumbs Up / Down)
  // ========================================
  // Share Button
  // ========================================

  function addShareButton(question, answer) {
    addShareButtonV2(question, answer);
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
    if (!question) {
      showError("Please enter a question.");
      return;
    }
    if (question.length < 3) {
      showError("Please enter a more detailed question.");
      return;
    }

    setLoading(true);

    try {
      // Try SSE streaming first
      await askStreaming(question);
    } catch (streamError) {
      console.warn('SSE streaming failed, falling back to /ask:', streamError);
      responseContainer.classList.remove('amt-streaming');

      // Fallback: non-streaming via WordPress AJAX or direct API
      try {
        const result = await askWithRetry(question);
        if (!result.success) {
          throw new Error(result.data?.message || "The service couldn't process your question.");
        }
        const data = result.data;
        if (!data.answer) throw new Error("No answer received from the service.");
        showAnswer(data.answer, data.citations || [], data.follow_up_questions || []);
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
      setLoading(false);
    }
  });

  // ========================================
  // Fallback: Non-streaming requests
  // ========================================

  async function askWithRetry(question, retried = false) {
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
    const apiUrl = API_BASE + '/ask';

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

  renderJourneyCard();

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
    console.log('[PWA] App installed successfully');
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
  // Push Notifications — Daily QOTD & New Episodes
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
            <strong>🔔 Notifications need Safari on iOS</strong>
            <span>Push notifications require the app to be installed as a PWA, which only works via <strong>Safari</strong> on iPhone and iPad. Open this page in Safari, then tap <strong>Share ⎋ → Add to Home Screen</strong>.</span>
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
            <strong>🔔 Want daily wisdom from Mirror Talk?</strong>
            <span>To receive notifications on iOS, first add this app to your home screen: tap <strong>Share</strong> <span style="font-size:1.2em">⎋</span> then <strong>"Add to Home Screen"</strong>, then open it from there to enable alerts.</span>
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
            <strong>🔔 Notifications require iOS 16.4+</strong>
            <span>Your iOS version does not support push notifications for web apps. Please update your iPhone/iPad to iOS 16.4 or later in Settings > General > Software Update.</span>
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
            <strong>🔔 Notifications are blocked</strong>
            <span>To enable notifications, click the 🔒 or ⓘ icon in your address bar, then change notification permissions to "Allow".</span>
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
          <strong>🔔 Get daily wisdom from Mirror Talk</strong>
          <span>Receive the Question of the Day and new episode alerts</span>
        </div>
        <div class="amt-notif-actions">
          <button class="amt-notif-enable" type="button">Enable</button>
          <button class="amt-notif-dismiss" type="button" aria-label="Not now">Not now</button>
        </div>
      </div>
      <div class="amt-notif-prefs" style="display:none;">
        <button class="amt-notif-back" type="button" aria-label="Go back">← Back</button>
        <label class="amt-notif-pref">
          <input type="checkbox" id="amt-notif-qotd" checked>
          <span>✨ Daily Question of the Day</span>
        </label>
        <label class="amt-notif-pref">
          <input type="checkbox" id="amt-notif-midday" checked>
          <span>💡 Midday motivation boost</span>
        </label>
        <label class="amt-notif-pref">
          <input type="checkbox" id="amt-notif-episodes" checked>
          <span>🎙️ New episode alerts</span>
        </label>
        <button class="amt-notif-save" type="button">Save & Enable</button>
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
            <span>✅ Notifications enabled! You'll receive daily wisdom from Mirror Talk.</span>
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
          errorMsg = 'Push notifications are being set up and will be available soon. Please check back later!';
        } else {
          errorMsg = 'Unable to enable notifications. Please try again later.';
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

      // Subscribe to push
      const subscription = await registration.pushManager.subscribe({
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
          // Bell is already shown by initNotifManageBtn, just ensure it's visible
          const bellBtn = document.getElementById('amt-notif-manage-btn');
          if (bellBtn) bellBtn.style.display = '';
        } catch (e) {}
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
      if (!subscription) return false;
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
      return res.ok;
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
  }

  function renderNotificationPrefsPanel(panel) {
    panel.innerHTML = `
      <p class="amt-nmp-heading">🔔 Notification settings</p>
      <div class="amt-nmp-prefs">
        <label class="amt-nmp-pref">
          <input type="checkbox" id="amt-nmp-qotd" checked>
          <span>☀️ Question of the Day <em class="amt-nmp-pref-desc">Daily morning nudge at 8 AM</em></span>
        </label>
        <label class="amt-nmp-pref">
          <input type="checkbox" id="amt-nmp-midday" checked>
          <span>🌤 Midday Motivation <em class="amt-nmp-pref-desc">A brief encouragement at noon</em></span>
        </label>
        <label class="amt-nmp-pref">
          <input type="checkbox" id="amt-nmp-episodes" checked>
          <span>🎙️ New Episode Alerts <em class="amt-nmp-pref-desc">When a new podcast episode is added</em></span>
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
        const err = document.createElement('span');
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
        retain.innerHTML = '<p class="amt-nmp-unsub-msg">You\'ve been unsubscribed. You can always re-enable notifications from the settings bell.</p>';
        // Hide the bell button — no longer subscribed
        const bellBtn = document.getElementById('amt-notif-manage-btn');
        setTimeout(() => {
          panel.style.display = 'none';
          if (bellBtn) {
            bellBtn.style.display = 'none';
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
    
    // Show bell for all users (subscribed or not)
    // If not subscribed, clicking will show the opt-in prompt
    // If subscribed, clicking will show the management panel
    const isStandalone = window.matchMedia('(display-mode: standalone)').matches ||
                         window.navigator.standalone === true;
    const hasStatsBar = document.getElementById('amt-stats-bar');
    
    // Show bell if user has visited before OR is in standalone mode (PWA installed)
    try {
      const lastSession = loadLastSession();
      const hasVisited = !!(lastSession && lastSession.question);
      if ((hasVisited || isStandalone) && hasStatsBar) {
        btn.style.display = '';
      }
    } catch (e) {}
    
    btn.addEventListener('click', () => {
      console.log('[Bell] Notification bell clicked');
      try {
        const isSubscribed = _loadMirroredFlag('amt_push_subscribed', PUSH_SUBSCRIBED_COOKIE_KEY);
        console.log('[Bell] Subscribed status:', isSubscribed);
        if (isSubscribed) {
          // User is subscribed — show management panel
          toggleNotificationManagePanel();
        } else {
          // User is not subscribed — show opt-in prompt (pass 'fromBell' to bypass dismissal checks)
          console.log('[Bell] Showing notification opt-in');
          showNotificationOptIn('fromBell');
        }
      } catch (e) {
        console.error('[Bell] Error:', e);
        // Fallback to showing opt-in
        showNotificationOptIn('fromBell');
      }
    });
  })();

  // Show notification opt-in after a delay.
  // For returning visitors: show after 5 seconds.
  // For new visitors: show after 15 seconds (give them time to explore first).
  // The install banner is separate and handled by 'beforeinstallprompt'.
  setTimeout(() => {
    try {
      const alreadySubscribed = _loadMirroredFlag('amt_push_subscribed', PUSH_SUBSCRIBED_COOKIE_KEY);

      if (!alreadySubscribed) {
        showNotificationOptIn();
      }
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
      savedAt: Number((entry && entry.savedAt) || Date.now()),
    }));
    try { localStorage.setItem('amt_reflect_notes', JSON.stringify(allNotes)); } catch (e) {}
    try { _cookieSet(REFLECTION_NOTES_COOKIE_KEY, JSON.stringify(backup), 365); } catch (e) {}
  }

  function loadStats() {
    try {
      const raw = localStorage.getItem('amt_gamification') || _cookieGet('amt_gx');
      if (raw) {
        const parsed = JSON.parse(raw);
        parsed.themesExplored = new Set(parsed.themesExplored || []);
        parsed.earnedBadges   = new Set(parsed.earnedBadges   || []);
        // Cookie recovery: re-hydrate localStorage so future writes work normally
        if (!localStorage.getItem('amt_gamification')) {
          try { localStorage.setItem('amt_gamification', raw); } catch (e) {}
        }
        return parsed;
      }
    } catch (e) {}
    return {
      totalQuestions:   0,
      currentStreak:    0,
      maxStreak:        0,
      lastActiveDate:   null,   // 'YYYY-MM-DD'
      themesExplored:   new Set(),
      earnedBadges:     new Set(),
      citationsClicked: 0,
      sharesCount:      0,
      insightsSaved:    0,
      lastReviveDate:   null,
      nightOwl:         false,
      dailyQuestions:   0,      // questions asked on lastSessionDate
      lastSessionDate:  null,   // 'YYYY-MM-DD' — tracks which day dailyQuestions counts
    };
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
      input.focus();
      form.scrollIntoView({ behavior: 'smooth', block: 'center' });
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

  function buildWeeklyRecapShareCard(recap) {
    const data = recap || getWeeklyRecapData();
    if (!data) return null;

    const W = 1200;
    const H = 1500;
    const canvas = document.createElement('canvas');
    canvas.width = W;
    canvas.height = H;
    const ctx = canvas.getContext('2d');

    const grad = ctx.createLinearGradient(0, 0, W, H);
    grad.addColorStop(0, '#eef8f5');
    grad.addColorStop(0.55, '#e4f1ed');
    grad.addColorStop(1, '#dbe8e4');
    ctx.fillStyle = grad;
    ctx.fillRect(0, 0, W, H);

    ctx.fillStyle = 'rgba(48,84,77,0.03)';
    for (let i = 0; i < 3200; i++) {
      ctx.fillRect(Math.random() * W, Math.random() * H, 1.5, 1.5);
    }

    ctx.strokeStyle = 'rgba(72,119,111,0.24)';
    ctx.lineWidth = 4;
    _roundRect(ctx, 44, 44, W - 88, H - 88, 30);
    ctx.stroke();

    ctx.fillStyle = '#48776f';
    ctx.font = '600 30px Georgia, serif';
    ctx.textAlign = 'center';
    ctx.fillText('ASK MIRROR TALK', W / 2, 126);

    ctx.fillStyle = '#2e2a24';
    ctx.font = '700 68px Georgia, serif';
    const headline = data.topTheme
      ? `This week I kept returning to ${data.topTheme}.`
      : 'This week I kept returning to reflection.';
    wrapCanvasText(ctx, headline, 150, 238, 900, 86, 4);

    const metrics = [
      { label: 'Questions', value: data.questionCount },
      { label: 'Saved', value: data.savedCount },
      { label: 'Shared', value: data.shareCount }
    ];
    const cardY = 520;
    const cardW = 250;
    const gap = 28;
    const startX = (W - (metrics.length * cardW + (metrics.length - 1) * gap)) / 2;
    metrics.forEach((metric, index) => {
      const x = startX + index * (cardW + gap);
      ctx.fillStyle = 'rgba(255,255,255,0.72)';
      _roundRect(ctx, x, cardY, cardW, 150, 24);
      ctx.fill();
      ctx.strokeStyle = 'rgba(72,119,111,0.18)';
      ctx.lineWidth = 2;
      _roundRect(ctx, x, cardY, cardW, 150, 24);
      ctx.stroke();

      ctx.fillStyle = '#48776f';
      ctx.font = '700 18px -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif';
      ctx.textAlign = 'center';
      ctx.fillText(metric.label.toUpperCase(), x + (cardW / 2), cardY + 42);

      ctx.fillStyle = '#2e2a24';
      ctx.font = '700 62px Georgia, serif';
      ctx.fillText(String(metric.value), x + (cardW / 2), cardY + 106);
    });

    ctx.fillStyle = 'rgba(255,255,255,0.82)';
    _roundRect(ctx, 108, 758, W - 216, 458, 34);
    ctx.fill();
    ctx.strokeStyle = 'rgba(72,119,111,0.18)';
    ctx.lineWidth = 2;
    _roundRect(ctx, 108, 758, W - 216, 458, 34);
    ctx.stroke();

    const subline = data.strongestDayCount >= 3
      ? `Strongest day: ${data.strongestDayCount} moments of reflection`
      : 'Small consistent returns are building momentum';
    ctx.fillStyle = '#48776f';
    ctx.font = '600 24px -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif';
    ctx.textAlign = 'center';
    ctx.fillText(subline, W / 2, 826);

    if (data.latestSavedInsight) {
      ctx.fillStyle = '#355750';
      ctx.font = '82px Georgia, serif';
      ctx.textAlign = 'left';
      ctx.fillText('“', 160, 920);

      ctx.fillStyle = '#2e2a24';
      ctx.font = '500 40px Georgia, serif';
      wrapCanvasText(ctx, data.latestSavedInsight.excerpt, 160, 970, W - 320, 58, 5);
    }

    ctx.fillStyle = '#2e2a24';
    ctx.font = '600 30px Georgia, serif';
    ctx.textAlign = 'center';
    ctx.fillText('mirrortalkpodcast.com/ask-mirror-talk', W / 2, 1328);

    ctx.fillStyle = '#48776f';
    ctx.font = '500 22px -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif';
    ctx.fillText('A week of reflection, saved and shared through Mirror Talk.', W / 2, 1372);

    return canvas.toDataURL('image/png');
  }

  function shareWeeklyRecapArtifact(recap) {
    const data = recap || getWeeklyRecapData();
    if (!data) return;

    const dataUrl = buildWeeklyRecapShareCard(data);
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

    weeklyRecapCard.innerHTML = `
      <div class="amt-weekly-recap-inner">
        <div class="amt-weekly-recap-copy">
          <span class="amt-weekly-recap-kicker">Weekly recap</span>
          <h3 class="amt-weekly-recap-title">${recap.topTheme ? `You kept returning to ${escapeHtml(recap.topTheme)}.` : 'Your reflection rhythm is taking shape.'}</h3>
          <p class="amt-weekly-recap-text">${recap.questionCount} question${recap.questionCount === 1 ? '' : 's'} asked, ${recap.savedCount} insight${recap.savedCount === 1 ? '' : 's'} saved, ${recap.shareCount} reflection${recap.shareCount === 1 ? '' : 's'} shared in the last 7 days.</p>
          <p class="amt-weekly-recap-subtext">${recap.strongestDayCount >= 3 ? `Your strongest day held ${recap.strongestDayCount} moments of reflection.` : 'Small consistent returns are building momentum.'}</p>
          ${recap.latestSavedInsight ? `<p class="amt-weekly-recap-quote">“${escapeHtml(recap.latestSavedInsight.excerpt)}”</p>` : ''}
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
        input.value = primaryBtn.dataset.q || recap.recapPrompt;
        input.focus();
        form.scrollIntoView({ behavior: 'smooth', block: 'center' });
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

  function renderStatsBar(stats) {
    const bar = document.getElementById('amt-stats-bar');
    if (!bar) return;

    document.getElementById('amt-streak-value').textContent   = stats.currentStreak;
    document.getElementById('amt-questions-value').textContent = stats.totalQuestions;
    document.getElementById('amt-themes-value').textContent   = stats.themesExplored.size;
    document.getElementById('amt-badge-count').textContent    = stats.earnedBadges.size;

    // Update streak count inside the dark-mode toggle pill
    const toggleStreak = document.getElementById('amt-toggle-streak');
    if (toggleStreak) {
      if (stats.currentStreak >= 1) {
        toggleStreak.textContent = '\uD83D\uDD25' + stats.currentStreak;
        toggleStreak.style.display = '';
      } else {
        toggleStreak.style.display = 'none';
      }
    }

    // Pulse the streak icon when streak > 0
    const streakIcon = bar.querySelector('.amt-stat-streak .amt-stat-icon');
    if (streakIcon) {
      streakIcon.classList.toggle('amt-streak-active', stats.currentStreak >= 3);
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
      <span class="amt-stats-prompt-kicker">Next up</span>
      <span class="amt-stats-prompt-text">${escapeHtml(getDailyMomentumText(stats))}</span>
    `;
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
      const open = badgeShelf.style.display !== 'none';
      badgeShelf.style.display = open ? 'none' : '';
      if (!open) renderBadgeShelf(loadStats());
    });
  }

  // Track citation clicks for the Deep Diver badge
  document.addEventListener('click', (e) => {
    if (e.target.closest('.citation-link') || e.target.closest('.citation-explore')) {
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
    try {
      if (localStorage.getItem('amt_onboarded')) return;
      
      // Skip onboarding if page was just reloaded by service worker
      if (sessionStorage.getItem('amt_sw_reloaded')) {
        // If we're reloading from SW and onboarding was in progress, mark as complete
        if (localStorage.getItem('amt_onboarding_started')) {
          localStorage.setItem('amt_onboarded', '1');
          localStorage.removeItem('amt_onboarding_started');
        }
        return;
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

    // Show after a short delay so the page renders first
    setTimeout(() => renderStep(0), 800);
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
    const isStandalone = window.matchMedia('(display-mode: standalone)').matches ||
                         window.navigator.standalone === true;
    // Show stats bar if user has asked questions OR is in standalone/PWA mode
    if (initStats.totalQuestions > 0 || isStandalone) {
      renderStatsBar(initStats);
      // Restore daily-depth glow if the user already hit ≥ 3 questions today
      const questionsIcon = document.querySelector('.amt-stat-questions .amt-stat-value');
      const isToday = initStats.lastSessionDate === todayStr();
      if (questionsIcon && isToday && (initStats.dailyQuestions || 0) >= 3) {
        questionsIcon.classList.add('amt-questions-active');
      }
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
  function buildShareCard(badge, stats, type) {
    const W = 1200, H = 630;
    const canvas = document.createElement('canvas');
    canvas.width  = W;
    canvas.height = H;
    const ctx = canvas.getContext('2d');

    // ── Background gradient ──
    const grad = ctx.createLinearGradient(0, 0, W, H);
    grad.addColorStop(0,   '#1a1410');
    grad.addColorStop(0.5, '#2d2318');
    grad.addColorStop(1,   '#1a1410');
    ctx.fillStyle = grad;
    ctx.fillRect(0, 0, W, H);

    // ── Subtle grain texture overlay ──
    ctx.fillStyle = 'rgba(255,255,255,0.015)';
    for (let i = 0; i < 4000; i++) {
      ctx.fillRect(
        Math.random() * W,
        Math.random() * H,
        Math.random() < 0.5 ? 1 : 2,
        1
      );
    }

    // ── Gold accent border ──
    ctx.strokeStyle = '#c9a84c';
    ctx.lineWidth = 4;
    ctx.strokeRect(20, 20, W - 40, H - 40);

    // ── Inner corner accents ──
    const accentLen = 40;
    ctx.lineWidth = 2;
    ctx.strokeStyle = 'rgba(201,168,76,0.4)';
    [[24, 24], [W - 24 - accentLen, 24], [24, H - 24 - accentLen], [W - 24 - accentLen, H - 24 - accentLen]].forEach(([x, y]) => {
      ctx.strokeRect(x, y, accentLen, accentLen);
    });

    // ── Branding ──
    ctx.textAlign = 'center';
    ctx.fillStyle = '#c9a84c';
    ctx.font = 'bold 22px Georgia, serif';
    ctx.fillText('MIRROR TALK', W / 2, 80);
    ctx.fillStyle = 'rgba(255,255,255,0.35)';
    ctx.font = '14px Georgia, serif';
    ctx.fillText('mirrortalkpodcast.com/ask-mirror-talk', W / 2, 105);

    if (type === 'badge' && badge) {
      // ── Big emoji ──
      ctx.font = '120px serif';
      ctx.textAlign = 'center';
      ctx.fillText(badge.emoji, W / 2, 310);

      // ── Badge name ──
      ctx.fillStyle = '#f5e6c8';
      ctx.font = 'bold 56px Georgia, serif';
      ctx.fillText(badge.name, W / 2, 390);

      // ── Subtitle ──
      ctx.fillStyle = 'rgba(245,230,200,0.65)';
      ctx.font = '26px Georgia, serif';
      ctx.fillText(badge.desc, W / 2, 438);

      // ── Unlocked pill ──
      const pillW = 240, pillH = 40, pillX = (W - pillW) / 2, pillY = 468;
      ctx.fillStyle = 'rgba(201,168,76,0.18)';
      _roundRect(ctx, pillX, pillY, pillW, pillH, 20);
      ctx.fill();
      ctx.strokeStyle = '#c9a84c';
      ctx.lineWidth = 1.5;
      _roundRect(ctx, pillX, pillY, pillW, pillH, 20);
      ctx.stroke();
      ctx.fillStyle = '#c9a84c';
      ctx.font = 'bold 16px Georgia, serif';
      ctx.textAlign = 'center';
      ctx.fillText('✨  BADGE UNLOCKED', W / 2, pillY + 26);

    } else if (type === 'streak') {
      ctx.font = '120px serif';
      ctx.textAlign = 'center';
      ctx.fillText('🔥', W / 2, 310);

      ctx.fillStyle = '#f7c948';
      ctx.font = `bold 100px Georgia, serif`;
      ctx.fillText(`${stats.currentStreak}`, W / 2, 415);

      ctx.fillStyle = '#f5e6c8';
      ctx.font = 'bold 40px Georgia, serif';
      ctx.fillText('DAY STREAK', W / 2, 467);

      ctx.fillStyle = 'rgba(245,230,200,0.55)';
      ctx.font = '24px Georgia, serif';
      ctx.fillText('Keep the wisdom flowing 🌊', W / 2, 510);

    } else {
      // ── Progress card ──
      ctx.font = '90px serif';
      ctx.textAlign = 'center';
      ctx.fillText('🌱', W / 2, 285);

      ctx.fillStyle = '#f5e6c8';
      ctx.font = 'bold 40px Georgia, serif';
      ctx.fillText('My Mirror Talk Journey', W / 2, 355);

      const cols = [
        { label: 'Questions', value: stats.totalQuestions },
        { label: 'Day Streak', value: stats.currentStreak },
        { label: 'Themes',    value: stats.themesExplored.size },
        { label: 'Badges',    value: stats.earnedBadges.size },
      ];
      const cellW = 220, startX = (W - cols.length * cellW) / 2;
      cols.forEach((col, i) => {
        const cx = startX + i * cellW + cellW / 2;
        const cy = 420;
        ctx.fillStyle = 'rgba(201,168,76,0.12)';
        _roundRect(ctx, cx - 90, cy - 55, 180, 110, 12);
        ctx.fill();
        ctx.strokeStyle = 'rgba(201,168,76,0.35)';
        ctx.lineWidth = 1;
        _roundRect(ctx, cx - 90, cy - 55, 180, 110, 12);
        ctx.stroke();
        ctx.fillStyle = '#f7c948';
        ctx.font = 'bold 44px Georgia, serif';
        ctx.textAlign = 'center';
        ctx.fillText(String(col.value), cx, cy + 10);
        ctx.fillStyle = 'rgba(245,230,200,0.55)';
        ctx.font = '18px Georgia, serif';
        ctx.fillText(col.label, cx, cy + 40);
      });
    }

    // ── Footer CTA ──
    ctx.textAlign = 'center';
    ctx.fillStyle = 'rgba(255,255,255,0.25)';
    ctx.font = '18px Georgia, serif';
    ctx.fillText('Ask your own questions at mirrortalkpodcast.com/ask-mirror-talk', W / 2, H - 38);

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

  function showShareModal(dataUrl, caption, options) {
    const modalOptions = options || {};
    const modalTitle = modalOptions.title || 'Share your achievement';
    const modalHint = modalOptions.hint || 'Platform buttons download the image first — then attach it to your post.';
    const downloadName = modalOptions.filename || 'mirror-talk-achievement.png';

    // Remove any existing modal
    const existing = document.getElementById('amt-share-card-modal');
    if (existing) existing.remove();

    const pageUrl = 'https://mirrortalkpodcast.com/ask-mirror-talk';
    const shareText = caption + '\n\n' + pageUrl;
    const encodedText = encodeURIComponent(shareText);
    const encodedUrl  = encodeURIComponent(pageUrl);

    // Detect Web Share API with file support (best path — native OS share sheet)
    const canNativeShare = !!(navigator.canShare);

    const nativeShareBtn = canNativeShare
      ? `<button class="amt-scm-btn amt-scm-native" id="amt-scm-native-btn">
           📲 Share with image
         </button>`
      : '';
    const divider = canNativeShare
      ? `<div class="amt-scm-divider"><span>or share to a specific platform</span></div>`
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
        <img class="amt-scm-preview" src="${dataUrl}" alt="Share card preview" />
        <p class="amt-scm-hint">${escapeHtml(modalHint)}</p>
        <div class="amt-scm-buttons">
          ${nativeShareBtn}
          <a class="amt-scm-btn amt-scm-download" href="${dataUrl}" download="${escapeHtml(downloadName)}">
            ⬇️ Download image
          </a>
          ${divider}
          <button class="amt-scm-btn amt-scm-twitter" data-url="https://twitter.com/intent/tweet?text=${encodedText}">
            𝕏 Twitter / X
          </button>
          <button class="amt-scm-btn amt-scm-facebook" data-url="https://www.facebook.com/sharer/sharer.php?u=${encodedUrl}">
            📘 Facebook
          </button>
          <button class="amt-scm-btn amt-scm-whatsapp" data-url="https://wa.me/?text=${encodedText}">
            💬 WhatsApp
          </button>
          <button class="amt-scm-btn amt-scm-instagram">
            📸 Instagram
          </button>
          <button class="amt-scm-btn amt-scm-copy">
            📋 Copy text
          </button>
        </div>
        <p class="amt-scm-platform-note" style="display:none;"></p>
      </div>
    `;

    document.body.appendChild(modal);
    requestAnimationFrame(() => modal.classList.add('amt-scm-visible'));

    const note = modal.querySelector('.amt-scm-platform-note');
    let hasTrackedShare = false;

    function markShareComplete() {
      if (hasTrackedShare) return;
      hasTrackedShare = true;
      trackRewardEvent('share');
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
          const file = await _dataUrlToFile(dataUrl, downloadName);
          if (navigator.canShare({ files: [file] })) {
            await navigator.share({ files: [file], text: caption, url: pageUrl });
            markShareComplete();
          } else {
            // canShare exists but files not supported — fall back to text-only share
            await navigator.share({ text: shareText });
            markShareComplete();
          }
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

    // ── Twitter / X ───────────────────────────────────────────────────────
    modal.querySelector('.amt-scm-twitter').addEventListener('click', function() {
      downloadThenOpen(
        this.dataset.url,
        '📥 Image saved! Attach it to your tweet — Twitter doesn\'t support auto-upload from web.'
      );
    });

    // ── Facebook ──────────────────────────────────────────────────────────
    modal.querySelector('.amt-scm-facebook').addEventListener('click', function() {
      downloadThenOpen(
        this.dataset.url,
        '📥 Image saved! On Facebook, create a post and upload the downloaded image.'
      );
    });

    // ── WhatsApp ──────────────────────────────────────────────────────────
    modal.querySelector('.amt-scm-whatsapp').addEventListener('click', function() {
      downloadThenOpen(
        this.dataset.url,
        '📥 Image saved! In WhatsApp, tap the attachment icon to add it to your message.'
      );
    });

    // ── Instagram ─────────────────────────────────────────────────────────
    modal.querySelector('.amt-scm-instagram').addEventListener('click', () => {
      _downloadImage(dataUrl, downloadName);
      markShareComplete();
      note.textContent = '📥 Image saved! Open Instagram, tap + and choose your downloaded image for a post or story.';
      note.style.display = '';
    });

    // ── Copy text ─────────────────────────────────────────────────────────
    modal.querySelector('.amt-scm-copy').addEventListener('click', async function() {
      try {
        await navigator.clipboard.writeText(shareText);
        markShareComplete();
        this.textContent = '✅ Copied!';
        setTimeout(() => { this.textContent = '📋 Copy text'; }, 2500);
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
    const caption = type === 'badge'
      ? `I just unlocked the "${badge.name}" badge on Mirror Talk! ${badge.emoji} ${badge.desc}`
      : type === 'streak'
      ? `🔥 ${stats.currentStreak}-day streak on Mirror Talk — asking questions, growing daily.`
      : `🌱 My Mirror Talk journey: ${stats.totalQuestions} questions · ${stats.currentStreak}-day streak · ${stats.earnedBadges.size} badges earned.`;
    showShareModal(dataUrl, caption);
  }

  // ── Wire share button into milestone toast ──
  // The toast now sprouts a "Share" button 1 s after appearing.
  const _origShowMilestoneToast = showMilestoneToast;
  // Override to attach a share button for badge toasts
  window._amtShareMilestone = shareMilestone; // expose for badge shelf buttons

  function normalizeInsightRecord(insight) {
    const question = String((insight && insight.question) || '').trim();
    const answer = String((insight && insight.answer) || '').trim();
    const theme = String((insight && insight.theme) || inferTheme(question, answer) || 'Reflection').trim();
    const excerpt = String((insight && insight.excerpt) || extractInsightExcerpt(answer) || truncateText(question, 180)).trim();

    return {
      question,
      answer,
      theme,
      excerpt,
      savedAt: (insight && insight.savedAt) || Date.now()
    };
  }

  function buildInsightShareCard(insight) {
    const normalized = normalizeInsightRecord(insight);
    const W = 1200;
    const H = 1500;
    const canvas = document.createElement('canvas');
    canvas.width = W;
    canvas.height = H;
    const ctx = canvas.getContext('2d');

    const grad = ctx.createLinearGradient(0, 0, W, H);
    grad.addColorStop(0, '#f7f0e4');
    grad.addColorStop(0.55, '#efe6d9');
    grad.addColorStop(1, '#e7dccd');
    ctx.fillStyle = grad;
    ctx.fillRect(0, 0, W, H);

    ctx.fillStyle = 'rgba(46,42,36,0.03)';
    for (let i = 0; i < 3200; i++) {
      ctx.fillRect(Math.random() * W, Math.random() * H, 1.5, 1.5);
    }

    ctx.strokeStyle = 'rgba(139,115,85,0.28)';
    ctx.lineWidth = 4;
    _roundRect(ctx, 44, 44, W - 88, H - 88, 30);
    ctx.stroke();

    ctx.fillStyle = '#8b7355';
    ctx.font = '600 30px Georgia, serif';
    ctx.textAlign = 'center';
    ctx.fillText('ASK MIRROR TALK', W / 2, 126);

    ctx.fillStyle = '#2e2a24';
    ctx.font = '700 76px Georgia, serif';
    wrapCanvasText(ctx, normalized.question, 170, 238, 860, 94, 4);

    ctx.fillStyle = 'rgba(46,42,36,0.1)';
    _roundRect(ctx, 150, 450, W - 300, 56, 28);
    ctx.fill();
    ctx.fillStyle = '#6b665d';
    ctx.font = '600 24px -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif';
    ctx.fillText(normalized.theme, W / 2, 486);

    ctx.fillStyle = 'rgba(255,255,255,0.82)';
    _roundRect(ctx, 108, 560, W - 216, 548, 34);
    ctx.fill();
    ctx.strokeStyle = 'rgba(139,115,85,0.18)';
    ctx.lineWidth = 2;
    _roundRect(ctx, 108, 560, W - 216, 548, 34);
    ctx.stroke();

    ctx.fillStyle = '#8b7355';
    ctx.font = '88px Georgia, serif';
    ctx.textAlign = 'left';
    ctx.fillText('“', 160, 664);

    ctx.fillStyle = '#2e2a24';
    ctx.font = '500 42px Georgia, serif';
    wrapCanvasText(ctx, normalized.excerpt, 160, 720, W - 320, 60, 7);

    ctx.fillStyle = '#6b665d';
    ctx.font = '500 24px -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif';
    ctx.textAlign = 'center';
    ctx.fillText('A saved reflection from the Mirror Talk library', W / 2, 1188);

    ctx.fillStyle = '#2e2a24';
    ctx.font = '600 30px Georgia, serif';
    ctx.fillText('mirrortalkpodcast.com/ask-mirror-talk', W / 2, 1318);

    ctx.fillStyle = '#8b7355';
    ctx.font = '500 22px -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif';
    ctx.fillText('Save the insight. Share the reflection. Come back for more.', W / 2, 1368);

    return canvas.toDataURL('image/png');
  }

  function wrapCanvasText(ctx, text, x, startY, maxWidth, lineHeight, maxLines) {
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

    const finalLines = lines.slice(0, maxLines);
    if (lines.length > maxLines) {
      finalLines[maxLines - 1] = truncateText(finalLines[maxLines - 1], Math.max(12, finalLines[maxLines - 1].length - 1));
    }

    ctx.textAlign = 'left';
    finalLines.forEach((line, index) => {
      ctx.fillText(line, x, startY + (index * lineHeight));
    });
  }

  function shareInsightArtifact(insight) {
    const normalized = normalizeInsightRecord(insight);
    const dataUrl = buildInsightShareCard(normalized);
    const caption = `A reflection I saved on Ask Mirror Talk: "${normalized.excerpt}"\n\nhttps://mirrortalkpodcast.com/ask-mirror-talk`;
    showShareModal(dataUrl, caption, {
      title: 'Share this reflection card',
      hint: 'Download or share a beautifully formatted reflection inspired by your answer.',
      filename: 'mirror-talk-reflection.png'
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

  function addSaveInsightButton(question, answerText) {
    const existing = document.getElementById('amt-save-insight-section');
    if (existing) existing.remove();
    if (!question || !answerText) return;

    const section = document.createElement('div');
    section.id = 'amt-save-insight-section';
    section.className = 'amt-save-insight-section';

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
    const count = loadInsights().length;
    btn.style.display = count > 0 ? '' : 'none';
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
        input.value = btn.dataset.q;
        panel.style.display = 'none';
        input.focus();
        form.scrollIntoView({ behavior: 'smooth', block: 'center' });
        setTimeout(() => form.dispatchEvent(new Event('submit', { cancelable: true })), 200);
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

  // Wire insights button
  (function initInsightsBtn() {
    const btn = document.getElementById('amt-insights-btn');
    const panel = document.getElementById('amt-insights-panel');
    if (!btn || !panel) return;
    updateInsightsBadge();
    btn.addEventListener('click', () => {
      if (panel.style.display !== 'none') {
        panel.style.display = 'none';
      } else {
        const insights = loadInsights();
        if (insights.length === 0) {
          panel.innerHTML = '<div class="amt-insights-empty"><p>No saved insights yet.</p><p class="amt-insights-empty-hint">After an answer, tap 🔖 Save insight to keep it here.</p></div>';
          panel.style.display = '';
        } else {
          renderInsightsPanel();
        }
      }
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
        input.focus();
        form.scrollIntoView({ behavior: 'smooth', block: 'center' });
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

    const prompt = REFLECT_PROMPTS[Math.floor(Math.random() * REFLECT_PROMPTS.length)];

    section.innerHTML = `
      <div class="amt-reflect-inner">
        <p class="amt-reflect-label">✍️ Take a moment to reflect…</p>
        <p class="amt-reflect-question">${escapeHtml(prompt)}</p>
        <button type="button" class="amt-reflect-toggle">Jot a note ↓</button>
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
      this.textContent = isOpen ? 'Jot a note ↓' : 'Hide note ↑';
      if (!isOpen) section.querySelector('.amt-reflect-textarea').focus();
    });

    section.querySelector('.amt-reflect-save-btn').addEventListener('click', () => {
      const textarea = section.querySelector('.amt-reflect-textarea');
      const note = textarea.value.trim();
      if (!note) return;
      try {
        const existing = loadReflectionNotes();
        existing.unshift({ note, prompt, savedAt: Date.now() });
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
  // FEATURE 5: Referral-Framed Share Copy
  // ========================================
  // Patch addShareButton to include both "Share Answer" and "Invite a Friend"

  function addShareButtonV2(question, answerText) {
    const existing = document.getElementById('amt-share-section');
    if (existing) existing.remove();

    const shareSection = document.createElement('div');
    shareSection.id = 'amt-share-section';
    shareSection.className = 'amt-share-section amt-share-section-v2';

    const pageUrl = 'https://mirrortalkpodcast.com/ask-mirror-talk';
    const reflectionInsight = normalizeInsightRecord({
      question,
      answer: answerText,
      theme: inferTheme(question, answerText),
      savedAt: Date.now()
    });
    const referralShare = `I've been exploring "${question.substring(0, 80)}" on Mirror Talk — ask your own question:\n${pageUrl}`;

    shareSection.innerHTML = `
      <div class="amt-share-intro">
        <span class="amt-share-kicker">Keep or pass on what mattered</span>
        <p class="amt-share-caption">Share a premium reflection card or invite someone into the Mirror Talk experience.</p>
      </div>
      <div class="amt-share-toggle-row">
        <button type="button" class="amt-share-mode-btn amt-share-mode-active" data-mode="answer">📤 Share Card</button>
        <button type="button" class="amt-share-mode-btn" data-mode="invite">🤝 Invite a Friend</button>
      </div>
      <button type="button" class="amt-share-btn" data-mode="answer">Share this reflection card</button>
    `;

    getAnswerUtilitiesRoot().appendChild(shareSection);

    shareSection.querySelectorAll('.amt-share-mode-btn').forEach(btn => {
      btn.addEventListener('click', () => {
        shareSection.querySelectorAll('.amt-share-mode-btn').forEach(b => b.classList.remove('amt-share-mode-active'));
        btn.classList.add('amt-share-mode-active');
        const mainBtn = shareSection.querySelector('.amt-share-btn');
        mainBtn.dataset.mode = btn.dataset.mode;
        mainBtn.textContent = btn.dataset.mode === 'answer' ? 'Share this reflection card' : 'Invite a friend';
      });
    });

    shareSection.querySelector('.amt-share-btn').addEventListener('click', async function() {
      const mode = this.dataset.mode;
      if (mode === 'answer') {
        shareInsightArtifact(reflectionInsight);
        return;
      }

      const textToShare = referralShare;
      const titleToShare = 'Ask Mirror Talk';

      if (navigator.share) {
        try {
          await navigator.share({ title: titleToShare, text: textToShare, url: pageUrl });
          trackRewardEvent('share');
        } catch (e) {
          if (e.name !== 'AbortError') console.warn('Share failed:', e);
        }
      } else {
        try {
          await navigator.clipboard.writeText(textToShare);
          trackRewardEvent('share');
          const btn = this;
          const origText = btn.textContent;
          btn.textContent = '✅ Copied!';
          setTimeout(() => { btn.textContent = origText; }, 2500);
        } catch (e) {}
      }
    });

    // Also add the save insight button here
    addSaveInsightButton(question, answerText);
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
        ? `<p class="amt-journal-empty">You haven't saved any reflection notes yet.<br>After asking a question, look for the <strong>✍️ Take a moment to reflect…</strong> section below the response.</p>`
        : notes.map((entry, i) => `
          <div class="amt-journal-entry" data-index="${i}">
            <p class="amt-journal-prompt">${escapeHtml(entry.prompt || '')}</p>
            <p class="amt-journal-note" data-index="${i}">${escapeHtml(entry.note || '')}</p>
            <div class="amt-journal-entry-footer">
              <span class="amt-journal-date">${formatDate(entry.savedAt)}</span>
              <div class="amt-journal-entry-actions">
                <button type="button" class="amt-journal-edit-btn" data-index="${i}" title="Edit this note">✏️ Edit</button>
                <button type="button" class="amt-journal-share-btn" data-index="${i}" title="Share this note">📤 Share</button>
                <button type="button" class="amt-journal-delete-btn" data-index="${i}" title="Delete this note">🗑</button>
              </div>
            </div>
          </div>
        `).join('');

      modal.innerHTML = `
        <div class="amt-journal-backdrop"></div>
        <div class="amt-journal-panel">
          <button class="amt-journal-close" aria-label="Close">✕</button>
          <h2 class="amt-journal-title">📓 My Reflection Notes</h2>
          <p class="amt-journal-subtitle">${notes.length} note${notes.length !== 1 ? 's' : ''} — private on this device, with browser recovery for reinstall</p>
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

          const shareText = `Reflection: ${entry.prompt}\n\nMy note: ${entry.note}`;
          if (navigator.share) {
            try {
              await navigator.share({ title: 'My Mirror Talk Reflection', text: shareText, url: pageUrl });
            } catch (e) {
              if (e.name !== 'AbortError') console.warn('Share failed:', e);
            }
          } else {
            try {
              await navigator.clipboard.writeText(`${shareText}\n\n${pageUrl}`);
              shareBtn.textContent = '✅ Copied!';
              setTimeout(() => { shareBtn.textContent = '📤 Share'; }, 2500);
            } catch (e) { console.warn('Copy failed:', e); }
          }
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
    { emoji: '❤️', label: 'Loving it' },
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

  // Replace addShareButton globally within this scope
  // (The original is still bound in the SSE done handler — we override it here)
  window._amtPostAnswerExtras = function(question, ans) {
    // Feature 1: save insight button (called inside V2 share)
    addShareButtonV2(question, ans);
    // Feature 3: reflect prompt
    setTimeout(() => showReflectPrompt(), 600);
    // Feature 9: copy button
    initCopyAnswerButton(ans);
    // Feature 8: mood reactions
    setTimeout(() => showMoodReactions(), 400);
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
          window._amtPostAnswerExtras(question, ans);
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

})();
