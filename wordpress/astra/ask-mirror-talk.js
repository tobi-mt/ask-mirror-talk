(function() {
  'use strict';

  const form = document.querySelector("#ask-mirror-talk-form");
  const input = document.querySelector("#ask-mirror-talk-input");
  const submitBtn = document.querySelector("#ask-mirror-talk-submit");
  const output = document.querySelector("#ask-mirror-talk-output");
  const citations = document.querySelector("#ask-mirror-talk-citations");
  const citationsContainer = document.querySelector(".ask-mirror-talk-citations");

  if (!form) return;

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

  // Helper: Parse timestamp string to seconds (handles "0:04:42" format)
  function parseTimestampToSeconds(timestamp) {
    if (!timestamp) return 0;
    const parts = timestamp.split(':').map(p => parseInt(p, 10));
    if (parts.length === 3) {
      return parts[0] * 3600 + parts[1] * 60 + parts[2];
    } else if (parts.length === 2) {
      return parts[0] * 60 + parts[1];
    }
    return parseInt(timestamp, 10) || 0;
  }

  // Helper: Convert markdown-style formatting to HTML
  function formatMarkdownToHtml(text) {
    if (!text) return '';
    
    // Convert **bold** to <strong>
    text = text.replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>');
    
    // Convert *italic* to <em>
    text = text.replace(/\*(.+?)\*/g, '<em>$1</em>');
    
    // Convert numbered lists (1. item) to <ol><li>
    const lines = text.split('\n');
    let inOrderedList = false;
    let inUnorderedList = false;
    const formattedLines = [];
    
    for (let i = 0; i < lines.length; i++) {
      const line = lines[i];
      const trimmedLine = line.trim();
      
      // Check for numbered list items (1. , 2. , etc.)
      const numberedMatch = trimmedLine.match(/^(\d+)\.\s+(.+)$/);
      if (numberedMatch) {
        if (!inOrderedList) {
          if (inUnorderedList) {
            formattedLines.push('</ul>');
            inUnorderedList = false;
          }
          formattedLines.push('<ol>');
          inOrderedList = true;
        }
        formattedLines.push(`<li>${numberedMatch[2]}</li>`);
        continue;
      }
      
      // Check for bullet list items (- item or * item)
      const bulletMatch = trimmedLine.match(/^[-*]\s+(.+)$/);
      if (bulletMatch) {
        if (!inUnorderedList) {
          if (inOrderedList) {
            formattedLines.push('</ol>');
            inOrderedList = false;
          }
          formattedLines.push('<ul>');
          inUnorderedList = true;
        }
        formattedLines.push(`<li>${bulletMatch[1]}</li>`);
        continue;
      }
      
      // Close any open lists if we encounter a non-list line
      if (inOrderedList && trimmedLine !== '') {
        formattedLines.push('</ol>');
        inOrderedList = false;
      }
      if (inUnorderedList && trimmedLine !== '') {
        formattedLines.push('</ul>');
        inUnorderedList = false;
      }
      
      // Regular line
      if (trimmedLine === '') {
        formattedLines.push('');  // Preserve empty lines
      } else if (!inOrderedList && !inUnorderedList) {
        formattedLines.push(line);
      }
    }
    
    // Close any remaining open lists
    if (inOrderedList) {
      formattedLines.push('</ol>');
    }
    if (inUnorderedList) {
      formattedLines.push('</ul>');
    }
    
    return formattedLines.join('\n');
  }

  // Helper: Show loading state
  function setLoading(isLoading) {
    if (isLoading) {
      submitBtn.disabled = true;
      submitBtn.textContent = 'Thinking...';
      input.disabled = true;
      output.innerHTML = '<div class="loading-spinner"></div><p>Searching through podcast episodes...</p>';
      output.classList.remove('error');
      citations.innerHTML = "";
      citationsContainer.style.display = "none";
    } else {
      submitBtn.disabled = false;
      submitBtn.textContent = 'Ask';
      input.disabled = false;
    }
  }

  // Helper: Show error message
  function showError(message) {
    output.classList.add('error');
    output.innerHTML = `<p><strong>⚠️ ${message}</strong></p>`;
    citations.innerHTML = "";
    citationsContainer.style.display = "none";
  }

  // Helper: Show success message
  function showAnswer(answer, citationsList) {
    output.classList.remove('error');
    
    // Convert markdown formatting to HTML
    let formattedAnswer = formatMarkdownToHtml(answer);
    
    // Convert double line breaks to paragraph breaks
    formattedAnswer = formattedAnswer
      .replace(/\n\n/g, '</p><p>')
      .replace(/\n/g, '<br>');
    
    output.innerHTML = `<p>${formattedAnswer}</p>`;

    // Show citations if available
    if (citationsList && citationsList.length > 0) {
      citations.innerHTML = "";
      citationsList.forEach((citation) => {
        const li = document.createElement("li");
        li.className = "citation-item";
        
        const episodeTitle = citation.episode_title || "Unknown Episode";
        
        // Use seconds if available, otherwise parse the timestamp strings
        const startSeconds = citation.timestamp_start_seconds !== undefined 
          ? citation.timestamp_start_seconds 
          : parseTimestampToSeconds(citation.timestamp_start);
        const endSeconds = citation.timestamp_end_seconds !== undefined 
          ? citation.timestamp_end_seconds 
          : parseTimestampToSeconds(citation.timestamp_end);
        
        const timestampStart = formatTimestamp(startSeconds);
        const timestampEnd = formatTimestamp(endSeconds);
        
        // Create podcast link with timestamp
        let podcastUrl = citation.episode_url || citation.audio_url || '';
        
        // If we have audio_url but not episode_url, add timestamp
        if (!citation.episode_url && citation.audio_url && startSeconds) {
          podcastUrl = `${citation.audio_url}#t=${startSeconds}`;
        }
        
        // Create clickable citation with podcast link
        if (podcastUrl) {
          const link = document.createElement("a");
          link.href = podcastUrl;
          link.target = "_blank";
          link.rel = "noopener noreferrer";
          link.className = "citation-link";
          link.title = `Listen from ${timestampStart}`;
          
          // Show range if start and end are different
          const timeDisplay = (startSeconds !== endSeconds && timestampEnd) 
            ? `${timestampStart} - ${timestampEnd}` 
            : timestampStart;
          
          link.innerHTML = `
            <span class="citation-title">${episodeTitle}</span>
            <span class="citation-time">🎧 ${timeDisplay}</span>
          `;
          li.appendChild(link);
        } else {
          // No link available, just show text
          const timeDisplay = (startSeconds !== endSeconds && timestampEnd) 
            ? `${timestampStart} - ${timestampEnd}` 
            : timestampStart;
          
          li.innerHTML = `
            <span class="citation-title">${episodeTitle}</span>
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
      const timeoutId = setTimeout(() => controller.abort(), 30000); // 30s timeout

      const response = await fetch(AskMirrorTalk.ajaxUrl, {
        method: "POST",
        headers: { "Content-Type": "application/x-www-form-urlencoded" },
        body: body.toString(),
        signal: controller.signal
      });

      clearTimeout(timeoutId);

      if (!response.ok) {
        throw new Error(`Server returned ${response.status}`);
      }

      const result = await response.json();
      
      if (!result.success) {
        const errorMsg = result.data?.message || "The service couldn't process your question.";
        throw new Error(errorMsg);
      }

      const data = result.data;
      
      if (!data.answer) {
        throw new Error("No answer received from the service.");
      }

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

  // Optional: Auto-focus input on page load
  input.focus();

  // Optional: Clear output when user starts typing a new question
  input.addEventListener('input', function() {
    if (this.value.trim() === '') {
      output.innerHTML = '';
      citations.innerHTML = '';
      citationsContainer.style.display = 'none';
    }
  });

})();
