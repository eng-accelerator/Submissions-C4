"""
utils/pdf_export.py
====================
Professional PDF report generation using FPDF2.

Generates a polished, well-formatted PDF from research report data.
Handles Unicode, long URLs, multi-line text, and clean typography.

USAGE:
    from utils.pdf_export import generate_pdf_bytes
    pdf_bytes = generate_pdf_bytes(report_dict, sources_list)
"""

from __future__ import annotations

import os
import logging
from datetime import datetime
from typing import Optional

from fpdf import FPDF

from config import settings

logger = logging.getLogger(__name__)

# ─────────────────────────────────────────────
# Color Palette
# ─────────────────────────────────────────────
COLORS = {
    "primary":        (41, 128, 185),    # Blue
    "primary_light":  (214, 234, 248),   # Light blue bg
    "dark":           (44, 62, 80),       # Dark blue-grey
    "body":           (60, 60, 60),       # Body text
    "muted":          (127, 140, 141),    # Grey text
    "green":          (39, 174, 96),      # Success
    "green_light":    (212, 239, 223),    # Light green bg
    "orange":         (243, 156, 18),     # Warning
    "orange_light":   (253, 235, 208),    # Light orange bg
    "red":            (231, 76, 60),      # Danger
    "red_light":      (250, 219, 216),    # Light red bg
    "white":          (255, 255, 255),
    "light_grey":     (245, 245, 245),
    "border":         (220, 220, 220),
}


