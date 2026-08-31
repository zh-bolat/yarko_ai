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
        mode: "single", // "single", "batch", "simulator"
        jsonView: false,
        lastResult: null,
        lastBatchResults: null,
        simHistory: [], // array of {role: 'user'|'bot', text: string}
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

        globalTabs: $$(".global-tab"),
        mobileModeSelect: $("#mobile-mode-select"),
        simMobileTabs: $$(".sim-mobile-tab"),
        simChatPanel: $(".simulator-chat"),
        simResultPanel: $(".simulator-result"),
        
        standardModeSection: $("#standard-mode-section"),
        simulatorModeSection: $("#simulator-mode-section"),
        historySection: $("#history-section"),
        
        innerTabs: $$(".inner-tab"),
        tabInput: $("#tab-input"),
        tabResult: $("#tab-result"),
        tabBtnResult: $("#tab-btn-result"),
        backToInputBtn: $("#back-to-input-btn"),

        messageInput: $("#message-input"),
        analyzeBtn: $("#analyze-btn"),
        clearBtn: $("#clear-btn"),
        btnText: $(".btn-text"),
        btnLoading: $(".btn-loading"),
        batchHint: $("#batch-hint"),

        // Results
        singleResultContainer: $("#single-result-container"),
        batchResultContainer: $("#batch-result-container"),
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
        batchSegmentBtns: $$(".batch-segment-btn"),
        batchCardView: $("#batch-card-view"),
        batchJsonView: $("#batch-json-view"),
        batchJsonOutput: $("#batch-json-output"),

        historyList: $("#history-list"),
        clearHistoryBtn: $("#clear-history-btn"),

        // Simulator
        simMessages: $("#sim-messages"),
        simInput: $("#sim-input"),
        simSendBtn: $("#sim-send-btn"),
        simResetBtn: $("#sim-reset-btn"),
        simCardContent: $("#sim-card-content"),
        simLoading: $("#sim-loading"),

        toastContainer: $("#toast-container"),
    };

    // ──────────────────────────────────────────
    // Init
    // ──────────────────────────────────────────

    function init() {
        if (state.token) showMainScreen();

        els.authBtn.addEventListener("click", handleAuth);
        els.authPassword.addEventListener("keydown", (e) => {
            if (e.key === "Enter") handleAuth();
        });

        // Global Modes
        els.globalTabs.forEach(tab => {
            tab.addEventListener("click", () => switchMode(tab.dataset.mode));
        });

        // Inner Tabs
        els.innerTabs.forEach(tab => {
            tab.addEventListener("click", () => {
                if (!tab.disabled) switchInnerTab(tab.dataset.tab);
            });
        });

        els.backToInputBtn.addEventListener("click", () => switchInnerTab("input"));
        
        // Mobile Mode Select
        if (els.mobileModeSelect) {
            els.mobileModeSelect.addEventListener("change", (e) => switchMode(e.target.value));
        }

        // Simulator Mobile Tabs
        if (els.simMobileTabs) {
            els.simMobileTabs.forEach(tab => {
                tab.addEventListener("click", () => {
                    els.simMobileTabs.forEach(t => t.classList.remove("active"));
                    tab.classList.add("active");
                    
                    if (tab.dataset.tab === "chat") {
                        els.simChatPanel.classList.remove("hidden-mobile");
                        els.simResultPanel.classList.add("hidden-mobile");
                    } else {
                        els.simChatPanel.classList.add("hidden-mobile");
                        els.simResultPanel.classList.remove("hidden-mobile");
                    }
                });
            });
            if (els.simResultPanel) els.simResultPanel.classList.add("hidden-mobile");
        }

        // Batch Segmented Control
        if (els.batchSegmentBtns) {
            els.batchSegmentBtns.forEach(btn => {
                btn.addEventListener("click", () => {
                    const target = btn.dataset.target;
                    els.batchSegmentBtns.forEach(b => b.classList.remove("active"));
                    btn.classList.add("active");
                    
                    if (target === "batch-json-view") {
                        els.batchCardView.classList.remove("active");
                        els.batchJsonView.classList.add("active");
                        
                        const indicator = btn.closest(".segment-control").querySelector(".segment-indicator");
                        if (indicator) indicator.style.transform = `translateX(100%)`;
                    } else {
                        els.batchCardView.classList.add("active");
                        els.batchJsonView.classList.remove("active");
                        
                        const indicator = btn.closest(".segment-control").querySelector(".segment-indicator");
                        if (indicator) indicator.style.transform = `translateX(0)`;
                    }
                });
            });
        }

        // Analyze
        els.analyzeBtn.addEventListener("click", handleAnalyze);
        els.clearBtn.addEventListener("click", () => {
            els.messageInput.value = "";
            els.messageInput.focus();
        });

        // Segmented Control (card / JSON)
        els.segmentBtns.forEach(btn => {
            btn.addEventListener("click", () => {
                const target = btn.dataset.target;
                els.segmentBtns.forEach(b => b.classList.remove("active"));
                btn.classList.add("active");
                
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

        // Batch copy/CSV
        els.batchCopyBtn.addEventListener("click", () => {
            if (state.lastBatchResults) {
                copyToClipboard(JSON.stringify(state.lastBatchResults, null, 2));
                showToast("Все результаты скопированы!", "success");
            }
        });
        els.batchCsvBtn.addEventListener("click", () => {
            if (state.lastBatchResults) downloadCSV(state.lastBatchResults.results);
        });

        // History
        els.clearHistoryBtn.addEventListener("click", () => {
            state.history = [];
            localStorage.removeItem("yarko_history");
            renderHistory();
            showToast("История очищена", "info");
        });

        els.messageInput.addEventListener("keydown", (e) => {
            if ((e.ctrlKey || e.metaKey) && e.key === "Enter") handleAnalyze();
        });

        // Simulator
        els.simSendBtn.addEventListener("click", handleSimSend);
        els.simInput.addEventListener("keydown", (e) => {
            if (e.key === "Enter" && !e.shiftKey) {
                e.preventDefault();
                handleSimSend();
            }
        });
        els.simResetBtn.addEventListener("click", handleSimReset);

        renderHistory();
        
        // Initialize tabs positioning after a short delay for layout
        setTimeout(() => switchMode(state.mode), 100);
    }

    // ──────────────────────────────────────────
    // Tabs & Modes
    // ──────────────────────────────────────────
    function switchMode(mode) {
        state.mode = mode;
        if (els.mobileModeSelect && els.mobileModeSelect.value !== mode) els.mobileModeSelect.value = mode;
        
        // Update tabs UI and move the white border indicator
        els.globalTabs.forEach(t => {
            t.classList.toggle("active", t.dataset.mode === mode);
            if (t.dataset.mode === mode) {
                const indicator = $(".global-tab-indicator");
                if (indicator) {
                    indicator.style.width = `${t.offsetWidth}px`;
                    indicator.style.transform = `translateX(${t.offsetLeft}px)`;
                }
            }
        });

        if (mode === "simulator") {
            els.standardModeSection.classList.add("hidden");
            els.simulatorModeSection.classList.remove("hidden");
        } else {
            els.standardModeSection.classList.remove("hidden");
            els.simulatorModeSection.classList.add("hidden");
            
            // Single vs Batch configuration
            const isBatch = mode === "batch";
            els.batchHint.classList.toggle("hidden", !isBatch);
            els.messageInput.placeholder = isBatch ? "Вставьте список сообщений (система разделит их автоматически)" : "Вставьте сообщение туриста...";
            
            // Switch back to input when changing mode
            switchInnerTab("input");
            els.tabBtnResult.disabled = true;
            els.backToInputBtn.closest(".back-to-input").classList.add("hidden");
        }
        
        renderHistory(); // Hide history in batch mode
    }

    function switchInnerTab(tabName) {
        els.innerTabs.forEach(t => t.classList.toggle("active", t.dataset.tab === tabName));
        els.tabInput.classList.toggle("active", tabName === "input");
        els.tabResult.classList.toggle("active", tabName === "result");

        if (tabName === "result") {
            els.tabBtnResult.disabled = false;
            els.backToInputBtn.closest(".back-to-input").classList.remove("hidden");
        }
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
            if (state.mode === "batch") {
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
        addToHistory(text, res);
        
        renderSingleResult(res);
        els.singleResultContainer.classList.remove("hidden");
        els.batchResultContainer.classList.add("hidden");
        
        switchInnerTab("result");
    }

    async function handleBatchAnalyze(text) {
        let messages = [];

        if (/^\s*---\s*$/m.test(text)) {
            messages = text.split(/^\s*---\s*$/m);
        } else if (/\n\s*\n/.test(text)) {
            messages = text.split(/\n\s*\n/);
        } else if (/^\s*\d+\.\s/m.test(text)) {
            messages = text.split(/^\s*\d+\.\s/m);
        } else {
            messages = text.split('\n');
        }

        messages = messages.map(m => m.trim()).filter(m => m.length > 0);

        if (messages.length === 0) {
            showToast("Не найдено сообщений для разбора", "error");
            return;
        }

        const res = await apiFetch("/api/batch", { messages });
        state.lastBatchResults = res;

        messages.forEach((msg, i) => {
            if (res.results[i]) addToHistory(msg, res.results[i]);
        });

        renderBatchResults(res);
        els.singleResultContainer.classList.add("hidden");
        els.batchResultContainer.classList.remove("hidden");
        
        switchInnerTab("result");
    }

    // ──────────────────────────────────────────
    // Simulator
    // ──────────────────────────────────────────
    async function handleSimSend() {
        const text = els.simInput.value.trim();
        if (!text) return;
        
        els.simInput.value = "";
        
        // Add to history
        state.simHistory.push({ role: "user", text });
        renderSimChat();
        
        els.simLoading.classList.remove("hidden");
        
        try {
            // Concatenate history for AI
            const combinedText = state.simHistory.map(msg => `${msg.role === 'user' ? 'Турист' : 'Бот'}: ${msg.text}`).join('\n\n');
            const res = await apiFetch("/api/analyze", { message: combinedText });
            
            if (res.draft_reply) {
                state.simHistory.push({ role: "bot", text: res.draft_reply });
                renderSimChat();
            }
            els.simCardContent.classList.remove("sim-card-empty");
            els.simCardContent.innerHTML = buildCardHTML(res);
            if (window.lucide) window.lucide.createIcons();
            
        } catch (err) {
            showToast("Ошибка симулятора: " + (err.message || "Сбой"), "error");
        } finally {
            els.simLoading.classList.add("hidden");
        }
    }
    
    function renderSimChat() {
        if (state.simHistory.length === 0) {
            els.simMessages.innerHTML = `
                <div class="chat-message bot">
                    <div class="msg-bubble">Отправьте первую реплику туриста, чтобы начать симуляцию сбора данных.</div>
                </div>
            `;
            return;
        }
        
        els.simMessages.innerHTML = state.simHistory.map(msg => `
            <div class="chat-message ${msg.role}">
                <div class="msg-bubble">${escapeHtml(msg.text)}</div>
            </div>
        `).join("");
        
        els.simMessages.scrollTop = els.simMessages.scrollHeight;
    }
    
    function handleSimReset() {
        state.simHistory = [];
        renderSimChat();
        els.simCardContent.classList.add("sim-card-empty");
        els.simCardContent.innerHTML = `
            <i data-lucide="layout-template"></i>
            <p>Карточка сформируется после первого сообщения</p>
        `;
        if (window.lucide) window.lucide.createIcons();
    }

    // ──────────────────────────────────────────
    // API
    // ──────────────────────────────────────────
    async function apiFetch(endpoint, body) {
        const headers = { "Content-Type": "application/json" };
        if (state.token) headers["Authorization"] = `Bearer ${state.token}`;

        const res = await fetch(endpoint, {
            method: "POST",
            headers,
            body: JSON.stringify(body),
        });

        if (res.status === 401) {
            state.token = null;
            localStorage.removeItem("yarko_token");
            els.mainScreen.classList.add("hidden");
            els.authScreen.classList.remove("hidden");
            throw new Error("Сессия истекла. Войдите снова.");
        }
        if (res.status === 429) throw new Error("Слишком много запросов.");
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
        els.cardView.innerHTML = buildCardHTML(result);
        els.jsonOutput.innerHTML = syntaxHighlight(JSON.stringify(result, null, 2));
        els.costValue.textContent = `₽${(result.cost_rub || 0).toFixed(4)}`;
        const tokens = result.tokens_used || {};
        els.costTokens.textContent = tokens.input ? `${tokens.input} → ${tokens.output} токенов` : "";
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
        const confidenceColor = confidencePct >= 80 ? "var(--intent-tour)" : confidencePct >= 50 ? "#facc15" : "var(--intent-urgent)";

        let html = `
            <div class="card-view">
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
        if (r.desired_dates) params.push(["calendar", "Даты", r.desired_dates]);
        if (r.is_urgent) params.push(["zap", "Срочность", "Да (Высокая)"]);

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

        const tags = [...(r.destination_preferences || []), ...(r.special_requests || [])];
        if (tags.length > 0) {
            html += '<div class="tags-row">';
            for (const tag of tags) html += `<span class="tag"><i data-lucide="tag"></i> ${escapeHtml(tag)}</span>`;
            html += "</div>";
        }

        if (r.notes) html += `<div class="notes-box mt-4" style="margin-top:16px"><i data-lucide="info"></i> <span>${escapeHtml(r.notes)}</span></div>`;
        if (r.draft_reply) {
            html += `
                <div class="draft-reply mt-4" style="margin-top:16px">
                    <div class="draft-reply-label"><i data-lucide="message-circle"></i> Черновик ответа</div>
                    ${escapeHtml(r.draft_reply)}
                </div>
            `;
        }

        html += '</div>'; // close .card-view
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
                        <span class="batch-item-number">Заявка #${i + 1}</span>
                    </div>
                    ${buildCardHTML(r)}
                </div>
            `;
        });
        els.batchResults.innerHTML = html;
        if (els.batchJsonOutput) els.batchJsonOutput.innerHTML = syntaxHighlight(JSON.stringify(data, null, 2));
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
            time: new Date().toLocaleTimeString("ru-RU", { hour: "2-digit", minute: "2-digit" }),
            timestamp: Date.now(),
        };
        state.history.unshift(item);
        if (state.history.length > 50) state.history.pop();
        localStorage.setItem("yarko_history", JSON.stringify(state.history));
        renderHistory();
    }

    function renderHistory() {
        if (state.history.length === 0 || state.mode !== "single") {
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

        els.historyList.querySelectorAll(".history-item").forEach((el) => {
            el.addEventListener("click", () => {
                const idx = parseInt(el.dataset.index);
                const item = state.history[idx];
                if (item) {
                    state.lastResult = item.result;
                    renderSingleResult(item.result);
                    els.singleResultContainer.classList.remove("hidden");
                    els.batchResultContainer.classList.add("hidden");
                    switchInnerTab("result");
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
                if (/^"/.test(match)) cls = /:$/.test(match) ? "json-key" : "json-string";
                else if (/true|false/.test(match)) cls = "json-bool";
                else if (/null/.test(match)) cls = "json-null";
                return `<span class="${cls}">${match}</span>`;
            }
        );
    }

    function copyToClipboard(text) {
        navigator.clipboard.writeText(text).catch(() => {
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
        const icons = { success: 'check-circle-2', error: 'alert-circle', info: 'info' };
        toast.innerHTML = `<i data-lucide="${icons[type]}"></i> <span>${message}</span>`;
        els.toastContainer.appendChild(toast);
        if (window.lucide) window.lucide.createIcons();
        setTimeout(() => toast.remove(), 2800);
    }

    document.addEventListener("DOMContentLoaded", init);
})();
