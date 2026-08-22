import os
import cv2
import numpy as np
import subprocess
import uuid
from typing import Generator, List, Dict, Optional, Any
from dataclasses import dataclass, field, asdict
from utils.logger import StageLogger
from stages.stage_3_tracking_fusion import FusedTrackFrame

logger = StageLogger("STAGE 4")

# Approved cheating / suspicious classes (NEVER includes person/student)
SUSPICIOUS_CLASSES = {"phone", "chit", "peeking", "supplement-passing", "hand"}

@dataclass
class InvolvedDeskRecord:
    zone_id: int
    track_id: int
    student_name: str
    location_desc: str
    activity: str
    risk_score: int
    confidence: float
    avg_motion_score: float
    zone_poly: Optional[List[List[int]]] = None

@dataclass
class EventRecord:
    event_id: str
    track_id: int
    zone_id: Optional[int]
    class_name: str
    start_frame: int
    end_frame: int
    start_timestamp: float
    end_timestamp: float
    duration_seconds: float
    avg_motion_score: float
    max_confidence: float
    clip_path: str
    is_room_wide: bool = False
    involved_desks: List[Dict[str, Any]] = field(default_factory=list)
    combined_risk_score: int = 0
    combined_risk_level: str = "LOW"
    is_multi_student: bool = False

class EventStateMachine:
    def __init__(self, track_id: int, zone_id: Optional[int], class_name: str, config: dict):
        self.track_id = track_id
        self.zone_id = zone_id
        self.class_name = class_name
        self.config = config
        
        self.start_threshold = config.get('start_threshold', 0.0015)
        self.start_n_frames = config.get('start_n_frames', 2)
        self.end_threshold = config.get('end_threshold', 0.0004)
        self.end_m_frames = config.get('end_m_frames', 8)
        
        self.state = "idle"
        self.consecutive_above = 0
        self.consecutive_below = 0
        
        self.start_frame = None
        self.start_timestamp = None
        self.last_frame = None
        self.last_timestamp = None
        self.motion_scores = []
        self.max_confidence = 0.0
        
    def update(
        self,
        frame_no: int,
        timestamp: float,
        motion_score: float,
        confidence: float,
        suspicion_score: float = 0.0,
        is_anomalous: bool = False,
        active_class: str = ""
    ) -> Optional[EventRecord]:
        self.last_frame = frame_no
        self.last_timestamp = timestamp
        
        clean_class = active_class.lower().strip() if active_class else ""
        if clean_class in SUSPICIOUS_CLASSES:
            self.class_name = clean_class
        
        # EXPLICIT RULE: person / student detections alone CANNOT trigger an event.
        # Only explicit suspicious classes, boundary crossing, or significant anomaly deviation trigger an event.
        has_suspicious_object = clean_class in SUSPICIOUS_CLASSES
        has_anomaly_signal = is_anomalous or suspicion_score >= 0.40
        
        has_trigger = has_suspicious_object or has_anomaly_signal

        if self.state == "idle":
            if has_trigger:
                self.consecutive_above += 1
                if self.consecutive_above >= self.start_n_frames:
                    self.state = "event_active"
                    self.start_frame = frame_no
                    self.start_timestamp = timestamp
                    self.motion_scores = [max(motion_score, suspicion_score * 0.01)]
                    self.max_confidence = confidence if confidence > 0 else 0.85
                    self.consecutive_below = 0
            else:
                self.consecutive_above = 0
                
        elif self.state == "event_active":
            self.motion_scores.append(max(motion_score, suspicion_score * 0.01))
            if confidence > self.max_confidence:
                self.max_confidence = confidence
            
            if not has_trigger and motion_score < self.end_threshold:
                self.consecutive_below += 1
                if self.consecutive_below >= self.end_m_frames:
                    return self.finalize_event()
            else:
                self.consecutive_below = 0
                
        return None
        
    def finalize_event(self, is_room_wide: bool = False) -> Optional[EventRecord]:
        if self.state == "event_active" and len(self.motion_scores) > 0:
            # ASSERTION: Discard if class is person/student
            if self.class_name.lower() in ("person", "student", ""):
                self.state = "idle"
                self.consecutive_above = 0
                self.consecutive_below = 0
                self.start_frame = None
                self.start_timestamp = None
                self.motion_scores = []
                return None

            avg_motion = sum(self.motion_scores) / len(self.motion_scores)
            duration = max(0.1, self.last_timestamp - self.start_timestamp)
            
            event = EventRecord(
                event_id=str(uuid.uuid4())[:8],
                track_id=self.track_id,
                zone_id=self.zone_id,
                class_name=self.class_name if not is_room_wide else "room_wide_event",
                start_frame=self.start_frame,
                end_frame=self.last_frame,
                start_timestamp=self.start_timestamp,
                end_timestamp=self.last_timestamp,
                duration_seconds=duration,
                avg_motion_score=avg_motion,
                max_confidence=max(0.80, self.max_confidence),
                clip_path="",
                is_room_wide=is_room_wide
            )
            
            self.state = "idle"
            self.consecutive_above = 0
            self.consecutive_below = 0
            self.start_frame = None
            self.start_timestamp = None
            self.motion_scores = []
            
            return event
        return None