class ResearchReportPDF(FPDF):
    """Professional PDF report with header, footer, and styled sections."""

    def __init__(self):
        super().__init__()
        self.set_auto_page_break(auto=True, margin=30)
        self.set_margins(left=15, top=20, right=15)

    # ── Header / Footer ──────────────────────────────────

    def header(self):
        if self.page_no() == 1:
            return  # No header on cover/first page
        self.set_font("Helvetica", "I", 8)
        self.set_text_color(*COLORS["muted"])
        self.cell(0, 6, "Multi-Agent AI Deep Researcher", align="L")
        self.set_draw_color(*COLORS["primary"])
        self.set_line_width(0.4)
        self.line(15, 14, self.w - 15, 14)
        self.ln(10)

    def footer(self):
        self.set_y(-20)
        self.set_draw_color(*COLORS["border"])
        self.set_line_width(0.2)
        self.line(15, self.get_y(), self.w - 15, self.get_y())
        self.ln(3)
        self.set_font("Helvetica", "I", 8)
        self.set_text_color(*COLORS["muted"])
        self.cell(0, 8, f"Page {self.page_no()} of {{nb}}", align="C")

    # ── Cover / Title Block ──────────────────────────────

    def add_cover(self, title: str, generated_at: str = ""):
        """Add a styled title block at the top of the first page."""
        self.ln(5)

        # Blue accent bar
        self.set_fill_color(*COLORS["primary"])
        self.rect(15, self.get_y(), self.w - 30, 3, "F")
        self.ln(10)

        # Title
        self.set_font("Helvetica", "B", 22)
        self.set_text_color(*COLORS["dark"])
        self.multi_cell(0, 11, self._safe(title), align="L")
        self.ln(3)

        # Subtitle / date
        date_str = generated_at or datetime.now().strftime("%B %d, %Y at %H:%M")
        self.set_font("Helvetica", "", 10)
        self.set_text_color(*COLORS["muted"])
        self.cell(0, 6, f"Generated: {date_str}", align="L")
        self.ln(3)
        self.cell(0, 6, "Multi-Agent AI Deep Researcher | LangGraph + Tavily + OpenRouter", align="L")
        self.ln(8)

        # Separator
        self.set_draw_color(*COLORS["primary"])
        self.set_line_width(0.4)
        self.line(15, self.get_y(), self.w - 15, self.get_y())
        self.ln(8)

    # ── Section Header ───────────────────────────────────

    def section(self, title: str):
        """Add a styled section header with colored left bar."""
        # Check if we need a new page (at least 40mm of space needed)
        if self.get_y() > self.h - 50:
            self.add_page()

        self.ln(6)

        # Colored left bar + title
        y = self.get_y()
        self.set_fill_color(*COLORS["primary"])
        self.rect(15, y, 3, 10, "F")
        self.set_x(22)
        self.set_font("Helvetica", "B", 13)
        self.set_text_color(*COLORS["dark"])
        self.cell(0, 10, self._safe(title))
        self.ln(14)

    # ── Body Text ────────────────────────────────────────

    def body(self, text: str):
        """Add body text with proper line height."""
        self.set_font("Helvetica", "", 10)
        self.set_text_color(*COLORS["body"])
        # Split into paragraphs for better spacing
        paragraphs = text.split("\n\n") if "\n\n" in text else [text]
        for para in paragraphs:
            para = para.strip()
            if para:
                self.multi_cell(0, 5.5, self._safe(para))
                self.ln(3)

    # ── Findings ─────────────────────────────────────────

    def add_finding(self, index: int, finding: dict):
        """Add a single finding with confidence badge and text inline."""
        confidence = finding.get("confidence", "N/A")
        finding_text = finding.get("finding", "")
        sources_count = finding.get("sources_count", 0)

        # Check page space
        if self.get_y() > self.h - 40:
            self.add_page()

        # Confidence badge color
        if isinstance(confidence, (int, float)):
            if confidence >= 70:
                badge_color = COLORS["green"]
                badge_bg = COLORS["green_light"]
            elif confidence >= 50:
                badge_color = COLORS["orange"]
                badge_bg = COLORS["orange_light"]
            else:
                badge_color = COLORS["red"]
                badge_bg = COLORS["red_light"]
            conf_str = f"{confidence}%"
        else:
            badge_color = COLORS["muted"]
            badge_bg = COLORS["light_grey"]
            conf_str = str(confidence)

        y_start = self.get_y()

        # Light background card
        self.set_fill_color(*COLORS["light_grey"])
        # We'll draw the background after we know the height

        # Finding number + confidence
        self.set_font("Helvetica", "B", 10)
        self.set_text_color(*COLORS["dark"])
        self.cell(8, 6, f"{index}.", align="R")

        # Badge
        self.set_x(self.get_x() + 2)
        badge_x = self.get_x()
        badge_w = self.get_string_width(f" {conf_str} ") + 4
        self.set_fill_color(*badge_bg)
        self.set_text_color(*badge_color)
        self.set_font("Helvetica", "B", 9)
        self.cell(badge_w, 6, f" {conf_str} ", fill=True, align="C")

        # Sources count
        if sources_count:
            self.set_x(self.get_x() + 3)
            self.set_font("Helvetica", "I", 8)
            self.set_text_color(*COLORS["muted"])
            self.cell(0, 6, f"{sources_count} source(s)")

        self.ln(8)

        # Finding text
        self.set_x(27)
        self.set_font("Helvetica", "", 10)
        self.set_text_color(*COLORS["body"])
        self.multi_cell(self.w - 42, 5.5, self._safe(finding_text))
        self.ln(4)

    # ── Quality Score ────────────────────────────────────

    def add_quality_score(self, score: float, breakdown: dict = None):
        """Add a visually prominent quality score section."""
        self.section("Research Quality Score")

        # Score box
        if score >= 70:
            box_color = COLORS["green"]
            box_bg = COLORS["green_light"]
        elif score >= 50:
            box_color = COLORS["orange"]
            box_bg = COLORS["orange_light"]
        else:
            box_color = COLORS["red"]
            box_bg = COLORS["red_light"]

        # Centered score box
        box_w = 60
        box_h = 20
        box_x = (self.w - box_w) / 2
        y = self.get_y()
        self.set_fill_color(*box_bg)
        self.set_draw_color(*box_color)
        self.set_line_width(0.8)
        self.rect(box_x, y, box_w, box_h, "DF")

        # Position text exactly inside the box
        self.set_xy(box_x, y)
        self.set_font("Helvetica", "B", 22)
        self.set_text_color(*box_color)
        self.cell(box_w, box_h, f"{score:.0f} / 100", align="C")

        # Move below the box
        self.set_y(y + box_h + 4)

        # Breakdown table
        if breakdown:
            self.set_font("Helvetica", "", 9)
            self.set_text_color(*COLORS["body"])
            # Clean up keys: replace underscores with spaces, title case
            parts = []
            for k, v in breakdown.items():
                clean_key = k.replace("_", " ").title()
                parts.append(f"{clean_key}: {v}")
            self.cell(0, 6, "  |  ".join(parts), align="C")
            self.ln(8)

    # ── Sources List ─────────────────────────────────────

    def add_source(self, index: int, title: str, url: str):
        """Add a single source with title and truncated URL."""
        if self.get_y() > self.h - 25:
            self.add_page()

        safe_title = self._safe(title)
        safe_url = self._safe(url)

        # Truncate very long URLs
        max_url_len = 90
        display_url = safe_url if len(safe_url) <= max_url_len else safe_url[:max_url_len] + "..."

        self.set_font("Helvetica", "B", 9)
        self.set_text_color(*COLORS["dark"])
        self.cell(0, 5, f"{index}. {safe_title}")
        self.ln(5)

        self.set_font("Helvetica", "", 8)
        self.set_text_color(*COLORS["primary"])
        self.cell(0, 4, f"   {display_url}")
        self.ln(6)

    # ── Utility ──────────────────────────────────────────

    @staticmethod
    def _safe(text: str) -> str:
        """Replace problematic Unicode characters with ASCII equivalents."""
        if not text:
            return ""
        replacements = {
            "\u2018": "'", "\u2019": "'",
            "\u201c": '"', "\u201d": '"',
            "\u2013": "-", "\u2014": "--",
            "\u2026": "...", "\u2022": "*",
            "\u00a0": " ", "\u200b": "",
            "\u2019": "'", "\u00e9": "e",
        }
        for old, new in replacements.items():
            text = text.replace(old, new)
        return text.encode("latin-1", errors="replace").decode("latin-1")


