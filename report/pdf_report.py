"""
report/pdf_report.py
--------------------
Forensic PDF report generator for Drishti AI Examination Surveillance Platform.

Consumes Stage 5 outputs (incidents.json, capsules/, zone_map.json, heatmaps)
and produces a professional multi-page examination forensic report using fpdf2.

Sections:
  Page 1  — Cover page (branding, metadata, overall risk banner)
  Page 2  — Executive summary (annotated frame, incident timeline strip, stats)
  Page 3+ — Per-incident evidence pages (top-3 capsule image trios + factor chart)
  Final   — Heatmap appendix + full zone index table

Standalone CLI:
  python -m report.pdf_report --incidents outputs/incidents.json \\
      --capsules outputs/capsules --zones outputs/zones/zone_map.json \\
      --timeline outputs/timeline.json \\
      --heatmap-student outputs/heatmap_student.png \\
      --heatmap-raw outputs/heatmap_raw.png \\
      --annotated outputs/annotated_frame.png \\
      --output outputs/forensic_report.pdf \\
      --video test2.mp4
"""

import os
import json
import argparse
from datetime import datetime
from typing import Dict, List, Optional, Tuple

from fpdf import FPDF

# ── Color palette (print-safe) ────────────────────────────────────────────────
COLOR_HIGH   = (190,  30,  45)   # deep red
COLOR_MEDIUM = (200, 100,   0)   # deep orange
COLOR_LOW    = (160, 130,   0)   # amber
COLOR_CLEAR  = ( 34, 130,  34)   # forest green
COLOR_HEADER = ( 15,  35,  75)   # dark navy
COLOR_ACCENT = ( 55,  90, 160)   # medium blue
COLOR_LIGHT  = (248, 248, 252)   # near-white background
COLOR_WHITE  = (255, 255, 255)
COLOR_BLACK  = (  0,   0,   0)
COLOR_DARK   = ( 30,  30,  30)
COLOR_GRAY   = (130, 130, 130)
COLOR_LGRAY  = (210, 210, 215)
COLOR_TBLHDR = ( 50,  75, 140)   # table header row

PAGE_W = 210          # A4 width mm
PAGE_H = 297          # A4 height mm
MARGIN = 15           # page margin mm
USE_W  = PAGE_W - 2 * MARGIN   # 180 mm usable width


# ── Helpers ───────────────────────────────────────────────────────────────────

def _risk_color(level: str) -> Tuple[int, int, int]:
    l = (level or '').upper()
    if any(k in l for k in ('HIGH', 'CRITICAL')):
        return COLOR_HIGH
    if 'MEDIUM' in l:
        return COLOR_MEDIUM
    if 'LOW' in l:
        return COLOR_LOW
    return COLOR_CLEAR


def _risk_label(level: str) -> str:
    l = (level or '').upper()
    if any(k in l for k in ('HIGH', 'CRITICAL')):
        return 'HIGH RISK'
    if 'MEDIUM' in l:
        return 'MEDIUM RISK'
    if 'LOW' in l:
        return 'LOW RISK'
    return 'CLEAR'


