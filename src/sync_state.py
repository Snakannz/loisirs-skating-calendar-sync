from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from pathlib import Path

from models import SkatingWindow


@dataclass(frozen=True)
class SyncedEvent:
    source_key: str
    google_event_id: str
    content_hash: str
    last_seen_at: str


@dataclass(frozen=True)
class SyncAction:
    action: str
    source_key: str
    window: SkatingWindow | None = None
    synced_event: SyncedEvent | None = None


class SyncState:
    def __init__(self, db_path: Path) -> None:
        self.db_path = db_path

    def initialize(self) -> None:
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        with self._connect() as connection:
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS synced_events (
                    source_key TEXT PRIMARY KEY,
                    google_event_id TEXT NOT NULL,
                    content_hash TEXT NOT NULL,
                    last_seen_at TEXT NOT NULL
                )
                """
            )

    def get(self, source_key: str) -> SyncedEvent | None:
        with self._connect() as connection:
            row = connection.execute(
                """
                SELECT source_key, google_event_id, content_hash, last_seen_at
                FROM synced_events
                WHERE source_key = ?
                """,
                (source_key,),
            ).fetchone()
        return _row_to_event(row) if row else None

    def get_all(self) -> dict[str, SyncedEvent]:
        with self._connect() as connection:
            rows = connection.execute(
                """
                SELECT source_key, google_event_id, content_hash, last_seen_at
                FROM synced_events
                ORDER BY source_key
                """
            ).fetchall()
        events = [_row_to_event(row) for row in rows]
        return {event.source_key: event for event in events}

    def upsert(self, event: SyncedEvent) -> None:
        with self._connect() as connection:
            connection.execute(
                """
                INSERT INTO synced_events (source_key, google_event_id, content_hash, last_seen_at)
                VALUES (?, ?, ?, ?)
                ON CONFLICT(source_key) DO UPDATE SET
                    google_event_id = excluded.google_event_id,
                    content_hash = excluded.content_hash,
                    last_seen_at = excluded.last_seen_at
                """,
                (event.source_key, event.google_event_id, event.content_hash, event.last_seen_at),
            )

    def mark_seen(self, source_key: str, last_seen_at: str) -> None:
        with self._connect() as connection:
            connection.execute(
                """
                UPDATE synced_events
                SET last_seen_at = ?
                WHERE source_key = ?
                """,
                (last_seen_at, source_key),
            )

    def delete(self, source_key: str) -> None:
        with self._connect() as connection:
            connection.execute(
                """
                DELETE FROM synced_events
                WHERE source_key = ?
                """,
                (source_key,),
            )

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.db_path)
        connection.row_factory = sqlite3.Row
        return connection


def plan_sync(windows: list[SkatingWindow], synced_events: dict[str, SyncedEvent]) -> list[SyncAction]:
    actions: list[SyncAction] = []
    current_by_key = {window.source_key: window for window in windows}

    for source_key, window in current_by_key.items():
        synced_event = synced_events.get(source_key)
        if synced_event is None:
            actions.append(SyncAction("create", source_key, window=window))
        elif synced_event.content_hash != window.content_hash():
            actions.append(SyncAction("update", source_key, window=window, synced_event=synced_event))
        else:
            actions.append(SyncAction("keep", source_key, window=window, synced_event=synced_event))

    for source_key, synced_event in synced_events.items():
        if source_key not in current_by_key:
            actions.append(SyncAction("delete", source_key, synced_event=synced_event))

    return actions


def summarize_actions(actions: list[SyncAction]) -> dict[str, int]:
    summary = {"create": 0, "update": 0, "keep": 0, "delete": 0}
    for action in actions:
        summary[action.action] += 1
    return summary


def _row_to_event(row: sqlite3.Row) -> SyncedEvent:
    return SyncedEvent(
        source_key=row["source_key"],
        google_event_id=row["google_event_id"],
        content_hash=row["content_hash"],
        last_seen_at=row["last_seen_at"],
    )