def _consolidate_single_zone_events(
    raw_events: List[EventRecord],
    merge_gap_sec: float = 3.5,
    min_dur_sec: float = 1.0,
    cooldown_sec: float = 3.0
) -> List[EventRecord]:
    """Merges contiguous triggers for the same desk into a continuous incident."""
    by_zone: Dict[int, List[EventRecord]] = {}
    for ev in raw_events:
        # Extra assertion: ignore any person/student detections
        if ev.class_name.lower() in ("person", "student"):
            continue
        by_zone.setdefault(ev.zone_id, []).append(ev)
        
    priority = {
        "phone": 5,
        "chit": 4,
        "peeking": 3,
        "supplement-passing": 2,
        "boundary_crossing": 1,
        "suspicious_motion": 0
    }

    consolidated = []
    for zid, ev_list in by_zone.items():
        ev_list.sort(key=lambda e: e.start_timestamp)
        curr = None
        for ev in ev_list:
            if curr is None:
                curr = ev
            else:
                gap = ev.start_timestamp - curr.end_timestamp
                if gap <= merge_gap_sec or gap <= cooldown_sec:
                    curr.end_timestamp = max(curr.end_timestamp, ev.end_timestamp)
                    curr.end_frame = max(curr.end_frame, ev.end_frame)
                    curr.duration_seconds = max(0.1, curr.end_timestamp - curr.start_timestamp)
                    curr.avg_motion_score = max(curr.avg_motion_score, ev.avg_motion_score)
                    curr.max_confidence = max(curr.max_confidence, ev.max_confidence)
                    curr.is_room_wide = curr.is_room_wide or ev.is_room_wide
                    
                    c_curr = curr.class_name.lower()
                    c_new = ev.class_name.lower()
                    if priority.get(c_new, 0) > priority.get(c_curr, 0):
                        curr.class_name = ev.class_name
                else:
                    if curr.duration_seconds >= min_dur_sec or priority.get(curr.class_name.lower(), 0) >= 2:
                        consolidated.append(curr)
                    curr = ev

        if curr and (curr.duration_seconds >= min_dur_sec or priority.get(curr.class_name.lower(), 0) >= 2):
            consolidated.append(curr)

    consolidated.sort(key=lambda e: e.start_timestamp)
    return consolidated


