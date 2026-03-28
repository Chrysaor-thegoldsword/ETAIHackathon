const chatContainer = document.getElementById("chat-container");
const composer = document.getElementById("composer");
const userInput = document.getElementById("user-input");
const sendBtn = document.getElementById("send-btn");
const uploadBtn = document.getElementById("upload-btn");
const documentInput = document.getElementById("document-input");
const uploadStatus = document.getElementById("upload-status");
const reportBtn = document.getElementById("report-btn");
const progressFill = document.getElementById("progress-fill");
const progressLabel = document.getElementById("progress-label");
const statusChip = document.getElementById("status-chip");

let sessionId = null;

function formatMoney(value) {
    if (value === null || value === undefined || Number.isNaN(Number(value))) {
        return "NA";
    }
    return `Rs ${Number(value).toLocaleString("en-IN", { maximumFractionDigits: 0 })}`;
}

function appendMessage(sender, text) {
    const node = document.createElement("div");
    node.className = `message ${sender}`;
    node.textContent = text;
    chatContainer.appendChild(node);
    chatContainer.scrollTop = chatContainer.scrollHeight;
}

function setProgress(progress) {
    const pct = Math.round((progress || 0) * 100);
    progressFill.style.width = `${pct}%`;
    progressLabel.textContent = `${pct}%`;
    statusChip.textContent = pct >= 100 ? "Analysis ready" : "Collecting profile";
}

function renderHealth(health) {
    if (!health) return;
    const score = Number(health.total || 0);
    const degrees = Math.round((score / 100) * 360);
    document.getElementById("score-ring").style.background =
        `conic-gradient(var(--brand) ${degrees}deg, #f1e5db ${degrees}deg)`;
    document.getElementById("score-value").textContent = Math.round(score);
    document.getElementById("score-band").textContent = health.band || "Pending";
    document.getElementById("score-summary").textContent =
        health.positives?.[0] || "Health analysis generated.";

    const metrics = health.metrics || {};
    document.getElementById("score-metrics").innerHTML = Object.entries(metrics)
        .map(([label, value]) => `
            <div class="metric-pill">
                <span>${label.replaceAll("_", " ")}</span>
                <strong>${value}</strong>
            </div>
        `)
        .join("");
}

function renderFlags(flags = []) {
    const node = document.getElementById("red-flags");
    if (!flags.length) {
        node.innerHTML = `<div class="list-item">No major red flags surfaced from the current profile.</div>`;
        return;
    }
    node.innerHTML = flags
        .map((flag) => `<div class="list-item flag">${flag}</div>`)
        .join("");
}

function renderTaxes(tax) {
    const node = document.getElementById("tax-cards");
    if (!tax) return;
    const recommended = String(tax.recommended_regime || "").toLowerCase();
    node.innerHTML = `
        <div class="tax-card ${recommended === "old" ? "recommended" : ""}">
            <label>Old regime</label>
            <strong>${formatMoney(tax.old_regime_tax)}</strong>
            <p>${tax.user_selected_regime === "old" ? "Currently selected by user." : "Alternative comparison path."}</p>
        </div>
        <div class="tax-card ${recommended === "new" ? "recommended" : ""}">
            <label>New regime</label>
            <strong>${formatMoney(tax.new_regime_tax)}</strong>
            <p>Recommended: ${(tax.recommended_regime || "unsure").toUpperCase()}</p>
        </div>
    `;
}

function renderGoals(goals) {
    const node = document.getElementById("goal-list");
    const allGoals = goals?.all_goals || [];
    if (!allGoals.length) {
        node.innerHTML = `<div class="list-item">No explicit goals were parsed yet. Add amount and timeline for sharper recommendations.</div>`;
        return;
    }
    node.innerHTML = allGoals.map((goal) => `
        <div class="list-item">
            <strong>${goal.name}</strong>
            <div class="item-meta">
                Target ${formatMoney(goal.target_amount)} over ${goal.horizon_months} months.<br />
                Required monthly investment ${formatMoney(goal.required_monthly_investment)}.<br />
                Recommended now ${formatMoney(goal.recommended_monthly_investment)}.
            </div>
            <span class="status-tag">${goal.status}</span>
        </div>
    `).join("");
}

function renderAllocation(portfolio) {
    const node = document.getElementById("allocation-bars");
    const allocation = portfolio?.allocation || {};
    if (!Object.keys(allocation).length) {
        node.innerHTML = `<div class="list-item">Portfolio split will appear once goals and risk appetite are known.</div>`;
        return;
    }
    node.innerHTML = Object.entries(allocation).map(([label, share]) => `
        <div class="allocation-row">
            <div class="allocation-head">
                <span>${label}</span>
                <span>${share}% | ${formatMoney(portfolio.monthly_plan?.[label])}/month</span>
            </div>
            <div class="allocation-track">
                <div class="allocation-fill" style="width:${share}%"></div>
            </div>
        </div>
    `).join("");
}

