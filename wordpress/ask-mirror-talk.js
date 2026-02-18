// Ask Mirror Talk Widget - Version 2.0.0
// Includes: UX improvements, better error handling, citation deduplication
const ASK_MIRROR_TALK_VERSION = '2.0.0';

const form = document.querySelector("#ask-mirror-talk-form");
const input = document.querySelector("#ask-mirror-talk-input");
const output = document.querySelector("#ask-mirror-talk-output");
const citations = document.querySelector("#ask-mirror-talk-citations");

// Log version for debugging
if (window.console) {
  console.log('Ask Mirror Talk Widget v' + ASK_MIRROR_TALK_VERSION + ' loaded');
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
    
    // Skip empty lines
    if (trimmedLine === '') {
      // Close any open lists before empty line
      if (inOrderedList) {
        formattedLines.push('</ol>');
        inOrderedList = false;
      }
      if (inUnorderedList) {
        formattedLines.push('</ul>');
        inUnorderedList = false;
      }
      formattedLines.push('');
      continue;
    }
    
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
      // Apply formatting to list item content
      let itemContent = numberedMatch[2];
      itemContent = itemContent.replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>');
      itemContent = itemContent.replace(/\*(.+?)\*/g, '<em>$1</em>');
      formattedLines.push(`<li>${itemContent}</li>`);
      continue;
    }
    
    // Check for bullet list items (- item or * item)
    const bulletMatch = trimmedLine.match(/^[-]\s+(.+)$/);
    if (bulletMatch) {
      if (!inUnorderedList) {
        if (inOrderedList) {
          formattedLines.push('</ol>');
          inOrderedList = false;
        }
        formattedLines.push('<ul>');
        inUnorderedList = true;
      }
      // Apply formatting to list item content
      let itemContent = bulletMatch[1];
      itemContent = itemContent.replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>');
      itemContent = itemContent.replace(/\*(.+?)\*/g, '<em>$1</em>');
      formattedLines.push(`<li>${itemContent}</li>`);
      continue;
    }
    
    // If we're in a list and encounter non-list text, close the list
    if (inOrderedList) {
      formattedLines.push('</ol>');
      inOrderedList = false;
    }
    if (inUnorderedList) {
      formattedLines.push('</ul>');
      inUnorderedList = false;
    }
    
    // Regular line (not in a list)
    formattedLines.push(line);
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

form.addEventListener("submit", async (event) => {
  event.preventDefault();
  
  const question = input.value.trim();
  if (!question) {
    output.innerHTML = '<p class="error">Please enter a question.</p>';
    return;
  }

  // Disable form during request
  input.disabled = true;
  form.querySelector('button').disabled = true;
  
  // Show loading state
  output.innerHTML = '<p class="loading">Searching through Mirror Talk episodes...</p>';
  citations.innerHTML = "";

  try {
    const response = await fetch(window.ASK_MIRROR_TALK_API, {
      method: "POST",
      headers: { 
        "Content-Type": "application/json",
        "Accept": "application/json"
      },
      body: JSON.stringify({ question })
    });

    // Check response status before parsing
    if (!response.ok) {
      const errorText = await response.text();
      console.error('Server error:', response.status, errorText);
      throw new Error(`Server returned ${response.status}: ${errorText || 'Unknown error'}`);
    }

    // Parse JSON response
    const data = await response.json();
    
    // Validate response has required fields
    if (!data || !data.answer) {
      console.error('Invalid response:', data);
      throw new Error('Invalid response from server - missing answer');
    }
    
    // Convert markdown to HTML
    const formattedAnswer = formatMarkdownToHtml(data.answer);
    
    // Split into paragraphs and wrap them properly
    const paragraphs = formattedAnswer.split('\n\n').filter(p => p.trim());
    const htmlParagraphs = paragraphs.map(p => {
      const trimmed = p.trim();
      // Don't wrap lists in <p> tags
      if (trimmed.startsWith('<ol>') || trimmed.startsWith('<ul>')) {
        return trimmed;
      }
      // Regular paragraphs - replace single newlines with <br>
      return '<p>' + trimmed.replace(/\n/g, '<br>') + '</p>';
    });
    
    output.innerHTML = htmlParagraphs.join('');

    // Display citations with clickable timestamps
    if (data.citations && data.citations.length > 0) {
      data.citations.forEach((c) => {
        const li = document.createElement("li");
        
        // Create clickable citation with timestamp
        const citationHtml = `
          <strong>${c.episode_title}</strong><br>
          ${c.text || ''}<br>
          <a href="${c.episode_url || c.audio_url}" 
             target="_blank" 
             rel="noopener" 
             class="timestamp-link"
             title="Listen from ${c.timestamp_start}">
            🎧 Listen at ${c.timestamp_start}
          </a>
        `;
        
        li.innerHTML = citationHtml;
        citations.appendChild(li);
      });
    }
    
  } catch (error) {
    console.error('Error fetching answer:', error);
    output.innerHTML = `
      <p class="error">
        <strong>Sorry, something went wrong.</strong><br>
        ${error.message || 'Unable to get an answer. Please try again.'}
      </p>
    `;
  } finally {
    // Re-enable form
    input.disabled = false;
    form.querySelector('button').disabled = false;
  }
});