def _fuse_cross_desk_overlapping_events(
    single_zone_events: List[EventRecord],
    zone_lookup: Dict[int, Any],
    time_overlap_tolerance: float = 3.5
) -> List[EventRecord]:
    """
    Fuses multiple simultaneous or overlapping cheating incidents occurring across DIFFERENT desks
    into a single unified multi-student Incident Record.
    """
    if not single_zone_events:
        return []

    sorted_events = sorted(single_zone_events, key=lambda e: e.start_timestamp)
    fused_incidents: List[EventRecord] = []
    visited = set()

    for i, base_ev in enumerate(sorted_events):
        if base_ev.event_id in visited:
            continue

        # Start cluster with base event
        cluster = [base_ev]
        visited.add(base_ev.event_id)

        cluster_start = base_ev.start_timestamp
        cluster_end = base_ev.end_timestamp
        cluster_start_frame = base_ev.start_frame
        cluster_end_frame = base_ev.end_frame

        # Find all other desks that overlap or trigger within tolerance
        for j in range(i + 1, len(sorted_events)):
            other_ev = sorted_events[j]
            if other_ev.event_id in visited:
                continue

            # Check for temporal overlap or near-coincidence
            overlaps = (
                (other_ev.start_timestamp <= cluster_end + time_overlap_tolerance) and
                (other_ev.end_timestamp >= cluster_start - time_overlap_tolerance)
            )

            if overlaps:
                cluster.append(other_ev)
                visited.add(other_ev.event_id)
                cluster_start = min(cluster_start, other_ev.start_timestamp)
                cluster_end = max(cluster_end, other_ev.end_timestamp)
                cluster_start_frame = min(cluster_start_frame, other_ev.start_frame)
                cluster_end_frame = max(cluster_end_frame, other_ev.end_frame)

        # Build involved desks list
        involved_desks: List[Dict[str, Any]] = []
        priority = {"phone": 5, "chit": 4, "peeking": 3, "supplement-passing": 2, "boundary_crossing": 1, "suspicious_motion": 0}
        
        # Calculate risk scores per involved desk
        desk_risk_scores = []
        for ev in cluster:
            z_spec = zone_lookup.get(ev.zone_id)
            s_name = getattr(z_spec, "name", f"S{ev.zone_id}")
            loc_desc = getattr(z_spec, "location_desc", f"Desk {ev.zone_id}")
            poly = getattr(z_spec, "polygon", None)

            # Base risk score calculation
            base_score = 40
            if "phone" in ev.class_name.lower(): base_score = 75
            elif "chit" in ev.class_name.lower(): base_score = 70
            elif "peeking" in ev.class_name.lower(): base_score = 65
            elif "supplement-passing" in ev.class_name.lower(): base_score = 65
            
            dur_bonus = min(15, int(ev.duration_seconds * 2))
            desk_score = min(100, base_score + dur_bonus)
            desk_risk_scores.append(desk_score)

            involved_desks.append({
                "zone_id": ev.zone_id,
                "track_id": ev.track_id,
                "student_name": s_name,
                "location_desc": loc_desc,
                "activity": ev.class_name,
                "risk_score": desk_score,
                "confidence": ev.max_confidence,
                "avg_motion_score": ev.avg_motion_score,
                "zone_poly": poly
            })

        combined_risk = max(desk_risk_scores) if desk_risk_scores else 50
        combined_level = "CRITICAL" if combined_risk >= 81 else ("HIGH" if combined_risk >= 61 else ("MEDIUM" if combined_risk >= 31 else "LOW"))

        # Determine primary activity summary
        if len(cluster) == 1:
            primary_act = cluster[0].class_name
            is_multi = False
        else:
            acts = list(set(ev.class_name.upper() for ev in cluster))
            primary_act = f"MULTI-DESK ANOMALY ({', '.join(acts)})"
            is_multi = True

        combined_event = EventRecord(
            event_id=cluster[0].event_id,
            track_id=cluster[0].track_id,
            zone_id=cluster[0].zone_id if len(cluster) == 1 else None,
            class_name=primary_act,
            start_frame=cluster_start_frame,
            end_frame=cluster_end_frame,
            start_timestamp=cluster_start,
            end_timestamp=cluster_end,
            duration_seconds=max(0.1, cluster_end - cluster_start),
            avg_motion_score=max(e.avg_motion_score for e in cluster),
            max_confidence=max(e.max_confidence for e in cluster),
            clip_path="",
            is_room_wide=any(e.is_room_wide for e in cluster),
            involved_desks=involved_desks,
            combined_risk_score=combined_risk,
            combined_risk_level=combined_level,
            is_multi_student=is_multi
        )
        fused_incidents.append(combined_event)

    return fused_incidents


def _find_ffmpeg_executable() -> Optional[str]:
    import shutil
    bin_path = shutil.which("ffmpeg")
    if bin_path:
        return bin_path
    try:
        import imageio_ffmpeg
        return imageio_ffmpeg.get_ffmpeg_exe()
    except Exception:
        return None