function renderWatchlist(portfolio) {
    const node = document.getElementById("watchlist");
    const items = portfolio?.top_choices || [];
    if (!items.length) {
        node.innerHTML = `<div class="list-item">Research-backed instruments will appear here after the analysis is ready.</div>`;
        return;
    }
    node.innerHTML = items.map((item) => `
        <div class="list-item">
            <strong>${item.name}</strong>
            <div class="item-meta">
                ${item.asset_class} | ${item.credit_quality} | ${item.expected_return}<br />
                ${item.why}<br />
                Tax angle: ${item.tax_note}
            </div>
            <a href="${item.source_url}" target="_blank" rel="noreferrer">${item.source_label}</a>
        </div>
    `).join("");
}

function renderSources(report) {
    const node = document.getElementById("source-list");
    const sources = report?.sources || [];
    if (!sources.length) {
        node.innerHTML = `<div class="list-item">Official tax references and research links will appear here.</div>`;
        return;
    }
    node.innerHTML = sources.map((source) => `
        <div class="list-item">
            <strong>${source.label}</strong>
            <a href="${source.url}" target="_blank" rel="noreferrer">${source.url}</a>
        </div>
    `).join("");
}

function updateHero(analysis) {
    document.getElementById("hero-score").textContent = analysis?.health_score?.total
        ? `${Math.round(analysis.health_score.total)}/100`
        : "--";
    document.getElementById("hero-tax").textContent = analysis?.tax?.recommended_regime
        ? String(analysis.tax.recommended_regime).toUpperCase()
        : "Pending";
    document.getElementById("hero-surplus").textContent = analysis?.goals
        ? formatMoney(analysis.goals.investable_surplus)
        : "Pending";
}

function renderAnalysis(analysis, report) {
    if (!analysis) return;
    renderHealth(analysis.health_score);
    renderFlags(analysis.health_score?.red_flags || []);
    renderTaxes(analysis.tax);
    renderGoals(analysis.goals);
    renderAllocation(analysis.portfolio);
    renderWatchlist(analysis.portfolio);
    renderSources(report);
    updateHero(analysis);
    reportBtn.disabled = !report;
}

async function sendMessage(message) {
    sendBtn.disabled = true;
    try {
        const response = await fetch("/api/chat", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ session_id: sessionId, message }),
        });
        const data = await response.json();
        sessionId = data.session_id;
        if (message.trim()) {
            appendMessage("user", message);
        }
        appendMessage("bot", data.response);
        setProgress(data.progress);
        renderAnalysis(data.analysis, data.report);
    } catch (error) {
        appendMessage("bot", "The advisor could not reach the server right now.");
    } finally {
        sendBtn.disabled = false;
        userInput.value = "";
        userInput.focus();
    }
}

composer.addEventListener("submit", async (event) => {
    event.preventDefault();
    const message = userInput.value.trim();
    if (!message) return;
    await sendMessage(message);
});

uploadBtn.addEventListener("click", async () => {
    if (!sessionId) {
        await sendMessage("");
    }

    const file = documentInput.files?.[0];
    if (!file) {
        uploadStatus.textContent = "Choose a file before uploading.";
        return;
    }

    uploadBtn.disabled = true;
    uploadStatus.textContent = "Uploading and extracting document hints...";

    try {
        const formData = new FormData();
        formData.append("file", file);
        formData.append("session_id", sessionId);
        const response = await fetch("/api/upload", {
            method: "POST",
            body: formData,
        });
        const data = await response.json();
        if (data.error) {
            uploadStatus.textContent = data.error;
            return;
        }
        uploadStatus.textContent = data.extracted?.document_summary || "Document linked to the profile.";
        appendMessage("bot", uploadStatus.textContent);
    } catch (error) {
        uploadStatus.textContent = "Upload failed. Please try again.";
    } finally {
        uploadBtn.disabled = false;
    }
});

reportBtn.addEventListener("click", async () => {
    if (!sessionId) return;
    try {
        const response = await fetch("/api/report", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ session_id: sessionId }),
        });
        if (!response.ok) {
            appendMessage("bot", "The detailed report could not be generated.");
            return;
        }
        const blob = await response.blob();
        const url = URL.createObjectURL(blob);
        const link = document.createElement("a");
        link.href = url;
        link.download = "et_money_mentor_report.pdf";
        document.body.appendChild(link);
        link.click();
        link.remove();
        URL.revokeObjectURL(url);
    } catch (error) {
        appendMessage("bot", "The report download failed.");
    }
});

sendMessage("");
