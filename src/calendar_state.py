from __future__ import annotations

from dataclasses import dataclass

from calendar_client import GoogleCalendarClient
from sync_state import SyncedEvent


@dataclass
class CalendarSyncState:
    calendar_client: GoogleCalendarClient
    calendar_id: str
    time_min: str | None = None

    def initialize(self) -> None:
        return None

    def get_all(self) -> dict[str, SyncedEvent]:
        events = self.calendar_client.list_managed_events(self.calendar_id, self.time_min)
        synced_events = {}

        for event in events:
            private = (event.get("extendedProperties") or {}).get("private") or {}
            source_key = private.get("source_key")
            content_hash = private.get("content_hash")
            if not source_key or not content_hash:
                continue

            synced_events[source_key] = SyncedEvent(
                source_key=source_key,
                google_event_id=event["id"],
                content_hash=content_hash,
                last_seen_at=private.get("last_seen_at") or event.get("updated") or "",
            )

        return synced_events

    def upsert(self, event: SyncedEvent) -> None:
        return None

    def mark_seen(self, source_key: str, last_seen_at: str) -> None:
        return None

    def delete(self, source_key: str) -> None:
        return None
