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
    
    // Format answer with proper line breaks
    const formattedAnswer = answer
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
        const timestampStart = formatTimestamp(citation.timestamp_start);
        const timestampEnd = formatTimestamp(citation.timestamp_end);
        
        // Create clickable citation with podcast link if available
        if (citation.episode_url) {
          const link = document.createElement("a");
          link.href = citation.episode_url;
          link.target = "_blank";
          link.rel = "noopener noreferrer";
          link.className = "citation-link";
          link.innerHTML = `
            <span class="citation-title">${episodeTitle}</span>
            <span class="citation-time">${timestampStart}${timestampEnd ? ' - ' + timestampEnd : ''}</span>
          `;
          li.appendChild(link);
        } else {
          li.innerHTML = `
            <span class="citation-title">${episodeTitle}</span>
            <span class="citation-time">${timestampStart}${timestampEnd ? ' - ' + timestampEnd : ''}</span>
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
