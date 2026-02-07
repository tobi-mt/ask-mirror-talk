const form = document.querySelector("#ask-mirror-talk-form");
const input = document.querySelector("#ask-mirror-talk-input");
const output = document.querySelector("#ask-mirror-talk-output");
const citations = document.querySelector("#ask-mirror-talk-citations");

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
    output.textContent = data.answer;

    data.citations.forEach((c) => {
      const li = document.createElement("li");
      li.textContent = `${c.episode_title} (${c.timestamp_start} - ${c.timestamp_end})`;
      citations.appendChild(li);
    });
  } catch (error) {
    output.textContent = "We couldn't reach the service. Please try again later.";
  }
});
