with open("static/index.html", "r", encoding="utf-8") as f:
    content = f.read()

# 1. Add mobile select and update global tabs
mobile_select = """
            <div class="mobile-mode-select-container">
                <select id="mobile-mode-select" class="input mobile-mode-select">
                    <option value="single">⚡ Быстрый разбор</option>
                    <option value="batch">📚 Несколько заявок</option>
                    <option value="simulator">💬 Симулятор чата</option>
                </select>
            </div>
"""

content = content.replace('<!-- Глобальные вкладки (Режимы) -->', '<!-- Глобальные вкладки (Режимы) -->\n' + mobile_select)

# 2. Fix sub-tab-content
content = content.replace('id="card-view" class="sub-tab-content active"', 'id="card-view" class="tab-content active"')
content = content.replace('id="json-view" class="sub-tab-content json-wrapper"', 'id="json-view" class="tab-content json-wrapper"')

# 3. Add segmented control for batch and json view
batch_result_old = """                        <div id="batch-result-container" class="hidden">
                            <div class="result-header">
                                <h2>Результаты</h2>
                                <div class="result-actions">
                                    <button id="batch-copy-btn" class="btn-icon" title="Copy All">
                                        <i data-lucide="copy"></i>
                                    </button>
                                    <button id="batch-csv-btn" class="btn-icon" title="Download CSV">
                                        <i data-lucide="file-spreadsheet"></i>
                                    </button>
                                </div>
                            </div>
                            <div id="batch-results" class="batch-results"></div>
                            <div class="cost-bar mt-4">
                                <div class="cost-left">
                                    <span class="cost-label">Общая стоимость:</span>
                                    <span id="batch-cost-value" class="cost-value">₽0.00</span>
                                </div>
                            </div>
                        </div>"""

batch_result_new = """                        <div id="batch-result-container" class="hidden">
                            <div class="result-header" style="margin-bottom:16px;">
                                <h2>Результаты</h2>
                                <div class="result-actions">
                                    <button id="batch-copy-btn" class="btn-icon" title="Copy All">
                                        <i data-lucide="copy"></i>
                                    </button>
                                    <button id="batch-csv-btn" class="btn-icon" title="Download CSV">
                                        <i data-lucide="file-spreadsheet"></i>
                                    </button>
                                </div>
                            </div>
                            
                            <div class="segment-control-wrapper">
                                <div class="segment-control">
                                    <button class="segment-btn batch-segment-btn active" data-target="batch-card-view">
                                        <i data-lucide="layout-template"></i> Карточки
                                    </button>
                                    <button class="segment-btn batch-segment-btn" data-target="batch-json-view">
                                        <i data-lucide="file-json-2"></i> JSON
                                    </button>
                                    <div class="segment-indicator batch-segment-indicator"></div>
                                </div>
                            </div>
                            
                            <div class="result-body">
                                <div id="batch-card-view" class="tab-content batch-tab-content active">
                                    <div id="batch-results" class="batch-results"></div>
                                </div>
                                <div id="batch-json-view" class="tab-content batch-tab-content json-wrapper">
                                    <pre><code id="batch-json-output"></code></pre>
                                </div>
                            </div>

                            <div class="cost-bar mt-4">
                                <div class="cost-left">
                                    <span class="cost-label">Общая стоимость:</span>
                                    <span id="batch-cost-value" class="cost-value">₽0.00</span>
                                </div>
                            </div>
                        </div>"""

content = content.replace(batch_result_old, batch_result_new)

# 4. Add Simulator mobile tabs
simulator_layout_old = '<div class="simulator-layout">'
simulator_layout_new = """                <!-- Мобильные вкладки симулятора -->
                <div class="sim-mobile-tabs">
                    <button class="sim-mobile-tab active" data-tab="chat"><i data-lucide="message-circle"></i> Чат</button>
                    <button class="sim-mobile-tab" data-tab="card"><i data-lucide="sparkles"></i> Карточка</button>
                </div>
                <div class="simulator-layout">"""

content = content.replace(simulator_layout_old, simulator_layout_new)

with open("static/index.html", "w", encoding="utf-8") as f:
    f.write(content)
print("Updated index.html")
