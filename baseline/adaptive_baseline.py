"""
baseline/adaptive_baseline.py
-----------------------------
USP #1: Adaptive Normal-Behavior Baseline

Learns normal examination activity from an initial configurable window or accumulated
low-risk frames. Estimates average motion, variance, movement burst frequency, duration,
and computes dynamic anomaly deviation metrics per examination zone.
"""

import numpy as np
from typing import Dict, List, Optional
from dataclasses import dataclass, field
from utils.logger import StageLogger

logger = StageLogger("BASELINE")

@dataclass
class ZoneBaselineProfile:
    zone_id: int
    mean_motion: float = 0.0005
    variance_motion: float = 0.0001
    std_motion: float = 0.01
    burst_count: int = 0
    total_samples: int = 0
    motion_history: List[float] = field(default_factory=list)
    recent_burst_timestamps: List[float] = field(default_factory=list)
    is_locked: bool = False

class AdaptiveBaselineEngine:
    def __init__(self, config: dict):
        baseline_cfg = config.get("baseline", {})
        self.sensitivity = baseline_cfg.get("sensitivity", 0.50)
        self.anomaly_threshold = baseline_cfg.get("anomaly_threshold", 0.60)
        self.history_window = baseline_cfg.get("history_window_frames", 120)
        self.profiles: Dict[int, ZoneBaselineProfile] = {}

    def register_zone(self, zone_id: int, initial_mean: float = 0.0005, initial_var: float = 0.0001):
        std = max(0.0001, float(np.sqrt(max(1e-8, initial_var))))
        self.profiles[zone_id] = ZoneBaselineProfile(
            zone_id=zone_id,
            mean_motion=initial_mean,
            variance_motion=initial_var,
            std_motion=std,
            motion_history=[initial_mean] * 10
        )

    def update(self, zone_id: int, motion_score: float, timestamp: float):
        """Updates moving baseline statistics for a zone."""
        if zone_id not in self.profiles:
            self.register_zone(zone_id, initial_mean=motion_score)

        prof = self.profiles[zone_id]
        prof.total_samples += 1
        prof.motion_history.append(motion_score)
        if len(prof.motion_history) > self.history_window:
            prof.motion_history.pop(0)

        # Update moving stats with exponential weighting
        alpha = 0.05
        prof.mean_motion = (1 - alpha) * prof.mean_motion + alpha * motion_score
        var_sample = (motion_score - prof.mean_motion) ** 2
        prof.variance_motion = (1 - alpha) * prof.variance_motion + alpha * var_sample
        prof.std_motion = max(0.0001, float(np.sqrt(max(1e-8, prof.variance_motion))))

        # Track bursts (activity above baseline + 2*std)
        if motion_score > (prof.mean_motion + 2.0 * prof.std_motion):
            prof.burst_count += 1
            prof.recent_burst_timestamps.append(timestamp)
            # Retain bursts in last 60 seconds
            prof.recent_burst_timestamps = [t for t in prof.recent_burst_timestamps if timestamp - t <= 60.0]

    def compute_anomaly_score(self, zone_id: int, motion_score: float) -> float:
        """
        Computes dynamic anomaly score between 0.0 and 1.0 using baseline Z-score.
        """
        if zone_id not in self.profiles:
            return 0.10

        prof = self.profiles[zone_id]
        z_score = (motion_score - prof.mean_motion) / max(0.0001, prof.std_motion)
        
        # Scale z-score by sensitivity
        scaled_z = max(0.0, z_score * self.sensitivity)
        
        # Sigmoid normalization to 0.0 -> 1.0
        anomaly_score = float(1.0 / (1.0 + np.exp(-scaled_z + 2.0)))
        return float(np.clip(anomaly_score, 0.0, 1.0))

    def is_anomalous(self, zone_id: int, motion_score: float) -> bool:
        return self.compute_anomaly_score(zone_id, motion_score) >= self.anomaly_threshold

    def get_profile(self, zone_id: int) -> dict:
        if zone_id not in self.profiles:
            return {}
        p = self.profiles[zone_id]
        return {
            "zone_id": p.zone_id,
            "mean_motion": round(p.mean_motion, 6),
            "std_motion": round(p.std_motion, 6),
            "bursts_last_minute": len(p.recent_burst_timestamps),
            "total_bursts": p.burst_count
        }
