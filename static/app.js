/**
 * Яркотревел AI — Клиентская логика
 * Авторизация, разбор сообщений, batch, экспорт, история
 */

(function () {
    "use strict";

    // ──────────────────────────────────────────
    // State
    // ──────────────────────────────────────────

    const state = {
        token: localStorage.getItem("yarko_token") || null,
        history: JSON.parse(localStorage.getItem("yarko_history") || "[]"),
        batchMode: false,
        jsonView: false,
        lastResult: null,
        lastBatchResults: null,
    };

    // ──────────────────────────────────────────
    // DOM Elements
    // ──────────────────────────────────────────

    const $ = (sel) => document.querySelector(sel);
    const $$ = (sel) => document.querySelectorAll(sel);

    const els = {
        authScreen: $("#auth-screen"),
        mainScreen: $("#main-screen"),
        authPassword: $("#auth-password"),
        authBtn: $("#auth-btn"),
        authError: $("#auth-error"),

        messageInput: $("#message-input"),
        analyzeBtn: $("#analyze-btn"),
        clearBtn: $("#clear-btn"),
        btnText: $(".btn-text"),
        btnLoading: $(".btn-loading"),

        batchModeToggle: $("#batch-mode-toggle"),
        batchHint: $("#batch-hint"),
        inputTitle: $("#input-title"),

        resultSection: $("#result-section"),
        batchResultSection: $("#batch-result-section"),
        cardView: $("#card-view"),
        jsonView: $("#json-view"),
        jsonOutput: $("#json-output"),
        segmentBtns: $$(".segment-btn"),
        segmentControl: $(".segment-control"),
        copyBtn: $("#copy-btn"),
        costValue: $("#cost-value"),
        costTokens: $("#cost-tokens"),

        batchResults: $("#batch-results"),
        batchCopyBtn: $("#batch-copy-btn"),
        batchCsvBtn: $("#batch-csv-btn"),
        batchCostValue: $("#batch-cost-value"),

        historySection: $("#history-section"),
        historyList: $("#history-list"),
        clearHistoryBtn: $("#clear-history-btn"),

        exportBtn: $("#export-btn"),
        toastContainer: $("#toast-container"),
    };

    // ──────────────────────────────────────────
    // Init
    // ──────────────────────────────────────────

    function init() {
        // Check if already authenticated
        if (state.token) {
            showMainScreen();
        }

        // Auth
        els.authBtn.addEventListener("click", handleAuth);
        els.authPassword.addEventListener("keydown", (e) => {
            if (e.key === "Enter") handleAuth();
        });

        // Analyze
        els.analyzeBtn.addEventListener("click", handleAnalyze);
        els.clearBtn.addEventListener("click", () => {
            els.messageInput.value = "";
            els.messageInput.focus();
        });

        // Batch mode toggle
        els.batchModeToggle.addEventListener("change", (e) => {
            state.batchMode = e.target.checked;
            els.batchHint.classList.toggle("hidden", !state.batchMode);
            
            if (state.batchMode) {
                els.inputTitle.innerHTML = '<i data-lucide="layers"></i> Сообщения (batch)';
                els.messageInput.placeholder = "Вставьте сообщения, разделяя их строкой ---";
            } else {
                els.inputTitle.innerHTML = '<i data-lucide="user"></i> Сообщение туриста';
                els.messageInput.placeholder = "Вставьте сообщение туриста...";
            }
            if (window.lucide) window.lucide.createIcons();
        });

        // Segmented Control (card / JSON)
        els.segmentBtns.forEach(btn => {
            btn.addEventListener("click", () => {
                const target = btn.dataset.target;
                
                // Update UI state
                els.segmentBtns.forEach(b => b.classList.remove("active"));
                btn.classList.add("active");
                
                // Update indicator position
                if (target === "json-view") {
                    els.segmentControl.dataset.active = "json";
                    state.jsonView = true;
                    els.cardView.classList.remove("active");
                    els.jsonView.classList.add("active");
                } else {
                    els.segmentControl.dataset.active = "card";
                    state.jsonView = false;
                    els.cardView.classList.add("active");
                    els.jsonView.classList.remove("active");
                }
            });
        });

        // Copy JSON
        els.copyBtn.addEventListener("click", () => {
            if (state.lastResult) {
                copyToClipboard(JSON.stringify(state.lastResult, null, 2));
                showToast("JSON скопирован!", "success");
            }
        });

        // Batch copy
        els.batchCopyBtn.addEventListener("click", () => {
            if (state.lastBatchResults) {
                copyToClipboard(JSON.stringify(state.lastBatchResults, null, 2));
                showToast("Все результаты скопированы!", "success");
            }
        });

        // Batch CSV
        els.batchCsvBtn.addEventListener("click", () => {
            if (state.lastBatchResults) {
                downloadCSV(state.lastBatchResults.results);
            }
        });

        // Export all history
        els.exportBtn.addEventListener("click", () => {
            if (state.history.length === 0) {
                showToast("Нет данных для экспорта", "error");
                return;
            }
            const blob = new Blob(
                [JSON.stringify(state.history, null, 2)],
                { type: "application/json" }
            );
            downloadBlob(blob, "yarko-ai-history.json");
            showToast("История экспортирована!", "success");
        });

        // Clear history
        els.clearHistoryBtn.addEventListener("click", () => {
            state.history = [];
            localStorage.removeItem("yarko_history");
            renderHistory();
            showToast("История очищена", "info");
        });

        // Keyboard shortcut: Ctrl+Enter to analyze
        els.messageInput.addEventListener("keydown", (e) => {
            if ((e.ctrlKey || e.metaKey) && e.key === "Enter") {
                handleAnalyze();
            }
        });

        renderHistory();
    }

    // ──────────────────────────────────────────
    // Auth
    // ──────────────────────────────────────────

    async function handleAuth() {
        const password = els.authPassword.value.trim();
        if (!password) return;

        els.authBtn.disabled = true;

        try {
            const res = await fetch("/api/auth", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ password }),
            });

            if (res.ok) {
                const data = await res.json();
                state.token = data.message;
                localStorage.setItem("yarko_token", state.token);
                showMainScreen();
            } else {
                els.authError.classList.remove("hidden");
                els.authPassword.value = "";
                els.authPassword.focus();
            }
        } catch (err) {
            els.authError.querySelector("span").textContent = "Ошибка соединения";
            els.authError.classList.remove("hidden");
        } finally {
            els.authBtn.disabled = false;
        }
    }

    function showMainScreen() {
        els.authScreen.classList.add("hidden");
        els.mainScreen.classList.remove("hidden");
        els.messageInput.focus();
        if (window.lucide) window.lucide.createIcons();
    }

    // ──────────────────────────────────────────
    // Analyze
    // ──────────────────────────────────────────

    async function handleAnalyze() {
        const text = els.messageInput.value.trim();
        if (!text) {
            showToast("Введите сообщение", "error");
            return;
        }

        setLoading(true);

        try {
            if (state.batchMode) {
                await handleBatchAnalyze(text);
            } else {
                await handleSingleAnalyze(text);
            }
        } catch (err) {
            console.error("Analyze error:", err);
            showToast("Ошибка: " + (err.message || "Попробуйте позже"), "error");
        } finally {
            setLoading(false);
        }
    }

    async function handleSingleAnalyze(text) {
        const res = await apiFetch("/api/analyze", { message: text });
        state.lastResult = res;

        // Add to history
        addToHistory(text, res);

        // Show result
        renderSingleResult(res);
        els.resultSection.classList.remove("hidden");
        els.batchResultSection.classList.add("hidden");
        els.resultSection.scrollIntoView({ behavior: "smooth", block: "start" });
    }

    async function handleBatchAnalyze(text) {
        const messages = text
            .split(/^---$/m)
            .map((m) => m.trim())
            .filter((m) => m.length > 0);

        if (messages.length === 0) {
            showToast("Не найдено сообщений для разбора", "error");
            return;
        }

        const res = await apiFetch("/api/batch", { messages });
        state.lastBatchResults = res;

        // Add each to history
        messages.forEach((msg, i) => {
            if (res.results[i]) {
                addToHistory(msg, res.results[i]);
            }
        });

        // Show results
        renderBatchResults(res);
        els.batchResultSection.classList.remove("hidden");
        els.resultSection.classList.add("hidden");
        els.batchResultSection.scrollIntoView({ behavior: "smooth", block: "start" });
    }

    // ──────────────────────────────────────────
    // API
    // ──────────────────────────────────────────

    async function apiFetch(endpoint, body) {
        const headers = { "Content-Type": "application/json" };
        if (state.token) {
            headers["Authorization"] = `Bearer ${state.token}`;
        }

        const res = await fetch(endpoint, {
            method: "POST",
            headers,
            body: JSON.stringify(body),
        });

        if (res.status === 401) {
            // Token expired
            state.token = null;
            localStorage.removeItem("yarko_token");
            els.mainScreen.classList.add("hidden");
            els.authScreen.classList.remove("hidden");
            throw new Error("Сессия истекла. Войдите снова.");
        }

        if (res.status === 429) {
            throw new Error("Слишком много запросов. Подождите минуту.");
        }

        if (!res.ok) {
            const err = await res.json().catch(() => ({}));
            throw new Error(err.detail || `Ошибка ${res.status}`);
        }

        return res.json();
    }

    // ──────────────────────────────────────────
    // Render: Single Result
    // ──────────────────────────────────────────

    function renderSingleResult(result) {
        // Card view
        els.cardView.innerHTML = buildCardHTML(result);

        // JSON view
        els.jsonOutput.innerHTML = syntaxHighlight(
            JSON.stringify(result, null, 2)
        );

        // Cost
        els.costValue.textContent = `₽${(result.cost_rub || 0).toFixed(4)}`;
        const tokens = result.tokens_used || {};
        els.costTokens.textContent = tokens.input
            ? `${tokens.input} → ${tokens.output} токенов`
            : "";
            
        if (window.lucide) window.lucide.createIcons();
    }

    function buildCardHTML(r) {
        const intentConfig = {
            подбор_тура: { class: "tour", icon: "map", label: "Подбор тура" },
            проблема_срочно: { class: "urgent", icon: "flame", label: "Проблема (срочно!)" },
            общий_вопрос: { class: "question", icon: "help-circle", label: "Общий вопрос" },
            спам: { class: "spam", icon: "shield-alert", label: "Спам" },
        };
        
        const conf = intentConfig[r.intent] || intentConfig.общий_вопрос;
        const confidencePct = Math.round((r.confidence || 0) * 100);
        const confidenceColor =
            confidencePct >= 80
                ? "var(--intent-tour)"
                : confidencePct >= 50
                ? "var(--sentiment-neutral)"
                : "var(--intent-urgent)";

        let html = `
            <div class="intent-header">
                <span class="intent-badge ${conf.class}">
                    <i data-lucide="${conf.icon}"></i> ${conf.label}
                </span>
                <div class="confidence-container">
                    <div class="confidence-bar">
                        <div class="confidence-fill" style="width:${confidencePct}%;background:${confidenceColor}"></div>
                    </div>
                    <span class="confidence-text">Уверенность: ${confidencePct}%</span>
                </div>
            </div>
        `;

        // Parameters grid
        const params = [];
        if (r.people_count != null) {
            let val = `${r.people_count} чел.`;
            if (r.has_children) val += ` <i data-lucide="baby" style="width:14px;height:14px;display:inline;color:var(--text-muted)"></i>`;
            params.push(["users", "Люди", val]);
        }
        if (r.has_children && r.children_ages && r.children_ages.length > 0) {
            params.push(["baby", "Дети", r.children_ages.join(", ") + " лет"]);
        }
        if (r.budget_max != null) {
            const per = r.budget_per_person ? "/чел." : "";
            params.push(["wallet", "Бюджет", formatMoney(r.budget_max) + per]);
        }
        if (r.desired_dates) {
            params.push(["calendar", "Даты", r.desired_dates]);
        }
        if (r.is_urgent) {
            params.push(["zap", "Срочность", "Да (Высокая)"]);
        }
        if (r.sentiment) {
            const sentIcon = { 
                позитивный: "smile", 
                нейтральный: "meh", 
                негативный: "frown" 
            };
            params.push([sentIcon[r.sentiment] || "message-square", "Тон", r.sentiment]);
        }

        if (params.length > 0) {
            html += '<div class="params-grid">';
            for (const [icon, label, value] of params) {
                html += `
                    <div class="param-item">
                        <div class="param-label"><i data-lucide="${icon}"></i> ${label}</div>
                        <div class="param-value">${value}</div>
                    </div>
                `;
            }
            html += "</div>";
        }

        // Tags (destinations + special requests)
        const tags = [
            ...(r.destination_preferences || []),
            ...(r.special_requests || []),
        ];
        if (tags.length > 0) {
            html += '<div class="tags-row">';
            for (const tag of tags) {
                html += `<span class="tag"><i data-lucide="tag"></i> ${escapeHtml(tag)}</span>`;
            }
            html += "</div>";
        }

        // Notes
        if (r.notes) {
            html += `<div class="notes-box"><i data-lucide="info"></i> <span>${escapeHtml(r.notes)}</span></div>`;
        }

        // Draft reply
        if (r.draft_reply) {
            html += `
                <div class="draft-reply">
                    <div class="draft-reply-label"><i data-lucide="message-circle"></i> Черновик ответа</div>
                    ${escapeHtml(r.draft_reply)}
                </div>
            `;
        }

        return html;
    }

    // ──────────────────────────────────────────
    // Render: Batch Results
    // ──────────────────────────────────────────

    function renderBatchResults(data) {
        let html = "";
        data.results.forEach((r, i) => {
            const intentConf = getIntentConfig(r.intent);
            html += `
                <div class="batch-item" style="animation-delay:${i * 0.05}s">
                    <div class="batch-item-header">
                        <span class="batch-item-number">#${i + 1}</span>
                        <span class="intent-badge ${intentConf.class}" style="font-size:0.75rem;padding:4px 10px">
                            <i data-lucide="${intentConf.icon}"></i> ${r.intent}
                        </span>
                    </div>
                    ${buildCardHTML(r)}
                </div>
            `;
        });
        els.batchResults.innerHTML = html;
        els.batchCostValue.textContent = `₽${(data.total_cost_rub || 0).toFixed(4)}`;
        
        if (window.lucide) window.lucide.createIcons();
    }

    // ──────────────────────────────────────────
    // History
    // ──────────────────────────────────────────

    function addToHistory(message, result) {
        const item = {
            message: message.substring(0, 200),
            result,
            time: new Date().toLocaleTimeString("ru-RU", {
                hour: "2-digit",
                minute: "2-digit",
            }),
            timestamp: Date.now(),
        };
        state.history.unshift(item);
        if (state.history.length > 50) state.history.pop();
        localStorage.setItem("yarko_history", JSON.stringify(state.history));
        renderHistory();
    }

    function renderHistory() {
        if (state.history.length === 0) {
            els.historySection.classList.add("hidden");
            return;
        }

        els.historySection.classList.remove("hidden");
        let html = "";
        state.history.forEach((item, i) => {
            const intentConf = getIntentConfig(item.result.intent);
            html += `
                <div class="history-item" data-index="${i}">
                    <div class="history-item-left">
                        <span class="history-number">#${state.history.length - i}</span>
                        <span class="intent-badge ${intentConf.class}" style="font-size:0.7rem;padding:2px 8px">
                            <i data-lucide="${intentConf.icon}" style="width:12px;height:12px"></i>
                        </span>
                        <span class="history-preview">${escapeHtml(item.message)}</span>
                    </div>
                    <span class="history-time">${item.time}</span>
                </div>
            `;
        });
        els.historyList.innerHTML = html;

        // Click to view
        els.historyList.querySelectorAll(".history-item").forEach((el) => {
            el.addEventListener("click", () => {
                const idx = parseInt(el.dataset.index);
                const item = state.history[idx];
                if (item) {
                    state.lastResult = item.result;
                    renderSingleResult(item.result);
                    els.resultSection.classList.remove("hidden");
                    els.batchResultSection.classList.add("hidden");
                    els.resultSection.scrollIntoView({ behavior: "smooth" });
                }
            });
        });
        
        if (window.lucide) window.lucide.createIcons();
    }

    // ──────────────────────────────────────────
    // Export CSV
    // ──────────────────────────────────────────

    function downloadCSV(results) {
        const headers = [
            "intent", "confidence", "people_count", "has_children",
            "budget_max", "is_urgent", "desired_dates",
            "destination_preferences", "special_requests",
            "draft_reply", "notes", "cost_rub",
        ];

        let csv = headers.join(",") + "\n";
        for (const r of results) {
            const row = headers.map((h) => {
                let val = r[h];
                if (Array.isArray(val)) val = val.join("; ");
                if (val == null) val = "";
                return `"${String(val).replace(/"/g, '""')}"`;
            });
            csv += row.join(",") + "\n";
        }

        const blob = new Blob(["\uFEFF" + csv], { type: "text/csv;charset=utf-8" });
        downloadBlob(blob, "yarko-ai-results.csv");
        showToast("CSV скачан!", "success");
    }

    // ──────────────────────────────────────────
    // Helpers
    // ──────────────────────────────────────────

    function setLoading(loading) {
        els.analyzeBtn.disabled = loading;
        els.btnText.classList.toggle("hidden", loading);
        els.btnLoading.classList.toggle("hidden", !loading);
    }

    function getIntentConfig(intent) {
        const map = {
            подбор_тура: { class: "tour", icon: "map" },
            проблема_срочно: { class: "urgent", icon: "flame" },
            общий_вопрос: { class: "question", icon: "help-circle" },
            спам: { class: "spam", icon: "shield-alert" },
        };
        return map[intent] || map["общий_вопрос"];
    }

    function formatMoney(amount) {
        return "до " + amount.toLocaleString("ru-RU") + " ₽";
    }

    function escapeHtml(text) {
        const div = document.createElement("div");
        div.textContent = text;
        return div.innerHTML;
    }

    function syntaxHighlight(json) {
        return json.replace(
            /("(\\u[a-zA-Z0-9]{4}|\\[^u]|[^\\"])*"(\s*:)?|\b(true|false|null)\b|-?\d+(?:\.\d*)?(?:[eE][+-]?\d+)?)/g,
            (match) => {
                let cls = "json-number";
                if (/^"/.test(match)) {
                    cls = /:$/.test(match) ? "json-key" : "json-string";
                } else if (/true|false/.test(match)) {
                    cls = "json-bool";
                } else if (/null/.test(match)) {
                    cls = "json-null";
                }
                return `<span class="${cls}">${match}</span>`;
            }
        );
    }

    function copyToClipboard(text) {
        navigator.clipboard.writeText(text).catch(() => {
            // Fallback
            const ta = document.createElement("textarea");
            ta.value = text;
            document.body.appendChild(ta);
            ta.select();
            document.execCommand("copy");
            document.body.removeChild(ta);
        });
    }

    function downloadBlob(blob, filename) {
        const url = URL.createObjectURL(blob);
        const a = document.createElement("a");
        a.href = url;
        a.download = filename;
        a.click();
        URL.revokeObjectURL(url);
    }

    function showToast(message, type = "success") {
        const toast = document.createElement("div");
        toast.className = `toast ${type}`;
        
        const icons = {
            success: 'check-circle-2',
            error: 'alert-circle',
            info: 'info'
        };
        
        toast.innerHTML = `<i data-lucide="${icons[type]}"></i> <span>${message}</span>`;
        els.toastContainer.appendChild(toast);
        
        if (window.lucide) window.lucide.createIcons();
        
        setTimeout(() => toast.remove(), 2800);
    }

    // ──────────────────────────────────────────
    // Start
    // ──────────────────────────────────────────

    document.addEventListener("DOMContentLoaded", init);
})();
