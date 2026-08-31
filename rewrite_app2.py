with open("static/app.js", "r", encoding="utf-8") as f:
    content = f.read()

# 1. Add elements to state and els
content = content.replace('globalTabs: $$(".global-tab"),', 'globalTabs: $$(".global-tab"),\n        mobileModeSelect: $("#mobile-mode-select"),\n        simMobileTabs: $$(".sim-mobile-tab"),\n        simChatPanel: $(".simulator-chat"),\n        simResultPanel: $(".simulator-result"),\n        batchSegmentBtns: $$(".batch-segment-btn"),\n        batchSegmentControl: $(".segment-control-wrapper .segment-control"),\n        batchCardView: $("#batch-card-view"),\n        batchJsonView: $("#batch-json-view"),\n        batchJsonOutput: $("#batch-json-output"),')

# 2. Add listeners in init()
listeners = """
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
            // Initial mobile state
            els.simResultPanel.classList.add("hidden-mobile");
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
"""
content = content.replace('els.backToInputBtn.addEventListener("click", () => switchInnerTab("input"));', 'els.backToInputBtn.addEventListener("click", () => switchInnerTab("input"));\n' + listeners)

# 3. Update switchMode to also set select value
mode_sync = """
        // Sync mobile select
        if (els.mobileModeSelect && els.mobileModeSelect.value !== mode) {
            els.mobileModeSelect.value = mode;
        }
"""
content = content.replace('state.mode = mode;', 'state.mode = mode;\n' + mode_sync)

# 4. Update batch render to populate JSON
batch_json = """        if (els.batchJsonOutput) {
            els.batchJsonOutput.innerHTML = syntaxHighlight(JSON.stringify(data, null, 2));
        }
"""
content = content.replace('els.batchResults.innerHTML = html;', 'els.batchResults.innerHTML = html;\n' + batch_json)

with open("static/app.js", "w", encoding="utf-8") as f:
    f.write(content)
print("Updated app.js")