def cut_unified_annotated_clip(
    source_video: str,
    start_time: float,
    end_time: float,
    event_id: str,
    involved_desks: List[Dict[str, Any]],
    combined_risk_level: str = "HIGH"
) -> str:
    """
    Renders a single unified browser-compatible H.264 MP4 clip that draws bounding polygons
    and activity labels for ALL involved students simultaneously.
    Encodes strictly with H.264 / AVC (libx264), yuv420p pixel format, and +faststart.
    """
    os.makedirs("outputs/events", exist_ok=True)
    out_path = f"outputs/events/event_{event_id}.mp4"
    
    cap = cv2.VideoCapture(source_video)
    if not cap.isOpened():
        return ""
        
    native_fps = cap.get(cv2.CAP_PROP_FPS) or 24.0
    native_w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    native_h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    
    start_frame = max(0, int(start_time * native_fps))
    end_frame = min(total_frames, int(end_time * native_fps) + int(native_fps * 0.5))
    
    cap.set(cv2.CAP_PROP_POS_FRAMES, start_frame)
    
    scale_x = native_w / 640.0
    scale_y = native_h / 480.0
    
    ffmpeg_exe = _find_ffmpeg_executable()
    use_ffmpeg = False
    proc = None
    av_container = None
    av_stream = None

    if ffmpeg_exe:
        cmd = [
            ffmpeg_exe, "-y", "-v", "error",
            "-f", "rawvideo", "-vcodec", "rawvideo",
            "-s", f"{native_w}x{native_h}",
            "-pix_fmt", "bgr24",
            "-r", str(native_fps),
            "-i", "-",
            "-c:v", "libx264",
            "-pix_fmt", "yuv420p",
            "-preset", "ultrafast",
            "-movflags", "+faststart",
            "-crf", "23",
            out_path
        ]
        try:
            proc = subprocess.Popen(cmd, stdin=subprocess.PIPE)
            use_ffmpeg = True
        except Exception as e:
            logger.warning(f"FFmpeg process launch failed: {e}")
            proc = None

    writer = None
    if not use_ffmpeg:
        # Fallback to PyAV for pure H.264 browser-compatible MP4 encoding, or OpenCV VideoWriter
        try:
            import av
            av_container = av.open(out_path, mode='w', format='mp4')
            codec_name = 'libx264' if 'libx264' in av.codecs_available else 'h264'
            av_stream = av_container.add_stream(codec_name, rate=int(round(native_fps)))
            av_stream.width = native_w
            av_stream.height = native_h
            av_stream.pix_fmt = 'yuv420p'
            av_stream.options = {'preset': 'ultrafast', 'movflags': '+faststart'}
        except Exception as e:
            logger.warning(f"PyAV H.264 encoding failed, falling back to cv2.VideoWriter: {e}")
            fourcc = cv2.VideoWriter_fourcc(*'mp4v')
            writer = cv2.VideoWriter(out_path, fourcc, native_fps, (native_w, native_h))

    curr_frame_idx = start_frame
    while curr_frame_idx <= end_frame:
        ret, frame = cap.read()
        if not ret or frame is None:
            break

        # Run YOLO detection on frame during anomaly window for target trained classes only (high confidence)
        try:
            if 'yolo_inst' not in locals():
                from ultralytics import YOLO
                m_path = "best.pt"
                for fallback in ['best.pt', 'models/best.pt', 'yolov8n.pt', 'models/yolov8n.pt']:
                    if os.path.exists(fallback):
                        m_path = fallback
                        break
                yolo_inst = YOLO(m_path)
            
            y_results = yolo_inst(frame, conf=0.40, verbose=False)
            for res in y_results:
                for box in res.boxes:
                    cls_id = int(box.cls[0])
                    c_name = res.names[cls_id].lower().strip()
                    c_conf = float(box.conf[0])
                    
                    # Strictly filter for target proctoring / cheating classes only
                    is_phone = any(p in c_name for p in ("phone", "cell", "mobile", "chit"))
                    is_person = c_name == "person"
                    is_target = is_phone or is_person or c_name in ("book", "laptop", "paper")
                    if not is_target:
                        continue

                    b = box.xyxy[0].cpu().numpy().astype(int)
                    x1, y1, x2, y2 = b[0], b[1], b[2], b[3]

                    b_color = (0, 0, 255) if is_phone else ((0, 255, 0) if is_person else (0, 210, 255))
                    lbl = f"ANOMALY DETECTED: CELL PHONE {int(c_conf*100)}%" if is_phone else f"{c_name.upper()} {int(c_conf*100)}%"

                    cv2.rectangle(frame, (x1, y1), (x2, y2), b_color, 3)
                    (tw, th), _ = cv2.getTextSize(lbl, cv2.FONT_HERSHEY_SIMPLEX, 0.55, 2)
                    ly = max(y1, th + 8)
                    cv2.rectangle(frame, (x1, ly - th - 6), (x1 + tw + 8, ly + 4), b_color, -1)
                    cv2.putText(frame, lbl, (x1 + 4, ly - 2), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (255, 255, 255), 2)
        except Exception:
            pass

        # Draw overlays for ALL involved desks simultaneously during the anomaly window
        for desk in involved_desks:
            poly = desk.get("zone_poly")
            s_name = desk.get("student_name", f"S{desk.get('zone_id')}")
            activity = desk.get("activity", "ANOMALY").upper()
            
            tag_color = (0, 0, 255) if any(k in activity.lower() for k in ("phone", "chit", "peeking", "suspicious")) else (0, 165, 255)
            
            if poly:
                scaled_pts = np.array([[int(p[0] * scale_x), int(p[1] * scale_y)] for p in poly], dtype=np.int32)
                cx = int(np.mean(scaled_pts[:, 0]))
                cy = int(np.min(scaled_pts[:, 1]))

                # Semi-transparent fill + border
                overlay = frame.copy()
                cv2.fillPoly(overlay, [scaled_pts], tag_color)
                cv2.addWeighted(overlay, 0.35, frame, 0.65, 0, frame)
                cv2.polylines(frame, [scaled_pts], isClosed=True, color=tag_color, thickness=3)

                # Floating Anomaly Alert Badge above student
                badge_text = f"⚠️ ANOMALY DETECTED: {s_name} | {activity}"
                (tw, th), _ = cv2.getTextSize(badge_text, cv2.FONT_HERSHEY_DUPLEX, 0.60, 2)
                bx = max(10, cx - tw // 2)
                by = max(th + 10, cy - 12)
                cv2.rectangle(frame, (bx - 6, by - th - 6), (bx + tw + 6, by + 6), (15, 23, 42), -1)
                cv2.rectangle(frame, (bx - 6, by - th - 6), (bx + tw + 6, by + 6), tag_color, 2)
                cv2.putText(frame, badge_text, (bx, by), cv2.FONT_HERSHEY_DUPLEX, 0.60, (255, 255, 255), 2)

        # Draw Top HUD Banner
        cv2.rectangle(frame, (0, 0), (native_w, 48), (15, 23, 42), -1)
        top_bar_color = (0, 0, 255) if combined_risk_level in ("HIGH", "CRITICAL") else (0, 210, 255)
        cv2.rectangle(frame, (0, 46), (native_w, 48), top_bar_color, -1)
        
        if len(involved_desks) > 1:
            desk_summaries = ", ".join(f"{d['student_name']}: {d['activity'].upper()}" for d in involved_desks[:3])
            hud_left = f"AI MULTI-STUDENT INCIDENT: {len(involved_desks)} DESKS ({desk_summaries})"
        else:
            d0 = involved_desks[0] if involved_desks else {}
            hud_left = f"AI ANOMALY DETECTED: {d0.get('student_name', 'Student')} -- {d0.get('activity', 'ANOMALY').upper()}"

        cv2.putText(frame, hud_left, (16, 32), cv2.FONT_HERSHEY_DUPLEX, 0.60, (0, 220, 255), 2)
        
        hud_right = f"Time: {start_time:.2f}s - {end_time:.2f}s | {combined_risk_level} RISK"
        (rw, _), _ = cv2.getTextSize(hud_right, cv2.FONT_HERSHEY_SIMPLEX, 0.55, 1)
        cv2.putText(frame, hud_right, (native_w - rw - 16, 32), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (220, 220, 220), 1)

        try:
            if use_ffmpeg and proc and proc.stdin:
                proc.stdin.write(frame.tobytes())
            elif av_container and av_stream:
                import av
                av_frame = av.VideoFrame.from_ndarray(frame, format='bgr24')
                for packet in av_stream.encode(av_frame):
                    av_container.mux(packet)
            elif writer is not None:
                writer.write(frame)
        except Exception:
            break
        curr_frame_idx += 1

    cap.release()
    if use_ffmpeg and proc:
        try:
            proc.stdin.close()
            proc.wait()
        except Exception:
            pass
    elif av_container:
        try:
            for packet in av_stream.encode():
                av_container.mux(packet)
            av_container.close()
        except Exception:
            pass
    elif writer is not None:
        writer.release()
        
    return out_path if os.path.exists(out_path) else ""


def event_segmentation_stage(
    fused_stream: Generator[FusedTrackFrame, None, None],
    source_video: str,
    config_dict: dict,
    debug_cfg: dict = None,
    zone_map: Any = None
) -> Generator[List[EventRecord], None, None]:
    
    logger.info("Started Stage 4 Event Segmentation with Multi-Student Coalescing")
    state_machines: Dict[str, EventStateMachine] = {}
    room_wide_thresh_pct = config_dict.get('room_wide_threshold_percent', 40.0)
    merge_gap_sec = config_dict.get('merge_gap_seconds', 3.5)
    min_dur_sec = config_dict.get('min_duration_seconds', 1.0)
    cooldown_sec = config_dict.get('cooldown_seconds', 3.0)
    frames_processed = 0
    raw_events: List[EventRecord] = []
    
    zone_lookup = {z.zone_id: z for z in (zone_map.zones if zone_map else [])}

    try:
        for f_frame in fused_stream:
            frames_processed += 1
            
            elevated_count = sum(
                1 for r in f_frame.records 
                if (any(o.lower() in SUSPICIOUS_CLASSES for o in r.detected_objects) or 
                    r.boundary_crossing or 
                    r.suspicion_score > 0.40)
            )
            total_seats = len(f_frame.records) if f_frame.records else 1
            room_wide = (elevated_count / float(total_seats)) >= (room_wide_thresh_pct / 100.0)

            if room_wide:
                logger.info(f"*** ROOM-WIDE EVENT DETECTED *** [Frame {f_frame.frame_no}] ({elevated_count}/{total_seats} zones elevated)")

            for r in f_frame.records:
                tid = r.track_id
                zid = r.zone_id
                
                # Check for suspicious objects only
                susp_objs = [o for o in r.detected_objects if o.lower() in SUSPICIOUS_CLASSES]
                cname = susp_objs[0] if susp_objs else ""
                
                m_score = r.motion_score
                conf = r.confidence
                susp_score = r.suspicion_score
                is_anom = r.boundary_crossing
                
                # If only person is detected and no boundary crossing / high anomaly, do not trigger
                if not susp_objs and not is_anom and susp_score < 0.40:
                    continue
                
                if not cname and (is_anom or susp_score >= 0.40):
                    cname = "suspicious_motion"
                
                key = f"{tid}_{zid}"
                if key not in state_machines:
                    state_machines[key] = EventStateMachine(tid, zid, cname, config_dict)
                    
                sm = state_machines[key]
                event = sm.update(
                    f_frame.frame_no, f_frame.timestamp, m_score, conf,
                    suspicion_score=susp_score, is_anomalous=is_anom, active_class=cname
                )
                
                if event:
                    event.is_room_wide = room_wide
                    raw_events.append(event)
                    
            yield []
            
        for key, sm in state_machines.items():
            event = sm.finalize_event()
            if event:
                raw_events.append(event)
        
        # ── Step 1: Intra-Desk Single-Zone Temporal Coalescing
        single_zone_events = _consolidate_single_zone_events(
            raw_events,
            merge_gap_sec=merge_gap_sec,
            min_dur_sec=min_dur_sec,
            cooldown_sec=cooldown_sec
        )

        # ── Step 2: Cross-Desk Simultaneous Multi-Student Incident Fusion
        fused_incidents = _fuse_cross_desk_overlapping_events(
            single_zone_events,
            zone_lookup=zone_lookup,
            time_overlap_tolerance=merge_gap_sec
        )
        
        # ── Step 3: Render Single Unified Annotated Video Clips
        for inc in fused_incidents:
            inc.clip_path = cut_unified_annotated_clip(
                source_video,
                start_time=inc.start_timestamp,
                end_time=inc.end_timestamp,
                event_id=inc.event_id,
                involved_desks=inc.involved_desks,
                combined_risk_level=inc.combined_risk_level
            )
            desk_labels = [d["student_name"] for d in inc.involved_desks]
            logger.info(
                f"Unified Incident {inc.event_id} | Desks: {desk_labels} | Activity: {inc.class_name} | "
                f"Time: {inc.start_timestamp:.2f}s->{inc.end_timestamp:.2f}s ({inc.duration_seconds:.2f}s) | "
                f"Clip: {inc.clip_path}"
            )
            
        if len(fused_incidents) > 0:
            yield fused_incidents
            
    except GeneratorExit:
        logger.info("Generator closed early by the caller.")
    except Exception as e:
        logger.error(f"Exception during event segmentation: {e}")
    finally:
        logger.info("=" * 55)
        logger.info("UNIQUE EVENT SEGMENTATION SUMMARY")
        logger.info(f"  Raw candidate triggers: {len(raw_events)}")
        logger.info(f"  Unified multi-desk incidents : {len(fused_incidents) if 'fused_incidents' in locals() else 0}")
        if 'fused_incidents' in locals():
            for inc in fused_incidents:
                desks = [f"{d['student_name']} ({d['activity']})" for d in inc.involved_desks]
                logger.info(f"    Incident {inc.event_id} [{inc.combined_risk_level}]: {', '.join(desks)} ({inc.duration_seconds:.2f}s)")
        logger.info("=" * 55)
        logger.info("Event segmentation completed.")
