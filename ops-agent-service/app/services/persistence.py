from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from threading import Lock
from typing import Any


class RunRepository:
    def __init__(self, db_path: str) -> None:
        self.db_path = Path(db_path)
        self._lock = Lock()
        self._init_schema()

    def _init_schema(self) -> None:
        with sqlite3.connect(self.db_path) as connection:
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS analysis_runs (
                    run_id TEXT PRIMARY KEY,
                    thread_id TEXT NOT NULL,
                    request_type TEXT NOT NULL,
                    request_payload TEXT NOT NULL,
                    normalized_query TEXT,
                    metrics_evidence TEXT,
                    log_evidence TEXT,
                    gateway_evidence TEXT,
                    anomaly_assessment TEXT,
                    final_answer TEXT,
                    status TEXT NOT NULL,
                    started_at TEXT NOT NULL,
                    finished_at TEXT NOT NULL,
                    duration_ms INTEGER NOT NULL,
                    error_message TEXT
                )
                """
            )
            connection.commit()

    def save_run(self, **payload: Any) -> None:
        serialized = {
            key: json.dumps(value, ensure_ascii=False) if isinstance(value, (dict, list)) else value
            for key, value in payload.items()
        }
        with self._lock, sqlite3.connect(self.db_path) as connection:
            connection.execute(
                """
                INSERT OR REPLACE INTO analysis_runs (
                    run_id,
                    thread_id,
                    request_type,
                    request_payload,
                    normalized_query,
                    metrics_evidence,
                    log_evidence,
                    gateway_evidence,
                    anomaly_assessment,
                    final_answer,
                    status,
                    started_at,
                    finished_at,
                    duration_ms,
                    error_message
                ) VALUES (
                    :run_id,
                    :thread_id,
                    :request_type,
                    :request_payload,
                    :normalized_query,
                    :metrics_evidence,
                    :log_evidence,
                    :gateway_evidence,
                    :anomaly_assessment,
                    :final_answer,
                    :status,
                    :started_at,
                    :finished_at,
                    :duration_ms,
                    :error_message
                )
                """,
                serialized,
            )
            connection.commit()
