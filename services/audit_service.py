"""Audit logging service for traceability and compliance."""

import json
import logging
from datetime import datetime
from typing import Optional, Dict, Any

from services.db import get_db

logger = logging.getLogger(__name__)


class AuditService:
    def __init__(self):
        self.db = get_db()

    def log(
        self,
        action: str,
        entity_type: str,
        entity_id: str,
        actor: str = "system",
        details: Optional[Dict[str, Any]] = None,
    ):
        self.db.insert("audit_log", {
            "timestamp": datetime.utcnow().isoformat(),
            "action": action,
            "entity_type": entity_type,
            "entity_id": entity_id,
            "actor": actor,
            "details": json.dumps(details or {}),
        })

    def log_model_call(
        self,
        provider: str,
        model_name: str,
        action: str,
        patient_id: str = "",
        input_tokens: int = 0,
        output_tokens: int = 0,
        latency_ms: float = 0,
    ):
        self.log(
            action=f"model_call:{action}",
            entity_type="model_invocation",
            entity_id=patient_id or "global",
            details={
                "provider": provider,
                "model_name": model_name,
                "input_tokens": input_tokens,
                "output_tokens": output_tokens,
                "latency_ms": round(latency_ms, 1),
            },
        )

    def get_recent_logs(self, limit: int = 50, entity_type: Optional[str] = None):
        if entity_type:
            return self.db.fetch_all(
                "SELECT * FROM audit_log WHERE entity_type = ? ORDER BY timestamp DESC LIMIT ?",
                (entity_type, limit),
            )
        return self.db.fetch_all(
            "SELECT * FROM audit_log ORDER BY timestamp DESC LIMIT ?",
            (limit,),
        )
