"""
search/nl_query_parser.py
-------------------------
USP #7: Natural-Language Video Search

Translates investigator natural language queries into structured search filters
without requiring external LLM dependencies, providing instant sub-millisecond
forensic incident and event search.
"""

import re
from typing import Dict, Any, List

class NaturalLanguageQueryParser:
    def __init__(self):
        pass

    def parse_query(self, query_str: str) -> Dict[str, Any]:
        """
        Parses a natural language search query into structured filter parameters.
        """
        q = query_str.lower().strip()
        filters: Dict[str, Any] = {
            "min_risk_score": None,
            "max_risk_score": None,
            "risk_levels": [],
            "objects": [],
            "behaviors": [],
            "camera_ids": [],
            "zone_ids": [],
            "min_duration": None,
            "time_start": None,
            "time_end": None,
            "is_cross_camera": None,
            "has_repetition": None
        }

        # 1. Risk level filters
        if "critical" in q:
            filters["risk_levels"].append("CRITICAL")
        if "high" in q or "high-risk" in q or "high risk" in q:
            filters["risk_levels"].extend(["HIGH", "CRITICAL"])
        if "medium" in q or "moderate" in q:
            filters["risk_levels"].append("MEDIUM")
        if "low" in q:
            filters["risk_levels"].append("LOW")

        # 2. Explicit risk number thresholds: "risk above 80", ">70", "score >= 85"
        risk_match = re.search(r'(?:risk|score)\s*(?:above|>|>=|\+)\s*(\d+)', q)
        if risk_match:
            filters["min_risk_score"] = int(risk_match.group(1))

        risk_below = re.search(r'(?:risk|score)\s*(?:below|<|<=)\s*(\d+)', q)
        if risk_below:
            filters["max_risk_score"] = int(risk_below.group(1))

        # 3. Specific Object & Behavior filters
        if "phone" in q or "mobile" in q or "cell" in q:
            filters["objects"].append("phone")
        if "chit" in q or "paper" in q or "notes" in q:
            filters["objects"].append("chit")
        if "peek" in q or "glance" in q or "looking" in q:
            filters["behaviors"].append("peeking")
        if "pass" in q or "supplement" in q or "hand" in q:
            filters["behaviors"].append("supplement-passing")
        if "bound" in q or "cross" in q or "reach" in q:
            filters["behaviors"].append("boundary_crossing")
        if "repeat" in q or "repetitive" in q or "periodic" in q:
            filters["has_repetition"] = True

        # 4. Cross-camera filter
        if "cross" in q or "multi" in q or "cameras" in q:
            filters["is_cross_camera"] = True

        # 5. Camera ID matching: "camera 1", "cam 2", "cam-01"
        cam_matches = re.findall(r'(?:camera|cam)[-\s]*(\d+)', q)
        for c in cam_matches:
            filters["camera_ids"].append(f"CAM-{int(c):02d}")

        # 6. Zone / Student matching: "student 7", "zone 4", "s2", "seat 3"
        zone_matches = re.findall(r'(?:zone|seat|student|s)[-\s]*(\d+)', q)
        for z in zone_matches:
            filters["zone_ids"].append(int(z))

        # 7. Time intervals: "between 00:02 and 00:08", "after 5s", "before 10s"
        time_range = re.search(r'(?:between|from)\s*(\d+(?:\.\d+)?)\s*(?:and|to)\s*(\d+(?:\.\d+)?)', q)
        if time_range:
            filters["time_start"] = float(time_range.group(1))
            filters["time_end"] = float(time_range.group(2))

        return filters

    def filter_incidents(self, incidents: List[dict], query_str: str) -> List[dict]:
        """Filters a list of incident dictionaries based on natural language query."""
        if not query_str or not query_str.strip():
            return incidents

        f = self.parse_query(query_str)
        results = []

        for inc in incidents:
            score = inc.get("risk_score", 0)
            level = inc.get("risk_level", "LOW")
            p_class = inc.get("primary_class", "").lower()
            cams = inc.get("camera_ids", [])
            zids = inc.get("zone_ids", [])
            t_start = inc.get("start_timestamp", 0.0)
            t_end = inc.get("end_timestamp", 0.0)

            # Check min risk
            if f["min_risk_score"] is not None and score < f["min_risk_score"]:
                continue
            if f["max_risk_score"] is not None and score > f["max_risk_score"]:
                continue

            # Check risk level
            if f["risk_levels"] and level not in f["risk_levels"]:
                continue

            # Check objects / behaviors
            if f["objects"] and not any(obj in p_class for obj in f["objects"]):
                continue
            if f["behaviors"] and not any(beh in p_class for beh in f["behaviors"]):
                continue

            # Check camera IDs
            if f["camera_ids"] and not any(c in cams for c in f["camera_ids"]):
                continue

            # Check zone IDs
            if f["zone_ids"] and not any(z in zids for z in f["zone_ids"]):
                continue

            # Check cross-camera
            if f["is_cross_camera"] and len(cams) <= 1:
                continue

            # Check time interval
            if f["time_start"] is not None and t_end < f["time_start"]:
                continue
            if f["time_end"] is not None and t_start > f["time_end"]:
                continue

            results.append(inc)

        return results
