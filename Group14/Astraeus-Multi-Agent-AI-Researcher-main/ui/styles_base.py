"""
Base theme styles for Astraeus - Multi-Agent AI Deep Researcher.

Includes: global resets, font imports, top bar, visualization containers,
report area, metric cards, responsive media queries, Streamlit UI polish,
scrollbars, buttons, and smooth scrolling.
"""


def get_global_css() -> str:
    """Return global font import and base app styles."""
    return """\
/* Global */
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

.stApp {
    font-family: 'Inter', sans-serif;
}
"""


def get_chrome_css() -> str:
    """Return top bar, visualization containers, report area, and metric card styles."""
    return """\
/* Top bar */
.top-bar {
    background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%);
    border-radius: 16px;
    padding: 24px 32px;
    margin-bottom: 24px;
    border: 1px solid transparent;
    background-clip: padding-box;
    position: relative;
}

.top-bar::before {
    content: '';
    position: absolute;
    inset: -1px;
    border-radius: 17px;
    background: linear-gradient(135deg, #f472b6, #06b6d4, #a78bfa, #10b981, #fbbf24, #3b82f6);
    background-size: 300% 300%;
    z-index: -1;
    opacity: 0.45;
    animation: topBarGlow 8s ease infinite;
}

@keyframes topBarGlow {
    0%, 100% { background-position: 0% 50%; }
    50% { background-position: 100% 50%; }
}

.app-title {
    font-size: 1.8rem;
    font-weight: 700;
    background: linear-gradient(135deg, #60a5fa, #a78bfa);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    margin-bottom: 4px;
}

.app-tagline {
    font-size: 0.85rem;
    color: #94a3b8;
    letter-spacing: 1px;
}

/* Visualization containers */
.viz-container {
    background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%);
    border: 1px solid #334155;
    border-radius: 16px;
    padding: 20px;
    margin: 12px 0;
}

/* Report area */
.report-container {
    background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%);
    border: 1px solid #334155;
    border-radius: 16px;
    padding: 24px;
    margin-top: 24px;
    max-height: 600px;
    overflow-y: auto;
    position: relative;
}

.report-container::-webkit-scrollbar {
    width: 6px;
}

.report-container::-webkit-scrollbar-track {
    background: transparent;
}

.report-container::-webkit-scrollbar-thumb {
    background: rgba(148, 163, 184, 0.3);
    border-radius: 999px;
}

.report-container::-webkit-scrollbar-thumb:hover {
    background: rgba(148, 163, 184, 0.5);
}

/* Metrics */
.metric-card {
    background: linear-gradient(145deg, rgba(255,255,255,0.04), rgba(255,255,255,0.08));
    border-radius: 12px;
    padding: 16px;
    text-align: center;
    border: 1px solid rgba(148, 163, 184, 0.15);
    transition: border-color 0.3s ease, box-shadow 0.3s ease;
}

.metric-card:hover {
    border-color: rgba(96, 165, 250, 0.35);
    box-shadow: 0 0 16px rgba(96, 165, 250, 0.1);
}

.metric-value {
    font-size: 1.8rem;
    font-weight: 700;
    background: linear-gradient(135deg, #60a5fa, #a78bfa);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
}

.metric-label {
    font-size: 0.75rem;
    color: #94a3b8;
    margin-top: 4px;
    text-transform: uppercase;
    letter-spacing: 0.04em;
}
"""


def get_responsive_css() -> str:
    """Return responsive media query overrides for laptop screens."""
    return """\
/* Responsive tuning for laptop screens */
@media (max-width: 1600px) {
    .agent-card {
        min-height: 238px;
        height: auto;
        padding: 9px 9px 0;
    }

    .robot-stage {
        width: 118px;
        height: 118px;
    }

    .robot-hero {
        inset: 12px;
    }

    .robot-head {
        width: 68px;
        height: 58px;
    }

    .robot-body {
        width: 50px;
        height: 29px;
    }

    .agent-name {
        font-size: 0.79rem;
        min-height: 20px;
    }

    .agent-status-inline {
        font-size: 0.68rem;
        padding: 3px 9px;
    }

    .agent-description {
        font-size: 0.62rem;
        min-height: 30px;
    }

    .agent-metrics {
        font-size: 0.6rem;
        min-height: 26px;
    }

    .agent-elapsed {
        font-size: 0.62rem;
    }

    .arrow-inactive,
    .arrow-flowing,
    .arrow-complete {
        font-size: 1.15rem;
    }
}

@media (max-width: 1366px) {
    .agent-card {
        min-height: 226px;
        height: auto;
        padding: 8px 8px 0;
    }

    .agent-main-hero {
        gap: 3px;
    }

    .robot-stage {
        width: 108px;
        height: 108px;
    }

    .robot-head {
        width: 62px;
        height: 53px;
        border-width: 1.6px;
    }

    .robot-eyes span {
        width: 7px;
        height: 7px;
    }

    .robot-mouth {
        height: 4px;
        margin-top: 9px;
    }

    .robot-body {
        width: 45px;
        height: 26px;
        border-width: 1.6px;
    }

    .agent-name {
        font-size: 0.74rem;
        min-height: 18px;
    }

    .agent-status-inline {
        font-size: 0.64rem;
        padding: 3px 8px;
    }

    .agent-description {
        font-size: 0.58rem;
        min-height: 26px;
    }

    .agent-metrics {
        font-size: 0.56rem;
        min-height: 22px;
        padding: 3px 5px;
    }

    .status-dot {
        width: 7px;
        height: 7px;
    }

    .agent-progress-track {
        height: 6px;
    }

    .agent-elapsed {
        font-size: 0.58rem;
    }

    .arrow-inactive,
    .arrow-flowing,
    .arrow-complete {
        font-size: 1rem;
    }
}
"""


def get_polish_css() -> str:
    """Return Streamlit UI polish, scrollbar, button, and smooth scrolling styles."""
    return """\
/* Streamlit tab polish */
.stTabs [data-baseweb="tab-list"] {
    gap: 4px;
}

.stTabs [data-baseweb="tab"] {
    border-radius: 8px 8px 0 0;
    padding: 8px 16px;
    font-size: 0.82rem;
    font-weight: 500;
    transition: background 0.2s ease;
}

.stTabs [data-baseweb="tab"]:hover {
    background: rgba(255,255,255,0.04);
}

.stTabs [aria-selected="true"] {
    background: rgba(96, 165, 250, 0.08) !important;
}

/* Expander polish */
.streamlit-expanderHeader {
    font-size: 0.85rem;
    font-weight: 500;
}

/* Custom scrollbar for the whole app */
::-webkit-scrollbar {
    width: 8px;
    height: 8px;
}

::-webkit-scrollbar-track {
    background: rgba(15, 23, 42, 0.3);
}

::-webkit-scrollbar-thumb {
    background: rgba(148, 163, 184, 0.25);
    border-radius: 999px;
}

::-webkit-scrollbar-thumb:hover {
    background: rgba(148, 163, 184, 0.4);
}

/* Button hover enhancement */
.stButton > button[kind="primary"] {
    transition: box-shadow 0.2s ease, transform 0.15s ease;
}

.stButton > button[kind="primary"]:hover {
    box-shadow: 0 4px 16px rgba(59, 130, 246, 0.3);
    transform: translateY(-1px);
}

/* Smooth scrolling for anchor navigation */
html {
    scroll-behavior: smooth;
}
"""
