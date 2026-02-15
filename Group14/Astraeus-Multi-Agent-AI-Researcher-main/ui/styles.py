"""
Custom CSS for Astraeus - Multi-Agent AI Deep Researcher.

Entry point that assembles CSS from sub-modules:
  - styles_base: global theme, top bar, layout chrome, metrics, responsive, UI polish
  - styles_components: agent cards, badges, robots, status, card progress
  - styles_pipeline: arrows, pipeline progress, timeline, easter egg
  - styles_animations: all @keyframes definitions
"""

from ui.styles_base import get_global_css, get_chrome_css, get_responsive_css, get_polish_css
from ui.styles_components import get_components_css
from ui.styles_pipeline import get_pipeline_css
from ui.styles_animations import get_animations_css


def get_custom_css() -> str:
    """Return the full custom CSS for the app.

    Concatenates sub-module CSS in the same order as the original
    monolithic file so the output is byte-for-byte identical.
    """
    return (
        "\n<style>\n"
        + get_global_css()
        + "\n"
        + get_components_css()
        + "\n"
        + get_pipeline_css()
        + "\n"
        + get_chrome_css()
        + "\n"
        + get_responsive_css()
        + "\n"
        + get_animations_css()
        + "\n"
        + get_polish_css()
        + "</style>\n"
    )