# ─────────────────────────────────────────────
# Public API
# ─────────────────────────────────────────────

def generate_pdf_bytes(report: dict, sources: list[dict] = None) -> bytes:
    """
    Generate a professional PDF report and return raw bytes.

    This avoids file I/O — bytes can be passed directly to
    Streamlit's st.download_button.

    Args:
        report: Report dict from the report agent.
        sources: List of source dicts.

    Returns:
        PDF file content as bytes.
    """
    sources = sources or []

    pdf = ResearchReportPDF()
    pdf.alias_nb_pages()
    pdf.add_page()

    # Cover
    pdf.add_cover(
        title=report.get("title", "Research Report"),
        generated_at=report.get("generated_at", ""),
    )

    # Executive Summary
    pdf.section("Executive Summary")
    pdf.body(report.get("executive_summary", "No summary available."))

    # Key Findings
    pdf.section("Key Findings")
    findings = report.get("key_findings", [])
    if findings:
        for i, f in enumerate(findings, 1):
            pdf.add_finding(i, f)
    else:
        pdf.body("No key findings extracted.")

    # Contradictions & Gaps
    pdf.section("Contradictions & Gaps")
    pdf.body(report.get("contradictions_and_gaps", "No contradictions or gaps identified."))

    # Insights & Trends
    pdf.section("Insights & Trends")
    pdf.body(report.get("insights_and_trends", "No insights generated."))

    # Source Reliability
    pdf.section("Source Reliability Assessment")
    pdf.body(report.get("source_reliability", "No assessment available."))

    # Quality Score
    pdf.add_quality_score(
        report.get("quality_score", 0),
        report.get("quality_breakdown", {}),
    )

    # Methodology
    pdf.section("Methodology")
    pdf.body(report.get("methodology_note", ""))

    # Sources Cited
    pdf.section(f"Sources Cited ({len(sources)})")
    for i, src in enumerate(sources, 1):
        title = src.get("title", "Unknown")
        url = src.get("url", "")
        pdf.add_source(i, title, url)

    return bytes(pdf.output())


def export_report_to_pdf(report, filename: str = None) -> str:
    """
    Legacy function: Export to a PDF file on disk.

    Args:
        report: Object with report attributes (title, executive_summary, etc.)
        filename: Output path. Defaults to timestamped name in outputs/.

    Returns:
        Absolute path to the generated PDF.
    """
    if filename is None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = os.path.join(settings.PDF_OUTPUT_DIR, f"research_report_{timestamp}.pdf")

    os.makedirs(os.path.dirname(filename) or ".", exist_ok=True)

    # Convert object to dict
    report_dict = {
        "title": getattr(report, "title", "Research Report"),
        "executive_summary": getattr(report, "executive_summary", ""),
        "key_findings": getattr(report, "key_findings", []),
        "contradictions_and_gaps": getattr(report, "contradictions_and_gaps", ""),
        "insights_and_trends": getattr(report, "insights_and_trends", ""),
        "source_reliability": getattr(report, "source_reliability", ""),
        "methodology_note": getattr(report, "methodology_note", ""),
        "quality_score": getattr(report, "quality_score", 0),
        "quality_breakdown": getattr(report, "quality_breakdown", {}),
        "generated_at": getattr(report, "generated_at", ""),
    }
    sources = [
        {"title": s.get("title", ""), "url": s.get("url", "")}
        for s in getattr(report, "sources_cited", [])
    ]

    pdf_bytes = generate_pdf_bytes(report_dict, sources)
    with open(filename, "wb") as f:
        f.write(pdf_bytes)

    logger.info(f"PDF report saved to: {filename}")
    return os.path.abspath(filename)
