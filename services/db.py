"""Database abstraction layer.

In Databricks mode: uses databricks-sql-connector against Delta Lake.
In demo/local mode: uses SQLite for zero-dependency testing.
"""

import json
import os
import sqlite3
import logging
from contextlib import contextmanager
from datetime import date, datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

_DEMO_DB_PATH = Path(__file__).parent.parent / "data" / "demo.db"
_connection: Optional[sqlite3.Connection] = None


def _serialize(val: Any) -> Any:
    if isinstance(val, (date, datetime)):
        return val.isoformat()
    if isinstance(val, (list, dict)):
        return json.dumps(val, default=str)
    return val


def _row_to_dict(cursor: sqlite3.Cursor, row: tuple) -> dict:
    return {desc[0]: row[i] for i, desc in enumerate(cursor.description)}


def get_demo_connection() -> sqlite3.Connection:
    global _connection
    if _connection is None:
        _DEMO_DB_PATH.parent.mkdir(parents=True, exist_ok=True)
        _connection = sqlite3.connect(str(_DEMO_DB_PATH), check_same_thread=False)
        _connection.row_factory = _row_to_dict
        _connection.execute("PRAGMA journal_mode=WAL")
        _connection.execute("PRAGMA foreign_keys=ON")
        _init_demo_tables(_connection)
    return _connection


