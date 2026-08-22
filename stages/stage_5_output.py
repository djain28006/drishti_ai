import os
import cv2
import json
import sqlite3
import numpy as np
import itertools
from typing import Generator, List, Dict, Optional, Tuple, Any
from dataclasses import asdict
from utils.logger import StageLogger
from stages.stage_2a_motion import MotionFrame
from stages.stage_4_event_segmentation import EventRecord
from stages.stage_1_5_zone_calibration import ZoneMap
from incident_fusion.incident_builder import IncidentFusionEngine, IncidentRecord
from evidence.capsule_generator import EvidenceCapsuleGenerator, EvidenceCapsule
from db.forensic_db import ForensicDatabase

logger = StageLogger("STAGE 5")

ZONE_COLOURS = [
    (255, 200,   0),  # cyan-yellow
    (  0, 200, 255),  # orange
    (200,   0, 255),  # magenta
    (  0, 255, 100),  # green
    (255,  80,  80),  # blue
    (80,  255,  80),  # lime
    (80,   80, 255),  # red
    (200, 200,   0),  # teal
]

def _suspicion_colour(score: float) -> tuple:
    score = max(0.0, min(1.0, score))
    if score < 0.4:
        t = score / 0.4
        b = int(255 * (1 - t))
        g = int(200 * t)
        r = 0
    else:
        t = (score - 0.4) / 0.6
        b = 0
        g = int(200 * (1 - t))
        r = int(255 * t)
    return (b, g, r)

