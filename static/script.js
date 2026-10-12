
document.addEventListener("DOMContentLoaded", () => {
    const chatHistory = document.getElementById("chat-history");
    const userInput = document.getElementById("user-input");
    const sendBtn = document.getElementById("send-btn");

    let sessionId = localStorage.getItem("novalead_session_id");

    if (!sessionId) {
        sessionId = `sess_${Math.random().toString(36).substring(2, 11)}`;
        localStorage.setItem("novalead_session_id", sessionId);
    }

    // Sidebar state elements
    const uiIntent = document.querySelector("#state-intent .value");
    const uiName = document.querySelector("#state-name .value");
    const uiEmail = document.querySelector("#state-email .value");
    const uiPlatform = document.querySelector("#state-platform .value");

    function renderLoader() {
        const loaderHTML = `
            <div class="message ai-message loader-msg" id="temp-loader">
                <div class="avatar">AI</div>
                <div class="content loading-indicator">
                    <div class="dot"></div>
                    <div class="dot"></div>
                    <div class="dot"></div>
                </div>
            </div>
        `;

        chatHistory.insertAdjacentHTML("beforeend", loaderHTML);
        scrollToBottom();
    }

    function removeLoader() {
        const loader = document.getElementById("temp-loader");
        if (loader) loader.remove();
    }

    function addMessage(text, isUser = false) {
        const msgType = isUser ? "user-message" : "ai-message";
        const avatarText = isUser ? "U" : "AI";

        // Convert model content blocks into displayable text.
        const messageText = normalizeReply(text);

        const contentHTML = isUser
            ? escapeHTML(messageText).replace(/\n/g, "<br>")
            : marked.parse(escapeHTML(messageText));

        const html = `
            <div class="message ${msgType}">
                <div class="avatar">${avatarText}</div>
                <div class="content">${contentHTML}</div>
            </div>
        `;

        chatHistory.insertAdjacentHTML("beforeend", html);
        scrollToBottom();
    }

    function normalizeReply(reply) {
        if (typeof reply === "string") {
            return reply;
        }

        if (Array.isArray(reply)) {
            return reply
                .map(item => {
                    if (typeof item === "string") return item;
                    if (item && typeof item.text === "string") return item.text;
                    return "";
                })
                .filter(Boolean)
                .join("\n\n");
        }

        if (reply && typeof reply.text === "string") {
            return reply.text;
        }

        return "The server returned an unexpected response format.";
    }

    function updateSidebarState(stateData) {
        if (!stateData) return;

        if (uiIntent) {
            uiIntent.textContent = stateData.intent || "UNKNOWN";
            uiIntent.style.color =
                stateData.intent === "LEAD_CAPTURE" ? "#f6ad55" : "#e2e8f0";
        }

        updateStateItem(uiName, stateData.name);
        updateStateItem(uiEmail, stateData.email);
        updateStateItem(uiPlatform, stateData.platform);
    }

    function updateStateItem(element, value) {
        if (!element) return;

        if (value) {
            element.textContent = value;
            element.classList.remove("missing");
            element.classList.add("found");
        } else {
            element.textContent = "Missing";
            element.classList.add("missing");
            element.classList.remove("found");
        }
    }

    function scrollToBottom() {
        chatHistory.scrollTop = chatHistory.scrollHeight;
    }

    function escapeHTML(value) {
        return String(value).replace(/[&<>'"]/g, character => ({
            "&": "&amp;",
            "<": "&lt;",
            ">": "&gt;",
            "'": "&#39;",
            '"': "&quot;"
        })[character]);
    }

    async function sendMessage() {
        const text = userInput.value.trim();

        if (!text) return;

        addMessage(text, true);
        userInput.value = "";
        sendBtn.disabled = true;
        renderLoader();

        try {
            const response = await fetch("/chat", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json"
                },
                body: JSON.stringify({
                    message: text,
                    session_id: sessionId
                })
            });

            const data = await response.json();
            removeLoader();

            if (!response.ok || data.status !== "success") {
                console.error("Chat API error:", data);
                addMessage(
                    typeof data.reply === "string"
                        ? data.reply
                        : "The server could not process your message.",
                    false
                );
                return;
            }

            // Save the returned session ID.
            if (data.session_id) {
                sessionId = data.session_id;
                localStorage.setItem("novalead_session_id", sessionId);
            }

            // Display the actual AI text, not the entire JSON response.
            addMessage(data.reply, false);
            updateSidebarState(data.state);

        } catch (error) {
            removeLoader();
            console.error("Chat request failed:", error);
            addMessage(
                "Unable to connect to the chat server. Check the terminal for errors and try again.",
                false
            );
        } finally {
            sendBtn.disabled = false;
            userInput.focus();
        }
    }

    sendBtn.addEventListener("click", sendMessage);

    userInput.addEventListener("keydown", event => {
        if (event.key === "Enter" && !event.shiftKey) {
            event.preventDefault();
            sendMessage();
        }
    });
});
