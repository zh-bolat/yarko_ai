with open("static/style.css", "a", encoding="utf-8") as f:
    f.write("""
/* ══════════════════════════════════════════════
   NEW UX: GLOBAL TABS & SIMULATOR
   ══════════════════════════════════════════════ */

/* ─── Global Tabs (Header) ─── */
.global-tabs-container {
    display: flex;
    justify-content: center;
    margin-bottom: 24px;
}

.global-tabs {
    position: relative;
    display: inline-flex;
    background: var(--bg-secondary);
    padding: 6px;
    border-radius: var(--radius-xl);
    border: 1px solid var(--border-color);
}

.global-tab {
    position: relative;
    z-index: 2;
    display: flex;
    align-items: center;
    gap: 8px;
    padding: 10px 20px;
    border: none;
    background: transparent;
    font-family: inherit;
    font-size: 0.9375rem;
    font-weight: 600;
    color: var(--text-secondary);
    cursor: pointer;
    transition: color var(--transition-fast);
}

.global-tab i { width: 18px; height: 18px; }
.global-tab.active { color: var(--text-primary); }

.global-tab-indicator {
    position: absolute;
    top: 6px; bottom: 6px; left: 6px;
    width: calc(33.333% - 4px); /* Fallback */
    background: white;
    border-radius: var(--radius-lg);
    box-shadow: 0 1px 3px rgba(0,0,0,0.1);
    transition: transform var(--transition-normal), width var(--transition-normal), left var(--transition-normal);
    z-index: 1;
}

/* ─── Inner Tabs (Input/Result) ─── */
.card-tabs-wrapper {
    padding: 0;
    overflow: hidden;
}

.inner-tabs {
    display: flex;
    border-bottom: 1px solid var(--border-color);
    background: var(--bg-secondary);
}

.inner-tab {
    flex: 1;
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 8px;
    padding: 16px;
    background: transparent;
    border: none;
    font-family: inherit;
    font-size: 0.9375rem;
    font-weight: 600;
    color: var(--text-secondary);
    cursor: pointer;
    transition: all var(--transition-fast);
    border-bottom: 2px solid transparent;
}

.inner-tab:not(:disabled):hover {
    background: rgba(0,0,0,0.02);
    color: var(--text-primary);
}

.inner-tab.active {
    color: var(--text-primary);
    background: var(--bg-primary);
    border-bottom-color: var(--accent-blue);
}

.inner-tab:disabled {
    opacity: 0.5;
    cursor: not-allowed;
}

.tab-pane {
    display: none;
    padding: 24px;
    animation: fadeIn 0.3s ease;
}

.tab-pane.active {
    display: block;
}

/* ─── Simulator Layout ─── */
.simulator-layout {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 24px;
    align-items: stretch;
}

.simulator-chat, .simulator-result {
    display: flex;
    flex-direction: column;
    padding: 0;
    overflow: hidden;
    height: 600px;
}

.chat-header {
    padding: 16px;
    border-bottom: 1px solid var(--border-color);
    background: var(--bg-secondary);
    display: flex;
    align-items: center;
    justify-content: space-between;
}

.chat-messages {
    flex: 1;
    padding: 16px;
    overflow-y: auto;
    display: flex;
    flex-direction: column;
    gap: 16px;
    background: var(--bg-primary);
}

.chat-message {
    display: flex;
    flex-direction: column;
    max-width: 85%;
}

.chat-message.user {
    align-self: flex-end;
}

.chat-message.bot {
    align-self: flex-start;
}

.msg-bubble {
    padding: 12px 16px;
    border-radius: 18px;
    font-size: 0.9375rem;
    line-height: 1.5;
}

.chat-message.user .msg-bubble {
    background: var(--accent-blue);
    color: white;
    border-bottom-right-radius: 4px;
}

.chat-message.bot .msg-bubble {
    background: var(--bg-secondary);
    color: var(--text-primary);
    border-bottom-left-radius: 4px;
    border: 1px solid var(--border-color);
}

.chat-input-area {
    padding: 16px;
    border-top: 1px solid var(--border-color);
    background: var(--bg-primary);
    display: flex;
    gap: 12px;
    align-items: flex-end;
}

.chat-input-area .textarea {
    min-height: 44px;
    padding: 10px 14px;
}

.sim-send {
    width: 44px; height: 44px;
    border-radius: 50%;
    padding: 0;
    flex-shrink: 0;
    display: flex; align-items: center; justify-content: center;
}

#sim-card-content {
    flex: 1;
    overflow-y: auto;
    padding: 24px;
}

.sim-card-empty {
    height: 100%;
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    gap: 12px;
    color: var(--text-muted);
}
.sim-card-empty i { width: 48px; height: 48px; opacity: 0.5; }

@media (max-width: 768px) {
    .simulator-layout {
        grid-template-columns: 1fr;
    }
    .simulator-chat, .simulator-result {
        height: 500px;
    }
    .global-tabs-container {
        overflow-x: auto;
        padding-bottom: 8px;
        justify-content: flex-start;
    }
}
""")
print("CSS updated")
