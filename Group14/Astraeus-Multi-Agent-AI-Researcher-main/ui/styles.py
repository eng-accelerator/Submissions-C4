"""
Custom CSS for Astraeus - Multi-Agent AI Deep Researcher.
"""


def get_custom_css() -> str:
    """Return the full custom CSS for the app."""
    return """
<style>
/* Global */
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

.stApp {
    font-family: 'Inter', sans-serif;
}

/* Agent cards */
.agent-card {
    border-radius: 18px;
    padding: 10px 10px 0;
    min-height: 252px;
    height: auto;
    width: 100%;
    position: relative;
    overflow: hidden;
    box-sizing: border-box;
    border: 1.8px solid rgba(148, 163, 184, 0.25);
    background: linear-gradient(150deg, #0b1220 0%, #131d33 100%);
    backdrop-filter: blur(6px);
    transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
}

.agent-main-hero {
    display: grid;
    grid-template-rows: auto auto auto auto auto;
    justify-items: center;
    gap: 3px;
    height: auto;
    align-content: start;
}

.agent-card.not_started {
    opacity: 0.86;
}

.agent-card.waiting {
    border-color: color-mix(in srgb, var(--agent-color), #ffffff 18%);
    box-shadow: 0 0 0 1px color-mix(in srgb, var(--agent-color), transparent 72%);
}

.agent-card.working {
    border-color: color-mix(in srgb, var(--agent-color), #ffffff 24%);
    box-shadow: 0 0 20px color-mix(in srgb, var(--agent-color), transparent 72%);
    transform: scale(1.02);
    animation: cardPulse 1.65s ease-in-out infinite;
}

.agent-card.complete {
    border-color: color-mix(in srgb, var(--agent-color), #ffffff 20%);
    box-shadow: 0 0 12px color-mix(in srgb, var(--agent-color), transparent 78%);
    animation: successFlash 0.55s ease-out;
}

.agent-card.error {
    border-color: #ef4444;
    box-shadow: 0 0 12px rgba(239, 68, 68, 0.35);
    animation: errorShake 0.45s ease-in-out;
}

.agent-card::before {
    content: '';
    position: absolute;
    inset: 0;
    background: linear-gradient(
        130deg,
        transparent 0%,
        color-mix(in srgb, var(--agent-color), transparent 90%) 38%,
        transparent 68%
    );
    transform: translateX(-130%);
    pointer-events: none;
    opacity: 0;
}

.agent-card.working::before {
    opacity: 1;
    animation: cardSweep 1.6s linear infinite;
}

.agent-badge {
    position: absolute;
    top: 8px;
    right: 8px;
    width: 22px;
    height: 22px;
    border-radius: 8px;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 0.8rem;
    background: color-mix(in srgb, var(--agent-color), #111827 72%);
    border: 1px solid color-mix(in srgb, var(--agent-color), #ffffff 25%);
    box-shadow: 0 0 10px color-mix(in srgb, var(--agent-color), transparent 78%);
}

.agent-info-trigger {
    cursor: help;
    z-index: 4;
}

.agent-info-trigger:focus-visible {
    outline: 2px solid #e2e8f0;
    outline-offset: 2px;
}

.agent-badge-icon {
    line-height: 1;
}

.agent-tooltip {
    position: absolute;
    top: 28px;
    right: 0;
    width: 220px;
    background: rgba(15, 23, 42, 0.96);
    border: 1px solid color-mix(in srgb, var(--agent-color), #ffffff 30%);
    border-radius: 10px;
    padding: 8px 10px;
    color: #cbd5e1;
    font-size: 0.62rem;
    line-height: 1.35;
    text-align: left;
    box-shadow: 0 10px 24px rgba(2, 6, 23, 0.55);
    opacity: 0;
    visibility: hidden;
    transform: translateY(-4px);
    transition: opacity 0.2s ease, transform 0.2s ease, visibility 0.2s ease;
    pointer-events: none;
}

.agent-info-trigger:hover .agent-tooltip,
.agent-info-trigger:focus-within .agent-tooltip,
.agent-info-trigger:focus-visible .agent-tooltip {
    opacity: 1;
    visibility: visible;
    transform: translateY(0);
}

.agent-tooltip-title {
    color: #e2e8f0;
    font-size: 0.66rem;
    font-weight: 600;
    margin-bottom: 5px;
}

.agent-tooltip-line + .agent-tooltip-line {
    margin-top: 4px;
}

/* Robot visuals */
.robot-stage {
    position: relative;
    width: 132px;
    height: 132px;
    margin-top: 0;
}

.robot-halo {
    position: absolute;
    inset: 6px;
    border-radius: 999px;
    background: radial-gradient(
        circle at center,
        color-mix(in srgb, var(--agent-color), #ffffff 20%) 0%,
        color-mix(in srgb, var(--agent-color), transparent 68%) 64%,
        transparent 100%
    );
    opacity: 0.25;
    transform: scale(0.95);
}

.agent-card.working .robot-halo {
    opacity: 0.58;
    animation: haloPulse 1.15s ease-in-out infinite;
}

.agent-card.complete .robot-halo {
    opacity: 0.36;
}

.robot-hero {
    position: absolute;
    inset: 14px;
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    transform-origin: center bottom;
    transition: transform 0.35s ease;
}

.agent-card.working .robot-hero {
    animation: robotBounce 1.25s ease-in-out infinite;
}

.agent-card.complete .robot-hero {
    transform: scale(1.02);
}

.robot-antenna {
    width: 2px;
    height: 12px;
    margin-bottom: 2px;
    background: color-mix(in srgb, var(--agent-color), #f8fafc 35%);
    position: relative;
}

.antenna-tip {
    position: absolute;
    width: 8px;
    height: 8px;
    border-radius: 999px;
    top: -6px;
    left: -3px;
    background: color-mix(in srgb, var(--agent-color), #ffffff 20%);
    box-shadow: 0 0 10px color-mix(in srgb, var(--agent-color), transparent 62%);
}

.robot-insight_generator .antenna-tip {
    width: 10px;
    height: 10px;
    top: -8px;
    left: -4px;
    border-radius: 3px 3px 50% 50%;
    background: #fef08a;
    box-shadow: 0 0 12px rgba(251, 191, 36, 0.75);
}

.agent-card.working .robot-insight_generator .antenna-tip {
    animation: lightbulbFlicker 0.7s ease-in-out infinite;
}

.robot-head {
    width: 74px;
    height: 62px;
    border-radius: 16px;
    background: linear-gradient(
        160deg,
        color-mix(in srgb, var(--agent-color), #ffffff 20%) 0%,
        color-mix(in srgb, var(--agent-color), #0f172a 62%) 100%
    );
    border: 2px solid color-mix(in srgb, var(--agent-color), #ffffff 30%);
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    box-shadow: inset 0 -8px 16px rgba(2, 6, 23, 0.28);
}

.robot-eyes {
    display: flex;
    gap: 18px;
}

.robot-eyes span {
    width: 9px;
    height: 9px;
    border-radius: 999px;
    background: #e2e8f0;
    box-shadow: 0 0 9px color-mix(in srgb, var(--agent-color), transparent 52%);
}

.agent-card.working .robot-eyes span {
    animation: eyeBlink 1.8s ease-in-out infinite;
}

.robot-mouth {
    width: 32px;
    height: 5px;
    border-radius: 999px;
    margin-top: 12px;
    background: color-mix(in srgb, var(--agent-color), #f8fafc 34%);
}

.robot-body {
    width: 56px;
    height: 32px;
    margin-top: 6px;
    border-radius: 12px 12px 16px 16px;
    background: linear-gradient(
        180deg,
        color-mix(in srgb, var(--agent-color), #ffffff 14%) 0%,
        color-mix(in srgb, var(--agent-color), #020617 70%) 100%
    );
    border: 2px solid color-mix(in srgb, var(--agent-color), #ffffff 20%);
}

.robot-coordinator .robot-mouth { width: 22px; }
.robot-retriever .robot-eyes span { border-radius: 2px; }
.robot-critical_analysis .robot-head { border-radius: 12px; }
.robot-fact_checker .robot-body { border-radius: 14px; }
.robot-insight_generator .robot-head { box-shadow: inset 0 -8px 16px rgba(2, 6, 23, 0.28), 0 0 16px rgba(251, 191, 36, 0.3); }
.robot-report_builder .robot-mouth { width: 38px; }

/* Agent-specific micro interactions while running */
.robot-coordinator .robot-head,
.robot-critical_analysis .robot-head,
.robot-fact_checker .robot-body,
.robot-report_builder .robot-body,
.robot-retriever .robot-body {
    position: relative;
    overflow: hidden;
}

.agent-card.working .robot-coordinator .robot-head::after {
    content: '';
    position: absolute;
    width: 15px;
    height: 15px;
    border: 2px solid rgba(226, 232, 240, 0.85);
    border-radius: 999px;
    right: 8px;
    top: 18px;
    box-shadow: 7px 7px 0 -5px rgba(226, 232, 240, 0.78);
    will-change: transform, opacity;
    animation: magnifierSweep 2.2s cubic-bezier(0.42, 0, 0.2, 1) infinite;
}

.agent-card.working .robot-retriever .robot-body::after {
    content: '';
    position: absolute;
    inset: 4px;
    background: repeating-linear-gradient(
        90deg,
        rgba(34, 211, 238, 0.05) 0,
        rgba(34, 211, 238, 0.05) 4px,
        rgba(34, 211, 238, 0.55) 4px,
        rgba(34, 211, 238, 0.55) 6px
    );
    will-change: transform, opacity;
    transform: translateX(-105%);
    animation: dataFlow 1.8s cubic-bezier(0.4, 0, 0.2, 1) infinite;
}

.agent-card.working .robot-critical_analysis .robot-head::before,
.agent-card.working .robot-critical_analysis .robot-head::after {
    content: '';
    position: absolute;
    width: 14px;
    height: 9px;
    border-radius: 3px;
    border: 1px solid rgba(226, 232, 240, 0.62);
    background: rgba(15, 23, 42, 0.78);
    top: 8px;
}

.agent-card.working .robot-critical_analysis .robot-head::before {
    left: 6px;
    animation: panelFlipLeft 1.1s ease-in-out infinite;
}

.agent-card.working .robot-critical_analysis .robot-head::after {
    right: 6px;
    animation: panelFlipRight 1.1s ease-in-out infinite;
}

.agent-card.working .robot-fact_checker .robot-body::before {
    content: '✓';
    position: absolute;
    font-size: 0.8rem;
    font-weight: 700;
    color: #34d399;
    left: 50%;
    top: 48%;
    transform: translate(-50%, -50%);
    will-change: transform, opacity;
    animation: tickBounce 1.55s cubic-bezier(0.34, 1.56, 0.64, 1) infinite;
}

.agent-card.working .robot-report_builder .robot-body::before {
    content: '';
    position: absolute;
    left: 7px;
    right: 7px;
    top: 7px;
    height: 2px;
    border-radius: 999px;
    background: rgba(226, 232, 240, 0.85);
    box-shadow: 0 6px 0 rgba(226, 232, 240, 0.72), 0 12px 0 rgba(226, 232, 240, 0.58);
    transform-origin: left;
    animation: reportTyping 1.1s ease-in-out infinite;
}

.agent-name {
    text-align: center;
    font-size: 0.86rem;
    font-weight: 600;
    color: #e2e8f0;
    min-height: 22px;
    display: flex;
    align-items: center;
    justify-content: center;
    line-height: 1.1;
}

/* Status */
.agent-status-inline {
    display: inline-flex;
    align-items: center;
    gap: 7px;
    border-radius: 999px;
    padding: 4px 10px;
    font-size: 0.72rem;
    font-weight: 600;
    letter-spacing: 0.01em;
}

.agent-description {
    width: 100%;
    font-size: 0.67rem;
    line-height: 1.25;
    color: #cbd5e1;
    text-align: center;
    min-height: 34px;
    display: -webkit-box;
    -webkit-line-clamp: 2;
    -webkit-box-orient: vertical;
    overflow: hidden;
    padding: 0 2px;
}

.agent-metrics {
    width: 100%;
    font-size: 0.64rem;
    line-height: 1.2;
    color: #93c5fd;
    text-align: center;
    min-height: 30px;
    display: -webkit-box;
    -webkit-line-clamp: 2;
    -webkit-box-orient: vertical;
    overflow: hidden;
    background: rgba(15, 23, 42, 0.45);
    border: 1px solid rgba(148, 163, 184, 0.2);
    border-radius: 8px;
    padding: 4px 6px;
}

.agent-card.complete .agent-metrics {
    color: color-mix(in srgb, var(--agent-color), #ffffff 14%);
    border-color: color-mix(in srgb, var(--agent-color), transparent 72%);
}

.agent-card.working .agent-metrics {
    color: color-mix(in srgb, var(--agent-color), #ffffff 22%);
    border-color: color-mix(in srgb, var(--agent-color), transparent 70%);
}

.agent-card.error .agent-metrics {
    color: #fecaca;
    border-color: rgba(239, 68, 68, 0.45);
}

.status-dot {
    width: 8px;
    height: 8px;
    border-radius: 999px;
    background: #94a3b8;
}

.status-not_started { background: rgba(71, 85, 105, 0.25); color: #cbd5e1; }
.status-waiting { background: color-mix(in srgb, var(--agent-color), transparent 82%); color: color-mix(in srgb, var(--agent-color), #ffffff 28%); }
.status-working { background: color-mix(in srgb, var(--agent-color), transparent 80%); color: color-mix(in srgb, var(--agent-color), #ffffff 16%); }
.status-complete { background: color-mix(in srgb, var(--agent-color), transparent 80%); color: color-mix(in srgb, var(--agent-color), #ffffff 10%); }
.status-error { background: rgba(239, 68, 68, 0.2); color: #fecaca; }

.status-not_started .status-dot { background: #64748b; }
.status-waiting .status-dot { background: color-mix(in srgb, var(--agent-color), #ffffff 10%); }
.status-working .status-dot {
    background: color-mix(in srgb, var(--agent-color), #ffffff 10%);
    animation: dotPulse 0.95s ease-in-out infinite;
}
.status-complete .status-dot { background: color-mix(in srgb, var(--agent-color), #ffffff 8%); }
.status-error .status-dot { background: #ef4444; }

/* Card progress */
.agent-progress-track {
    width: 100%;
    height: 7px;
    border-radius: 999px;
    background: rgba(15, 23, 42, 0.82);
    overflow: hidden;
    border: 1px solid rgba(148, 163, 184, 0.22);
    margin-top: 2px;
}

.agent-progress-fill {
    height: 100%;
    border-radius: 999px;
    transition: width 0.45s ease, background-color 0.35s ease;
}

.agent-progress-fill.state-not_started { background: #475569; }
.agent-progress-fill.state-waiting,
.agent-progress-fill.state-working,
.agent-progress-fill.state-complete { background: var(--agent-color); }
.agent-progress-fill.state-working { animation: progressPulse 0.95s ease-in-out infinite; }
.agent-progress-fill.state-error { background: #ef4444; }

.agent-elapsed {
    margin-top: 0;
    font-size: 0.66rem;
    color: #94a3b8;
    line-height: 1;
    padding-bottom: 0;
}

/* Arrows */
.arrow-container {
    display: flex;
    align-items: center;
    justify-content: center;
    min-height: 42px;
    position: relative;
    overflow: visible;
}

.arrow-inactive,
.arrow-flowing,
.arrow-complete {
    font-size: 1.45rem;
    transition: all 0.25s ease;
    color: var(--arrow-color, #64748b);
}

.arrow-inactive {
    opacity: 0.25;
}

.arrow-flowing {
    opacity: 0.95;
    animation: arrowFlow 1s ease-in-out infinite;
    text-shadow: 0 0 10px color-mix(in srgb, var(--arrow-color), transparent 60%);
}

.arrow-beam {
    position: absolute;
    width: 8px;
    height: 8px;
    border-radius: 999px;
    background: color-mix(in srgb, var(--arrow-color), #ffffff 20%);
    box-shadow: 0 0 10px color-mix(in srgb, var(--arrow-color), transparent 45%);
    animation: dataBeamTravel 0.9s ease-in-out infinite;
}

.arrow-complete {
    opacity: 0.78;
}

/* Pipeline progress */
.pipeline-progress-wrap {
    margin: 12px 0 18px;
}

.pipeline-progress {
    display: flex;
    gap: 6px;
    height: 10px;
    border-radius: 999px;
    overflow: hidden;
    background: #0f172a;
    padding: 2px;
}

.progress-segment {
    flex: 1;
    border-radius: 999px;
    transition: all 0.35s ease;
}

.progress-segment.not_started {
    background: #334155;
}

.progress-segment.waiting,
.progress-segment.working,
.progress-segment.complete {
    background: color-mix(in srgb, var(--segment-color), #ffffff 6%);
}

.progress-segment.working {
    animation: segmentPulse 0.85s ease-in-out infinite;
}

.progress-segment.error {
    background: #ef4444;
}

.pipeline-progress-meta {
    margin-top: 7px;
    display: flex;
    justify-content: space-between;
    font-size: 0.74rem;
    color: #94a3b8;
}

/* Fixed timeline at bottom */
.pipeline-timeline {
    position: fixed;
    left: 0;
    right: 0;
    bottom: 0;
    height: 5px;
    background: rgba(15, 23, 42, 0.9);
    z-index: 1200;
    border-top: 1px solid rgba(148, 163, 184, 0.25);
}

.pipeline-timeline-fill {
    height: 100%;
    background: linear-gradient(90deg, #f472b6, #06b6d4, #a78bfa, #10b981, #fbbf24, #3b82f6);
    transition: width 0.4s ease;
    box-shadow: 0 0 12px rgba(96, 165, 250, 0.65);
}

.pipeline-timeline.state-error .pipeline-timeline-fill {
    background: #ef4444;
    box-shadow: 0 0 12px rgba(239, 68, 68, 0.75);
}

/* Easter egg celebration */
.pipeline-easter-egg {
    position: fixed;
    left: 0;
    right: 0;
    top: 78px;
    height: 0;
    pointer-events: none;
    z-index: 1300;
}

.egg-dot {
    position: absolute;
    width: 8px;
    height: 8px;
    border-radius: 999px;
    opacity: 0;
    animation: confettiDrop 1.7s ease-out forwards;
}

.egg-dot.dot-1 { left: 12%; background: #f472b6; animation-delay: 0.02s; }
.egg-dot.dot-2 { left: 24%; background: #06b6d4; animation-delay: 0.08s; }
.egg-dot.dot-3 { left: 36%; background: #a78bfa; animation-delay: 0.14s; }
.egg-dot.dot-4 { left: 48%; background: #10b981; animation-delay: 0.03s; }
.egg-dot.dot-5 { left: 58%; background: #fbbf24; animation-delay: 0.11s; }
.egg-dot.dot-6 { left: 68%; background: #3b82f6; animation-delay: 0.18s; }
.egg-dot.dot-7 { left: 78%; background: #f59e0b; animation-delay: 0.07s; }
.egg-dot.dot-8 { left: 88%; background: #22d3ee; animation-delay: 0.15s; }

/* Top bar */
.top-bar {
    background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%);
    border-radius: 16px;
    padding: 24px 32px;
    margin-bottom: 24px;
    border: 1px solid #334155;
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
}

/* Metrics */
.metric-card {
    background: rgba(255,255,255,0.05);
    border-radius: 12px;
    padding: 16px;
    text-align: center;
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
}

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

/* Motion */
@keyframes robotBounce {
    0%, 100% { transform: translateY(0); }
    50% { transform: translateY(-4px); }
}

@keyframes haloPulse {
    0%, 100% { transform: scale(0.92); opacity: 0.4; }
    50% { transform: scale(1.05); opacity: 0.7; }
}

@keyframes cardPulse {
    0%, 100% { box-shadow: 0 0 18px color-mix(in srgb, var(--agent-color), transparent 72%); }
    50% { box-shadow: 0 0 28px color-mix(in srgb, var(--agent-color), transparent 65%); }
}

@keyframes progressPulse {
    0%, 100% { opacity: 0.85; }
    50% { opacity: 1; }
}

@keyframes segmentPulse {
    0%, 100% { opacity: 0.72; }
    50% { opacity: 1; }
}

@keyframes dotPulse {
    0%, 100% { transform: scale(0.95); opacity: 0.8; }
    50% { transform: scale(1.2); opacity: 1; }
}

@keyframes cardSweep {
    0% { transform: translateX(-130%); }
    100% { transform: translateX(130%); }
}

@keyframes arrowFlow {
    0%, 100% { transform: translateX(0); }
    50% { transform: translateX(3px); }
}

@keyframes eyeBlink {
    0%, 44%, 50%, 100% { transform: scaleY(1); }
    47% { transform: scaleY(0.2); }
}

@keyframes successFlash {
    0% { box-shadow: 0 0 8px color-mix(in srgb, var(--agent-color), transparent 86%); }
    50% { box-shadow: 0 0 26px color-mix(in srgb, var(--agent-color), transparent 60%); }
    100% { box-shadow: 0 0 12px color-mix(in srgb, var(--agent-color), transparent 78%); }
}

@keyframes errorShake {
    0%, 100% { transform: translateX(0); }
    25% { transform: translateX(-5px); }
    75% { transform: translateX(5px); }
}

@keyframes magnifierSweep {
    0% { transform: translate3d(-6px, 1px, 0) scale(0.94); opacity: 0.5; }
    18% { transform: translate3d(-2px, 0, 0) scale(0.98); opacity: 0.82; }
    50% { transform: translate3d(5px, -1px, 0) scale(1.02); opacity: 0.96; }
    82% { transform: translate3d(-1px, 0, 0) scale(0.98); opacity: 0.8; }
    100% { transform: translate3d(-6px, 1px, 0) scale(0.94); opacity: 0.5; }
}

@keyframes dataFlow {
    0% { transform: translate3d(-105%, 0, 0); opacity: 0.22; }
    16% { opacity: 0.45; }
    48% { opacity: 0.9; }
    78% { opacity: 0.58; }
    100% { transform: translate3d(105%, 0, 0); opacity: 0.2; }
}

@keyframes panelFlipLeft {
    0%, 100% { transform: rotateY(0deg) scale(1); opacity: 0.7; }
    50% { transform: rotateY(50deg) scale(1.04); opacity: 1; }
}

@keyframes panelFlipRight {
    0%, 100% { transform: rotateY(0deg) scale(1); opacity: 0.7; }
    50% { transform: rotateY(-50deg) scale(1.04); opacity: 1; }
}

@keyframes tickBounce {
    0% { transform: translate3d(-50%, -50%, 0) scale(0.88); opacity: 0.8; }
    25% { transform: translate3d(-50%, -54%, 0) scale(1.03); opacity: 1; }
    52% { transform: translate3d(-50%, -48%, 0) scale(0.96); opacity: 0.9; }
    78% { transform: translate3d(-50%, -51%, 0) scale(1.01); opacity: 0.96; }
    100% { transform: translate3d(-50%, -50%, 0) scale(0.88); opacity: 0.8; }
}

@keyframes reportTyping {
    0% { transform: scaleX(0.2); opacity: 0.5; }
    50% { transform: scaleX(1); opacity: 1; }
    100% { transform: scaleX(0.35); opacity: 0.65; }
}

@keyframes lightbulbFlicker {
    0%, 100% { opacity: 1; box-shadow: 0 0 12px rgba(251, 191, 36, 0.75); }
    50% { opacity: 0.45; box-shadow: 0 0 6px rgba(251, 191, 36, 0.38); }
}

@keyframes dataBeamTravel {
    0% { transform: translateX(-14px) scale(0.7); opacity: 0; }
    25% { opacity: 1; }
    75% { opacity: 1; }
    100% { transform: translateX(14px) scale(1); opacity: 0; }
}

@keyframes confettiDrop {
    0% { transform: translateY(-8px) scale(0.8); opacity: 0; }
    20% { opacity: 1; }
    100% { transform: translateY(112px) scale(0.6); opacity: 0; }
}

/* Smooth scrolling for anchor navigation */
html {
    scroll-behavior: smooth;
}
</style>
"""
