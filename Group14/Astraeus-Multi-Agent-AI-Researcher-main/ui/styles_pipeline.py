"""
Pipeline and navigation CSS for Astraeus - Multi-Agent AI Deep Researcher.

Includes: card progress bars, arrows between agent cards, pipeline
progress bar, fixed timeline at bottom, and easter egg celebration dots.
"""


def get_pipeline_css() -> str:
    """Return card progress, arrow, pipeline progress, timeline, and easter egg CSS."""
    return """\
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
"""
