"""
incident_fusion/incident_builder.py
-----------------------------------
USP #4: Cross-Camera & Multi-Desk Incident Fusion

Fuses correlated events across multiple camera angles or temporal streams into
unified multi-camera Incidents with aggregated risk scoring and evidence synchronization.
"""

from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field, asdict
import uuid
from risk_engine.risk_scorer import TemporalRiskScorer, RiskBreakdown

@dataclass
class IncidentRecord:
    incident_id: str
    camera_ids: List[str]
    zone_ids: List[int]
    primary_class: str
    start_timestamp: float
    end_timestamp: float
    duration_seconds: float
    risk_score: int
    risk_level: str                       # LOW | MEDIUM | HIGH | CRITICAL
    confidence: float
    contributing_factors: List[str]
    factor_breakdown: Dict[str, int]
    related_event_ids: List[str]
    location_desc: str
    explanation_text: str
    involved_desks: List[Dict[str, Any]] = field(default_factory=list)
    clip_path: str = ""
    heatmap_path: str = ""
    snapshot_path: str = ""
    is_multi_student: bool = False

class IncidentFusionEngine:
    def __init__(self, config: dict = None):
        cfg = (config or {}).get("incident_fusion", {})
        self.time_tolerance = cfg.get("time_tolerance_seconds", 3.5)
        self.max_event_gap = cfg.get("max_event_time_gap", 3.0)
        self.scorer = TemporalRiskScorer(config)

    def fuse_events_into_incidents(
        self,
        events: List[dict],
        camera_id: str = "CAM-01",
        zone_lookup: Optional[Dict[int, Any]] = None
    ) -> List[IncidentRecord]:
        """
        Groups correlated events by temporal proximity across zones and cameras,
        performing cross-camera or multi-desk incident fusion into prioritized Incidents.
        """
        if not events:
            return []

        # Sort events chronologically
        sorted_events = sorted(events, key=lambda e: e.get("start_timestamp", 0.0))
        
        incidents: List[IncidentRecord] = []
        visited = set()

        for i, ev in enumerate(sorted_events):
            eid = ev.get("event_id")
            if eid in visited:
                continue

            # Start cluster
            cluster = [ev]
            visited.add(eid)

            t_start = ev.get("start_timestamp", 0.0)
            t_end = ev.get("end_timestamp", 0.0)

            # Find matching/overlapping events across any desk within time tolerance
            for j in range(i + 1, len(sorted_events)):
                other = sorted_events[j]
                other_id = other.get("event_id")
                if other_id in visited:
                    continue

                other_start = other.get("start_timestamp", 0.0)
                other_end = other.get("end_timestamp", 0.0)

                # Temporal overlap or close proximity across zones
                temporal_match = (other_start <= t_end + self.time_tolerance)

                if temporal_match:
                    cluster.append(other)
                    visited.add(other_id)
                    t_start = min(t_start, other_start)
                    t_end = max(t_end, other_end)

            # Build unified incident from cluster
            inc_id = f"INC-{str(uuid.uuid4())[:6].upper()}"
            duration = max(0.1, t_end - t_start)
            
            # Aggregate signals
            avg_motion = max(e.get("avg_motion_score", 0.0) for e in cluster)
            max_conf = max(e.get("max_confidence", 0.85) for e in cluster)
            
            # Collect involved desks
            all_involved_desks: List[Dict[str, Any]] = []
            for e in cluster:
                desks = e.get("involved_desks", [])
                if desks:
                    for d in desks:
                        if not any(x.get("zone_id") == d.get("zone_id") and x.get("activity") == d.get("activity") for x in all_involved_desks):
                            all_involved_desks.append(d)
                else:
                    zid = e.get("zone_id")
                    z_spec = zone_lookup.get(zid) if zone_lookup else None
                    s_name = getattr(z_spec, "name", f"S{zid}")
                    loc_desc = getattr(z_spec, "location_desc", f"Desk {zid}")
                    poly = getattr(z_spec, "polygon", None)
                    all_involved_desks.append({
                        "zone_id": zid,
                        "track_id": e.get("track_id", zid),
                        "student_name": s_name,
                        "location_desc": loc_desc,
                        "activity": e.get("class_name", "ANOMALY"),
                        "risk_score": e.get("combined_risk_score", 60),
                        "confidence": e.get("max_confidence", 0.85),
                        "avg_motion_score": e.get("avg_motion_score", 0.0),
                        "zone_poly": poly
                    })

            # Zone IDs
            zone_ids = list(set([d["zone_id"] for d in all_involved_desks if d.get("zone_id") is not None]))

            # Location description
            if len(all_involved_desks) == 1:
                loc_desc = all_involved_desks[0].get("location_desc", f"Desk {zone_ids[0] if zone_ids else ''}")
                primary_class = all_involved_desks[0].get("activity", "ANOMALY")
                is_multi = False
            else:
                desk_names = [f"{d.get('student_name', 'Student')} ({d.get('activity', 'ANOMALY').upper()})" for d in all_involved_desks]
                loc_desc = f"{len(all_involved_desks)} Desks Involved: {', '.join(d.get('location_desc', '') for d in all_involved_desks)}"
                primary_class = f"MULTI-STUDENT ANOMALY ({', '.join(desk_names)})"
                is_multi = True

            # Score incident
            cross_cameras = list(set([e.get("camera_id", camera_id) for e in cluster]))
            
            # Risk scoring
            priority_order = ["phone", "chit", "peeking", "supplement-passing", "boundary_crossing", "suspicious_motion"]
            scoring_class = next((p for p in priority_order if any(p in d.get("activity", "").lower() for d in all_involved_desks)), "peeking")

            risk: RiskBreakdown = self.scorer.score_event(
                avg_motion=avg_motion,
                duration=duration,
                repetition_count=float(len(cluster)),
                boundary_crossing=any(e.get("boundary_crossing", False) for e in cluster),
                class_name=scoring_class,
                confidence=max_conf,
                cross_camera_matches=max(0, len(cross_cameras) - 1)
            )

            # Combined risk score
            desk_scores = [d.get("risk_score", risk.total_score) for d in all_involved_desks]
            final_risk_score = max(risk.total_score, max(desk_scores) if desk_scores else risk.total_score)
            
            if final_risk_score >= 81: final_risk_level = "CRITICAL"
            elif final_risk_score >= 61: final_risk_level = "HIGH"
            elif final_risk_score >= 31: final_risk_level = "MEDIUM"
            else: final_risk_level = "LOW"

            # Representative clip path
            clip_path = next((e.get("clip_path", "") for e in cluster if e.get("clip_path")), "")

            if is_multi:
                desk_str = ', '.join([f"{d.get('student_name', 'Student')} [{d.get('activity', 'ANOMALY').upper()}]" for d in all_involved_desks])
                explanation = (
                    f"Multi-student simultaneous anomalous activity detected involving {len(all_involved_desks)} desks "
                    f"({desk_str}). "
                    f"Time window: {t_start:.2f}s to {t_end:.2f}s ({duration:.2f}s duration) with combined risk index of {final_risk_score}/100."
                )
            else:
                explanation = (
                    f"Potentially anomalous pattern '{primary_class.upper()}' detected at {loc_desc}. "
                    f"Activity persisted across {duration:.2f}s with an aggregated risk index of {final_risk_score}/100. "
                    f"Contributing factors: {', '.join(risk.contributing_factors)}."
                )

            incidents.append(IncidentRecord(
                incident_id=inc_id,
                camera_ids=cross_cameras,
                zone_ids=zone_ids,
                primary_class=primary_class,
                start_timestamp=t_start,
                end_timestamp=t_end,
                duration_seconds=duration,
                risk_score=final_risk_score,
                risk_level=final_risk_level,
                confidence=max_conf,
                contributing_factors=risk.contributing_factors,
                factor_breakdown=risk.factor_breakdown,
                related_event_ids=[e.get("event_id") for e in cluster if e.get("event_id")],
                location_desc=loc_desc,
                explanation_text=explanation,
                involved_desks=all_involved_desks,
                clip_path=clip_path,
                is_multi_student=is_multi
            ))

        # Sort incidents by risk score descending
        incidents.sort(key=lambda x: x.risk_score, reverse=True)
        return incidents
