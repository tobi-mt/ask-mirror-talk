(function() {
  'use strict';

  console.log('Ask Mirror Talk Widget v4.7.2 loaded');

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

  if (!form) {
    console.warn('⚠️ Ask Mirror Talk form not found on this page');
    return;
  }

  // ─── API URL ────────────────────────────────────────────────
  const API_BASE = (AskMirrorTalk.apiUrl || 'https://ask-mirror-talk-production.up.railway.app');

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
              <span class="amt-qotd-theme">${data.theme || ''}</span>
            </div>
            <p class="amt-qotd-text">"${data.question}"</p>
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
    const question = params.get('autoask');
    if (question) {
      // Remove the param from the browser URL so sharing/refreshing doesn't re-fire
      const cleanUrl = window.location.pathname +
        (params.toString().replace(/autoask=[^&]*&?/, '').replace(/&$/, '').replace(/^\?$/, '') || '') +
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

  // ─── Handle AUTO_SUBMIT from service worker (already-open tab) ─
  if ('serviceWorker' in navigator) {
    navigator.serviceWorker.addEventListener('message', (event) => {
      if (event.data && event.data.type === 'AUTO_SUBMIT' && event.data.question) {
        autoSubmitQuestion(event.data.question);
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
            <button type="button" class="amt-topic-btn" title="Explore ${t.label}${t.episode_count ? ` (${t.episode_count} episodes)` : ''}">
              <span class="amt-topic-icon">${t.icon}</span>
              <span class="amt-topic-name">${t.label}</span>
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
        topicsContainer.style.display = '';
      })
      .catch(err => {
        console.warn('Could not load topics:', err);
        topicsContainer.style.display = 'none';
      });
  }

  loadTopics();

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
      responseContainer.querySelector('h3').textContent = 'Response';

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
        <div class="amt-player-episode">${episodeTitle}</div>
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

    if (citationsList && citationsList.length > 0) {
      citations.innerHTML = "";
      
      citationsList.forEach((citation) => {
        const li = document.createElement("li");
        li.className = "citation-item";
        
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
        
        if (podcastUrl) {
          const link = document.createElement("a");
          link.href = podcastUrl;
          link.className = "citation-link";
          link.title = `Listen from ${timestampStart}`;
          link.setAttribute('data-episode-id', citation.episode_id);
          link.setAttribute('data-timestamp', startSeconds);
          link.setAttribute('data-audio-url', audioUrl);
          link.setAttribute('data-start', startSeconds);
          link.setAttribute('data-end', endSeconds);
          
          const timeDisplay = (startSeconds !== endSeconds && timestampEnd) 
            ? `${timestampStart} – ${timestampEnd}` 
            : timestampStart;

          // Build the quote snippet (truncated text already returned by API)
          const quoteText = citation.text || '';
          const quoteHtml = quoteText
            ? `<span class="citation-quote">"${quoteText}"</span>`
            : '';

          const yearHtml = citation.episode_year
            ? `<span class="citation-year">${citation.episode_year}</span>`
            : '';

          link.innerHTML = `
            <div class="citation-info">
              <span class="citation-title">${episodeTitle}${yearHtml}</span>
              ${quoteHtml}
            </div>
            <span class="citation-time">▶ ${timeDisplay}</span>
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
          const timeDisplay = (startSeconds !== endSeconds && timestampEnd) 
            ? `${timestampStart} – ${timestampEnd}` 
            : timestampStart;

          const quoteText = citation.text || '';
          const quoteHtml = quoteText
            ? `<p class="citation-quote">"${quoteText}"</p>`
            : '';

          const yearHtml = citation.episode_year
            ? `<span class="citation-year">${citation.episode_year}</span>`
            : '';

          li.innerHTML = `
            <div class="citation-info">
              <span class="citation-title">${episodeTitle}${yearHtml}</span>
              ${quoteHtml}
            </div>
            <span class="citation-time">${timeDisplay}</span>
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

            // Gamification: record the answered question
            onQuestionAnswered(question, window._amtLastTheme || null);
            window._amtLastTheme = null;

            // Conversation memory: append this turn
            appendConversationTurn(question, answerText);

            // Scroll to top of response so user reads from the beginning.
            // Small delay lets the DOM finish painting the depth indicator + share button.
            setTimeout(() => {
              responseContainer.scrollIntoView({ behavior: 'smooth', block: 'start' });
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

    responseContainer.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
  }

  // ========================================
  // Save to Email
  // ========================================

  function addSaveToEmailButton(question, answer) {
    const existing = document.getElementById('amt-email-section');
    if (existing) existing.remove();
    if (!question || !answer) return;

    const shareSection = document.getElementById('amt-share-section');

    const section = document.createElement('div');
    section.id = 'amt-email-section';
    section.className = 'amt-email-section';
    section.innerHTML = `<button class="amt-email-btn" type="button" title="Save to email">📧 Save to email</button>`;

    if (shareSection && shareSection.parentNode) {
      shareSection.parentNode.insertBefore(section, shareSection.nextSibling);
    } else {
      responseContainer.appendChild(section);
    }

    section.querySelector('.amt-email-btn').addEventListener('click', () => {
      const subject = encodeURIComponent(`Mirror Talk: ${question.substring(0, 80)}`);
      const body = encodeURIComponent(
        `Question: ${question}\n\n` +
        `Answer from Mirror Talk:\n${answer}\n\n` +
        `— Answered by Ask Mirror Talk\nhttps://mirrortalk.com/ask-mirror-talk/`
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
    // Remove previous share button if exists
    const existing = document.getElementById('amt-share-section');
    if (existing) existing.remove();

    const shareSection = document.createElement('div');
    shareSection.id = 'amt-share-section';
    shareSection.className = 'amt-share-section';

    const shareText = `Q: ${question}\n\n${answer}\n\nAnswered by Ask Mirror Talk`;
    const pageUrl = window.location.href;

    shareSection.innerHTML = `
      <button class="amt-share-btn" title="Share this answer">
        📤 Share this insight
      </button>
    `;

    // Insert after the response container
    responseContainer.appendChild(shareSection);

    shareSection.querySelector('.amt-share-btn').addEventListener('click', async () => {
      if (navigator.share) {
        try {
          await navigator.share({
            title: `Mirror Talk: ${question}`,
            text: shareText,
            url: pageUrl
          });
        } catch (e) {
          if (e.name !== 'AbortError') console.warn('Share failed:', e);
        }
      } else {
        // Fallback: copy to clipboard
        try {
          await navigator.clipboard.writeText(`${shareText}\n\n${pageUrl}`);
          const btn = shareSection.querySelector('.amt-share-btn');
          btn.textContent = '✅ Copied to clipboard!';
          setTimeout(() => { btn.innerHTML = '📤 Share this insight'; }, 2500);
        } catch (e) {
          console.warn('Copy failed:', e);
        }
      }
    });
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

  input.addEventListener('input', function() {
    // Update character counter
    const charCounter = document.getElementById('amt-char-counter');
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

  function saveLastSession(question, answer) {
    try {
      localStorage.setItem('amt_last_question', question);
      localStorage.setItem('amt_last_answer', answer.substring(0, 2000));
      localStorage.setItem('amt_last_time', Date.now().toString());
    } catch (e) { /* localStorage not available */ }
  }

  // Save session after successful answer — MutationObserver watches output for new content
  const sessionObserver = new MutationObserver(() => {
    const q = input.value.trim();
    const a = output.textContent.trim();
    if (q && a && a.length > 50 && !output.querySelector('.amt-loading')) {
      saveLastSession(q, a);
    }
  });
  sessionObserver.observe(output, { childList: true, subtree: true, characterData: true });

  // On page load, show a contextual "continue your journey" hint
  try {
    const stats = loadStats();
    const lastQ = localStorage.getItem('amt_last_question');
    const lastTime = parseInt(localStorage.getItem('amt_last_time') || '0');
    const hoursAgo = (Date.now() - lastTime) / (1000 * 60 * 60);

    // Find an unexplored theme to suggest
    const exploredThemes = stats.themesExplored || new Set();
    const unexploredThemes = AMT_THEMES.filter(t => !exploredThemes.has(t));

    if (!input.value && unexploredThemes.length > 0 && stats.totalQuestions >= 1) {
      // Pick a pseudo-random unexplored theme based on day index for consistency
      const dayIndex = new Date().toISOString().slice(0, 10).split('').reduce((a, c) => a + c.charCodeAt(0), 0);
      const theme = unexploredThemes[dayIndex % unexploredThemes.length];

      // Find a matching starter question from QOTD pool or topic starters
      const themeMap = {
        'Self-worth': "How do I stop comparing myself to others?",
        'Forgiveness': "What does it mean to truly forgive someone?",
        'Inner peace': "How do I find peace when everything feels uncertain?",
        'Purpose': "How do I find my purpose in life?",
        'Surrender': "What does it look like to let go and surrender?",
        'Leadership': "What makes a great leader?",
        'Relationships': "What's the key to building healthy relationships?",
        'Gratitude': "What role does gratitude play in overcoming hardship?",
        'Boundaries': "How do I set boundaries without feeling guilty?",
        'Healing': "How do I start the healing process?",
        'Grief': "How do I deal with grief and loss?",
        'Fear': "How can I overcome fear and self-doubt?",
        'Parenting': "How do I raise kids who are emotionally resilient?",
        'Growth': "What can I learn from failure?",
        'Communication': "How do I have hard conversations without damaging the relationship?",
        'Faith': "What role does faith play in personal growth?",
        'Identity': "How do I discover my true identity?",
        'Empowerment': "How do I find my voice when I've been silenced?",
        'Transition': "How do I move forward after a major life change?",
        'Community': "What does Mirror Talk teach about the power of community?",
      };
      const suggestedQ = themeMap[theme] || `What does Mirror Talk say about ${theme.toLowerCase()}?`;

      const resumeHint = document.createElement('div');
      resumeHint.className = 'amt-resume-hint';
      resumeHint.innerHTML = `
        <div class="amt-resume-hint-inner">
          <span class="amt-resume-label">You haven't explored <strong>${theme}</strong> yet</span>
          <button type="button" class="amt-resume-btn">
            ${suggestedQ}
          </button>
        </div>
      `;
      form.insertBefore(resumeHint, form.firstChild);

      resumeHint.querySelector('.amt-resume-btn').addEventListener('click', () => {
        input.value = suggestedQ;
        resumeHint.remove();
        input.focus();
        form.dispatchEvent(new Event('submit', { cancelable: true }));
      });
    } else if (lastQ && hoursAgo < 24 && !input.value && stats.totalQuestions === 0) {
      // Fallback for users with no gamification data yet: show last question
      const resumeHint = document.createElement('div');
      resumeHint.className = 'amt-resume-hint';
      resumeHint.innerHTML = `
        <button type="button" class="amt-resume-btn">
          ↩ Continue: "${lastQ.substring(0, 60)}${lastQ.length > 60 ? '…' : ''}"
        </button>
      `;
      form.insertBefore(resumeHint, form.firstChild);

      resumeHint.querySelector('.amt-resume-btn').addEventListener('click', () => {
        input.value = lastQ;
        resumeHint.remove();
        input.focus();
        form.dispatchEvent(new Event('submit', { cancelable: true }));
      });
    }
  } catch (e) { /* localStorage not available */ }

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

    // After install, prompt for notifications after a short delay
    setTimeout(() => showNotificationOptIn(), 2000);
  });

  // ── iOS Safari fallback ──
  // Safari doesn't fire 'beforeinstallprompt', so show a manual instruction banner.
  (function showIOSInstallHint() {
    const isIOS = /iP(hone|ad|od)/.test(navigator.userAgent) && !window.MSStream;
    const isSafari = /Safari/.test(navigator.userAgent) && !/CriOS|FxiOS|OPiOS|EdgiOS/.test(navigator.userAgent);
    const isStandalone = window.matchMedia('(display-mode: standalone)').matches ||
                         window.navigator.standalone === true;

    if (!isIOS || !isSafari || isStandalone) return;

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
  function showNotificationOptIn() {
    const isIOS = /iP(hone|ad|od)/.test(navigator.userAgent) && !window.MSStream;
    const isStandalone = window.matchMedia('(display-mode: standalone)').matches ||
                         window.navigator.standalone === true;

    // iOS Safari (not added to home screen): Push API is not available.
    // Show a banner explaining they need to install the PWA first.
    if (isIOS && !isStandalone) {
      // Don't show if dismissed
      try {
        if (sessionStorage.getItem('amt_notif_dismissed')) return;
        if (localStorage.getItem('amt_notif_dismissed_permanent')) return;
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
      const heading = widget ? widget.querySelector('h2') : null;
      if (heading && heading.nextSibling) {
        widget.insertBefore(banner, heading.nextSibling);
      } else if (widget) {
        widget.appendChild(banner);
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
        if (sessionStorage.getItem('amt_notif_dismissed')) return;
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
      const heading = widget ? widget.querySelector('h2') : null;
      if (heading && heading.nextSibling) {
        widget.insertBefore(banner, heading.nextSibling);
      } else if (widget) {
        widget.appendChild(banner);
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
    if (!('PushManager' in window) || !('Notification' in window)) return;

    // Already granted or denied — don't nag
    if (Notification.permission !== 'default') return;

    // Don't show if dismissed this session
    try {
      if (sessionStorage.getItem('amt_notif_dismissed')) return;
    } catch (e) {}

    // Don't show if they dismissed permanently
    try {
      if (localStorage.getItem('amt_notif_dismissed_permanent')) return;
    } catch (e) {}

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
        <label class="amt-notif-pref">
          <input type="checkbox" id="amt-notif-qotd" checked>
          <span>✨ Daily Question of the Day</span>
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
    const heading = widget ? widget.querySelector('h2') : null;
    if (heading && heading.nextSibling) {
      widget.insertBefore(banner, heading.nextSibling);
    } else if (widget) {
      widget.appendChild(banner);
    } else {
      document.body.appendChild(banner);
    }

    // Show preferences on "Enable" click
    banner.querySelector('.amt-notif-enable').addEventListener('click', () => {
      banner.querySelector('.amt-notif-actions').style.display = 'none';
      banner.querySelector('.amt-notif-prefs').style.display = '';
    });

    // "Save & Enable" — request permission and subscribe
    banner.querySelector('.amt-notif-save').addEventListener('click', async () => {
      const qotd = document.getElementById('amt-notif-qotd').checked;
      const episodes = document.getElementById('amt-notif-episodes').checked;

      banner.querySelector('.amt-notif-save').textContent = 'Enabling…';
      banner.querySelector('.amt-notif-save').disabled = true;

      const result = await subscribeToPush(qotd, episodes);
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
      try { sessionStorage.setItem('amt_notif_dismissed', '1'); } catch (e) {}
    });

    // Auto-dismiss after 20 seconds
    setTimeout(() => {
      if (banner.parentNode && !banner.querySelector('.amt-notif-prefs[style=""]')) {
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
  async function subscribeToPush(notifyQotd = true, notifyEpisodes = true) {
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
          notify_midday: true,
          timezone: userTimezone,
          preferred_qotd_hour: 8,
        }),
      });

      if (res.ok) {
        console.log('[Push] Subscription registered successfully');
        try { localStorage.setItem('amt_push_subscribed', '1'); } catch (e) {}
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

  // Show notification opt-in after a delay.
  // For returning visitors: show after 5 seconds.
  // For new visitors: show after 15 seconds (give them time to explore first).
  // The install banner is separate and handled by 'beforeinstallprompt'.
  setTimeout(() => {
    try {
      const alreadySubscribed = localStorage.getItem('amt_push_subscribed');

      if (!alreadySubscribed) {
        showNotificationOptIn();
      }
    } catch (e) {}
  }, (() => {
    try {
      const isReturning = localStorage.getItem('amt_last_question') ||
                          window.matchMedia('(display-mode: standalone)').matches;
      return isReturning ? 5000 : 15000;
    } catch (e) { return 10000; }
  })());

  // ========================================
  // Gamification — Streak, Badges, Explorer
  // ========================================

  const AMT_BADGES = [
    { id: 'first_step',   emoji: '🌱', name: 'First Step',         desc: 'Asked your first question',              check: s => s.totalQuestions >= 1 },
    { id: 'curious',      emoji: '🔍', name: 'Curious Mind',        desc: 'Asked 10 questions',                     check: s => s.totalQuestions >= 10 },
    { id: 'streak_3',     emoji: '🔥', name: 'On Fire',             desc: 'Kept a 3-day streak',                    check: s => s.maxStreak >= 3 },
    { id: 'streak_7',     emoji: '💫', name: 'Week Warrior',        desc: 'Kept a 7-day streak',                    check: s => s.maxStreak >= 7 },
    { id: 'streak_30',    emoji: '💎', name: 'Devoted',             desc: 'Kept a 30-day streak',                   check: s => s.maxStreak >= 30 },
    { id: 'explorer',     emoji: '🗺️', name: 'Explorer',            desc: 'Explored 5 different topics',            check: s => s.themesExplored.size >= 5 },
    { id: 'deep_diver',   emoji: '⚡', name: 'Deep Diver',          desc: 'Clicked a podcast citation',             check: s => s.citationsClicked >= 1 },
    { id: 'sharer',       emoji: '📤', name: 'Sharer',              desc: 'Shared an insight',                      check: s => s.sharesCount >= 1 },
    { id: 'night_owl',    emoji: '🌙', name: 'Night Owl',           desc: 'Asked a question after 10pm',            check: s => s.nightOwl },
    { id: 'completionist',emoji: '🏆', name: 'Completionist',       desc: 'Explored all 20 topics',                 check: s => s.themesExplored.size >= 20 },
  ];

  // Themes the backend already uses in the QOTD pool
  const AMT_THEMES = [
    'Self-worth','Forgiveness','Inner peace','Purpose','Surrender',
    'Leadership','Relationships','Gratitude','Boundaries','Healing',
    'Grief','Fear','Parenting','Growth','Communication',
    'Faith','Identity','Empowerment','Transition','Community',
  ];

  function loadStats() {
    try {
      const raw = localStorage.getItem('amt_gamification');
      if (raw) {
        const parsed = JSON.parse(raw);
        // themesExplored is serialised as an array
        parsed.themesExplored = new Set(parsed.themesExplored || []);
        parsed.earnedBadges   = new Set(parsed.earnedBadges   || []);
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
      nightOwl:         false,
    };
  }

  function saveStats(s) {
    try {
      const serialisable = Object.assign({}, s, {
        themesExplored: [...s.themesExplored],
        earnedBadges:   [...s.earnedBadges],
      });
      localStorage.setItem('amt_gamification', JSON.stringify(serialisable));
    } catch (e) {}
  }

  function todayStr() {
    return new Date().toISOString().slice(0, 10); // 'YYYY-MM-DD'
  }

  function recordQuestion(stats, themeHint) {
    const today = todayStr();
    const last  = stats.lastActiveDate;

    if (last !== today) {
      // Check streak continuity
      const yesterday = new Date();
      yesterday.setDate(yesterday.getDate() - 1);
      const yStr = yesterday.toISOString().slice(0, 10);

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

    stats.totalQuestions += 1;

    // Night owl check (22:00–23:59)
    const hour = new Date().getHours();
    if (hour >= 22) stats.nightOwl = true;

    // Theme tracking — try to match from the question text
    if (themeHint) {
      stats.themesExplored.add(themeHint);
    } else {
      // Simple keyword → theme mapping for organic questions
      const q = (themeHint || '').toLowerCase();
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
  }

  function renderBadgeShelf(stats) {
    const shelf = document.getElementById('amt-badge-shelf');
    if (!shelf) return;
    shelf.innerHTML = '';

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
      shelf.appendChild(el);
    }

    // Add a "Share my progress" button at the bottom of the shelf
    const progressBtn = document.createElement('button');
    progressBtn.className = 'amt-share-progress-btn';
    progressBtn.innerHTML = '📊 Share my progress';
    progressBtn.addEventListener('click', () => shareMilestone(null, 'progress'));
    shelf.appendChild(progressBtn);

    if (stats.currentStreak >= 3) {
      const streakBtn = document.createElement('button');
      streakBtn.className = 'amt-share-progress-btn';
      streakBtn.innerHTML = `🔥 Share my ${stats.currentStreak}-day streak`;
      streakBtn.addEventListener('click', () => shareMilestone(null, 'streak'));
      shelf.appendChild(streakBtn);
    }
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

  const STREAK_MILESTONES = new Set([3, 7, 14, 30, 60, 100]);

  function onQuestionAnswered(questionText, themeHint) {
    let stats = loadStats();
    const prevStreak = stats.currentStreak;

    stats = recordQuestion(stats, themeHint);
    const newBadges = checkAndAwardBadges(stats);
    saveStats(stats);
    renderStatsBar(stats);

    // Streak milestone toast
    if (stats.currentStreak !== prevStreak && STREAK_MILESTONES.has(stats.currentStreak)) {
      showMilestoneToast('🔥', `${stats.currentStreak}-day streak!`, 'Keep the wisdom flowing.');
    }

    // New badge toasts (queue sequentially)
    newBadges.forEach((badge, i) => {
      setTimeout(() => {
        showMilestoneToast(badge.emoji, `Badge unlocked: ${badge.name}`, badge.desc, badge);
      }, i * 4200);
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

  // Track share button clicks for the Sharer badge
  document.addEventListener('click', (e) => {
    if (e.target.closest('#amt-share-section')) {
      try {
        const s = loadStats();
        s.sharesCount = (s.sharesCount || 0) + 1;
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
    try {
      if (localStorage.getItem('amt_onboarded')) return;
    } catch (e) { return; }

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
      try { localStorage.setItem('amt_onboarded', '1'); } catch (e) {}
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
    if (initStats.totalQuestions > 0) {
      renderStatsBar(initStats);
    }
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
  function _downloadImage(dataUrl) {
    const a = document.createElement('a');
    a.href = dataUrl;
    a.download = 'mirror-talk-achievement.png';
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
  }

  function showShareModal(dataUrl, caption) {
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
    modal.setAttribute('aria-label', 'Share your badge');

    modal.innerHTML = `
      <div class="amt-scm-backdrop"></div>
      <div class="amt-scm-panel">
        <button class="amt-scm-close" aria-label="Close">&times;</button>
        <h3 class="amt-scm-title">Share your achievement 🎉</h3>
        <img class="amt-scm-preview" src="${dataUrl}" alt="Share card preview" />
        <p class="amt-scm-hint">Platform buttons download the image first — then attach it to your post.</p>
        <div class="amt-scm-buttons">
          ${nativeShareBtn}
          <a class="amt-scm-btn amt-scm-download" href="${dataUrl}" download="mirror-talk-achievement.png">
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

    // ── Helper: download image then open platform URL ──────────────────
    function downloadThenOpen(platformUrl, platformNote) {
      _downloadImage(dataUrl);
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
          const file = await _dataUrlToFile(dataUrl, 'mirror-talk-achievement.png');
          if (navigator.canShare({ files: [file] })) {
            await navigator.share({ files: [file], text: caption, url: pageUrl });
          } else {
            // canShare exists but files not supported — fall back to text-only share
            await navigator.share({ text: shareText });
          }
        } catch (err) {
          if (err.name !== 'AbortError') {
            // Fallback to download
            _downloadImage(dataUrl);
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
      _downloadImage(dataUrl);
      note.textContent = '📥 Image saved! Open Instagram, tap + and choose your downloaded image for a post or story.';
      note.style.display = '';
    });

    // ── Copy text ─────────────────────────────────────────────────────────
    modal.querySelector('.amt-scm-copy').addEventListener('click', async function() {
      try {
        await navigator.clipboard.writeText(shareText);
        this.textContent = '✅ Copied!';
        setTimeout(() => { this.textContent = '📋 Copy text'; }, 2500);
      } catch (e) {
        this.textContent = '⚠️ Copy failed';
      }
    });

    // Track share in gamification stats
    try {
      const s = loadStats();
      s.sharesCount = (s.sharesCount || 0) + 1;
      const newBadges = checkAndAwardBadges(s);
      saveStats(s);
      newBadges.forEach(b => showMilestoneToast(b.emoji, `Badge unlocked: ${b.name}`, b.desc));
    } catch (e2) {}
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

})();
