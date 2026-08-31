with open("static/style.css", "r", encoding="utf-8") as f:
    content = f.read()

# 1. Hide mobile select on desktop, hide tabs on mobile
new_css = """
.mobile-mode-select-container {
    display: none;
    margin-bottom: 24px;
    padding: 0 16px;
}
.mobile-mode-select {
    width: 100%;
    font-weight: 600;
    font-size: 1rem;
    appearance: none;
    background-image: url("data:image/svg+xml;charset=UTF-8,%3csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' stroke='currentColor' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'%3e%3cpolyline points='6 9 12 15 18 9'%3e%3c/polyline%3e%3c/svg%3e");
    background-repeat: no-repeat;
    background-position: right 1rem center;
    background-size: 1em;
}

.sim-mobile-tabs {
    display: none;
    margin-bottom: 16px;
    border-bottom: 1px solid var(--border-color);
}
.sim-mobile-tab {
    flex: 1;
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 8px;
    padding: 12px;
    background: transparent;
    border: none;
    font-weight: 600;
    color: var(--text-secondary);
    border-bottom: 2px solid transparent;
}
.sim-mobile-tab.active {
    color: var(--text-primary);
    border-bottom-color: var(--accent-blue);
}

@media (max-width: 768px) {
    .global-tabs-container {
        display: none;
    }
    .mobile-mode-select-container {
        display: block;
    }
    
    .sim-mobile-tabs {
        display: flex;
    }
    
    .simulator-chat.hidden-mobile {
        display: none !important;
    }
    .simulator-result.hidden-mobile {
        display: none !important;
    }
}
"""

content += new_css

with open("static/style.css", "w", encoding="utf-8") as f:
    f.write(content)
print("Updated style.css")