def _init_demo_tables(conn: sqlite3.Connection):
    conn.executescript("""
    CREATE TABLE IF NOT EXISTS patients (
        patient_id TEXT PRIMARY KEY,
        asha_worker_id TEXT DEFAULT '',
        full_name TEXT NOT NULL,
        age INTEGER NOT NULL,
        village TEXT NOT NULL,
        phone TEXT DEFAULT '',
        consent_status TEXT DEFAULT 'granted',
        language_preference TEXT DEFAULT 'hi',
        lmp_date TEXT,
        edd_date TEXT,
        gestational_weeks INTEGER,
        trimester TEXT,
        gravida INTEGER DEFAULT 1,
        parity INTEGER DEFAULT 0,
        known_conditions TEXT DEFAULT '[]',
        current_medications TEXT DEFAULT '[]',
        blood_group TEXT DEFAULT '',
        height_cm REAL,
        risk_band TEXT DEFAULT 'NORMAL',
        risk_score REAL DEFAULT 0.0,
        created_at TEXT,
        updated_at TEXT
    );

    CREATE TABLE IF NOT EXISTS asha_workers (
        worker_id TEXT PRIMARY KEY,
        full_name TEXT NOT NULL,
        phone TEXT DEFAULT '',
        village TEXT NOT NULL,
        language TEXT DEFAULT 'hi'
    );

    CREATE TABLE IF NOT EXISTS observations (
        observation_id TEXT PRIMARY KEY,
        patient_id TEXT NOT NULL,
        obs_date TEXT,
        hemoglobin REAL,
        systolic_bp INTEGER,
        diastolic_bp INTEGER,
        blood_sugar_fasting REAL,
        blood_sugar_pp REAL,
        weight_kg REAL,
        urine_protein TEXT,
        urine_sugar TEXT,
        edema TEXT,
        fetal_movement TEXT,
        fetal_heart_rate INTEGER,
        fundal_height_cm REAL,
        pallor TEXT,
        source_report_id TEXT,
        notes TEXT DEFAULT '',
        FOREIGN KEY (patient_id) REFERENCES patients(patient_id)
    );

    CREATE TABLE IF NOT EXISTS reports (
        report_id TEXT PRIMARY KEY,
        patient_id TEXT NOT NULL,
        file_path TEXT DEFAULT '',
        file_type TEXT DEFAULT '',
        report_date TEXT,
        extracted_json TEXT DEFAULT '{}',
        extracted_text TEXT DEFAULT '',
        extractor_confidence REAL DEFAULT 0.0,
        abnormality_flags TEXT DEFAULT '[]',
        created_at TEXT,
        FOREIGN KEY (patient_id) REFERENCES patients(patient_id)
    );

    CREATE TABLE IF NOT EXISTS encounters (
        encounter_id TEXT PRIMARY KEY,
        patient_id TEXT NOT NULL,
        encounter_time TEXT,
        modality TEXT DEFAULT 'text',
        source_language TEXT DEFAULT 'hi',
        original_text TEXT DEFAULT '',
        normalized_text TEXT DEFAULT '',
        translated_text TEXT DEFAULT '',
        summary TEXT DEFAULT '',
        symptoms TEXT DEFAULT '[]',
        extracted_health_updates TEXT DEFAULT '{}',
        ai_response TEXT DEFAULT '',
        translated_response TEXT DEFAULT '',
        retrieved_chunks TEXT DEFAULT '[]',
        risk_snapshot TEXT DEFAULT '',
        red_flag INTEGER DEFAULT 0,
        escalation_status TEXT DEFAULT 'none',
        FOREIGN KEY (patient_id) REFERENCES patients(patient_id)
    );

    CREATE TABLE IF NOT EXISTS schedules (
        schedule_id TEXT PRIMARY KEY,
        patient_id TEXT NOT NULL,
        visit_type TEXT,
        visit_number INTEGER,
        due_date TEXT,
        suggested_slot TEXT DEFAULT '',
        facility_name TEXT DEFAULT '',
        tests_due TEXT DEFAULT '[]',
        status TEXT DEFAULT 'scheduled',
        is_pmsma_aligned INTEGER DEFAULT 0,
        escalation_flag INTEGER DEFAULT 0,
        notes TEXT DEFAULT '',
        FOREIGN KEY (patient_id) REFERENCES patients(patient_id)
    );

    CREATE TABLE IF NOT EXISTS alerts (
        alert_id TEXT PRIMARY KEY,
        patient_id TEXT NOT NULL,
        severity TEXT,
        alert_type TEXT,
        reason_codes TEXT DEFAULT '[]',
        message TEXT DEFAULT '',
        created_at TEXT,
        resolved_at TEXT,
        active INTEGER DEFAULT 1,
        FOREIGN KEY (patient_id) REFERENCES patients(patient_id)
    );

    CREATE TABLE IF NOT EXISTS ration_plans (
        ration_id TEXT PRIMARY KEY,
        patient_id TEXT NOT NULL,
        week_start TEXT,
        trimester TEXT,
        calorie_target INTEGER DEFAULT 0,
        protein_target_g INTEGER DEFAULT 0,
        recommendation_json TEXT DEFAULT '{}',
        supplements TEXT DEFAULT '[]',
        special_adjustments TEXT DEFAULT '[]',
        rationale TEXT DEFAULT '',
        rule_basis TEXT DEFAULT '[]',
        approval_status TEXT DEFAULT 'recommended',
        distributed INTEGER DEFAULT 0,
        FOREIGN KEY (patient_id) REFERENCES patients(patient_id)
    );

    CREATE TABLE IF NOT EXISTS appointments (
        appointment_id TEXT PRIMARY KEY,
        patient_id TEXT NOT NULL,
        facility_name TEXT,
        facility_type TEXT DEFAULT 'PHC',
        scheduled_datetime TEXT,
        appointment_type TEXT DEFAULT 'ANC',
        status TEXT DEFAULT 'booked',
        notes TEXT DEFAULT '',
        FOREIGN KEY (patient_id) REFERENCES patients(patient_id)
    );

    CREATE TABLE IF NOT EXISTS guidelines (
        guideline_id TEXT PRIMARY KEY,
        source_name TEXT,
        category TEXT,
        language TEXT DEFAULT 'en',
        title TEXT,
        chunk_text TEXT,
        source_url TEXT DEFAULT '',
        effective_date TEXT
    );

    CREATE TABLE IF NOT EXISTS medical_thresholds (
        threshold_id TEXT PRIMARY KEY,
        parameter_name TEXT NOT NULL,
        pregnancy_stage TEXT,
        normal_min REAL,
        normal_max REAL,
        warning_low REAL,
        warning_high REAL,
        critical_low REAL,
        critical_high REAL,
        unit TEXT DEFAULT '',
        source_ref TEXT DEFAULT ''
    );

    CREATE TABLE IF NOT EXISTS nutrition_rules (
        rule_id TEXT PRIMARY KEY,
        trimester TEXT,
        condition_tag TEXT DEFAULT '',
        calorie_target INTEGER DEFAULT 0,
        protein_target_g INTEGER DEFAULT 0,
        iron_mg REAL DEFAULT 0,
        calcium_mg REAL DEFAULT 0,
        folic_acid_mg REAL DEFAULT 0,
        supplement_recommendation TEXT DEFAULT '[]',
        food_recommendations TEXT DEFAULT '[]',
        foods_to_avoid TEXT DEFAULT '[]',
        source_ref TEXT DEFAULT ''
    );

    CREATE TABLE IF NOT EXISTS schedule_rules (
        rule_id TEXT PRIMARY KEY,
        pregnancy_stage TEXT,
        visit_type TEXT,
        visit_number INTEGER,
        week_start INTEGER,
        week_end INTEGER,
        tests_due TEXT DEFAULT '[]',
        interval_days INTEGER DEFAULT 28,
        escalation_condition TEXT DEFAULT '',
        source_ref TEXT DEFAULT ''
    );

    CREATE TABLE IF NOT EXISTS facilities (
        facility_id TEXT PRIMARY KEY,
        name TEXT NOT NULL,
        facility_type TEXT DEFAULT 'PHC',
        village TEXT DEFAULT '',
        district TEXT DEFAULT '',
        phone TEXT DEFAULT '',
        available_slots TEXT DEFAULT '[]'
    );

    CREATE TABLE IF NOT EXISTS guideline_chunks (
        chunk_id TEXT PRIMARY KEY,
        guideline_id TEXT,
        chunk_index INTEGER,
        chunk_text TEXT,
        source_name TEXT,
        category TEXT,
        embedding TEXT DEFAULT ''
    );

    CREATE TABLE IF NOT EXISTS patient_memory_chunks (
        chunk_id TEXT PRIMARY KEY,
        patient_id TEXT,
        chunk_type TEXT,
        chunk_text TEXT,
        source_date TEXT,
        embedding TEXT DEFAULT ''
    );

    CREATE TABLE IF NOT EXISTS audit_log (
        log_id INTEGER PRIMARY KEY AUTOINCREMENT,
        timestamp TEXT,
        action TEXT,
        entity_type TEXT,
        entity_id TEXT,
        actor TEXT DEFAULT 'system',
        details TEXT DEFAULT '{}'
    );

    CREATE TABLE IF NOT EXISTS dashboard_snapshots (
        snapshot_id TEXT PRIMARY KEY,
        village TEXT,
        snapshot_date TEXT,
        snapshot_type TEXT DEFAULT 'daily',
        data_json TEXT DEFAULT '{}'
    );
    """)
    conn.commit()


