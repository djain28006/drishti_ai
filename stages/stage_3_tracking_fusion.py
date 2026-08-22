import cv2
import numpy as np
from typing import Generator, List, Dict, Optional, Tuple
from dataclasses import dataclass, field
from collections import defaultdict
from utils.logger import StageLogger
from stages.stage_1_5_zone_calibration import ZoneMap, ZoneSpec
from stages.stage_2a_motion import MotionFrame, ZoneMotionResult
from stages.stage_2b_object import ObjectDetectionFrame

logger = StageLogger("STAGE 3")


@dataclass
class FusedTrackRecord:
    track_id: int
    zone_id: int
    motion_score: float
    baseline_deviation: float
    boundary_crossing: bool
    crossed_into_zone_id: Optional[int]
    detected_objects: List[str]
    confidence: float
    bbox: Tuple[int, int, int, int]
    suspicion_score: float = 0.0      # Fused normalized suspicion [0..1]
    zone_stable: bool = True          # False if zone assignment changed this frame
    calib_confidence: float = 1.0     # calibration-time detection confidence (DO NOT use as activity score)


@dataclass
class FusedTrackFrame:
    records: List[FusedTrackRecord]
    frame_no: int
    timestamp: float
    color_frame: Optional[np.ndarray] = None


# ─────────────────────────────────────────────
# Geometry helpers
# ─────────────────────────────────────────────

def point_in_polygon(point: Tuple[int, int], polygon: List[List[int]]) -> bool:
    """Checks if (x, y) is inside a convex polygon contour."""
    pts = np.array(polygon, dtype=np.int32)
    return cv2.pointPolygonTest(pts, (float(point[0]), float(point[1])), False) >= 0


def dist_to_polygon_center(point: Tuple[int, int], zone: ZoneSpec) -> float:
    cx, cy = zone.center
    return float(np.sqrt((point[0] - cx) ** 2 + (point[1] - cy) ** 2))


# ─────────────────────────────────────────────
# Per-zone hysteresis state
# ─────────────────────────────────────────────

class ZoneHysteresisState:
    """
    Tracks temporal stability of a calibrated zone's activity.

    Rules
    -----
    - A detection_object is 'in zone' only if its bottom-center (foot point)
      is inside the polygon OR within tolerance_px of its boundary.
    - A single-frame boundary crossing does NOT change the zone.
      Requires `zone_change_frames` consecutive frames before switching.
    - If a detection disappears, the zone retains its last known state for
      `preserve_frames` frames before being reset.
    """

    def __init__(self, zone_id: int, preserve_frames: int = 5,
                 zone_change_frames: int = 3, tolerance_px: int = 15):
        self.zone_id = zone_id
        self.preserve_frames = preserve_frames
        self.zone_change_frames = zone_change_frames
        self.tolerance_px = tolerance_px

        self.last_seen_frame: int = -999
        self.pending_switch_to: Optional[int] = None   # zone_id we might switch to
        self.pending_switch_count: int = 0             # consecutive frames suggesting switch
        self.zone_switches: int = 0
        self.track_losses: int = 0
        self._was_lost: bool = False

    def update(self, frame_no: int, detection_in_zone: bool, candidate_zone: Optional[int]) -> bool:
        """
        Returns True if this zone is still considered active/occupied.
        `detection_in_zone` = YOLO/motion says the student is here this frame.
        `candidate_zone`    = which other zone the detection fell into (if not here).
        """
        gap = frame_no - self.last_seen_frame

        if detection_in_zone:
            # Clear any pending switch if student is back in zone
            self.pending_switch_to = None
            self.pending_switch_count = 0
            if self._was_lost and gap > 1:
                self.track_losses += 1
            self._was_lost = False
            self.last_seen_frame = frame_no
            return True

        # Detection not in zone this frame
        if gap <= self.preserve_frames:
            # Within tolerance window — keep zone active, track as temporarily lost
            self._was_lost = True

            if candidate_zone is not None and candidate_zone != self.zone_id:
                if candidate_zone == self.pending_switch_to:
                    self.pending_switch_count += 1
                else:
                    self.pending_switch_to = candidate_zone
                    self.pending_switch_count = 1

                if self.pending_switch_count >= self.zone_change_frames:
                    # Confirmed zone switch after N consecutive frames
                    self.zone_switches += 1
                    self.pending_switch_to = None
                    self.pending_switch_count = 0
                    return False  # Let this zone go

            return True  # Still within preserve window

        # Gap > preserve_frames → zone truly lost
        return False

    @property
    def is_stable(self) -> bool:
        return self.pending_switch_count == 0 and not self._was_lost


