(function() {
  'use strict';

  console.log('Ask Mirror Talk Widget v2.5.0 loaded');

  const form = document.querySelector("#ask-mirror-talk-form");
  const input = document.querySelector("#ask-mirror-talk-input");
  const submitBtn = document.querySelector("#ask-mirror-talk-submit");
  const output = document.querySelector("#ask-mirror-talk-output");
  const citations = document.querySelector("#ask-mirror-talk-citations");
  const citationsContainer = document.querySelector(".ask-mirror-talk-citations");
  const responseContainer = document.querySelector(".ask-mirror-talk-response");

  if (!form) {
    console.warn('⚠️ Ask Mirror Talk form not found on this page');
    return;
  }

  // Hide response and citations on initial load if empty
  if (responseContainer && (!output.innerHTML || output.innerHTML.trim() === '')) {
    responseContainer.style.display = 'none';
  }
  if (citationsContainer) {
    citationsContainer.style.display = 'none';
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
  let activePlayer = null; // Track the currently active inline audio player

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

  // Show loading state with animated dots and rotating messages
  function setLoading(isLoading) {
    if (isLoading) {
      submitBtn.disabled = true;
      submitBtn.textContent = 'Thinking…';
      input.disabled = true;

      // Remove old feedback section
      const oldFeedback = document.getElementById('amt-feedback-section');
      if (oldFeedback) oldFeedback.remove();

      // Show response container
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

      // Rotate loading messages
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
    }
  }

  // Show error message with shake animation
  function showError(message) {
    responseContainer.style.display = '';
    output.classList.add('error');
    output.innerHTML = `<p><strong>⚠️ ${message}</strong></p>`;
    citations.innerHTML = "";
    citationsContainer.style.display = "none";
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

  // Show answer with smooth reveal
  function showAnswer(answer, citationsList) {
    output.classList.remove('error');
    
    let formattedAnswer = formatMarkdownToHtml(answer);
    
    const paragraphs = formattedAnswer.split('\n\n').filter(p => p.trim());
    const htmlParagraphs = paragraphs.map(p => {
      const trimmed = p.trim();
      if (trimmed.startsWith('<ol>') || trimmed.startsWith('<ul>')) return trimmed;
      return '<p>' + trimmed.replace(/\n/g, '<br>') + '</p>';
    });
    
    // Set content (CSS handles staggered fadeInUp animations)
    output.innerHTML = htmlParagraphs.join('');

    // Close any active player from previous answer
    if (activePlayer) {
      closeInlinePlayer(activePlayer);
    }

    // Show citations if available
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
          
          link.innerHTML = `
            <span class="citation-title">${episodeTitle}</span>
            <span class="citation-time">🎧 ${timeDisplay}</span>
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
        } else {
          const timeDisplay = (startSeconds !== endSeconds && timestampEnd) 
            ? `${timestampStart} – ${timestampEnd}` 
            : timestampStart;
          
          li.innerHTML = `
            <span class="citation-title">${episodeTitle}</span>
            <span class="citation-time">${timeDisplay}</span>
          `;
        }
        
        citations.appendChild(li);
      });

      // Reveal citations container with animation
      citationsContainer.style.display = "block";
    } else {
      citations.innerHTML = "";
      citationsContainer.style.display = "none";
    }

    // Smooth scroll to the answer
    responseContainer.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
  }

  // Main form submission handler
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
      const body = new URLSearchParams();
      body.set("action", "ask_mirror_talk");
      body.set("nonce", AskMirrorTalk.nonce);
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

      if (!response.ok) throw new Error(`Server returned ${response.status}`);

      const result = await response.json();
      
      if (!result.success) {
        throw new Error(result.data?.message || "The service couldn't process your question.");
      }

      const data = result.data;
      if (!data.answer) throw new Error("No answer received from the service.");

      showAnswer(data.answer, data.citations || []);
      
    } catch (error) {
      console.error("Ask Mirror Talk Error:", error);
      
      if (error.name === 'AbortError') {
        showError("The request took too long. Please try again.");
      } else if (error.message.includes('Failed to fetch') || error.message.includes('NetworkError')) {
        showError("Unable to reach the service. Please check your connection and try again.");
      } else {
        showError(error.message || "Something went wrong. Please try again later.");
      }
    } finally {
      setLoading(false);
    }
  });

  // Subtle input interaction: show placeholder hint
  input.addEventListener('focus', function() {
    if (!this.value) {
      this.setAttribute('placeholder', 'e.g. How do I deal with grief? What does the Bible say about forgiveness?');
    }
  });

  input.addEventListener('blur', function() {
    this.setAttribute('placeholder', 'Ask a question...');
  });

  // Clear output when user clears input
  input.addEventListener('input', function() {
    if (this.value.trim() === '') {
      output.innerHTML = '';
      citations.innerHTML = '';
      citationsContainer.style.display = 'none';
      responseContainer.style.display = 'none';
      const oldFeedback = document.getElementById('amt-feedback-section');
      if (oldFeedback) oldFeedback.remove();
    }
  });

})();