class DemoDB:
    """Lightweight wrapper around SQLite for demo mode."""

    def __init__(self):
        self.conn = get_demo_connection()

    def execute(self, sql: str, params: tuple = ()) -> sqlite3.Cursor:
        return self.conn.execute(sql, params)

    def execute_many(self, sql: str, params_list: list):
        self.conn.executemany(sql, params_list)
        self.conn.commit()

    def fetch_one(self, sql: str, params: tuple = ()) -> Optional[dict]:
        cur = self.conn.execute(sql, params)
        row = cur.fetchone()
        return row

    def fetch_all(self, sql: str, params: tuple = ()) -> List[dict]:
        cur = self.conn.execute(sql, params)
        return cur.fetchall()

    def insert(self, table: str, data: dict) -> str:
        cols = list(data.keys())
        vals = [_serialize(data[c]) for c in cols]
        placeholders = ", ".join(["?"] * len(cols))
        col_str = ", ".join(cols)
        self.conn.execute(
            f"INSERT OR REPLACE INTO {table} ({col_str}) VALUES ({placeholders})",
            tuple(vals),
        )
        self.conn.commit()
        return data.get(f"{table[:-1]}_id", data.get("patient_id", ""))

    def update(self, table: str, key_col: str, key_val: str, updates: dict):
        sets = ", ".join([f"{k} = ?" for k in updates.keys()])
        vals = [_serialize(v) for v in updates.values()] + [key_val]
        self.conn.execute(f"UPDATE {table} SET {sets} WHERE {key_col} = ?", tuple(vals))
        self.conn.commit()

    def delete(self, table: str, key_col: str, key_val: str):
        self.conn.execute(f"DELETE FROM {table} WHERE {key_col} = ?", (key_val,))
        self.conn.commit()

    def count(self, table: str, where: str = "", params: tuple = ()) -> int:
        sql = f"SELECT COUNT(*) as cnt FROM {table}"
        if where:
            sql += f" WHERE {where}"
        row = self.fetch_one(sql, params)
        return row["cnt"] if row else 0


def get_db() -> DemoDB:
    """Factory: returns a DemoDB for demo mode, extendable to Databricks SQL."""
    return DemoDB()
