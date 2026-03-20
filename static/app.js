let mode = "email";

/* =========================
   LOGIN
========================= */
function login() {
    fetch("/login", {
        method: "POST",
        headers: {"Content-Type":"application/json"},
        body: JSON.stringify({
            username: username.value,
            password: password.value
        })
    }).then(r => {
        if (r.ok) window.location.href = "/";
    });
}

/* =========================
   REGISTER
========================= */
function register() {
    fetch("/register", {
        method: "POST",
        headers: {"Content-Type":"application/json"},
        body: JSON.stringify({
            username: username.value,
            password: password.value
        })
    }).then(() => window.location.href = "/login");
}

/* =========================
   MODE SELECT
========================= */
function setMode(m, btn) {
    mode = m;

    document.querySelectorAll(".sidebar button")
        .forEach(b => b.classList.remove("active"));

    if (btn) btn.classList.add("active");
}

/* =========================
   TYPE ANIMATION
========================= */
function typeText(element, text, speed = 15) {
    element.innerHTML = "";
    let i = 0;

    function typing() {
        if (i < text.length) {
            element.innerHTML += text.charAt(i);
            i++;
            setTimeout(typing, speed);
        }
    }

    typing();
}

/* =========================
   GENERATE AI
========================= */
function generate() {
    let loading = document.getElementById("loading");

    loading.classList.remove("hidden");
    output.innerHTML = "";

    fetch("/generate", {
        method: "POST",
        headers: {"Content-Type":"application/json"},
        body: JSON.stringify({
            text: input.value,
            mode: mode
        })
    })
    .then(r => r.json())
    .then(data => {

        loading.classList.add("hidden");

        // typing effect output
        typeText(output, data.result);

        loadHistory();
    });
}

/* =========================
   HISTORY (LIVE)
========================= */
function loadHistory() {
    fetch("/history")
    .then(r => r.json())
    .then(data => {
        historyList.innerHTML = data.map(h =>
            `<p><b>${h.mode}</b>: ${h.input}</p>`
        ).join("");
    });
}

/* auto refresh history */
setInterval(() => {
    if (window.location.pathname === "/") {
        loadHistory();
    }
}, 5000);

/* init */
if (window.location.pathname === "/") {
    loadHistory();
}