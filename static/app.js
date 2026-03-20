let currentMode = "email";

const modeConfig = {
    email: {
        label: "email",
        placeholder: "Write the idea, topic, or message you want turned into an email..."
    },
    text: {
        label: "fix writing",
        placeholder: "Paste rough writing here and I'll clean the spelling, grammar, and wording..."
    },
    reply: {
        label: "reply",
        placeholder: "Paste the message or situation you want to reply to..."
    },
    improve: {
        label: "improve",
        placeholder: "Paste your writing here and I'll make it sound more polished and clear..."
    }
};

function showMessage(elementId, text, type = "error") {
    const element = document.getElementById(elementId);
    if (!element) return;

    element.textContent = text;
    element.classList.remove("hidden", "error", "success");
    element.classList.add(type);
}

function hideMessage(elementId) {
    const element = document.getElementById(elementId);
    if (!element) return;

    element.textContent = "";
    element.classList.add("hidden");
    element.classList.remove("error", "success");
}

async function sendJSON(url, data) {
    const response = await fetch(url, {
        method: "POST",
        headers: {
            "Content-Type": "application/json"
        },
        body: JSON.stringify(data)
    });

    let result;
    try {
        result = await response.json();
    } catch (error) {
        result = {
            success: false,
            message: "Invalid server response."
        };
    }

    return { response, result };
}

function applyModeUI(mode) {
    const badge = document.getElementById("modeBadge");
    const inputText = document.getElementById("inputText");

    const config = modeConfig[mode] || modeConfig.email;

    if (badge) {
        badge.textContent = config.label;
    }

    if (inputText) {
        inputText.placeholder = config.placeholder;
    }
}

const loginForm = document.getElementById("loginForm");

if (loginForm) {
    loginForm.addEventListener("submit", async function (event) {
        event.preventDefault();
        hideMessage("message");

        const username = document.getElementById("username").value.trim();
        const password = document.getElementById("password").value.trim();

        try {
            const { response, result } = await sendJSON("/api/login", {
                username: username,
                password: password
            });

            if (!response.ok) {
                showMessage("message", result.message || "Login failed.");
                return;
            }

            showMessage("message", result.message || "Login successful.", "success");

            setTimeout(() => {
                window.location.href = result.redirect || "/dashboard";
            }, 300);
        } catch (error) {
            showMessage("message", "Something went wrong during login.");
        }
    });
}

const registerForm = document.getElementById("registerForm");

if (registerForm) {
    registerForm.addEventListener("submit", async function (event) {
        event.preventDefault();
        hideMessage("message");

        const username = document.getElementById("username").value.trim();
        const password = document.getElementById("password").value.trim();

        try {
            const { response, result } = await sendJSON("/api/register", {
                username: username,
                password: password
            });

            if (!response.ok) {
                showMessage("message", result.message || "Registration failed.");
                return;
            }

            showMessage("message", result.message || "Account created.", "success");

            setTimeout(() => {
                window.location.href = result.redirect || "/dashboard";
            }, 300);
        } catch (error) {
            showMessage("message", "Something went wrong during registration.");
        }
    });
}

function setupModeButtons() {
    const buttons = document.querySelectorAll(".mode-btn");

    if (!buttons.length) return;

    buttons.forEach((button) => {
        button.addEventListener("click", function () {
            buttons.forEach((btn) => btn.classList.remove("active"));
            this.classList.add("active");
            currentMode = this.dataset.mode || "email";
            applyModeUI(currentMode);
        });
    });

    applyModeUI(currentMode);
}

async function generateContent() {
    hideMessage("dashboardMessage");

    const inputText = document.getElementById("inputText");
    const outputText = document.getElementById("outputText");
    const generateBtn = document.getElementById("generateBtn");

    if (!inputText || !outputText || !generateBtn) return;

    const text = inputText.value.trim();

    if (!text) {
        showMessage("dashboardMessage", "Please enter some text first.");
        return;
    }

    generateBtn.disabled = true;
    generateBtn.textContent = "Generating...";
    outputText.textContent = "Generating...";

    try {
        const { response, result } = await sendJSON("/api/generate", {
            text: text,
            mode: currentMode
        });

        if (!response.ok) {
            outputText.textContent = "Your generated result will appear here...";
            showMessage("dashboardMessage", result.message || "Generation failed.");
            return;
        }

        outputText.textContent = result.result || "No result returned.";
        loadHistory();
    } catch (error) {
        outputText.textContent = "Your generated result will appear here...";
        showMessage("dashboardMessage", "Something went wrong while generating.");
    } finally {
        generateBtn.disabled = false;
        generateBtn.textContent = "Generate";
    }
}

function escapeHTML(text) {
    const div = document.createElement("div");
    div.textContent = text;
    return div.innerHTML;
}

function prettifyMode(mode) {
    if (mode === "text") return "fix writing";
    return mode;
}

async function loadHistory() {
    const historyList = document.getElementById("historyList");
    if (!historyList) return;

    try {
        const response = await fetch("/api/history");
        const result = await response.json();

        if (!response.ok || !result.success) {
            historyList.innerHTML = `<div class="empty-history">Could not load history.</div>`;
            return;
        }

        const items = result.history || [];

        if (!items.length) {
            historyList.innerHTML = `<div class="empty-history">No history yet.</div>`;
            return;
        }

        historyList.innerHTML = items.map((item) => `
            <div class="history-item">
                <div class="history-top">
                    <span class="history-mode">${escapeHTML(prettifyMode(item.mode))}</span>
                    <span>${escapeHTML(item.created_at || "")}</span>
                </div>

                <div class="history-block">
                    <div class="history-label">Input</div>
                    <div class="history-text">${escapeHTML(item.input_text)}</div>
                </div>

                <div class="history-block">
                    <div class="history-label">Output</div>
                    <div class="history-text">${escapeHTML(item.output_text)}</div>
                </div>
            </div>
        `).join("");
    } catch (error) {
        historyList.innerHTML = `<div class="empty-history">Could not load history.</div>`;
    }
}

function setupCopyButton() {
    const copyBtn = document.getElementById("copyBtn");
    const outputText = document.getElementById("outputText");

    if (!copyBtn || !outputText) return;

    copyBtn.addEventListener("click", async function () {
        try {
            await navigator.clipboard.writeText(outputText.textContent);
            const originalText = copyBtn.textContent;
            copyBtn.textContent = "Copied!";
            setTimeout(() => {
                copyBtn.textContent = originalText;
            }, 1200);
        } catch (error) {
            alert("Copy failed.");
        }
    });
}

document.addEventListener("DOMContentLoaded", function () {
    setupModeButtons();
    setupCopyButton();

    const generateBtn = document.getElementById("generateBtn");
    if (generateBtn) {
        generateBtn.addEventListener("click", generateContent);
        loadHistory();
    }
});