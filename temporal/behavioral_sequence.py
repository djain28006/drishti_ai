"""
temporal/behavioral_sequence.py
-------------------------------
USP #2: Temporal Behavior Analysis

Tracks and models multi-frame behavioral sequences per student zone.
Calculates motion intensity, repetition rate, temporal persistence,
directional boundary shifts, and object interactions across time.
"""

from typing import Dict, List, Optional
from dataclasses import dataclass, field
import numpy as np

@dataclass
class TemporalBehaviorRecord:
    zone_id: int
    timestamps: List[float] = field(default_factory=list)
    motion_history: List[float] = field(default_factory=list)
    boundary_crossings: int = 0
    object_interactions: List[str] = field(default_factory=list)
    consecutive_motion_frames: int = 0
    total_active_seconds: float = 0.0
    repetition_score: float = 0.0

class BehavioralSequenceTracker:
    def __init__(self, fps: float = 5.0):
        self.fps = fps
        self.zone_records: Dict[int, TemporalBehaviorRecord] = {}

    def update_frame(
        self,
        zone_id: int,
        timestamp: float,
        motion_score: float,
        boundary_crossing: bool,
        detected_objects: List[str]
    ):
        if zone_id not in self.zone_records:
            self.zone_records[zone_id] = TemporalBehaviorRecord(zone_id=zone_id)

        rec = self.zone_records[zone_id]
        rec.timestamps.append(timestamp)
        rec.motion_history.append(motion_score)

        if len(rec.motion_history) > 100:
            rec.motion_history.pop(0)
            rec.timestamps.pop(0)

        if boundary_crossing:
            rec.boundary_crossings += 1

        for obj in detected_objects:
            if obj.lower() not in ("person", "student") and obj not in rec.object_interactions:
                rec.object_interactions.append(obj)

        if motion_score > 0.001:
            rec.consecutive_motion_frames += 1
            rec.total_active_seconds += (1.0 / self.fps)
        else:
            rec.consecutive_motion_frames = max(0, rec.consecutive_motion_frames - 1)

        # Repetition calculation: count auto-correlation peaks or periodic spikes
        if len(rec.motion_history) >= 20:
            arr = np.array(rec.motion_history[-20:])
            peaks = np.sum((arr[1:-1] > arr[:-2]) & (arr[1:-1] > arr[2:]) & (arr[1:-1] > 0.002))
            rec.repetition_score = float(peaks)

    def extract_features(self, zone_id: int, event_duration: float, avg_motion: float) -> dict:
        rec = self.zone_records.get(zone_id, TemporalBehaviorRecord(zone_id=zone_id))
        
        return {
            "zone_id": zone_id,
            "motion_intensity": avg_motion,
            "motion_duration": event_duration,
            "motion_repetition": rec.repetition_score,
            "boundary_crossings": rec.boundary_crossings,
            "object_interactions": list(rec.object_interactions),
            "total_active_seconds": round(rec.total_active_seconds, 2)
        }
