"""
audit_repository.py
===================
Thread-safe, in-memory repository for Phase 7 Audit Logging.

Guarantees:
- Thread-safe appending and querying using RLock.
- Bounded retention: Keeps a sliding window of the most recent 5,000 events.
- Immutable records: Does not provide update or delete methods.
- Clean query interface with filtering by actor, role, event type, status, and target.
"""

from collections import deque
from threading import RLock
from typing import List, Optional, Dict, Any
from datetime import datetime

from .audit_models import AuditEvent, AuditEventType, AuditStatus


class AuditLogRepository:
    """
    In-memory audit log store with bounded capacity and thread safety.
    """
    MAX_CAPACITY = 5000

    def __init__(self, max_capacity: int = MAX_CAPACITY):
        self._max_capacity = max_capacity
        self._lock = RLock()
        # Sliding window of audit records
        self._events: deque[AuditEvent] = deque(maxlen=self._max_capacity)

    def record_event(self, event: AuditEvent) -> AuditEvent:
        """
        Appends an immutable audit event to the repository.
        Enforces thread-safety and bounded sliding-window capacity.
        """
        if not isinstance(event, AuditEvent):
            raise TypeError("event must be an instance of AuditEvent.")
        with self._lock:
            self._events.append(event)
            return event

    def get_by_id(self, event_id: str) -> Optional[AuditEvent]:
        """
        Retrieves a single audit event by unique event_id.
        """
        if not event_id:
            return None
        clean_id = event_id.strip()
        with self._lock:
            for ev in self._events:
                if ev.event_id == clean_id:
                    return ev
            return None

    def query_logs(
        self,
        user_id: Optional[str] = None,
        role: Optional[str] = None,
        event_type: Optional[str] = None,
        status: Optional[str] = None,
        target_id: Optional[str] = None,
        from_date: Optional[str] = None,
        to_date: Optional[str] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[AuditEvent]:
        """
        Queries audit logs with optional filtering, returned in reverse chronological order (newest first).
        """
        with self._lock:
            # Snapshot list of events in reverse order (newest first)
            filtered = list(reversed(self._events))

        if user_id:
            clean_uid = user_id.strip()
            filtered = [e for e in filtered if e.actor_user_id == clean_uid or e.actor_username.lower() == clean_uid.lower()]

        if role:
            clean_role = role.strip().upper()
            filtered = [e for e in filtered if e.actor_role == clean_role]

        if event_type:
            clean_type = event_type.strip().upper()
            filtered = [e for e in filtered if e.event_type.value == clean_type or str(e.event_type) == clean_type]

        if status:
            clean_status = status.strip().upper()
            filtered = [e for e in filtered if e.status.value == clean_status or str(e.status) == clean_status]

        if target_id:
            clean_target = target_id.strip().upper()
            filtered = [e for e in filtered if e.target_id and clean_target in e.target_id.upper()]

        if from_date:
            filtered = [e for e in filtered if e.timestamp >= from_date]

        if to_date:
            filtered = [e for e in filtered if e.timestamp <= to_date]

        return filtered[offset : offset + limit]

    def count_logs(
        self,
        user_id: Optional[str] = None,
        role: Optional[str] = None,
        event_type: Optional[str] = None,
        status: Optional[str] = None,
        target_id: Optional[str] = None,
        from_date: Optional[str] = None,
        to_date: Optional[str] = None,
    ) -> int:
        """
        Counts matching audit logs based on criteria.
        """
        with self._lock:
            filtered = list(self._events)

        if user_id:
            clean_uid = user_id.strip()
            filtered = [e for e in filtered if e.actor_user_id == clean_uid or e.actor_username.lower() == clean_uid.lower()]

        if role:
            clean_role = role.strip().upper()
            filtered = [e for e in filtered if e.actor_role == clean_role]

        if event_type:
            clean_type = event_type.strip().upper()
            filtered = [e for e in filtered if e.event_type.value == clean_type or str(e.event_type) == clean_type]

        if status:
            clean_status = status.strip().upper()
            filtered = [e for e in filtered if e.status.value == clean_status or str(e.status) == clean_status]

        if target_id:
            clean_target = target_id.strip().upper()
            filtered = [e for e in filtered if e.target_id and clean_target in e.target_id.upper()]

        if from_date:
            filtered = [e for e in filtered if e.timestamp >= from_date]

        if to_date:
            filtered = [e for e in filtered if e.timestamp <= to_date]

        return len(filtered)

    def get_total_count(self) -> int:
        with self._lock:
            return len(self._events)

    def clear(self) -> None:
        """Clears all audit logs. Intended for test isolation."""
        with self._lock:
            self._events.clear()


def create_demo_audit_repository() -> AuditLogRepository:
    """
    Factory creating a fresh AuditLogRepository.
    """
    return AuditLogRepository()