# ─────────────────────────────────────────────
# Main tracking + fusion stage
# ─────────────────────────────────────────────

def tracking_fusion_stage(
    motion_stream: Generator[MotionFrame, None, None],
    detection_stream: Generator[ObjectDetectionFrame, None, None],
    zone_map: ZoneMap,
    config_dict: dict,
    debug_cfg: dict = None
) -> Generator[FusedTrackFrame, None, None]:
    """
    Zone-anchored signal fusion stage.

    Design
    ------
    Zone identity comes exclusively from the calibrated ZoneMap (single source
    of truth). Each calibrated zone gets one permanent track_id == zone_id.
    No new IDs are generated mid-stream.

    For object detection assignment, uses the detection's BOTTOM-CENTER (foot
    point) for more stable ground-plane zone matching, with a configurable
    pixel tolerance beyond the polygon boundary.

    Temporal hysteresis prevents single-frame boundary fluctuations from
    triggering zone switches or track losses.

    Calibration confidence (zone.zone_confidence) is stored in every record
    but is NEVER used as the activity score. Activity is measured solely by
    motion/suspicion signals at runtime.
    """
    tracking_cfg = config_dict.get('tracking', {})
    preserve_frames  = tracking_cfg.get('preserve_frames',  5)
    zone_change_frames = tracking_cfg.get('zone_change_frames', 3)
    tolerance_px     = tracking_cfg.get('boundary_tolerance_px', 20)

    # One hysteresis state per calibrated zone (keyed by zone_id)
    hysteresis: Dict[int, ZoneHysteresisState] = {
        z.zone_id: ZoneHysteresisState(z.zone_id, preserve_frames,
                                        zone_change_frames, tolerance_px)
        for z in zone_map.zones
    }

    suspicious_obj_classes = {"phone", "chit", "peeking", "supplement-passing"}

    logger.info(f"Started Stage 3 Tracking & Signal Fusion "
                f"(Zones: {len(zone_map.zones)}, "
                f"preserve_frames={preserve_frames}, "
                f"zone_change_frames={zone_change_frames}, "
                f"boundary_tolerance_px={tolerance_px})")
    frames_processed = 0

    try:
        for m_frame, od_frame in zip(motion_stream, detection_stream):
            if m_frame.frame_no != od_frame.frame_no:
                logger.error(f"Stream out of sync: {m_frame.frame_no} != {od_frame.frame_no}")
                continue

            color_frame = od_frame.color_frame
            detections  = od_frame.detections
            zone_motion_map: Dict[int, ZoneMotionResult] = {
                z.zone_id: z for z in m_frame.zone_results
            }

            fused_records: List[FusedTrackRecord] = []

            for z_spec in zone_map.zones:
                zid  = z_spec.zone_id
                poly = z_spec.polygon
                pts  = np.array(poly, dtype=np.int32)
                x1_z = max(0, int(np.min(pts[:, 0])))
                y1_z = max(0, int(np.min(pts[:, 1])))
                x2_z = int(np.max(pts[:, 0]))
                y2_z = int(np.max(pts[:, 1]))

                # ── Motion signals from Stage 2A (already zone-locked)
                z_motion = zone_motion_map.get(zid)
                m_score = z_motion.motion_score         if z_motion else 0.0
                b_dev   = z_motion.baseline_deviation   if z_motion else 0.0
                b_cross = z_motion.boundary_crossing    if z_motion else False
                c_into  = z_motion.crossed_into_zone_id if z_motion else None

                # ── Object detection: assign using BOTTOM-CENTER (foot point)
                #    + configurable pixel tolerance beyond polygon boundary
                detected_objs = []
                max_conf = 0.90

                for d in detections:
                    bx, by, bw, bh = d.bbox
                    # Foot point = bottom-center of the detection bounding box
                    foot_x = int(bx + bw / 2.0)
                    foot_y = int(by + bh)          # bottom edge

                    in_zone = point_in_polygon((foot_x, foot_y), poly)

                    if not in_zone and tolerance_px > 0:
                        # Check if within tolerance of the polygon boundary
                        dist = abs(cv2.pointPolygonTest(
                            pts, (float(foot_x), float(foot_y)), True))
                        in_zone = dist <= tolerance_px

                    if in_zone:
                        detected_objs.append(d.class_name)
                        max_conf = max(max_conf, d.confidence)

                # ── Temporal hysteresis update
                hyst = hysteresis[zid]
                detection_present = bool(detected_objs) or m_score > 0.0005
                hyst.update(od_frame.frame_no, detection_present, c_into)
                zone_stable = hyst.is_stable

                # ── Fused suspicion score
                # NOTE: z_spec.zone_confidence = calibration confidence (DO NOT use for activity)
                zone_std = float(np.sqrt(z_spec.baseline_variance + 1e-8))
                z_score  = max(0.0, b_dev / (zone_std + 1e-6))
                obj_bonus = sum(0.5 for obj in detected_objs
                                if obj.lower() in suspicious_obj_classes)
                crossing_bonus = 0.3 if b_cross else 0.0
                suspicion = round(min(1.0, z_score + crossing_bonus + obj_bonus), 4)

                f_rec = FusedTrackRecord(
                    track_id=zid,           # zone_id IS the permanent track_id
                    zone_id=zid,
                    motion_score=m_score,
                    baseline_deviation=b_dev,
                    boundary_crossing=b_cross,
                    crossed_into_zone_id=c_into,
                    detected_objects=detected_objs if detected_objs else ["student"],
                    confidence=round(max_conf, 2),
                    bbox=(x1_z, y1_z, x2_z - x1_z, y2_z - y1_z),
                    suspicion_score=suspicion,
                    zone_stable=zone_stable,
                    calib_confidence=z_spec.zone_confidence  # store but never use for activity
                )
                fused_records.append(f_rec)

                if m_score > 0.0001 or b_dev > 0 or b_cross or detected_objs:
                    logger.info(
                        f"DEBUG TRACE [Frame {od_frame.frame_no}] Zone/Track {zid} | "
                        f"Objects: {detected_objs} | Motion: {m_score:.4f} | "
                        f"Dev: {b_dev:.4f} | BoundaryCross: {b_cross} | "
                        f"Stable: {zone_stable}"
                    )

            output = FusedTrackFrame(
                records=fused_records,
                frame_no=od_frame.frame_no,
                timestamp=od_frame.timestamp,
                color_frame=color_frame
            )
            frames_processed += 1
            yield output

    except GeneratorExit:
        logger.info("Generator closed early by the caller.")
    except Exception as e:
        logger.error(f"Exception during tracking fusion: {str(e)}")
        raise
    finally:
        # ── End-of-stream stability summary (printed once, not every frame)
        total_switches = sum(h.zone_switches for h in hysteresis.values())
        total_losses   = sum(h.track_losses   for h in hysteresis.values())
        logger.info("=" * 55)
        logger.info("TRACKING STABILITY SUMMARY")
        for z_spec in zone_map.zones:
            h = hysteresis[z_spec.zone_id]
            status = "stable" if h.zone_switches == 0 and h.track_losses == 0 else "unstable"
            logger.info(
                f"  {z_spec.name} -> zone {z_spec.zone_id} -> {status} "
                f"(switches={h.zone_switches}, losses={h.track_losses})"
            )
        logger.info(f"  TOTAL zone switches : {total_switches}")
        logger.info(f"  TOTAL track losses  : {total_losses}")
        logger.info("=" * 55)
        logger.info("Tracking fusion completed.")
        logger.info(f"Total frames processed: {frames_processed}")
