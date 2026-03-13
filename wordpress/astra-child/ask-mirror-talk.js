(function() {
  'use strict';

  console.log('Ask Mirror Talk Widget v3.9.0 loaded');

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

  // Hide response and citations on initial load if empty
  if (responseContainer && (!output.innerHTML || output.innerHTML.trim() === '')) {
    responseContainer.style.display = 'none';
  }
  if (citationsContainer) {
    citationsContainer.style.display = 'none';
  }

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
          const btn = document.createElement('button');
          btn.type = 'button';
          btn.className = 'amt-topic-btn';
          btn.title = `Explore ${t.label}` + (t.episode_count ? ` (${t.episode_count} episodes)` : '');
          btn.innerHTML = `<span class="amt-topic-icon">${t.icon}</span><span class="amt-topic-name">${t.label}</span>`;
          btn.addEventListener('click', () => {
            input.value = t.query;
            input.focus();
            topicsContainer.style.display = 'none';
            form.dispatchEvent(new Event('submit', { cancelable: true }));
          });
          topicsList.appendChild(btn);
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
    setTimeout(() => {
      followupsContainer.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
    }, 300);
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

      responseContainer.style.display = '';
      responseContainer.querySelector('h3').textContent = 'Response';

      output.innerHTML = `
        <div class="amt-loading">
          <div class="amt-loading-dots">
            <span></span><span></span><span></span>
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
      citationsContainer.style.display = "none";
    } else {
      clearInterval(loadingInterval);
      loadingInterval = null;
      submitBtn.disabled = false;
      submitBtn.textContent = 'Ask';
      input.disabled = false;
      responseContainer.classList.remove('amt-streaming');
    }
  }

  // Show error message with shake animation
  function showError(message) {
    responseContainer.style.display = '';
    responseContainer.classList.remove('amt-streaming');
    output.classList.add('error');
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
          
          link.innerHTML = `
            <div class="citation-info">
              <span class="citation-title">${episodeTitle}</span>
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
              // Fallback: open in new tab if no audio URL
              window.open(this.href, '_blank');
            }
          });

          li.appendChild(link);

          // "Explore this episode" button — links to full episode page
          if (audioUrl) {
            const exploreBtn = document.createElement("a");
            exploreBtn.href = audioUrl;
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

          li.innerHTML = `
            <div class="citation-info">
              <span class="citation-title">${episodeTitle}</span>
              ${quoteHtml}
            </div>
            <span class="citation-time">${timeDisplay}</span>
          `;
        }
        
        citations.appendChild(li);
      });

      citationsContainer.style.display = "block";
    } else {
      citations.innerHTML = "";
      citationsContainer.style.display = "none";
    }
  }

  // ========================================
  // SSE Streaming Answer
  // ========================================

  /**
   * Stream an answer via SSE (Server-Sent Events).
   * Falls back to the non-streaming /ask endpoint on error.
   */
  async function askStreaming(question) {
    const response = await fetch(`${API_BASE}/ask/stream`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ question })
    });

    if (!response.ok) {
      throw new Error(`Stream request failed: ${response.status}`);
    }

    const reader = response.body.getReader();
    const decoder = new TextDecoder();
    let answerText = '';
    let buffer = '';

    // Clear error state and prepare for streaming — keep loading dots visible
    // until the first chunk of answer text arrives
    output.classList.remove('error', 'amt-complete');
    responseContainer.classList.add('amt-streaming');
    lastDepthMessage = '';

    // Scroll the response container into view once at start so the user
    // can watch the answer appear; we won't auto-scroll after that to
    // avoid bouncing the page.
    responseContainer.scrollIntoView({ behavior: 'smooth', block: 'start' });

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
            // Capture depth messages like "Drawing from 6 episodes…"
            if (event.message && event.message.includes('episode')) {
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
            // Add share button and SEO schema after answer is complete
            addShareButton(question, answerText);
            injectFAQSchema(question, answerText);
          }
        } catch (parseErr) {
          console.warn('SSE parse error:', parseErr, jsonStr);
        }
      }
    }

    return answerText;
  }

  // Show answer (used for non-streaming fallback)
  function showAnswer(answer, citationsList, followUpQuestions) {
    output.classList.remove('error');
    responseContainer.classList.remove('amt-streaming');
    
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
    injectFAQSchema(questionText, answer);

    responseContainer.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
  }

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

    const shareText = `Q: ${question}\n\n${answer.substring(0, 200)}…\n\nAnswered by Ask Mirror Talk`;
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

  input.addEventListener('input', function() {
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

  // Save session after successful answer (hook into output rendering)
  const originalSetLoading = setLoading;
  // Watch for answer completion: override setLoading(false) to save session
  const origFormHandler = form.onsubmit;

  // Intercept: after successful stream or fallback, persist the Q&A
  const _origDispatch = form.dispatchEvent.bind(form);

  // Simple approach: MutationObserver on output to detect answer rendered
  const sessionObserver = new MutationObserver(() => {
    const q = input.value.trim();
    const a = output.textContent.trim();
    if (q && a && a.length > 50 && !output.querySelector('.amt-loading')) {
      saveLastSession(q, a);
    }
  });
  sessionObserver.observe(output, { childList: true, subtree: true, characterData: true });

  // On page load, show a subtle "last session" prompt if within 24 hours
  try {
    const lastQ = localStorage.getItem('amt_last_question');
    const lastTime = parseInt(localStorage.getItem('amt_last_time') || '0');
    const hoursAgo = (Date.now() - lastTime) / (1000 * 60 * 60);

    if (lastQ && hoursAgo < 24 && !input.value) {
      // Show a subtle prompt to re-ask the last question
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

      // Send subscription to our API
      const res = await fetch(`${API_BASE}/api/push/subscribe`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          endpoint: subJson.endpoint,
          keys: subJson.keys,
          notify_qotd: notifyQotd,
          notify_new_episodes: notifyEpisodes,
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

})();
