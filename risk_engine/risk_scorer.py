"""
risk_engine/risk_scorer.py
--------------------------
USP #3: Temporal Risk Scoring Engine

Calculates an explainable, transparent risk score between 0 and 100 with
explicit contributing factor breakdowns and standardized risk classifications.
"""

from typing import Dict, List, Any
from dataclasses import dataclass, field

@dataclass
class RiskBreakdown:
    total_score: int
    risk_level: str                       # LOW | MEDIUM | HIGH | CRITICAL
    confidence: float
    factor_breakdown: Dict[str, int]      # motion_intensity: 18, repetition: 20, etc.
    contributing_factors: List[str]       # Human-readable explanations

class TemporalRiskScorer:
    def __init__(self, config: dict = None):
        cfg = (config or {}).get("risk_engine", {})
        self.weights = cfg.get("weights", {
            "motion_intensity": 0.25,
            "motion_repetition": 0.25,
            "duration": 0.15,
            "directional_movement": 0.15,
            "object_interaction": 0.20,
        })
        self.thresholds = cfg.get("thresholds", {
            "low": 30,
            "medium": 60,
            "high": 80,
            "critical": 81
        })
        self.multipliers = cfg.get("class_multipliers", {
            "phone": 1.0,
            "chit": 0.95,
            "peeking": 0.85,
            "supplement-passing": 0.90,
            "boundary_crossing": 0.70,
            "suspicious_motion": 0.50,
            "student": 0.30
        })

    def score_event(
        self,
        avg_motion: float,
        duration: float,
        repetition_count: float,
        boundary_crossing: bool,
        class_name: str,
        confidence: float = 0.90,
        cross_camera_matches: int = 0
    ) -> RiskBreakdown:
        
        # 1. Motion Intensity component (max 25 pts)
        # Normalized: 0.001 -> 5 pts, 0.005 -> 15 pts, >=0.015 -> 25 pts
        motion_norm = min(1.0, avg_motion / 0.015)
        score_motion = int(motion_norm * 25)

        # 2. Repetition component (max 25 pts)
        # 1 burst -> 8 pts, 2 bursts -> 16 pts, >=3 bursts -> 25 pts
        rep_norm = min(1.0, repetition_count / 3.0)
        score_rep = int(rep_norm * 25)

        # 3. Duration component (max 15 pts)
        # 1.0s -> 5 pts, 3.0s -> 10 pts, >=6.0s -> 15 pts
        dur_norm = min(1.0, duration / 6.0)
        score_dur = int(dur_norm * 15)

        # 4. Directional / Boundary Movement (max 15 pts)
        score_dir = 15 if boundary_crossing else int(score_dur * 0.4)

        # 5. Object / Behavior Class component (max 20 pts)
        c_lower = class_name.lower()
        multiplier = self.multipliers.get(c_lower, 0.50)
        score_obj = int(20 * multiplier)

        # 6. Cross-camera corroboration (bonus up to 10 pts)
        score_cross = min(10, cross_camera_matches * 5)

        total_raw = score_motion + score_rep + score_dur + score_dir + score_obj + score_cross
        total_score = min(100, max(0, total_raw))

        # Risk Classification
        if total_score >= self.thresholds.get("critical", 81):
            risk_level = "CRITICAL"
        elif total_score >= self.thresholds.get("high", 61):
            risk_level = "HIGH"
        elif total_score >= self.thresholds.get("medium", 31):
            risk_level = "MEDIUM"
        else:
            risk_level = "LOW"

        # Explainable contributing factors
        factors = []
        if score_obj >= 15:
            factors.append(f"High-priority anomalous pattern detected: {class_name.upper()}")
        elif score_obj >= 10:
            factors.append(f"Anomalous posture/movement signature: {class_name.upper()}")

        if score_motion >= 15:
            factors.append("Motion intensity significantly elevated above baseline")
        if score_rep >= 12:
            factors.append(f"Repeated movement cycles observed ({int(repetition_count)} cycles)")
        if score_dur >= 10:
            factors.append(f"Prolonged activity persistence ({duration:.1f} seconds)")
        if boundary_crossing:
            factors.append("Inter-zone boundary crossing reaching into adjacent desk")
        if score_cross > 0:
            factors.append(f"Corroborated across {cross_camera_matches + 1} synchronized camera angles")

        if not factors:
            factors.append("Minor baseline activity deviation recorded")

        breakdown = {
            "Motion Intensity": score_motion,
            "Motion Repetition": score_rep,
            "Duration Persistence": score_dur,
            "Directional / Boundary": score_dir,
            "Object / Behavior": score_obj,
            "Cross-Camera Corroboration": score_cross
        }

        return RiskBreakdown(
            total_score=total_score,
            risk_level=risk_level,
            confidence=confidence,
            factor_breakdown=breakdown,
            contributing_factors=factors
        )
