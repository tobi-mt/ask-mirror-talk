const form = document.querySelector("#ask-mirror-talk-form");
const input = document.querySelector("#ask-mirror-talk-input");
const output = document.querySelector("#ask-mirror-talk-output");
const citations = document.querySelector("#ask-mirror-talk-citations");

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
  output.textContent = "Thinking...";
  citations.innerHTML = "";

  const question = input.value.trim();
  if (!question) {
    output.textContent = "Please enter a question.";
    return;
  }

  try {
    const response = await fetch(window.ASK_MIRROR_TALK_API, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ question })
    });

    if (!response.ok) {
      throw new Error("Request failed");
    }

    const data = await response.json();
    
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

    data.citations.forEach((c) => {
      const li = document.createElement("li");
      li.textContent = `${c.episode_title} (${c.timestamp_start} - ${c.timestamp_end})`;
      citations.appendChild(li);
    });
  } catch (error) {
    output.textContent = "We couldn't reach the service. Please try again later.";
  }
});
