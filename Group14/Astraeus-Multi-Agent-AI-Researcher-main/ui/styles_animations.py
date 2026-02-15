"""
Keyframe animations for Astraeus - Multi-Agent AI Deep Researcher.

All @keyframes definitions used by agent cards, robots, progress bars,
arrows, and celebration effects.
"""


def get_animations_css() -> str:
    """Return all @keyframes animation definitions."""
    return """\
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
"""
