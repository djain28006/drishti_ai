"""
evidence/capsule_generator.py
-----------------------------
USP #5: Evidence Capsule Generation

Generates comprehensive, self-contained forensic Evidence Capsules for
investigators including before/during/after frame snapshots, ROI crops,
heatmap visualizations, and explainable risk factor breakdowns.
"""

import os
import cv2
import json
import numpy as np
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, asdict
from incident_fusion.incident_builder import IncidentRecord
from utils.logger import StageLogger

logger = StageLogger("EVIDENCE_CAPSULE")

@dataclass
class EvidenceCapsule:
    capsule_id: str
    incident_id: str
    cameras: List[str]
    zone_id: int
    location_desc: str
    time_start: float
    time_end: float
    duration_seconds: float
    risk_score: int
    risk_level: str
    confidence: float
    primary_behavior: str
    detected_objects: List[str]
    factor_breakdown: Dict[str, int]
    contributing_factors: List[str]
    explanation: str
    before_snapshot_path: str
    during_snapshot_path: str
    after_snapshot_path: str
    roi_crop_path: str
    heatmap_crop_path: str
    clip_path: str
    disclaimer: str = (
        "AI-generated forensic evidence is intended exclusively to assist qualified examination "
        "proctors and investigators. The platform flags anomalous patterns and does not establish "
        "academic misconduct independently."
    )

class EvidenceCapsuleGenerator:
    def __init__(self, output_dir: str = "outputs/capsules"):
        self.output_dir = output_dir
        os.makedirs(self.output_dir, exist_ok=True)

    def extract_snapshots(
        self,
        video_path: str,
        t_start: float,
        t_end: float,
        incident_id: str,
        roi_polygon: Optional[List[List[int]]] = None
    ) -> Dict[str, str]:
        if not os.path.exists(video_path):
            for candidate in [os.path.join("uploads", os.path.basename(video_path)), os.path.basename(video_path)]:
                if os.path.exists(candidate):
                    video_path = candidate
                    break

        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            return {"before": "", "during": "", "after": "", "roi": ""}

        fps = cap.get(cv2.CAP_PROP_FPS) or 24.0
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

        f_before = max(0, int((t_start - 1.0) * fps))
        f_during = max(0, int(((t_start + t_end) / 2.0) * fps))
        f_after = min(total_frames - 1, int((t_end + 1.0) * fps))

        ref_preview = os.path.join("outputs", "zones", "zone_calibration_preview.jpg")

        paths = {}
        for name, frame_idx in [("before", f_before), ("during", f_during), ("after", f_after)]:
            cap.set(cv2.CAP_PROP_POS_FRAMES, frame_idx)
            ret, frame = cap.read()
            p = os.path.join(self.output_dir, f"{incident_id}_{name}.jpg")
            
            if ret and frame is not None:
                if roi_polygon:
                    h, w = frame.shape[:2]
                    sx, sy = w / 640.0, h / 480.0
                    scaled_pts = np.array([[int(pt[0]*sx), int(pt[1]*sy)] for pt in roi_polygon], dtype=np.int32)
                    cv2.polylines(frame, [scaled_pts], isClosed=True, color=(0, 255, 200), thickness=2)
                cv2.imwrite(p, frame)
                paths[name] = p
            elif os.path.exists(ref_preview):
                import shutil
                shutil.copy(ref_preview, p)
                paths[name] = p
            else:
                paths[name] = ""

        # Extract ROI crop from 'during' frame
        paths["roi"] = ""
        if roi_polygon and paths.get("during"):
            img = cv2.imread(paths["during"])
            if img is not None:
                pts = np.array(roi_polygon, dtype=np.int32)
                h, w = img.shape[:2]
                sx, sy = w / 640.0, h / 480.0
                scaled_pts = np.array([[int(p[0]*sx), int(p[1]*sy)] for p in roi_polygon], dtype=np.int32)
                x1, y1 = max(0, int(np.min(scaled_pts[:, 0]))), max(0, int(np.min(scaled_pts[:, 1])))
                x2, y2 = min(w, int(np.max(scaled_pts[:, 0]))), min(h, int(np.max(scaled_pts[:, 1])))
                if x2 > x1 and y2 > y1:
                    crop = img[y1:y2, x1:x2]
                    roi_path = os.path.join(self.output_dir, f"{incident_id}_roi.jpg")
                    cv2.imwrite(roi_path, crop)
                    paths["roi"] = roi_path

        cap.release()
        return paths

    def generate_capsule(
        self,
        incident: IncidentRecord,
        video_path: str,
        roi_polygon: Optional[List[List[int]]] = None,
        heatmap_path: str = "outputs/heatmap_student.png"
    ) -> EvidenceCapsule:
        """Builds a complete forensic evidence capsule."""
        snaps = self.extract_snapshots(
            video_path,
            incident.start_timestamp,
            incident.end_timestamp,
            incident.incident_id,
            roi_polygon=roi_polygon
        )

        capsule = EvidenceCapsule(
            capsule_id=f"CAP-{incident.incident_id}",
            incident_id=incident.incident_id,
            cameras=incident.camera_ids,
            zone_id=incident.zone_ids[0] if incident.zone_ids else 0,
            location_desc=incident.location_desc,
            time_start=incident.start_timestamp,
            time_end=incident.end_timestamp,
            duration_seconds=incident.duration_seconds,
            risk_score=incident.risk_score,
            risk_level=incident.risk_level,
            confidence=incident.confidence,
            primary_behavior=incident.primary_class.upper(),
            detected_objects=[incident.primary_class],
            factor_breakdown=incident.factor_breakdown,
            contributing_factors=incident.contributing_factors,
            explanation=incident.explanation_text,
            before_snapshot_path=snaps.get("before", ""),
            during_snapshot_path=snaps.get("during", ""),
            after_snapshot_path=snaps.get("after", ""),
            roi_crop_path=snaps.get("roi", ""),
            heatmap_crop_path=heatmap_path,
            clip_path=incident.clip_path
        )

        def _serial(obj):
            if hasattr(obj, 'item'):
                return obj.item()
            if isinstance(obj, (float, int, str, bool)) or obj is None:
                return obj
            if isinstance(obj, dict):
                return {str(k): _serial(v) for k, v in obj.items()}
            if isinstance(obj, (list, tuple, set)):
                return [_serial(x) for x in obj]
            if hasattr(obj, '__dict__'):
                return _serial(obj.__dict__)
            return str(obj)

        # Save JSON capsule artifact
        json_path = os.path.join(self.output_dir, f"{incident.incident_id}_capsule.json")
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(_serial(asdict(capsule)), f, indent=2, default=_serial)

        return capsule
