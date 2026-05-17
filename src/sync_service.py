from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from zoneinfo import ZoneInfo

from calendar_client import GoogleCalendarClient
from config import DEFAULT_TIME_ZONE
from models import SkatingWindow
from sync_state import SyncAction, SyncState, SyncedEvent, plan_sync, summarize_actions


@dataclass(frozen=True)
class SyncResult:
    actions: list[SyncAction]

    @property
    def summary(self) -> dict[str, int]:
        return summarize_actions(self.actions)


def sync_calendar(
    windows: list[SkatingWindow],
    state: SyncState,
    calendar_client: GoogleCalendarClient,
    calendar_id: str,
    time_zone: str = DEFAULT_TIME_ZONE,
) -> SyncResult:
    state.initialize()
    actions = plan_sync(windows, state.get_all())
    synced_at = datetime.now(ZoneInfo(time_zone)).isoformat()

    for action in actions:
        if action.action == "create":
            _create_event(action, state, calendar_client, calendar_id, synced_at)
        elif action.action == "update":
            _update_event(action, state, calendar_client, calendar_id, synced_at)
        elif action.action == "keep":
            state.mark_seen(action.source_key, synced_at)
        elif action.action == "delete":
            _delete_event(action, state, calendar_client, calendar_id)
        else:
            raise ValueError(f"Unknown sync action: {action.action}")

    return SyncResult(actions)


def _create_event(
    action: SyncAction,
    state: SyncState,
    calendar_client: GoogleCalendarClient,
    calendar_id: str,
    synced_at: str,
) -> None:
    if action.window is None:
        raise ValueError("Create action requires a skating window.")

    event = calendar_client.create_event(calendar_id, action.window)
    state.upsert(
        SyncedEvent(
            source_key=action.source_key,
            google_event_id=event["id"],
            content_hash=action.window.content_hash(),
            last_seen_at=synced_at,
        )
    )


def _update_event(
    action: SyncAction,
    state: SyncState,
    calendar_client: GoogleCalendarClient,
    calendar_id: str,
    synced_at: str,
) -> None:
    if action.window is None or action.synced_event is None:
        raise ValueError("Update action requires a skating window and synced event.")

    event = calendar_client.update_event(calendar_id, action.synced_event.google_event_id, action.window)
    state.upsert(
        SyncedEvent(
            source_key=action.source_key,
            google_event_id=event["id"],
            content_hash=action.window.content_hash(),
            last_seen_at=synced_at,
        )
    )


def _delete_event(
    action: SyncAction,
    state: SyncState,
    calendar_client: GoogleCalendarClient,
    calendar_id: str,
) -> None:
    if action.synced_event is None:
        raise ValueError("Delete action requires a synced event.")

    calendar_client.delete_event(calendar_id, action.synced_event.google_event_id)
    state.delete(action.source_key)
