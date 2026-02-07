const form = document.querySelector("#ask-mirror-talk-form");
const input = document.querySelector("#ask-mirror-talk-input");
const output = document.querySelector("#ask-mirror-talk-output");
const citations = document.querySelector("#ask-mirror-talk-citations");

if (form) {
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
      const body = new URLSearchParams();
      body.set("action", "ask_mirror_talk");
      body.set("nonce", AskMirrorTalk.nonce);
      body.set("question", question);

      const response = await fetch(AskMirrorTalk.ajaxUrl, {
        method: "POST",
        headers: { "Content-Type": "application/x-www-form-urlencoded" },
        body: body.toString()
      });

      if (!response.ok) {
        throw new Error("Request failed");
      }

      const result = await response.json();
      if (!result.success) {
        throw new Error(result.data?.message || "Request failed");
      }

      const data = result.data;
      output.textContent = data.answer || "";

      (data.citations || []).forEach((c) => {
        const li = document.createElement("li");
        li.textContent = `${c.episode_title} (${c.timestamp_start} - ${c.timestamp_end})`;
        citations.appendChild(li);
      });
    } catch (error) {
      output.textContent = "We couldn't reach the service. Please try again later.";
    }
  });
}
