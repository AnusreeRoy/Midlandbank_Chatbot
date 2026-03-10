// chatbot/static/chatbot/js/chatbot.js
const Chatbot = (() => {
  let chatVisible = false;
  let isExpanded = false;
  let chatHistory = [];
  let typingInterval = null;

  const chatInterface = () => document.getElementById("chatInterface");
  const chatBody = () => document.getElementById("chatBody");
  const chatInput = () => document.getElementById("chatInput");
  const expandIcon = () => document.getElementById("expandIcon");

  // --- UTILITIES ---
function scrollToNewMessage() {
  // Ensure the DOM has rendered the new message
  requestAnimationFrame(() => {
    const body = chatBody();
    const messages = body.querySelectorAll(".message-container");
    if (messages.length === 0) return;

    const lastMessage = messages[messages.length - 1];
    if (!lastMessage) return;

    // Scroll the top of the last message into view instantly
    lastMessage.scrollIntoView({ behavior: "auto", block: "start" });
  });
}

  function sanitize(text) {
    return text
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/\n/g, "<br/>");
  }

  function addMessage(text, isUser, isLoading = false) {
    chatHistory.push({ text, isUser, isLoading });
    renderChat();
    scrollToNewMessage();
  }

  function removeMessage(msgObj) {
    const index = chatHistory.indexOf(msgObj);
    if (index !== -1) {
      chatHistory.splice(index, 1);
      renderChat();
    }
  }

  // --- CHAT BEHAVIOR ---
function toggleChat() {
  chatVisible = !chatVisible;

  if (chatVisible) {
    chatInterface().classList.remove("hidden"); // show chat
    setTimeout(() => chatInput().focus(), 100);

    // Show greeting only if first time
    if (!chatHistory.some(msg => msg.isUser === false)) addGreeting();
  } else {
    chatInterface().classList.add("hidden"); // hide chat
  }
}


  function toggleExpand() {
    isExpanded = !isExpanded;
    chatInterface().classList.toggle("expanded", isExpanded);
    expandIcon().classList.toggle("fa-expand", !isExpanded);
    expandIcon().classList.toggle("fa-compress", isExpanded);
  }

function addGreeting() {
  const hour = new Date().getHours();
  const timeGreeting =
    hour < 12
      ? "Good morning"
      : hour < 18
      ? "Good afternoon"
      : "Good evening";

  // Show loading indicator
  addMessage("", false, true);

  setTimeout(() => {
    // Remove the last loading message
    chatHistory = chatHistory.filter(msg => !msg.isLoading);
    renderChat();

    addMessage(
      `👋 ${timeGreeting}! I'm the Midland Bank AI Assistant. How can I help you today?`,
      false
    );
  }, 350); // 2 seconds typing
}


  // --- SENDING MESSAGE ---
  function sendMessage() {
  const text = chatInput().value.trim();
  if (!text) return;

  if (text.length > 1000) {
    alert("Your message exceeds the 1000 character limit. Please shorten your message and try again.");
    return;
  }

  addMessage(text, true);
  chatInput().value = "";

  // Add a "Thinking" placeholder with animated dots
  const loadingMessage = { text: "Thinking", isUser: false, isLoading: true };
  addMessage(loadingMessage.text, false, true);

  // Send request to backend
  fetch("/chatbot/", {
    method: "POST",
    credentials: "same-origin",
    headers: {
      "Content-Type": "application/json",
      "X-CSRFToken": getCSRFToken(),
    },
    body: JSON.stringify({ message: text }),
  })
    .then((res) => res.json())
    .then((data) => {
      // Remove all loading messages
      chatHistory = chatHistory.filter(m => !m.isLoading);
      renderChat();
      addMessage(data.response, false);
    })
    .catch((err) => {
      chatHistory = chatHistory.filter(m => !m.isLoading);
      renderChat();
      console.error("Chatbot error:", err);
      addMessage("Error communicating with chatbot.", false);
    });
}


  // --- RENDER ---
  function renderChat() {
  const body = chatBody();
  body.innerHTML = chatHistory
    .map((msg) => {
      const safeText = sanitize(msg.text);
      if (msg.isUser) {
        return `
          <div class="message-container">
            <div class="user-message">
              <div class="message-wrapper user-side">
                <div class="message-header user-header">
                  <img src="/static/chatbot/images/user-icon.png" class="user-message-icon"/>
                  <span class="message-name">Me</span>
                </div>
                <p class="message-text">${safeText}
                ${msg.isLoading ? `<span class="loading-indicator">
                  <span></span><span></span><span></span>
                </span>` : ''}</p>
              </div>
            </div>
          </div>`;
      } else {
        return `
          <div class="message-container">
            <div class="bot-message">
              <div class="message-wrapper">
                <div class="message-header">
                  <img src="/static/chatbot/images/chat-icon.png" class="message-icon"/>
                  <span class="message-name">Midland Bank AI Assistant</span>
                </div>
                <p class="message-text">
                  ${safeText}
                  ${msg.isLoading ? `
                    <span class="loading-indicator">
                      <span></span><span></span><span></span>
                    </span>` : ''}
                </p>
              </div>
            </div>
          </div>`;
      }
    })
    .join("");
}

  // --- CLOSE ON OUTSIDE CLICK ---
  document.addEventListener("click", (event) => {
    const target = event.target;
    const insideChat = target.closest(".chat-interface");
    const chatIcon = target.closest(".chatbot-icon");
    if (!insideChat && !chatIcon) {
      chatVisible = false;
      chatInterface().classList.add("hidden");
    }
  });

  // --- CSRF TOKEN HELPER ---
  function getCSRFToken() {
    const name = "csrftoken";
    const cookies = document.cookie.split(";");
    for (const cookie of cookies) {
      const [key, value] = cookie.trim().split("=");
      if (key === name) return decodeURIComponent(value);
    }
    return "";
  }

  // --- PUBLIC API ---
  return { toggleChat, toggleExpand, sendMessage };
})();

// ✅ Make functions accessible globally for inline onclick handlers
window.toggleChat = Chatbot.toggleChat;
window.toggleExpand = Chatbot.toggleExpand;
window.sendMessage = Chatbot.sendMessage;