def _fmt_ts(s: float) -> str:
    m = int(s // 60)
    sec = s % 60
    return f"{m:02d}:{sec:05.2f}"

def _to_json_serializable(obj):
    if isinstance(obj, (np.floating, np.float32, np.float64, float)):
        return float(obj)
    if isinstance(obj, (np.integer, np.int32, np.int64, int)):
        return int(obj)
    if isinstance(obj, (np.bool_, bool)):
        return bool(obj)
    if isinstance(obj, np.ndarray):
        return [_to_json_serializable(x) for x in obj.tolist()]
    if isinstance(obj, dict):
        return {str(k): _to_json_serializable(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple, set)):
        return [_to_json_serializable(x) for x in obj]
    if hasattr(obj, '__dict__'):
        return _to_json_serializable(obj.__dict__)
    return str(obj)

class EventDatabase:
    def __init__(self, db_path: str):
        self.db_path = db_path
        os.makedirs(os.path.dirname(db_path) or ".", exist_ok=True)
        self.conn = sqlite3.connect(db_path)
        self.create_table()

    def create_table(self):
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS events (
                event_id TEXT PRIMARY KEY,
                track_id INTEGER,
                zone_id INTEGER,
                class_name TEXT,
                start_frame INTEGER,
                end_frame INTEGER,
                start_timestamp REAL,
                end_timestamp REAL,
                duration_seconds REAL,
                avg_motion_score REAL,
                max_confidence REAL,
                clip_path TEXT,
                involved_desks TEXT,
                combined_risk_score INTEGER,
                is_multi_student INTEGER
            )
        """)
        self.conn.commit()

    def insert_events(self, events: List[EventRecord]):
        for e in events:
            desks_json = json.dumps(_to_json_serializable(getattr(e, 'involved_desks', [])), default=_to_json_serializable)
            self.conn.execute("""
                INSERT OR REPLACE INTO events VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
            """, (
                str(e.event_id), int(e.track_id) if e.track_id is not None else None,
                int(e.zone_id) if e.zone_id is not None else None, str(e.class_name),
                int(e.start_frame), int(e.end_frame), float(e.start_timestamp), float(e.end_timestamp),
                float(e.duration_seconds), float(e.avg_motion_score), float(e.max_confidence),
                str(e.clip_path), desks_json, int(getattr(e, 'combined_risk_score', 0)),
                1 if getattr(e, 'is_multi_student', False) else 0
            ))
        self.conn.commit()

    def close(self):
        self.conn.close()

def _generate_raw_motion_heatmap(
    raw_acc: np.ndarray,
    out_path: str,
    colormap: int
) -> float:
    os.makedirs(os.path.dirname(out_path) or ".", exist_ok=True)
    norm = cv2.normalize(raw_acc, None, 0, 255, cv2.NORM_MINMAX)
    u8 = norm.astype(np.uint8)
    colored = cv2.applyColorMap(u8, colormap)
    cv2.imwrite(out_path, colored)
    return float(np.var(raw_acc))

def _draw_dashed_rect_canvas(canvas, x1, y1, x2, y2, color, thickness=2, dash_len=8):
    pts = [(x1,y1),(x2,y1),(x2,y2),(x1,y2),(x1,y1)]
    for i in range(len(pts)-1):
        p1, p2 = pts[i], pts[i+1]
        dx = p2[0]-p1[0]; dy = p2[1]-p1[1]
        dist = max(1, int(np.sqrt(dx*dx+dy*dy)))
        for d in range(0, dist, dash_len*2):
            t0 = d/dist; t1 = min((d+dash_len)/dist, 1.0)
            s = (int(p1[0]+t0*dx), int(p1[1]+t0*dy))
            e = (int(p1[0]+t1*dx), int(p1[1]+t1*dy))
            cv2.line(canvas, s, e, color, thickness)

def _generate_student_activity_heatmap(
    zone_map: ZoneMap,
    zone_activity: Dict[int, List[float]],
    out_path: str,
    annotated_out_path: str,
    events: List[EventRecord]
):
    os.makedirs(os.path.dirname(out_path) or ".", exist_ok=True)
    h, w = zone_map.frame_shape

    ref_path = getattr(zone_map, 'reference_frame_path', None)
    if ref_path and os.path.exists(ref_path):
        canvas = cv2.imread(ref_path)
    else:
        canvas = np.zeros((h, w, 3), dtype=np.uint8)

    overlay = canvas.copy()

    mean_scores: Dict[int, float] = {}
    events_per_zone: Dict[int, int] = {}
    for ev in events:
        if ev.zone_id is not None:
            events_per_zone[ev.zone_id] = events_per_zone.get(ev.zone_id, 0) + 1

    for z in zone_map.zones:
        scores = zone_activity.get(z.zone_id, [])
        mean_scores[z.zone_id] = float(np.mean(scores)) if scores else 0.0

    detected_scores = [mean_scores[z.zone_id] for z in zone_map.zones if not z.is_estimated]
    max_score = max(detected_scores) if detected_scores and max(detected_scores) > 1e-6 else 1.0

    for z in zone_map.zones:
        pts = np.array(z.polygon, dtype=np.int32).reshape((-1, 1, 2))
        score = mean_scores[z.zone_id]
        norm_score = score / max_score if not z.is_estimated else 0.0

        if not z.is_estimated:
            fill_colour = _suspicion_colour(norm_score)
            cv2.fillPoly(overlay, [pts], fill_colour)

    cv2.addWeighted(overlay, 0.40, canvas, 0.60, 0, canvas)

    for z in zone_map.zones:
        pts = np.array(z.polygon, dtype=np.int32).reshape((-1, 1, 2))
        score = mean_scores[z.zone_id]
        norm_score = score / max_score if not z.is_estimated else 0.0

        x1, y1 = z.polygon[0]
        x2, y2 = z.polygon[2]
        cx, cy = z.center[0], z.center[1]

        if z.is_estimated:
            border_colour = (0, 165, 255)
            _draw_dashed_rect_canvas(canvas, x1, y1, x2, y2, border_colour, thickness=2)
        else:
            border_colour = _suspicion_colour(norm_score)
            cv2.polylines(canvas, [pts], isClosed=True, color=border_colour, thickness=2)

        for dx, dy in [(-1,-1),(1,1),(-1,1),(1,-1)]:
            cv2.putText(canvas, z.name, (cx+dx-10, cy+dy-14),
                        cv2.FONT_HERSHEY_DUPLEX, 0.65, (0,0,0), 2)
        cv2.putText(canvas, z.name, (cx-10, cy-14),
                    cv2.FONT_HERSHEY_DUPLEX, 0.65, border_colour, 2)

        status = "EST" if z.is_estimated else "DET"
        pct = int(norm_score * 100) if not z.is_estimated else 0
        n_ev = events_per_zone.get(z.zone_id, 0)
        sub = f"{status} | {pct}% | {n_ev}ev"
        cv2.putText(canvas, sub, (cx-34, cy+12),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.38, (255,255,255), 1)

    cv2.rectangle(canvas, (0,0), (w, 46), (10,10,10), -1)
    det_n = sum(1 for z in zone_map.zones if not z.is_estimated)
    est_n = sum(1 for z in zone_map.zones if z.is_estimated)
    cv2.putText(canvas,
        f"STUDENT ACTIVITY HEATMAP  |  DET:{det_n} (solid)  EST:{est_n} (dashed-orange)  |  intensity=suspicion",
        (8, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.50, (0, 220, 255), 1)

    legend_w = 280; lx, ly = 8, h - 30
    for xi in range(legend_w):
        cv2.rectangle(canvas, (lx+xi, ly), (lx+xi+1, ly+18), _suspicion_colour(xi/legend_w), -1)
    cv2.putText(canvas, "LOW", (lx, ly-4), cv2.FONT_HERSHEY_SIMPLEX, 0.36, (200,200,200), 1)
    cv2.putText(canvas, "HIGH", (lx+legend_w-34, ly-4), cv2.FONT_HERSHEY_SIMPLEX, 0.36, (200,200,200), 1)

    cv2.imwrite(out_path, canvas)
    cv2.imwrite(annotated_out_path, canvas)
    logger.info(f"Saved student-activity heatmap to: {out_path}")
    logger.info(f"Saved annotated surveillance frame to: {annotated_out_path}")

def output_stage(
    motion_stream: Generator[MotionFrame, None, None],
    fused_stream,
    event_stream: Generator[List[EventRecord], None, None],
    zone_map: ZoneMap,
    config_dict: dict,
    video_path: str = "test2.mp4"
):
    logger.info("Started Output Generation & Forensic Synthesis Stage (Stage 5)")

    heatmap_cfg = config_dict.get('heatmap', {})
    alpha = heatmap_cfg.get('alpha', 0.02)
    raw_heatmap_out = heatmap_cfg.get('output_path', 'outputs/heatmap_raw.png')
    student_heatmap_out = heatmap_cfg.get('student_heatmap_path', 'outputs/heatmap_student.png')
    annotated_out = heatmap_cfg.get('annotated_frame_path', 'outputs/annotated_frame.png')
    colormap_str = heatmap_cfg.get('colormap', 'COLORMAP_JET')
    colormap = getattr(cv2, colormap_str, cv2.COLORMAP_JET)

    output_cfg = config_dict.get('output', {})
    json_path = output_cfg.get('timeline_json_path', 'outputs/timeline.json')
    db_path = output_cfg.get('sqlite_db_path', 'outputs/events.db')
    forensic_db_path = output_cfg.get('forensic_db_path', 'outputs/forensic.db')
    camera_id = config_dict.get('video', {}).get('camera_id', 'CAM-01')

    db = EventDatabase(db_path)
    forensic_db = ForensicDatabase(forensic_db_path)
    fusion_engine = IncidentFusionEngine(config_dict)
    capsule_gen = EvidenceCapsuleGenerator("outputs/capsules")

    raw_accumulator = None
    zone_activity: Dict[int, List[float]] = {z.zone_id: [] for z in zone_map.zones}
    all_events: List[EventRecord] = []

    frames_processed = 0

    try:
        for m_frame, f_frame, events in itertools.zip_longest(
            motion_stream, fused_stream, event_stream, fillvalue=None
        ):
            if events:
                all_events.extend(events)
                db.insert_events(events)

            if m_frame is not None and m_frame.motion_mask is not None:
                mask = m_frame.motion_mask
                if raw_accumulator is None:
                    raw_accumulator = np.zeros(mask.shape, dtype=np.float32)
                cv2.accumulateWeighted(mask, raw_accumulator, alpha)
                frames_processed += 1

            if f_frame is not None:
                for rec in f_frame.records:
                    if rec.zone_id in zone_activity:
                        zone_activity[rec.zone_id].append(rec.suspicion_score)

    except Exception as e:
        logger.error(f"Exception in Output Stage: {e}")
        raise
    finally:
        logger.info("Output Generation completed.")

    # 1. Raw motion heatmap
    raw_var = 0.0
    if raw_accumulator is not None:
        raw_var = _generate_raw_motion_heatmap(raw_accumulator, raw_heatmap_out, colormap)
        logger.info(f"Saved raw motion heatmap to {raw_heatmap_out} (Variance: {raw_var:.2f})")

    # 2. Student-activity heatmap
    _generate_student_activity_heatmap(
        zone_map, zone_activity, student_heatmap_out, annotated_out, all_events
    )

    # 3. Timeline JSON
    os.makedirs(os.path.dirname(json_path) or ".", exist_ok=True)
    timeline_records = []
    for e in all_events:
        d = _to_json_serializable(asdict(e))
        d["start_time"] = _fmt_ts(float(e.start_timestamp))
        d["end_time"] = _fmt_ts(float(e.end_timestamp))
        timeline_records.append(d)
        
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(timeline_records, f, indent=2, default=_to_json_serializable)
    logger.info(f"Saved timeline to {json_path} (Total Events: {len(all_events)})")

    # 4. Incident Fusion & Evidence Capsule Generation
    zone_lookup = {z.zone_id: z for z in zone_map.zones}
    event_dicts = [_to_json_serializable(asdict(e)) for e in all_events]
    incidents = fusion_engine.fuse_events_into_incidents(
        event_dicts, camera_id=camera_id, zone_lookup=zone_lookup
    )

    logger.info(f"Fused {len(all_events)} events into {len(incidents)} prioritized Incidents.")

    # Generate Evidence Capsules & Save to Forensic DB
    for inc in incidents:
        forensic_db.insert_incident(inc)
        z_poly = zone_lookup[inc.zone_ids[0]].polygon if (inc.zone_ids and inc.zone_ids[0] in zone_lookup) else None
        capsule = capsule_gen.generate_capsule(
            inc, video_path=video_path, roi_polygon=z_poly, heatmap_path=student_heatmap_out
        )
        forensic_db.insert_capsule(capsule)

    # Save incidents.json
    incidents_json_path = "outputs/incidents.json"
    with open(incidents_json_path, 'w', encoding='utf-8') as f:
        json.dump([_to_json_serializable(asdict(inc)) for inc in incidents], f, indent=2, default=_to_json_serializable)
    logger.info(f"Saved {len(incidents)} fused incidents to {incidents_json_path}")

    forensic_db.log_audit("PIPELINE_COMPLETE", f"Processed {len(all_events)} events into {len(incidents)} incidents.")

    return raw_var, all_events, incidents
