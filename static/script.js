document.addEventListener("DOMContentLoaded", () => {
    const chatHistory = document.getElementById("chat-history");
    const userInput = document.getElementById("user-input");
    const sendBtn = document.getElementById("send-btn");
    
    let sessionId = localStorage.getItem("inflx_session_id");
    if (!sessionId) {
        sessionId = `sess_${Math.random().toString(36).substr(2, 9)}`;
        localStorage.setItem("inflx_session_id", sessionId);
    }

    // State elements
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
        chatHistory.insertAdjacentHTML('beforeend', loaderHTML);
        document.getElementById('temp-loader').style.display = 'flex';
        scrollToBottom();
    }

    function removeLoader() {
        const loader = document.getElementById('temp-loader');
        if (loader) loader.remove();
    }

    function addMessage(text, isUser = false) {
        const msgType = isUser ? "user-message" : "ai-message";
        const avatarText = isUser ? "U" : "AI";
        
        const html = `
            <div class="message ${msgType}">
                <div class="avatar">${avatarText}</div>
                <div class="content">${isUser ? escapeHTML(text) : marked.parse(text)}</div>
            </div>
        `;
        chatHistory.insertAdjacentHTML('beforeend', html);
        scrollToBottom();
    }

    function updateSidebarState(stateData) {
        if (!stateData) return;
        
        uiIntent.textContent = stateData.intent || "UNKNOWN";
        uiIntent.style.color = stateData.intent === "LEAD_CAPTURE" ? "#f6ad55" : "#e2e8f0";

        updateStateItem(uiName, stateData.name);
        updateStateItem(uiEmail, stateData.email);
        updateStateItem(uiPlatform, stateData.platform);
    }

    function updateStateItem(element, value) {
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

    function escapeHTML(str) {
        return str.replace(/[&<>'"]/g, tag => ({
            '&': '&amp;',
            '<': '&lt;',
            '>': '&gt;',
            "'": '&#39;',
            '"': '&quot;'
        }[tag]));
    }

    async function sendMessage() {
        const text = userInput.value.trim();
        if (!text) return;

        addMessage(text, true);
        userInput.value = "";
        
        renderLoader();

        try {
            const res = await fetch("/chat", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ message: text, session_id: sessionId })
            });
            const data = await res.json();
            
            removeLoader();
            
            if (data.status === "success") {
                addMessage(data.reply, false);
                updateSidebarState(data.state);
            } else {
                addMessage("Oops! Something went wrong on the server.", false);
            }
        } catch (err) {
            removeLoader();
            addMessage("Network error. Is the server running?", false);
        }
    }

    sendBtn.addEventListener("click", sendMessage);
    userInput.addEventListener("keypress", (e) => {
        if (e.key === "Enter") {
            sendMessage();
        }
    });
});