def _fmt_ts(seconds: float) -> str:
    m = int(seconds // 60)
    s = int(seconds % 60)
    return f'{m:02d}:{s:02d}'


def _safe_text(s: str, max_len: int = 0) -> str:
    """Sanitize text for Helvetica (Latin-1 only). Replaces common Unicode chars
    with ASCII equivalents and strips anything outside the 0x00-0xFF range."""
    if not s:
        return ''
    replacements = [
        ('\u2022', '*'),   # bullet
        ('\u2026', '...'), # ellipsis
        ('\u2014', ' - '), # em dash
        ('\u2013', '-'),   # en dash
        ('\u2019', "'"),   # right single quote
        ('\u2018', "'"),   # left single quote
        ('\u201c', '"'),   # left double quote
        ('\u201d', '"'),   # right double quote
        ('\u2192', '->'),  # right arrow
        ('\u2190', '<-'),  # left arrow
        ('\u00d7', 'x'),   # multiplication sign
        ('\u2212', '-'),   # minus sign
        ('\u00b7', '.'),   # middle dot
        ('\u00e2', 'a'),   # a with circumflex
        ('\u25cf', '*'),   # black circle
    ]
    for uni, asc in replacements:
        s = s.replace(uni, asc)
    # Strip any remaining non-Latin-1 characters
    s = s.encode('latin-1', errors='ignore').decode('latin-1')
    if max_len and len(s) > max_len:
        s = s[:max_len] + '...'
    return s


def _safe_image(pdf: 'ForensicPDF', path: str, x: float, y: float, w: float, h: float) -> bool:
    """Embed image file; draw a labeled placeholder rectangle if unavailable."""
    if path and os.path.exists(str(path)) and os.path.getsize(str(path)) > 0:
        try:
            pdf.image(str(path), x=x, y=y, w=w, h=h)
            return True
        except Exception:
            pass
    # Placeholder box
    pdf.set_draw_color(*COLOR_LGRAY)
    pdf.set_fill_color(*COLOR_LIGHT)
    pdf.rect(x, y, w, h, 'FD')
    pdf.set_font('Helvetica', 'I', 6)
    pdf.set_text_color(*COLOR_GRAY)
    pdf.set_xy(x, y + h / 2 - 2)
    pdf.cell(w, 4, '[image unavailable]', align='C')
    pdf.set_text_color(*COLOR_BLACK)
    return False


def _draw_h_rule(pdf: 'ForensicPDF', y: float, color: tuple = None):
    color = color or COLOR_LGRAY
    pdf.set_draw_color(*color)
    pdf.set_line_width(0.3)
    pdf.line(MARGIN, y, PAGE_W - MARGIN, y)
    pdf.set_line_width(0.2)
    pdf.set_draw_color(*COLOR_BLACK)


def _section_title(pdf: 'ForensicPDF', title: str, y: float = None):
    """Draw a dark-accented section heading bar."""
    if y is not None:
        pdf.set_y(y)
    pdf.set_fill_color(*COLOR_ACCENT)
    pdf.set_text_color(*COLOR_WHITE)
    pdf.set_font('Helvetica', 'B', 9)
    pdf.cell(USE_W, 7, f'  {title.upper()}', border=0, new_x="LMARGIN", new_y="NEXT", align='L', fill=True)
    pdf.set_text_color(*COLOR_BLACK)
    pdf.ln(2)


def _draw_bar_chart(
    pdf: 'ForensicPDF',
    breakdown: Dict[str, float],
    x: float, y: float,
    chart_w: float,
    bar_h: float = 4.5,
    gap: float = 1.5,
) -> float:
    """Draw a horizontal bar chart for a factor breakdown dict.
    Returns the total vertical height consumed (mm)."""
    if not breakdown:
        return 0.0
    vals = list(breakdown.values())
    max_val = max(vals) if max(vals) > 0 else 1
    label_w  = 52.0
    val_w    = 12.0
    bar_area = chart_w - label_w - val_w
    cy = y
    for label, val in breakdown.items():
        filled = (val / max_val) * bar_area if max_val > 0 else 0
        # Row label
        pdf.set_font('Helvetica', '', 6.5)
        pdf.set_text_color(*COLOR_DARK)
        pdf.set_xy(x, cy)
        short = (label[:26] + '...') if len(label) > 26 else label
        pdf.cell(label_w, bar_h, short, align='L')
        # Background track
        pdf.set_fill_color(*COLOR_LGRAY)
        pdf.rect(x + label_w, cy + 1.0, bar_area, bar_h - 2, 'F')
        # Filled portion
        if filled > 0.5:
            pdf.set_fill_color(*COLOR_ACCENT)
            pdf.rect(x + label_w, cy + 1.0, filled, bar_h - 2, 'F')
        # Value label
        pdf.set_font('Helvetica', 'B', 6)
        pdf.set_text_color(*COLOR_GRAY)
        pdf.set_xy(x + label_w + bar_area + 1, cy)
        pdf.cell(val_w - 1, bar_h, str(int(val)), align='L')
        cy += bar_h + gap
    pdf.set_text_color(*COLOR_BLACK)
    return cy - y


# ── PDF class ─────────────────────────────────────────────────────────────────

class ForensicPDF(FPDF):
    """FPDF subclass with running footer on all pages except the cover."""

    def __init__(self, report_meta: dict):
        super().__init__(orientation='P', unit='mm', format='A4')
        self._meta = report_meta
        self.set_margins(MARGIN, MARGIN, MARGIN)
        self.set_auto_page_break(auto=True, margin=MARGIN + 6)

    def footer(self):
        if self.page_no() == 1:
            return
        y_rule = PAGE_H - 15
        self.set_draw_color(*COLOR_LGRAY)
        self.set_line_width(0.25)
        self.line(MARGIN, y_rule, PAGE_W - MARGIN, y_rule)
        self.set_line_width(0.2)
        self.set_y(y_rule + 1)
        self.set_font('Helvetica', '', 6.5)
        self.set_text_color(*COLOR_GRAY)
        cam = self._meta.get('camera_id', 'CAM-01')
        gen = self._meta.get('generated_at', '')
        self.set_x(MARGIN)
        self.cell(
            USE_W * 0.8, 4,
            f'Drishti AI Forensic Report  |  {cam}  |  Generated: {gen}  |  CONFIDENTIAL',
            align='L',
        )
        self.set_x(MARGIN)
        self.cell(USE_W, 4, f'Page {self.page_no()}', align='R')
        self.set_text_color(*COLOR_BLACK)


# ── Page builders ─────────────────────────────────────────────────────────────

def _cover_page(pdf: ForensicPDF, incidents: List[dict], meta: dict):
    pdf.add_page()

    # ── Dark navy header band ──────────────────────────────────────────────
    pdf.set_fill_color(*COLOR_HEADER)
    pdf.rect(0, 0, PAGE_W, 52, 'F')

    # Accent stripe
    pdf.set_fill_color(*COLOR_ACCENT)
    pdf.rect(0, 48, PAGE_W, 4, 'F')

    # Branding text
    pdf.set_text_color(*COLOR_WHITE)
    pdf.set_font('Helvetica', 'B', 26)
    pdf.set_xy(MARGIN, 10)
    pdf.cell(USE_W, 12, 'DRISHTI AI', align='L')

    pdf.set_font('Helvetica', '', 13)
    pdf.set_xy(MARGIN, 24)
    pdf.cell(USE_W, 7, 'Examination Video Forensic Report', align='L')

    pdf.set_font('Helvetica', '', 8)
    pdf.set_xy(MARGIN, 33)
    pdf.cell(USE_W, 5, 'AI-Powered Surveillance | Automated Cheating Detection | Forensic Evidence Synthesis', align='L')

    # Right-align AI logo text
    pdf.set_font('Helvetica', 'B', 9)
    pdf.set_xy(MARGIN, 38)
    pdf.cell(USE_W, 5, 'v1.0  |  Confidential', align='R')

    # ── Metadata block ─────────────────────────────────────────────────────
    pdf.set_text_color(*COLOR_BLACK)
    y = 62
    pdf.set_fill_color(*COLOR_LIGHT)
    pdf.rect(MARGIN, y, USE_W, 36, 'F')

    fields = [
        ('Video File',      meta.get('video_name', 'N/A')),
        ('Camera ID',       meta.get('camera_id', 'N/A')),
        ('Video Duration',  meta.get('video_duration_str', 'N/A')),
        ('Report Date',     meta.get('generated_at', 'N/A')),
    ]
    pdf.set_font('Helvetica', '', 9)
    label_w = 42
    fy = y + 5
    for label, val in fields:
        pdf.set_xy(MARGIN + 5, fy)
        pdf.set_font('Helvetica', 'B', 9)
        pdf.set_text_color(*COLOR_HEADER)
        pdf.cell(label_w, 6, label + ':', align='L')
        pdf.set_font('Helvetica', '', 9)
        pdf.set_text_color(*COLOR_DARK)
        pdf.cell(USE_W - label_w - 5, 6, str(val), align='L')
        fy += 7

    # ── Overall risk banner ────────────────────────────────────────────────
    # CONFIRMED: uses max(incidents, key=risk_score) — not last-processed
    overall_level = meta.get('overall_risk_level', 'CLEAR')
    overall_score = meta.get('overall_risk_score', 0)
    banner_color  = _risk_color(overall_level)
    banner_label  = _risk_label(overall_level)

    y_banner = 108
    pdf.set_fill_color(*banner_color)
    pdf.rect(MARGIN, y_banner, USE_W, 28, 'F')

    pdf.set_text_color(*COLOR_WHITE)
    pdf.set_font('Helvetica', '', 9)
    pdf.set_xy(MARGIN, y_banner + 5)
    pdf.cell(USE_W, 6, 'OVERALL RISK ASSESSMENT', align='C')

    pdf.set_font('Helvetica', 'B', 22)
    pdf.set_xy(MARGIN, y_banner + 12)
    pdf.cell(USE_W, 10, banner_label, align='C')

    pdf.set_font('Helvetica', '', 10)
    pdf.set_xy(MARGIN, y_banner + 21)
    pdf.cell(USE_W, 5, f'Aggregate Risk Index: {overall_score}/100', align='C')

    # ── Summary stats strip ────────────────────────────────────────────────
    pdf.set_text_color(*COLOR_BLACK)
    y_stats = y_banner + 38
    stat_w  = USE_W / 4

    stats = [
        ('TOTAL INCIDENTS',    str(meta.get('total_incidents', 0))),
        ('DESKS MONITORED',    str(meta.get('total_zones', 0))),
        ('HIGH-RISK DESKS',    str(meta.get('high_risk_desks', 0))),
        ('VIDEO DURATION',     meta.get('video_duration_str', 'N/A')),
    ]

    for i, (label, val) in enumerate(stats):
        sx = MARGIN + i * stat_w
        # Alternating fill
        fill = COLOR_LIGHT if i % 2 == 0 else COLOR_WHITE
        pdf.set_fill_color(*fill)
        pdf.rect(sx, y_stats, stat_w, 22, 'F')
        pdf.set_font('Helvetica', 'B', 16)
        pdf.set_text_color(*COLOR_ACCENT)
        pdf.set_xy(sx, y_stats + 4)
        pdf.cell(stat_w, 10, val, align='C')
        pdf.set_font('Helvetica', '', 7)
        pdf.set_text_color(*COLOR_GRAY)
        pdf.set_xy(sx, y_stats + 14)
        pdf.cell(stat_w, 5, label, align='C')

    # Border around stats strip
    pdf.set_draw_color(*COLOR_LGRAY)
    pdf.rect(MARGIN, y_stats, USE_W, 22)
    pdf.set_text_color(*COLOR_BLACK)

    # ── Incidents quick list ───────────────────────────────────────────────
    y_list = y_stats + 32
    _section_title(pdf, 'Incidents Overview', y=y_list)
    y_list = pdf.get_y()

    if incidents:
        col_ws = [30, 20, 50, 22, 58]   # ID, Score, Primary Class, Duration, Location
        headers = ['Incident ID', 'Risk', 'Type', 'Duration', 'Location']
        # Header row
        pdf.set_fill_color(*COLOR_TBLHDR)
        pdf.set_text_color(*COLOR_WHITE)
        pdf.set_font('Helvetica', 'B', 7.5)
        pdf.set_xy(MARGIN, y_list)
        for hdr, cw in zip(headers, col_ws):
            pdf.cell(cw, 6, hdr, border=1, align='C', fill=True)
        pdf.ln()
        # Data rows
        for idx, inc in enumerate(incidents):
            fill = COLOR_LIGHT if idx % 2 == 0 else COLOR_WHITE
            pdf.set_fill_color(*fill)
            pdf.set_text_color(*COLOR_DARK)
            pdf.set_font('Helvetica', '', 7)
            row = [
                inc.get('incident_id', 'N/A'),
                f"{inc.get('risk_score', 0)}/100",
                (inc.get('primary_class', '') or '')[:28],
                f"{inc.get('duration_seconds', 0):.1f}s",
                (inc.get('location_desc', '') or '')[:38],
            ]
            pdf.set_xy(MARGIN, pdf.get_y())
            for val, cw in zip(row, col_ws):
                pdf.cell(cw, 5.5, str(val), border=1, align='L', fill=True)
            pdf.ln()
    else:
        pdf.set_font('Helvetica', 'I', 9)
        pdf.set_text_color(*COLOR_GRAY)
        pdf.set_xy(MARGIN, y_list)
        pdf.cell(USE_W, 8, 'No incidents detected.', align='C')
        pdf.set_text_color(*COLOR_BLACK)

    # ── Cover footer ───────────────────────────────────────────────────────
    pdf.set_fill_color(*COLOR_HEADER)
    pdf.rect(0, PAGE_H - 20, PAGE_W, 20, 'F')
    pdf.set_font('Helvetica', '', 7)
    pdf.set_text_color(*COLOR_WHITE)
    pdf.set_xy(MARGIN, PAGE_H - 14)
    pdf.cell(USE_W, 5, 'CONFIDENTIAL -- FOR AUTHORIZED EXAMINER USE ONLY -- Drishti AI Examination Forensics Platform', align='C')
    pdf.set_xy(MARGIN, PAGE_H - 9)
    pdf.cell(USE_W, 5, 'This document was automatically generated by an AI system. All findings must be reviewed by a qualified examiner.', align='C')
    pdf.set_text_color(*COLOR_BLACK)


def _executive_summary(
    pdf: ForensicPDF,
    incidents: List[dict],
    timeline: List[dict],
    annotated_frame: str,
    meta: dict,
):
    pdf.add_page()
    pdf.set_font('Helvetica', 'B', 14)
    pdf.set_text_color(*COLOR_HEADER)
    pdf.cell(USE_W, 10, 'Executive Summary', new_x="LMARGIN", new_y="NEXT")
    _draw_h_rule(pdf, pdf.get_y())
    pdf.ln(3)

    # ── Annotated surveillance frame ───────────────────────────────────────
    frame_h = 72
    _safe_image(pdf, annotated_frame, MARGIN, pdf.get_y(), USE_W, frame_h)
    pdf.set_y(pdf.get_y() + frame_h + 2)
    pdf.set_font('Helvetica', 'I', 7)
    pdf.set_text_color(*COLOR_GRAY)
    pdf.cell(USE_W, 4, 'Figure 1: Annotated surveillance frame with zone boundaries and desk IDs', align='C', new_x="LMARGIN", new_y="NEXT")
    pdf.set_text_color(*COLOR_BLACK)
    pdf.ln(3)

    # ── 4-column stats row ─────────────────────────────────────────────────
    stat_w = USE_W / 4
    stats = [
        ('Desks Monitored',    str(meta.get('total_zones', 0))),
        ('Zones Calibrated',   str(meta.get('total_zones', 0))),
        ('Incidents Detected', str(meta.get('total_incidents', 0))),
        ('Peak Risk Score',    f"{meta.get('overall_risk_score', 0)}/100"),
    ]
    y_stat = pdf.get_y()
    for i, (label, val) in enumerate(stats):
        sx = MARGIN + i * stat_w
        fill = COLOR_LIGHT if i % 2 == 0 else COLOR_WHITE
        pdf.set_fill_color(*fill)
        pdf.rect(sx, y_stat, stat_w, 15, 'F')
        pdf.set_draw_color(*COLOR_LGRAY)
        pdf.rect(sx, y_stat, stat_w, 15)
        pdf.set_font('Helvetica', 'B', 13)
        pdf.set_text_color(*COLOR_ACCENT)
        pdf.set_xy(sx, y_stat + 2)
        pdf.cell(stat_w, 7, val, align='C')
        pdf.set_font('Helvetica', '', 6.5)
        pdf.set_text_color(*COLOR_GRAY)
        pdf.set_xy(sx, y_stat + 9)
        pdf.cell(stat_w, 4, label, align='C')
    pdf.set_text_color(*COLOR_BLACK)
    pdf.set_y(y_stat + 18)

    # ── Incident timeline strip ────────────────────────────────────────────
    _section_title(pdf, 'Incident Timeline')
    y_tl = pdf.get_y()

    # Determine total video duration from timeline or incident data
    all_ends = [t.get('end_timestamp', 0) for t in timeline] + \
               [i.get('end_timestamp', 0) for i in incidents]
    video_dur = max(all_ends) if all_ends else 60.0
    if video_dur < 1:
        video_dur = 60.0

    tl_h   = 12.0
    tl_w   = USE_W
    tl_x   = MARGIN
    tl_y   = y_tl

    # Background track
    pdf.set_fill_color(*COLOR_LGRAY)
    pdf.rect(tl_x, tl_y, tl_w, tl_h, 'F')

    # Incident segments
    for inc in incidents:
        t0  = inc.get('start_timestamp', 0)
        t1  = inc.get('end_timestamp', video_dur)
        lvl = inc.get('risk_level', 'LOW')
        x0  = tl_x + (t0 / video_dur) * tl_w
        seg_w = max(2.0, ((t1 - t0) / video_dur) * tl_w)
        pdf.set_fill_color(*_risk_color(lvl))
        pdf.rect(x0, tl_y, seg_w, tl_h, 'F')

    # Tick marks every 10 seconds
    pdf.set_draw_color(*COLOR_GRAY)
    pdf.set_font('Helvetica', '', 5.5)
    pdf.set_text_color(*COLOR_GRAY)
    tick_interval = max(10, int(video_dur // 10))
    t = 0
    while t <= video_dur:
        tx = tl_x + (t / video_dur) * tl_w
        pdf.line(tx, tl_y + tl_h, tx, tl_y + tl_h + 2)
        pdf.set_xy(tx - 4, tl_y + tl_h + 2)
        pdf.cell(8, 3, _fmt_ts(t), align='C')
        t += tick_interval

    # Incident ID labels inside segments (if wide enough)
    for inc in incidents:
        t0  = inc.get('start_timestamp', 0)
        t1  = inc.get('end_timestamp', video_dur)
        seg_w = max(2.0, ((t1 - t0) / video_dur) * tl_w)
        if seg_w > 12:
            x0 = tl_x + (t0 / video_dur) * tl_w
            pdf.set_text_color(*COLOR_WHITE)
            pdf.set_font('Helvetica', 'B', 5)
            pdf.set_xy(x0 + 1, tl_y + 4)
            pdf.cell(seg_w - 1, 4, _safe_text(inc.get('incident_id', '')), align='L')

    pdf.set_text_color(*COLOR_BLACK)
    pdf.set_y(tl_y + tl_h + 8)

    # ── Risk factor breakdown chart ────────────────────────────────────────
    if incidents:
        # Aggregate factor breakdown across all incidents (summed)
        agg_breakdown: Dict[str, float] = {}
        for inc in incidents:
            for factor, val in (inc.get('factor_breakdown') or {}).items():
                agg_breakdown[factor] = agg_breakdown.get(factor, 0) + val

        _section_title(pdf, 'Aggregated Risk Factor Breakdown')
        chart_y = pdf.get_y()
        height_used = _draw_bar_chart(pdf, agg_breakdown, MARGIN, chart_y, USE_W * 0.6, bar_h=5, gap=2)
        pdf.set_y(chart_y + height_used + 4)


def _incident_page(
    pdf: ForensicPDF,
    incident: dict,
    all_capsules: List[dict],
    max_capsules_images: int = 3,
):
    pdf.add_page()

    iid      = incident.get('incident_id', 'N/A')
    level    = incident.get('risk_level', 'LOW')
    score    = incident.get('risk_score', 0)
    dur      = incident.get('duration_seconds', 0)
    loc      = incident.get('location_desc', '')
    factors  = incident.get('contributing_factors') or []
    breakdown = incident.get('factor_breakdown') or {}
    explanation = incident.get('explanation_text', '') or ''

    # ── Severity banner ────────────────────────────────────────────────────
    banner_h = 18
    pdf.set_fill_color(*_risk_color(level))
    pdf.rect(0, MARGIN, PAGE_W, banner_h, 'F')

    pdf.set_text_color(*COLOR_WHITE)
    pdf.set_font('Helvetica', 'B', 13)
    pdf.set_xy(MARGIN, MARGIN + 2)
    pdf.cell(USE_W * 0.6, 7, f'Incident {iid}', align='L')

    pdf.set_font('Helvetica', 'B', 10)
    pdf.set_xy(MARGIN, MARGIN + 10)
    pdf.cell(USE_W * 0.6, 5, f'Status: {_risk_label(level)}', align='L')

    pdf.set_font('Helvetica', 'B', 18)
    pdf.set_xy(MARGIN, MARGIN)
    pdf.cell(USE_W, banner_h - 2, f'{score}/100', align='R')

    pdf.set_text_color(*COLOR_BLACK)
    pdf.set_y(MARGIN + banner_h + 3)

    # ── Metadata row ───────────────────────────────────────────────────────
    pdf.set_font('Helvetica', '', 8)
    meta_items = [
        ('Duration', f'{dur:.1f}s ({_fmt_ts(incident.get("start_timestamp",0))} -> {_fmt_ts(incident.get("end_timestamp",0))})'),
        ('Confidence', f'{incident.get("confidence", 0)*100:.0f}%'),
        ('Desks Involved', str(len(incident.get('zone_ids', [])))),
    ]
    col_w = USE_W / len(meta_items)
    for i, (k, v) in enumerate(meta_items):
        sx = MARGIN + i * col_w
        fill = COLOR_LIGHT if i % 2 == 0 else COLOR_WHITE
        pdf.set_fill_color(*fill)
        pdf.rect(sx, pdf.get_y(), col_w, 10, 'F')
        pdf.set_xy(sx + 2, pdf.get_y() + 1)
        pdf.set_font('Helvetica', 'B', 7)
        pdf.set_text_color(*COLOR_HEADER)
        pdf.cell(col_w - 2, 4, k, align='L')
        pdf.set_xy(sx + 2, pdf.get_y() + 4)
        pdf.set_font('Helvetica', '', 7.5)
        pdf.set_text_color(*COLOR_DARK)
        pdf.cell(col_w - 2, 4, v, align='L')

    pdf.set_text_color(*COLOR_BLACK)
    pdf.set_y(pdf.get_y() + 13)

    # Location
    pdf.set_font('Helvetica', '', 7.5)
    pdf.set_text_color(*COLOR_GRAY)
    short_loc = _safe_text(loc, max_len=120)
    pdf.multi_cell(USE_W, 4, f'Location: {short_loc}', align='L')
    pdf.ln(2)
    pdf.set_text_color(*COLOR_BLACK)

    # ── Top-N capsule evidence images ──────────────────────────────────────
    top_caps = all_capsules[:max_capsules_images]
    rest_caps = all_capsules[max_capsules_images:]

    if top_caps:
        _section_title(pdf, f'Forensic Evidence -- Top {len(top_caps)} Highest-Risk Desks')
        y_imgs = pdf.get_y()
        img_col_w = USE_W / 3
        img_row_h = 36.0   # height of each image cell

        for cap_idx, cap in enumerate(top_caps):
            desk_label = cap.get('location_desc', f"Zone {cap.get('zone_id','?')}")
            cap_score  = cap.get('risk_score', 0)
            cap_level  = cap.get('risk_level', 'LOW')

            row_y = y_imgs + cap_idx * (img_row_h + 6)

            # Desk header label
            pdf.set_fill_color(*_risk_color(cap_level))
            pdf.set_text_color(*COLOR_WHITE)
            pdf.set_font('Helvetica', 'B', 7)
            pdf.rect(MARGIN, row_y, USE_W, 5, 'F')
            pdf.set_xy(MARGIN + 2, row_y + 0.5)
            pdf.cell(USE_W - 4, 4,
                     _safe_text(f'{desk_label}  |  Risk: {cap_score}/100  |  {cap.get("primary_behavior","?")}'),
                     align='L')
            pdf.set_text_color(*COLOR_BLACK)
            row_y += 5.5

            # 3 images: before / during / after
            img_labels = ['BEFORE', 'DURING', 'AFTER']
            img_paths  = [
                cap.get('before_snapshot_path', ''),
                cap.get('during_snapshot_path', ''),
                cap.get('after_snapshot_path', ''),
            ]
            for j, (lbl, ipath) in enumerate(zip(img_labels, img_paths)):
                ix = MARGIN + j * img_col_w
                _safe_image(pdf, ipath, ix, row_y, img_col_w - 1, img_row_h - 2)
                pdf.set_font('Helvetica', 'B', 6)
                pdf.set_text_color(*COLOR_GRAY)
                pdf.set_xy(ix, row_y + img_row_h - 2)
                pdf.cell(img_col_w - 1, 3, lbl, align='C')
                pdf.set_text_color(*COLOR_BLACK)

        pdf.set_y(y_imgs + len(top_caps) * (img_row_h + 6) + 2)

    # ── Remaining desks compact table ──────────────────────────────────────
    if rest_caps:
        _section_title(pdf, f'Additional Desks ({len(rest_caps)} more)')
        col_ws = [35, 55, 18, 30, 42]
        headers = ['Desk / Zone', 'Location', 'Risk', 'Behavior', 'Contributing']
        pdf.set_fill_color(*COLOR_TBLHDR)
        pdf.set_text_color(*COLOR_WHITE)
        pdf.set_font('Helvetica', 'B', 6.5)
        pdf.set_x(MARGIN)
        for hdr, cw in zip(headers, col_ws):
            pdf.cell(cw, 5, hdr, border=1, align='C', fill=True)
        pdf.ln()
        for idx, cap in enumerate(rest_caps):
            fill = COLOR_LIGHT if idx % 2 == 0 else COLOR_WHITE
            pdf.set_fill_color(*fill)
            pdf.set_text_color(*COLOR_DARK)
            pdf.set_font('Helvetica', '', 6)
            zone_lbl = _safe_text(f'Zone {cap.get("zone_id","?")}' )
            loc_str  = _safe_text(cap.get('location_desc', '') or '', max_len=32)
            cf_str   = _safe_text((cap.get('contributing_factors') or [''])[0], max_len=28)
            row = [zone_lbl, loc_str, f"{cap.get('risk_score',0)}/100",
                   _safe_text(cap.get('primary_behavior','') or '', max_len=15), cf_str]
            pdf.set_x(MARGIN)
            for val, cw in zip(row, col_ws):
                pdf.cell(cw, 4.5, str(val), border=1, align='L', fill=True)
            pdf.ln()
        pdf.ln(2)

    # ── Risk factor breakdown chart ────────────────────────────────────────
    if breakdown:
        _section_title(pdf, 'Risk Factor Breakdown')
        cy = pdf.get_y()
        h_used = _draw_bar_chart(pdf, breakdown, MARGIN, cy, USE_W * 0.65, bar_h=5, gap=2)
        pdf.set_y(cy + h_used + 3)

    # ── Contributing factors ───────────────────────────────────────────────
    if factors:
        _section_title(pdf, 'Contributing Factors')
        for fac in factors:
            pdf.set_font('Helvetica', '', 7.5)
            pdf.set_text_color(*COLOR_DARK)
            pdf.set_x(MARGIN + 3)
            pdf.cell(3, 5, '-', align='L')
            pdf.set_x(MARGIN + 8)
            pdf.multi_cell(USE_W - 8, 5, _safe_text(str(fac)), align='L')
        pdf.ln(1)

    # ── Analyst explanation ────────────────────────────────────────────────
    if explanation:
        _section_title(pdf, 'AI Analysis')
        pdf.set_font('Helvetica', '', 7.5)
        pdf.set_text_color(*COLOR_DARK)
        short_expl = _safe_text(explanation, max_len=600)
        pdf.multi_cell(USE_W, 5, short_expl, align='J')
        pdf.set_text_color(*COLOR_BLACK)


def _heatmap_appendix(
    pdf: ForensicPDF,
    zones: List[dict],
    heatmap_student: str,
    heatmap_raw: str,
):
    pdf.add_page()
    pdf.set_font('Helvetica', 'B', 14)
    pdf.set_text_color(*COLOR_HEADER)
    pdf.cell(USE_W, 10, 'Heatmap Appendix & Zone Index', new_x="LMARGIN", new_y="NEXT")
    _draw_h_rule(pdf, pdf.get_y())
    pdf.ln(3)

    # ── Side-by-side heatmaps ──────────────────────────────────────────────
    hm_w = USE_W / 2 - 2
    hm_h = 70.0
    y_hm = pdf.get_y()

    _safe_image(pdf, heatmap_student, MARGIN,           y_hm, hm_w, hm_h)
    _safe_image(pdf, heatmap_raw,     MARGIN + hm_w + 4, y_hm, hm_w, hm_h)

    pdf.set_font('Helvetica', 'I', 7)
    pdf.set_text_color(*COLOR_GRAY)
    pdf.set_xy(MARGIN, y_hm + hm_h + 1)
    pdf.cell(hm_w, 4, 'Figure 2: Student Activity Heatmap', align='C')
    pdf.set_xy(MARGIN + hm_w + 4, y_hm + hm_h + 1)
    pdf.cell(hm_w, 4, 'Figure 3: Raw Motion Variance Heatmap', align='C')
    pdf.set_text_color(*COLOR_BLACK)
    pdf.set_y(y_hm + hm_h + 8)

    # ── Zone index table ───────────────────────────────────────────────────
    _section_title(pdf, 'Zone Calibration Index')

    col_ws  = [18, 22, 70, 28, 22, 20]
    headers = ['Zone ID', 'Desk ID', 'Location', 'Center (px)', 'Confidence', 'Status']

    pdf.set_fill_color(*COLOR_TBLHDR)
    pdf.set_text_color(*COLOR_WHITE)
    pdf.set_font('Helvetica', 'B', 7)
    pdf.set_x(MARGIN)
    for hdr, cw in zip(headers, col_ws):
        pdf.cell(cw, 6, hdr, border=1, align='C', fill=True)
    pdf.ln()

    for idx, zone in enumerate(zones):
        fill = COLOR_LIGHT if idx % 2 == 0 else COLOR_WHITE
        pdf.set_fill_color(*fill)
        pdf.set_text_color(*COLOR_DARK)
        pdf.set_font('Helvetica', '', 6.5)

        zid    = str(zone.get('zone_id', '?'))
        desk   = zone.get('desk_id', f'S{zid}')
        loc    = (zone.get('location_desc', '') or '')[:40]
        cx, cy_ = zone.get('center', [0, 0])
        center  = f'({int(cx)}, {int(cy_)})'
        conf    = zone.get('zone_confidence', 0)
        conf_str = f'{conf*100:.0f}%'
        status  = 'ESTIMATED' if zone.get('is_estimated', False) else 'DETECTED'

        # Color confidence cell
        conf_color = COLOR_CLEAR if conf >= 0.6 else (COLOR_MEDIUM if conf >= 0.3 else COLOR_HIGH)

        row_vals = [zid, desk, loc, center, conf_str, status]
        pdf.set_x(MARGIN)
        for col_i, (val, cw) in enumerate(zip(row_vals, col_ws)):
            if col_i == 4:   # confidence column — color-coded
                pdf.set_text_color(*conf_color)
                pdf.set_font('Helvetica', 'B', 6.5)
            else:
                pdf.set_text_color(*COLOR_DARK)
                pdf.set_font('Helvetica', '', 6.5)
            pdf.cell(cw, 5, str(val), border=1, align='C' if col_i != 2 else 'L', fill=True)
        pdf.ln()

    pdf.set_text_color(*COLOR_BLACK)
    pdf.ln(5)

    # ── Disclaimer ────────────────────────────────────────────────────────
    pdf.set_fill_color(*COLOR_LIGHT)
    pdf.set_draw_color(*COLOR_LGRAY)
    y_disc = pdf.get_y()
    pdf.rect(MARGIN, y_disc, USE_W, 22, 'FD')
    pdf.set_font('Helvetica', 'B', 7.5)
    pdf.set_text_color(*COLOR_HEADER)
    pdf.set_xy(MARGIN + 3, y_disc + 3)
    pdf.cell(USE_W - 6, 5, 'DISCLAIMER', align='L')
    pdf.set_font('Helvetica', '', 6.5)
    pdf.set_text_color(*COLOR_DARK)
    disclaimer = (
        'This report was automatically generated by the Drishti AI Examination Video Forensics Platform. '
        'All AI-generated findings are probabilistic in nature and must be reviewed and verified by a qualified '
        'human examiner before any disciplinary action is taken. Drishti AI does not constitute legal evidence '
        'without human oversight and institutional validation procedures.'
    )
    pdf.set_xy(MARGIN + 3, y_disc + 9)
    pdf.multi_cell(USE_W - 6, 4, disclaimer, align='J')
    pdf.set_text_color(*COLOR_BLACK)


# ── Public API ────────────────────────────────────────────────────────────────

def generate_forensic_report(
    incidents_path: str,
    capsules_dir: str,
    zone_map_path: str,
    timeline_path: str,
    heatmap_student: str,
    heatmap_raw: str,
    annotated_frame: str,
    output_pdf_path: str,
    video_path: str,
    config: dict,
) -> str:
    """
    Build and write a forensic PDF report from Stage 5 outputs.

    Overall risk level on the cover page is determined by max(risk_score)
    across all incidents — not by ordering or the last-processed incident.

    Returns the path of the written PDF file.
    """
    # ── Load incidents (sorted high→low risk) ──────────────────────────────
    incidents: List[dict] = []
    if os.path.exists(incidents_path):
        with open(incidents_path, encoding='utf-8') as f:
            incidents = json.load(f)
    incidents.sort(key=lambda x: x.get('risk_score', 0), reverse=True)

    # ── Determine overall risk — explicit max-reduce (not order-dependent) ──
    if incidents:
        top_inc = max(incidents, key=lambda x: x.get('risk_score', 0))
        overall_risk_score = top_inc.get('risk_score', 0)
        overall_risk_level = top_inc.get('risk_level', 'LOW')
    else:
        overall_risk_score = 0
        overall_risk_level = 'CLEAR'

    # ── Load capsules grouped by incident_id ───────────────────────────────
    capsules_by_incident: Dict[str, List[dict]] = {}
    if os.path.isdir(capsules_dir):
        for fname in sorted(os.listdir(capsules_dir)):
            if not fname.endswith('_capsule.json'):
                continue
            try:
                cap_path = os.path.join(capsules_dir, fname)
                with open(cap_path, encoding='utf-8') as f:
                    cap = json.load(f)
                iid = cap.get('incident_id', '__orphan__')
                capsules_by_incident.setdefault(iid, []).append(cap)
            except Exception:
                continue
    # Sort capsules per incident by risk score (desc)
    for iid in capsules_by_incident:
        capsules_by_incident[iid].sort(key=lambda x: x.get('risk_score', 0), reverse=True)

    # ── Load zone map ──────────────────────────────────────────────────────
    zones: List[dict] = []
    if os.path.exists(zone_map_path):
        with open(zone_map_path, encoding='utf-8') as f:
            raw = json.load(f)
        # Supports both list-of-zones and {'zones': [...]} formats
        zones = raw if isinstance(raw, list) else raw.get('zones', [])

    # ── Load timeline ──────────────────────────────────────────────────────
    timeline: List[dict] = []
    if timeline_path and os.path.exists(timeline_path):
        with open(timeline_path, encoding='utf-8') as f:
            timeline = json.load(f)

    # ── Derive video duration ──────────────────────────────────────────────
    all_ends = (
        [t.get('end_timestamp', 0) for t in timeline] +
        [i.get('end_timestamp', 0) for i in incidents]
    )
    video_dur = max(all_ends) if all_ends else 60.0

    # ── Count high-risk desks ──────────────────────────────────────────────
    high_risk_desks = 0
    for inc in incidents:
        if (inc.get('risk_level') or '').upper() in ('HIGH', 'CRITICAL'):
            high_risk_desks += len(inc.get('zone_ids') or [])

    # ── Build report metadata ──────────────────────────────────────────────
    video_name   = os.path.basename(video_path) if video_path else 'N/A'
    generated_at = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    camera_id    = (config.get('video') or {}).get('camera_id', 'CAM-01')
    meta = {
        'video_name':          video_name,
        'camera_id':           camera_id,
        'generated_at':        generated_at,
        'overall_risk_level':  overall_risk_level,
        'overall_risk_score':  overall_risk_score,
        'total_incidents':     len(incidents),
        'total_zones':         len(zones),
        'high_risk_desks':     high_risk_desks,
        'video_duration_str':  _fmt_ts(video_dur),
    }

    # ── Create PDF ─────────────────────────────────────────────────────────
    pdf = ForensicPDF(report_meta=meta)
    pdf.set_creator('Drishti AI — Examination Forensics Platform v1.0')
    pdf.set_author('Drishti AI')
    pdf.set_title(f'Forensic Report — {video_name}')

    # ── Build pages ────────────────────────────────────────────────────────
    _cover_page(pdf, incidents, meta)
    _executive_summary(pdf, incidents, timeline, annotated_frame, meta)

    max_caps = (config.get('report') or {}).get('max_capsules_per_incident', 3)
    for inc in incidents:
        caps = capsules_by_incident.get(inc.get('incident_id', ''), [])
        _incident_page(pdf, inc, caps, max_capsules_images=max_caps)

    if (config.get('report') or {}).get('include_heatmaps', True):
        _heatmap_appendix(pdf, zones, heatmap_student, heatmap_raw)

    # ── Save ───────────────────────────────────────────────────────────────
    out_dir = os.path.dirname(output_pdf_path)
    if out_dir:
        os.makedirs(out_dir, exist_ok=True)
    pdf.output(output_pdf_path)
    return output_pdf_path


# ── Standalone CLI ────────────────────────────────────────────────────────────

def _cli():
    parser = argparse.ArgumentParser(
        description='Drishti AI — Generate forensic PDF report from Stage 5 outputs.'
    )
    parser.add_argument('--incidents',        default='outputs/incidents.json')
    parser.add_argument('--capsules',         default='outputs/capsules')
    parser.add_argument('--zones',            default='outputs/zones/zone_map.json')
    parser.add_argument('--timeline',         default='outputs/timeline.json')
    parser.add_argument('--heatmap-student',  default='outputs/heatmap_student.png')
    parser.add_argument('--heatmap-raw',      default='outputs/heatmap_raw.png')
    parser.add_argument('--annotated',        default='outputs/annotated_frame.png')
    parser.add_argument('--output',           default='outputs/forensic_report.pdf')
    parser.add_argument('--video',            default='')
    parser.add_argument('--camera-id',        default='CAM-01')
    args = parser.parse_args()

    config = {
        'video':  {'camera_id': args.camera_id},
        'report': {'enabled': True, 'include_heatmaps': True, 'max_capsules_per_incident': 3},
    }
    path = generate_forensic_report(
        incidents_path  = args.incidents,
        capsules_dir    = args.capsules,
        zone_map_path   = args.zones,
        timeline_path   = args.timeline,
        heatmap_student = args.heatmap_student,
        heatmap_raw     = args.heatmap_raw,
        annotated_frame = args.annotated,
        output_pdf_path = args.output,
        video_path      = args.video,
        config          = config,
    )
    size_kb = os.path.getsize(path) // 1024
    print(f'[Drishti AI] Forensic PDF written: {path} ({size_kb} KB)')


if __name__ == '__main__':
    _cli()
