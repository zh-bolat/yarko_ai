import re

with open("static/index.html", "r", encoding="utf-8") as f:
    content = f.read()

new_main = """        <main class="main-content">
            <!-- Глобальные вкладки (Режимы) -->
            <div class="global-tabs-container">
                <div class="global-tabs">
                    <button class="global-tab active" data-mode="single">
                        <i data-lucide="zap"></i> Быстрый разбор
                    </button>
                    <button class="global-tab" data-mode="batch">
                        <i data-lucide="layers"></i> Несколько заявок
                    </button>
                    <button class="global-tab" data-mode="simulator">
                        <i data-lucide="message-square"></i> Симулятор чата
                    </button>
                    <div class="global-tab-indicator"></div>
                </div>
            </div>

            <!-- Режим: Быстрый разбор / Пакетная загрузка -->
            <section id="standard-mode-section" class="mode-section active">
                <div class="card card-tabs-wrapper">
                    <!-- Внутренние вкладки -->
                    <div class="inner-tabs">
                        <button class="inner-tab active" data-tab="input">
                            <i data-lucide="edit-3"></i> Ввод
                        </button>
                        <button class="inner-tab" data-tab="result" disabled id="tab-btn-result">
                            <i data-lucide="sparkles"></i> Результат
                        </button>
                    </div>

                    <!-- Вкладка Ввод -->
                    <div id="tab-input" class="tab-pane active">
                        <textarea 
                            id="message-input" 
                            class="textarea" 
                            placeholder="Вставьте сообщение туриста..."
                            rows="6"
                        ></textarea>
                        <p id="batch-hint" class="hint hidden" style="margin-top:12px;">
                            <i data-lucide="info"></i>
                            Система сама разделит ваши сообщения. Можно вставить список с нумерацией или пустыми строками.
                        </p>
                        <div class="input-actions mt-4">
                            <button id="analyze-btn" class="btn btn-primary">
                                <span class="btn-text">Анализировать</span>
                                <span class="btn-loading hidden">
                                    <i data-lucide="loader-2" class="spinner-icon"></i> Обработка...
                                </span>
                            </button>
                            <button id="clear-btn" class="btn btn-ghost" title="Очистить">
                                <i data-lucide="trash-2"></i>
                            </button>
                        </div>
                    </div>

                    <!-- Вкладка Результат -->
                    <div id="tab-result" class="tab-pane">
                        <div class="back-to-input mb-4 hidden">
                            <button id="back-to-input-btn" class="btn-ghost btn btn-small">
                                <i data-lucide="arrow-left"></i> Назад к вводу
                            </button>
                        </div>
                        
                        <div id="single-result-container">
                            <div class="segment-control-wrapper">
                                <div class="segment-control">
                                    <button class="segment-btn active" data-target="card-view">
                                        <i data-lucide="layout-template"></i> Карточка
                                    </button>
                                    <button class="segment-btn" data-target="json-view">
                                        <i data-lucide="file-json-2"></i> JSON
                                    </button>
                                    <div class="segment-indicator"></div>
                                </div>
                                <button id="copy-btn" class="btn-icon btn-icon-small" title="Копировать">
                                    <i data-lucide="copy"></i>
                                </button>
                            </div>
                            <div class="result-body">
                                <div id="card-view" class="sub-tab-content active"></div>
                                <div id="json-view" class="sub-tab-content json-wrapper">
                                    <pre><code id="json-output"></code></pre>
                                </div>
                            </div>
                            <div class="cost-bar mt-4">
                                <div class="cost-left">
                                    <span class="cost-label">Стоимость:</span>
                                    <span id="cost-value" class="cost-value">₽0.00</span>
                                </div>
                                <span class="cost-tokens" id="cost-tokens"></span>
                            </div>
                        </div>

                        <div id="batch-result-container" class="hidden">
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
                        </div>
                    </div>
                </div>
                
                <!-- История (показывается только для Single режима) -->
                <section id="history-section" class="history-section hidden mt-8">
                    <div class="card">
                        <div class="result-header">
                            <h2>История</h2>
                            <button id="clear-history-btn" class="btn-icon" title="Clear History">
                                <i data-lucide="trash-2"></i>
                            </button>
                        </div>
                        <div id="history-list" class="history-list"></div>
                    </div>
                </section>
            </section>

            <!-- Режим: Симулятор чата -->
            <section id="simulator-mode-section" class="mode-section hidden">
                <div class="simulator-layout">
                    <!-- Левая панель: Чат -->
                    <div class="card simulator-chat">
                        <div class="chat-header">
                            <h2 style="font-size:1rem;font-weight:600;display:flex;align-items:center;gap:8px;">
                                <i data-lucide="message-circle" style="width:18px;height:18px;"></i> Чат
                            </h2>
                            <button id="sim-reset-btn" class="btn-icon btn-icon-small" title="Сбросить">
                                <i data-lucide="rotate-ccw"></i>
                            </button>
                        </div>
                        <div id="sim-messages" class="chat-messages">
                            <div class="chat-message bot">
                                <div class="msg-bubble">Отправьте первую реплику туриста, чтобы начать симуляцию сбора данных.</div>
                            </div>
                        </div>
                        <div class="chat-input-area">
                            <textarea id="sim-input" class="textarea" placeholder="Турист пишет..." rows="2"></textarea>
                            <button id="sim-send-btn" class="btn-primary sim-send" title="Отправить">
                                <i data-lucide="send"></i>
                            </button>
                        </div>
                    </div>

                    <!-- Правая панель: Живая карточка -->
                    <div class="card simulator-result">
                        <div class="chat-header">
                            <h2 style="font-size:1rem;font-weight:600;display:flex;align-items:center;gap:8px;">
                                <i data-lucide="sparkles" style="width:18px;height:18px;"></i> Живая карточка (Merge)
                            </h2>
                            <span id="sim-loading" class="sim-loading hidden"><i data-lucide="loader-2" class="spinner-icon"></i></span>
                        </div>
                        <div id="sim-card-content" class="sim-card-empty">
                            <i data-lucide="layout-template"></i>
                            <p>Карточка сформируется после первого сообщения</p>
                        </div>
                    </div>
                </div>
            </section>
        </main>"""

start_idx = content.find('<main class="main-content">')
end_idx = content.find('</main>') + 7

new_content = content[:start_idx] + new_main + content[end_idx:]

with open("static/index.html", "w", encoding="utf-8") as f:
    f.write(new_content)
print("Updated index.html")
