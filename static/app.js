document.addEventListener("DOMContentLoaded", () => {
    const loginForm = document.getElementById("loginForm");
    const registerForm = document.getElementById("registerForm");
    const generateBtn = document.getElementById("generateBtn");

    // Unified helper utility to pop feedback messages into auth containers
    function showAuthMessage(text, isSuccess = false) {
        const msgEl = document.getElementById("message");
        if (!msgEl) return;
        msgEl.innerText = text;
        msgEl.className = `message ${isSuccess ? 'success' : 'error'}`;
        msgEl.classList.remove("hidden");
    }

    // ==========================================
    // 🔐 SECURE AUTHENTICATION ACTION LISTENERS
    // ==========================================
    if (loginForm) {
        loginForm.addEventListener("submit", async (e) => {
            e.preventDefault();
            const usernameInput = document.getElementById("username").value.trim();
            const passwordInput = document.getElementById("password").value;
            const submitBtn = loginForm.querySelector('button[type="submit"]');

            try {
                submitBtn.disabled = true;
                submitBtn.innerText = "Authenticating Session...";

                const response = await fetch("/api/login", {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({ username: usernameInput, password: passwordInput })
                });
                const data = await response.json();

                if (data.success) {
                    showAuthMessage("Success! Access granted. Redirecting...", true);
                    setTimeout(() => { window.location.href = data.redirect; }, 1000);
                } else {
                    showAuthMessage(data.message || "Invalid account authorization info.");
                    submitBtn.disabled = false;
                    submitBtn.innerText = "Login";
                }
            } catch (error) {
                showAuthMessage("A networking pipeline error has occurred.");
                submitBtn.disabled = false;
                submitBtn.innerText = "Login";
            }
        });
    }

    if (registerForm) {
        registerForm.addEventListener("submit", async (e) => {
            e.preventDefault();
            const usernameInput = document.getElementById("username").value.trim();
            const passwordInput = document.getElementById("password").value;
            const submitBtn = registerForm.querySelector('button[type="submit"]');

            if (usernameInput.length < 3 || passwordInput.length < 6) {
                showAuthMessage("Ensure inputs fulfill safety length constraints (User >=3, Pass >=6).");
                return;
            }

            try {
                submitBtn.disabled = true;
                submitBtn.innerText = "Provisioning Workspace Environment...";

                const response = await fetch("/api/register", {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({ username: usernameInput, password: passwordInput })
                });
                const data = await response.json();

                if (data.success) {
                    showAuthMessage("Account registered successfully! Tuning dashboards...", true);
                    setTimeout(() => { window.location.href = data.redirect; }, 1000);
                } else {
                    showAuthMessage(data.message || "Failed to create workspace profile mapping.");
                    submitBtn.disabled = false;
                    submitBtn.innerText = "Register";
                }
            } catch (error) {
                showAuthMessage("Internal gateway transmission connectivity break.");
                submitBtn.disabled = false;
                submitBtn.innerText = "Register";
            }
        });
    }

    // ==========================================
    // 🤖 CONTENT GENERATION LOGIC ENGINE 
    // ==========================================
    if (generateBtn) {
        const modeButtons = document.querySelectorAll(".mode-btn");
        const modeBadge = document.getElementById("modeBadge");
        const inputText = document.getElementById("inputText");
        const outputText = document.getElementById("outputText");
        const copyBtn = document.getElementById("copyBtn");
        const historyList = document.getElementById("historyList");
        const dashMessage = document.getElementById("dashboardMessage");

        let currentMode = "email";
        
        // Dynamically rotate input context placeholder instructions matching selected sidebar item tags
        const placeholders = {
            email: "Write the idea, topic, or rough draft notes you want turned into a polished email...",
            text: "Paste sentences containing grammar bugs, typos, or unclear structural flow...",
            reply: "Paste a client/boss message along with rough notes of what you want to answer...",
            improve: "Paste an essay, paragraph, or text snippet you want to dramatically elevate..."
        };

        // Navigation state activation click handler
        modeButtons.forEach(btn => {
            btn.addEventListener("click", () => {
                modeButtons.forEach(b => b.classList.remove("active"));
                btn.classList.add("active");
                
                currentMode = btn.getAttribute("data-mode");
                if (modeBadge) modeBadge.innerText = currentMode;
                if (inputText) inputText.placeholder = placeholders[currentMode] || "Provide context input string details here...";
            });
        });

        // Query backend live Large Language Model route pipelines
        generateBtn.addEventListener("click", async () => {
            const contextPayload = inputText.value.trim();
            if (!contextPayload) {
                dashMessage.innerText = "Please provide data context or copy notes inside the input box before generating.";
                dashMessage.className = "message error";
                dashMessage.classList.remove("hidden");
                return;
            }
            dashMessage.classList.add("hidden");

            try {
                generateBtn.disabled = true;
                generateBtn.innerText = "AI is writing...";
                outputText.innerText = "Connecting to live Gemini AI Engine. Stream writing responses...";

                const response = await fetch("/api/generate", {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({ text: contextPayload, mode: currentMode })
                });
                const data = await response.json();

                if (data.success) {
                    outputText.innerText = data.result;
                    fetchHistoryLogs(); // Run background logs refresh sync
                } else {
                    outputText.innerText = `Pipeline Error Context: ${data.message}`;
                }
            } catch (err) {
                outputText.innerText = "Connection break. Ensure your local Python microservice instance environment is running.";
            } finally {
                generateBtn.disabled = false;
                generateBtn.innerText = "Generate with AI";
            }
        });

        // Clipboard management helper
        if (copyBtn) {
            copyBtn.addEventListener("click", () => {
                const copyTextString = outputText.innerText;
                if (!copyTextString || copyTextString.startsWith("Your real-time generated")) return;
                
                navigator.clipboard.writeText(copyTextString).then(() => {
                    const defaultLabel = copyBtn.innerText;
                    copyBtn.innerText = "Copied!";
                    setTimeout(() => { copyBtn.innerText = defaultLabel; }, 2000);
                });
            });
        }

        // Populate execution registry logs stack values from backend stub profiles
        async function fetchHistoryLogs() {
            if (!historyList) return;
            try {
                const res = await fetch("/api/history");
                const data = await res.json();
                if (data.success && data.history && data.history.length > 0) {
                    historyList.innerHTML = ""; // Wipe blank state placeholder element rules
                    data.history.forEach(item => {
                        const historyCard = document.createElement("div");
                        historyCard.className = "history-item";
                        historyCard.innerHTML = `
                            <div class="history-item-header">
                                <span class="history-mode-tag">${item.mode.toUpperCase()}</span>
                            </div>
                            <p class="history-snippet-input"><strong>Input Context:</strong> ${item.input_text.substring(0, 60)}...</p>
                        `;
                        historyCard.addEventListener("click", () => {
                            inputText.value = item.input_text;
                            outputText.innerText = item.output_text;
                            currentMode = item.mode;
                            if (modeBadge) modeBadge.innerText = item.mode;
                            modeButtons.forEach(b => {
                                if(b.getAttribute("data-mode") === item.mode) b.classList.add("active");
                                else b.classList.remove("active");
                            });
                        });
                        historyList.appendChild(historyCard);
                    });
                }
            } catch (err) { console.error("Database log mapping error background pull down: ", err); }
        }
        fetchHistoryLogs();
    }
});