"""
PDF Report Generator using fpdf2
Produces professional printable PDFs for complete reports and per-student reports.
All strings use latin-1 compatible ASCII text to prevent font encoding errors.
"""
import os
import json
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any, Optional

try:
    from fpdf import FPDF
    FPDF2 = True
except ImportError:
    from fpdf import FPDF
    FPDF2 = False

BASE_DIR   = Path(__file__).resolve().parent.parent
OUTPUTS    = BASE_DIR / "outputs"
ZONES_DIR  = OUTPUTS / "zones"
EVENTS_DIR = OUTPUTS / "events"
PDF_OUT    = OUTPUTS / "reports"
PDF_OUT.mkdir(exist_ok=True)


def _read_json(p: Path):
    if not p.exists(): return None
    with open(p, encoding="utf-8") as f:
        return json.load(f)


def _fmt_time(s: float) -> str:
    m = int(s // 60); sec = s % 60
    return f"{m:02d}:{sec:05.2f}"


def _clean_str(text: str) -> str:
    """Replaces Unicode characters with ASCII equivalents."""
    if not isinstance(text, str):
        text = str(text)
    return (
        text.replace("—", "--")
            .replace("–", "-")
            .replace("→", "->")
            .replace("•", "*")
            .replace("✓", "[OK]")
            .replace("⚠️", "[!]")
            .replace("🛡", "")
            .replace("🎥", "")
            .replace("👥", "")
            .replace("🔴", "[HIGH]")
            .replace("🟡", "[MED]")
            .replace("🟢", "[LOW]")
    )


def _compute_scores(zones, events):
    """Returns dict: zone_id -> {activity_pct, risk, event_count, raw_motion}"""
    if not zones: return {}
    zone_motion: Dict[int, List[float]] = {z["zone_id"]: [] for z in zones}
    for ev in (events or []):
        zid = ev.get("zone_id")
        if zid in zone_motion:
            zone_motion[zid].append(ev.get("avg_motion_score", 0))
    zone_avg = {zid: (sum(s)/len(s) if s else 0.0) for zid, s in zone_motion.items()}
    max_s = max(zone_avg.values()) if zone_avg else 1e-9
    max_s = max(max_s, 1e-9)
    out = {}
    for z in zones:
        zid = z["zone_id"]
        raw = zone_avg.get(zid, 0.0)
        pct = round((raw / max_s) * 100)
        n_ev = sum(1 for ev in (events or []) if ev.get("zone_id") == zid)
        if pct >= 70: risk = "HIGH"
        elif pct >= 30: risk = "MEDIUM"
        elif n_ev > 0: risk = "LOW"
        else: risk = "NONE"
        out[zid] = {"activity_pct": pct, "risk": risk, "event_count": n_ev, "raw_motion": raw}
    return out


class ExamGuardPDF(FPDF):
    def header(self):
        self.set_fill_color(15, 23, 42)
        self.rect(0, 0, 210, 15, 'F')
        self.set_font("Helvetica", "B", 9)
        self.set_text_color(0, 220, 255)
        self.set_xy(10, 4)
        self.cell(100, 7, "AI EXAM GUARD -- CONFIDENTIAL", align="L")
        self.set_text_color(150, 150, 150)
        self.set_xy(110, 4)
        self.cell(90, 7, datetime.now().strftime("%d %b %Y  %H:%M"), align="R")
        self.ln(8)

    def footer(self):
        self.set_y(-15)
        self.set_fill_color(15, 23, 42)
        self.rect(0, self.get_y(), 210, 20, 'F')
        self.set_font("Helvetica", "", 8)
        self.set_text_color(100, 100, 100)
        self.cell(0, 10, f"Page {self.page_no()} | AI-generated -- for human review only", align="C")

    def cover_page(self, title: str, subtitle: str, video_name: str):
        self.add_page()
        # Dark background block
        self.set_fill_color(15, 23, 42)
        self.rect(0, 0, 210, 297, 'F')
        # Accent line
        self.set_fill_color(0, 220, 255)
        self.rect(20, 80, 170, 2, 'F')
        # Title
        self.set_font("Helvetica", "B", 28)
        self.set_text_color(0, 220, 255)
        self.set_xy(20, 88)
        self.cell(170, 15, "AI EXAM GUARD", align="C", ln=True)
        self.set_font("Helvetica", "", 14)
        self.set_text_color(200, 200, 220)
        self.set_xy(20, 106)
        self.cell(170, 10, _clean_str(title), align="C", ln=True)
        # Video name box
        self.set_fill_color(30, 41, 59)
        self.set_xy(40, 130)
        self.cell(130, 12, _clean_str(f"  Video: {video_name}"), fill=True, align="L", border=0)
        # Date
        self.set_text_color(100, 120, 140)
        self.set_font("Helvetica", "", 10)
        self.set_xy(40, 148)
        self.cell(130, 8, f"Analysis Date: {datetime.now().strftime('%d %B %Y, %H:%M')}", align="C")
        # Disclaimer
        self.set_fill_color(20, 30, 50)
        self.set_xy(20, 250)
        self.set_font("Helvetica", "I", 8)
        self.set_text_color(100, 100, 120)
        self.multi_cell(170, 5, "IMPORTANT: AI-generated results indicate detected or suspicious activity and are intended to assist human review. The system does not independently establish academic misconduct.", align="C")

    def section_title(self, text: str):
        self.ln(4)
        self.set_fill_color(0, 80, 120)
        self.set_text_color(255, 255, 255)
        self.set_font("Helvetica", "B", 11)
        self.cell(0, 8, _clean_str(f"  {text}"), fill=True, ln=True)
        self.set_text_color(30, 30, 30)
        self.ln(2)

    def kv_row(self, key: str, val: str):
        self.set_font("Helvetica", "B", 9)
        self.set_text_color(60, 80, 100)
        self.cell(55, 6, _clean_str(key), ln=False)
        self.set_font("Helvetica", "", 9)
        self.set_text_color(20, 20, 20)
        self.cell(0, 6, _clean_str(val), ln=True)

    def embed_image(self, path: Path, w: float = 160, caption: str = ""):
        if path.exists():
            x = (210 - w) / 2
            self.image(str(path), x=x, w=w)
            if caption:
                self.set_font("Helvetica", "I", 8)
                self.set_text_color(100, 100, 100)
                self.cell(0, 5, _clean_str(caption), align="C", ln=True)
        else:
            self.set_font("Helvetica", "I", 9)
            self.set_text_color(180, 50, 50)
            self.cell(0, 6, _clean_str(f"[Image not available: {path.name}]"), ln=True)
        self.ln(2)


def generate_complete_report() -> Path:
    """Generate a complete analysis PDF report."""
    zones   = _read_json(ZONES_DIR / "zone_map.json") or []
    events  = _read_json(OUTPUTS / "timeline.json") or []
    scores  = _compute_scores(zones, events)

    video_name = "test2.mp4"
    try:
        import yaml
        with open(BASE_DIR / "config" / "config.yaml") as f:
            cfg = yaml.safe_load(f)
        video_name = Path(cfg["video"]["input_path"]).name
    except Exception:
        pass

    high_risk = sum(1 for v in scores.values() if v["risk"] == "HIGH")
    total_ev  = len(events)

    pdf = ExamGuardPDF()
    pdf.set_auto_page_break(auto=True, margin=20)

    # Cover
    pdf.cover_page("Complete Analysis Report", "Examination Monitoring", video_name)

    # Executive Summary
    pdf.add_page()
    pdf.section_title("Executive Summary")
    pdf.kv_row("Video File:", video_name)
    pdf.kv_row("Analysis Date:", datetime.now().strftime("%d %B %Y, %H:%M"))
    pdf.kv_row("Students Analyzed:", str(len(zones)))
    pdf.kv_row("Total Events Detected:", str(total_ev))
    pdf.kv_row("High-Risk Students:", str(high_risk))
    pdf.kv_row("Detected Zones:", str(sum(1 for z in zones if not z.get("is_estimated"))))
    pdf.kv_row("Estimated Zones:", str(sum(1 for z in zones if z.get("is_estimated"))))

    # Student Risk Ranking
    pdf.section_title("Student Risk Ranking")
    pdf.set_font("Helvetica", "B", 9)
    pdf.set_fill_color(30, 50, 80)
    pdf.set_text_color(255, 255, 255)
    for h, w in [("Rank", 18), ("Student", 28), ("Activity %", 32), ("Events", 22), ("Risk", 25), ("Zone", 22)]:
        pdf.cell(w, 7, h, fill=True, align="C")
    pdf.ln()

    sorted_zones = sorted(zones, key=lambda z: -scores.get(z["zone_id"], {}).get("activity_pct", 0))
    for rank, z in enumerate(sorted_zones, 1):
        zid = z["zone_id"]
        sc  = scores.get(zid, {})
        pdf.set_fill_color(240, 245, 255) if rank % 2 == 0 else pdf.set_fill_color(255, 255, 255)
        pdf.set_text_color(20, 20, 20)
        pdf.set_font("Helvetica", "", 9)
        pdf.cell(18, 6, str(rank), align="C")
        pdf.cell(28, 6, z["name"])
        pdf.cell(32, 6, f"{sc.get('activity_pct', 0)}%", align="C")
        pdf.cell(22, 6, str(sc.get("event_count", 0)), align="C")
        risk = sc.get("risk", "NONE")
        colors_map = {"HIGH": (200, 30, 30), "MEDIUM": (200, 120, 0), "LOW": (30, 130, 30), "NONE": (120, 120, 120)}
        r, g, b = colors_map.get(risk, (80,80,80))
        pdf.set_text_color(r, g, b)
        pdf.set_font("Helvetica", "B", 9)
        pdf.cell(25, 6, risk, align="C")
        pdf.set_text_color(20, 20, 20)
        pdf.set_font("Helvetica", "", 9)
        pdf.cell(22, 6, f"Zone {zid}", align="C")
        pdf.ln()

    # Calibration Map
    pdf.section_title("Calibration -- Classroom Zone Map")
    pdf.embed_image(ZONES_DIR / "zone_calibration_preview.jpg",
                    caption="Green solid = DETECTED   |   Orange dashed = ESTIMATED")

    # Heatmap
    pdf.section_title("Student Activity Heatmap")
    pdf.embed_image(OUTPUTS / "heatmap_student.png",
                    caption="Zone colour intensity represents relative suspicion/activity level")

    # Events
    pdf.section_title("Event Summary")
    sorted_events = sorted(events, key=lambda e: -e.get("avg_motion_score", 0))
    max_m = max((e.get("avg_motion_score", 0) for e in sorted_events), default=1e-9)
    for ev in sorted_events:
        motion = ev.get("avg_motion_score", 0)
        susp_pct = round((motion / max(max_m, 1e-9)) * 100)
        zid = ev.get("zone_id")
        zone = next((z for z in zones if z["zone_id"] == zid), {})
        student_name = zone.get("name", f"S{zid}")
        pdf.set_font("Helvetica", "B", 9)
        pdf.set_text_color(30, 30, 80)
        pdf.cell(0, 6, _clean_str(f"Event {ev['event_id']}  --  {student_name} (Zone {zid})"), ln=True)
        pdf.kv_row("  Time:", f"{_fmt_time(ev.get('start_timestamp',0))} -> {_fmt_time(ev.get('end_timestamp',0))}")
        pdf.kv_row("  Duration:", f"{ev.get('duration_seconds',0):.2f}s")
        pdf.kv_row("  Avg Motion:", f"{motion:.5f}")
        pdf.kv_row("  Suspicion:", f"{susp_pct}%")
        pdf.ln(2)

    # Per-student detail
    for z in sorted_zones:
        zid = z["zone_id"]
        sc  = scores.get(zid, {})
        z_events = [e for e in events if e.get("zone_id") == zid]
        pdf.add_page()
        pdf.section_title(f"Student {z['name']} -- Zone {zid}")
        pdf.kv_row("Student ID:", z["name"])
        pdf.kv_row("Zone ID:", str(zid))
        pdf.kv_row("Activity Score:", f"{sc.get('activity_pct', 0)}%")
        pdf.kv_row("Risk Level:", sc.get("risk", "NONE"))
        pdf.kv_row("Events:", str(sc.get("event_count", 0)))
        pdf.kv_row("Calibration Status:", "ESTIMATED" if z.get("is_estimated") else "DETECTED")
        if z_events:
            pdf.section_title("  Evidence Events")
            for ev in z_events:
                motion = ev.get("avg_motion_score", 0)
                susp_pct = round((motion / max(max_m, 1e-9)) * 100)
                pdf.set_font("Helvetica", "B", 9)
                pdf.cell(0, 6, f"Event {ev['event_id']}", ln=True)
                pdf.kv_row("    Time:", f"{_fmt_time(ev.get('start_timestamp',0))} -> {_fmt_time(ev.get('end_timestamp',0))}")
                pdf.kv_row("    Duration:", f"{ev.get('duration_seconds',0):.2f}s")
                pdf.kv_row("    Avg Motion:", f"{motion:.5f}  |  Suspicion: {susp_pct}%")
                pdf.set_font("Helvetica", "I", 8)
                pdf.set_text_color(60, 60, 80)
                pdf.multi_cell(0, 5, _clean_str(
                    f"    AI Note: {z['name']} showed elevated movement in zone {zid} during "
                    f"{_fmt_time(ev.get('start_timestamp',0))} to {_fmt_time(ev.get('end_timestamp',0))}. "
                    f"Motion score: {motion:.5f}. Suspicious activity detected -- manual review recommended."))
                pdf.set_text_color(20, 20, 20)
                pdf.ln(2)
        else:
            pdf.set_font("Helvetica", "I", 9)
            pdf.set_text_color(100, 100, 100)
            pdf.cell(0, 6, f"No suspicious events detected for {z['name']}.", ln=True)

    # Disclaimer
    pdf.add_page()
    pdf.section_title("Important Disclaimer")
    pdf.set_font("Helvetica", "", 10)
    pdf.set_text_color(40, 40, 40)
    pdf.multi_cell(0, 6,
        "AI-generated results indicate detected or suspicious activity and are intended to assist human review. "
        "The system does not independently establish academic misconduct.\n\n"
        "All findings in this report are based on automated motion analysis and object detection. "
        "Human review by qualified personnel is required before any action is taken based on these results.\n\n"
        "Motion scores and suspicion levels are relative measurements within this specific video analysis "
        "and should not be interpreted as absolute indicators of dishonest behavior.")

    out_path = PDF_OUT / "ExamGuard_Complete_Report.pdf"
    pdf.output(str(out_path))
    return out_path


def generate_student_report(zone_id: int) -> Path:
    """Generate a per-student PDF report."""
    zones   = _read_json(ZONES_DIR / "zone_map.json") or []
    events  = _read_json(OUTPUTS / "timeline.json") or []
    scores  = _compute_scores(zones, events)

    zone = next((z for z in zones if z["zone_id"] == zone_id), None)
    if not zone:
        raise ValueError(f"Zone {zone_id} not found")

    sc = scores.get(zone_id, {})
    z_events = [e for e in events if e.get("zone_id") == zone_id]
    max_m = max((e.get("avg_motion_score", 0) for e in events), default=1e-9)

    video_name = "test2.mp4"
    try:
        import yaml
        with open(BASE_DIR / "config" / "config.yaml") as f:
            cfg = yaml.safe_load(f)
        video_name = Path(cfg["video"]["input_path"]).name
    except Exception:
        pass

    pdf = ExamGuardPDF()
    pdf.set_auto_page_break(auto=True, margin=20)
    pdf.cover_page(f"Student Report -- {zone['name']}", "Individual Investigation", video_name)

    pdf.add_page()
    pdf.section_title(f"Student Information -- {zone['name']}")
    pdf.kv_row("Student ID:", zone["name"])
    pdf.kv_row("Zone ID:", str(zone_id))
    pdf.kv_row("Video File:", video_name)
    pdf.kv_row("Risk Level:", sc.get("risk", "NONE"))
    pdf.kv_row("Activity Score:", f"{sc.get('activity_pct', 0)}%")
    pdf.kv_row("Events Detected:", str(sc.get("event_count", 0)))
    pdf.kv_row("Calibration Status:", "ESTIMATED" if zone.get("is_estimated") else "DETECTED")
    pdf.kv_row("Zone Center:", f"({zone['center'][0]}, {zone['center'][1]})")

    # Calibration preview
    pdf.section_title("Zone Location -- Classroom Map")
    pdf.embed_image(ZONES_DIR / "zone_calibration_preview.jpg",
                    caption=f"Student {zone['name']} location in examination hall")

    # Events
    if z_events:
        pdf.section_title("Detected Events")
        for i, ev in enumerate(z_events, 1):
            motion = ev.get("avg_motion_score", 0)
            susp_pct = round((motion / max(max_m, 1e-9)) * 100)
            pdf.set_font("Helvetica", "B", 10)
            pdf.set_text_color(30, 30, 80)
            pdf.cell(0, 7, f"Event #{i}  --  {ev['event_id']}", ln=True)
            pdf.kv_row("Timestamp:", f"{_fmt_time(ev.get('start_timestamp',0))} -> {_fmt_time(ev.get('end_timestamp',0))}")
            pdf.kv_row("Duration:", f"{ev.get('duration_seconds',0):.2f} seconds")
            pdf.kv_row("Motion Score:", f"{motion:.5f}")
            pdf.kv_row("Suspicion Level:", f"{susp_pct}%")
            # AI explanation
            pdf.ln(2)
            pdf.set_fill_color(240, 248, 255)
            pdf.set_font("Helvetica", "B", 9)
            pdf.set_text_color(0, 80, 140)
            pdf.cell(0, 6, "AI Observed Behavior:", ln=True, fill=True)
            pdf.set_font("Helvetica", "", 9)
            pdf.set_text_color(30, 30, 30)
            pdf.multi_cell(0, 5, _clean_str(
                f"  - Elevated movement activity detected within the calibrated examination zone.\n"
                f"  - Motion score {'significantly' if motion > 0.015 else 'moderately' if motion > 0.005 else 'slightly'} "
                f"exceeded the zone baseline threshold.\n"
                f"  - Activity persisted for {ev.get('duration_seconds',0):.2f} seconds.\n\n"
                f"  Assessment: {'HIGH ACTIVITY -- MANUAL REVIEW RECOMMENDED' if susp_pct >= 70 else 'MODERATE ACTIVITY -- REVIEW SUGGESTED' if susp_pct >= 35 else 'LOW ACTIVITY -- FOR RECORD'}\n\n"
                f"  Note: Suspicious activity detected -- manual review recommended. "
                f"This system does not confirm academic misconduct."))
            pdf.ln(3)
    else:
        pdf.section_title("Events")
        pdf.set_font("Helvetica", "I", 10)
        pdf.set_text_color(80, 80, 80)
        pdf.cell(0, 8, f"No suspicious events detected for {zone['name']}.", ln=True)

    # Disclaimer
    pdf.ln(4)
    pdf.set_font("Helvetica", "I", 8)
    pdf.set_text_color(120, 120, 120)
    pdf.multi_cell(0, 5,
        "DISCLAIMER: AI-generated results indicate detected or suspicious activity and are intended to assist human review. "
        "The system does not independently establish academic misconduct.")

    out_path = PDF_OUT / f"ExamGuard_Student_S{zone_id}.pdf"
    pdf.output(str(out_path))
    return out_path


def generate_capsule_report(incident_id: str) -> Path:
    """Generates an official Evidence Capsule Forensic PDF Report."""
    from db.forensic_db import ForensicDatabase
    db = ForensicDatabase(str(BASE_DIR / "outputs" / "forensic.db"))
    capsule = db.get_capsule_by_incident(incident_id)
    if not capsule:
        inc = db.get_incident_by_id(incident_id)
        if not inc:
            raise ValueError(f"Incident {incident_id} not found")
        capsule = inc

    pdf = ExamGuardPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()

    pdf.section_title(f"FORENSIC EVIDENCE CAPSULE: {incident_id}")

    # Header stats table
    pdf.set_font("Helvetica", "B", 10)
    pdf.set_fill_color(30, 41, 59)
    pdf.set_text_color(255, 255, 255)
    pdf.cell(45, 8, "Incident ID", border=1, fill=True)
    pdf.cell(45, 8, "Risk Level & Score", border=1, fill=True)
    pdf.cell(50, 8, "Seating Desk / Location", border=1, fill=True)
    pdf.cell(50, 8, "Time Interval", border=1, fill=True)
    pdf.ln()

    pdf.set_font("Helvetica", "", 10)
    pdf.set_text_color(30, 41, 59)
    pdf.set_fill_color(248, 250, 252)
    score_str = f"{capsule.get('risk_level', 'HIGH')} ({capsule.get('risk_score', 0)}/100)"
    loc_str = _clean_str(capsule.get('location_desc', 'Unknown'))
    t_start = capsule.get('time_start', capsule.get('start_timestamp', 0))
    t_end = capsule.get('time_end', capsule.get('end_timestamp', 0))
    time_str = f"{t_start:.2f}s -> {t_end:.2f}s"

    pdf.cell(45, 8, _clean_str(incident_id), border=1, fill=True)
    pdf.cell(45, 8, score_str, border=1, fill=True)
    pdf.cell(50, 8, loc_str, border=1, fill=True)
    pdf.cell(50, 8, time_str, border=1, fill=True)
    pdf.ln(12)

    # Contributing Risk Factors
    pdf.section_title("Contributing Forensic Risk Factors")
    factors = capsule.get("contributing_factors", [])
    breakdown = capsule.get("factor_breakdown", {})
    
    pdf.set_font("Helvetica", "", 9.5)
    for k, v in breakdown.items():
        pdf.cell(80, 6, f"* {_clean_str(k)}:", border=0)
        pdf.set_font("Helvetica", "B", 9.5)
        pdf.cell(30, 6, f"+{v} pts", border=0)
        pdf.set_font("Helvetica", "", 9.5)
        pdf.ln()
    pdf.ln(4)

    pdf.section_title("Detailed AI Behavioral Note")
    pdf.set_font("Helvetica", "", 9.5)
    pdf.multi_cell(0, 5.5, _clean_str(capsule.get("explanation", capsule.get("explanation_text", ""))))
    pdf.ln(6)

    # Add Snapshots if available
    before_p = capsule.get("before_snapshot_path")
    during_p = capsule.get("during_snapshot_path")
    after_p = capsule.get("after_snapshot_path")

    if during_p and os.path.exists(during_p):
        pdf.section_title("Visual Evidence Snapshots (During Incident)")
        try:
            pdf.image(during_p, x=15, w=180)
            pdf.ln(6)
        except Exception:
            pass

    pdf.set_font("Helvetica", "I", 8)
    pdf.set_text_color(120, 120, 120)
    pdf.multi_cell(0, 5,
        "DISCLAIMER: AI-generated results indicate detected or suspicious activity and are intended to assist human review. "
        "The system does not independently establish academic misconduct.")

    out_path = PDF_OUT / f"Drishti_Capsule_{incident_id}.pdf"
    pdf.output(str(out_path))
    return out_path
