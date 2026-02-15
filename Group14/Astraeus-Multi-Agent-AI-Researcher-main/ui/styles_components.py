"""Component CSS: agent cards, badges, tooltips, robots, status, card progress."""

def get_components_css() -> str:
    """Return component-specific CSS for agent cards and related elements."""
    return """\
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
    content: '\u2713';
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
"""
