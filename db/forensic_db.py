"""
db/forensic_db.py
-----------------
USP #11: Searchable Event & Incident Forensic Database

SQLite storage engine for examination incidents, evidence capsules,
audit trails, and cross-camera forensic metadata.
"""

import os
import sqlite3
import json
from typing import List, Dict, Any, Optional
from dataclasses import asdict
from incident_fusion.incident_builder import IncidentRecord
from evidence.capsule_generator import EvidenceCapsule
from utils.logger import StageLogger

def _to_json_serializable(obj):
    if hasattr(obj, 'item'):
        return obj.item()
    if isinstance(obj, (float, int, str, bool)) or obj is None:
        return obj
    if isinstance(obj, dict):
        return {str(k): _to_json_serializable(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple, set)):
        return [_to_json_serializable(x) for x in obj]
    if hasattr(obj, '__dict__'):
        return _to_json_serializable(obj.__dict__)
    return str(obj)

class ForensicDatabase:
    def __init__(self, db_path: str = "outputs/forensic.db"):
        self.db_path = db_path
        os.makedirs(os.path.dirname(db_path) or ".", exist_ok=True)
        self.conn = sqlite3.connect(db_path, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        self.create_tables()

    def create_tables(self):
        with self.conn:
            self.conn.execute("""
                CREATE TABLE IF NOT EXISTS incidents (
                    incident_id TEXT PRIMARY KEY,
                    camera_ids TEXT,
                    zone_ids TEXT,
                    location_desc TEXT,
                    primary_class TEXT,
                    start_timestamp REAL,
                    end_timestamp REAL,
                    duration_seconds REAL,
                    risk_score INTEGER,
                    risk_level TEXT,
                    confidence REAL,
                    factor_breakdown TEXT,
                    contributing_factors TEXT,
                    related_event_ids TEXT,
                    explanation_text TEXT,
                    clip_path TEXT,
                    involved_desks TEXT,
                    is_multi_student INTEGER DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            try:
                self.conn.execute("ALTER TABLE incidents ADD COLUMN involved_desks TEXT")
            except Exception:
                pass
            try:
                self.conn.execute("ALTER TABLE incidents ADD COLUMN is_multi_student INTEGER DEFAULT 0")
            except Exception:
                pass

            self.conn.execute("""
                CREATE TABLE IF NOT EXISTS events (
                    event_id TEXT PRIMARY KEY,
                    incident_id TEXT,
                    camera_id TEXT,
                    zone_id INTEGER,
                    class_name TEXT,
                    start_timestamp REAL,
                    end_timestamp REAL,
                    duration_seconds REAL,
                    avg_motion_score REAL,
                    max_confidence REAL,
                    clip_path TEXT,
                    is_room_wide BOOLEAN
                )
            """)

            self.conn.execute("""
                CREATE TABLE IF NOT EXISTS evidence_capsules (
                    capsule_id TEXT PRIMARY KEY,
                    incident_id TEXT,
                    capsule_data TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            self.conn.execute("""
                CREATE TABLE IF NOT EXISTS audit_logs (
                    log_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    action TEXT,
                    details TEXT,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

    def insert_incident(self, inc: IncidentRecord):
        with self.conn:
            desks_json = json.dumps(_to_json_serializable(getattr(inc, 'involved_desks', [])), default=_to_json_serializable)
            self.conn.execute("""
                INSERT OR REPLACE INTO incidents (
                    incident_id, camera_ids, zone_ids, location_desc, primary_class,
                    start_timestamp, end_timestamp, duration_seconds, risk_score,
                    risk_level, confidence, factor_breakdown, contributing_factors,
                    related_event_ids, explanation_text, clip_path, involved_desks, is_multi_student
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                str(inc.incident_id),
                json.dumps(_to_json_serializable(inc.camera_ids), default=_to_json_serializable),
                json.dumps(_to_json_serializable(inc.zone_ids), default=_to_json_serializable),
                str(inc.location_desc),
                str(inc.primary_class),
                float(inc.start_timestamp),
                float(inc.end_timestamp),
                float(inc.duration_seconds),
                int(inc.risk_score),
                str(inc.risk_level),
                float(inc.confidence),
                json.dumps(_to_json_serializable(inc.factor_breakdown), default=_to_json_serializable),
                json.dumps(_to_json_serializable(inc.contributing_factors), default=_to_json_serializable),
                json.dumps(_to_json_serializable(inc.related_event_ids), default=_to_json_serializable),
                str(inc.explanation_text),
                str(inc.clip_path),
                desks_json,
                1 if getattr(inc, 'is_multi_student', False) else 0
            ))

    def insert_capsule(self, cap: EvidenceCapsule):
        with self.conn:
            self.conn.execute("""
                INSERT OR REPLACE INTO evidence_capsules (
                    capsule_id, incident_id, capsule_data
                ) VALUES (?, ?, ?)
            """, (
                str(cap.capsule_id),
                str(cap.incident_id),
                json.dumps(_to_json_serializable(asdict(cap)), default=_to_json_serializable)
            ))

    def get_all_incidents(self) -> List[Dict[str, Any]]:
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM incidents ORDER BY risk_score DESC, start_timestamp ASC")
        rows = cursor.fetchall()
        results = []
        for r in rows:
            d = dict(r)
            d["camera_ids"] = json.loads(d["camera_ids"]) if d.get("camera_ids") else []
            d["zone_ids"] = json.loads(d["zone_ids"]) if d.get("zone_ids") else []
            d["factor_breakdown"] = json.loads(d["factor_breakdown"]) if d.get("factor_breakdown") else {}
            d["contributing_factors"] = json.loads(d["contributing_factors"]) if d.get("contributing_factors") else []
            d["related_event_ids"] = json.loads(d["related_event_ids"]) if d.get("related_event_ids") else []
            d["involved_desks"] = json.loads(d["involved_desks"]) if d.get("involved_desks") else []
            d["is_multi_student"] = bool(d.get("is_multi_student", 0))
            results.append(d)
        return results

    def get_incident_by_id(self, incident_id: str) -> Optional[Dict[str, Any]]:
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM incidents WHERE incident_id = ?", (incident_id,))
        row = cursor.fetchone()
        if not row:
            return None
        d = dict(row)
        d["camera_ids"] = json.loads(d["camera_ids"]) if d.get("camera_ids") else []
        d["zone_ids"] = json.loads(d["zone_ids"]) if d.get("zone_ids") else []
        d["factor_breakdown"] = json.loads(d["factor_breakdown"]) if d.get("factor_breakdown") else {}
        d["contributing_factors"] = json.loads(d["contributing_factors"]) if d.get("contributing_factors") else []
        d["related_event_ids"] = json.loads(d["related_event_ids"]) if d.get("related_event_ids") else []
        d["involved_desks"] = json.loads(d["involved_desks"]) if d.get("involved_desks") else []
        d["is_multi_student"] = bool(d.get("is_multi_student", 0))
        return d

    def get_capsule_by_incident(self, incident_id: str) -> Optional[Dict[str, Any]]:
        cursor = self.conn.cursor()
        cursor.execute("SELECT capsule_data FROM evidence_capsules WHERE incident_id = ?", (incident_id,))
        row = cursor.fetchone()
        if row and row["capsule_data"]:
            return json.loads(row["capsule_data"])
        return None

    def log_audit(self, action: str, details: str = ""):
        with self.conn:
            self.conn.execute("INSERT INTO audit_logs (action, details) VALUES (?, ?)", (action, details))
