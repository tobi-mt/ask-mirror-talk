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
    
    // Convert markdown to HTML and set as innerHTML instead of textContent
    const formattedAnswer = formatMarkdownToHtml(data.answer)
      .replace(/\n\n/g, '</p><p>')
      .replace(/\n/g, '<br>');
    output.innerHTML = `<p>${formattedAnswer}</p>`;

    data.citations.forEach((c) => {
      const li = document.createElement("li");
      li.textContent = `${c.episode_title} (${c.timestamp_start} - ${c.timestamp_end})`;
      citations.appendChild(li);
    });
  } catch (error) {
    output.textContent = "We couldn't reach the service. Please try again later.";
  }
});
