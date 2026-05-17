import sys
import tempfile
import unittest
from dataclasses import replace
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from calendar_client import build_smoke_test_window
from sync_service import sync_calendar
from sync_state import SyncState, SyncedEvent


class FakeCalendarClient:
    def __init__(self) -> None:
        self.created = []
        self.updated = []
        self.deleted = []
        self.next_id = 1

    def create_event(self, calendar_id, window):
        event = {"id": f"event-{self.next_id}"}
        self.next_id += 1
        self.created.append((calendar_id, window, event))
        return event

    def update_event(self, calendar_id, event_id, window):
        self.updated.append((calendar_id, event_id, window))
        return {"id": event_id}

    def delete_event(self, calendar_id, event_id):
        self.deleted.append((calendar_id, event_id))


class SyncServiceTest(unittest.TestCase):
    def test_first_sync_creates_event_and_second_sync_keeps_it(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            state = SyncState(Path(directory) / "sync.sqlite")
            calendar_client = FakeCalendarClient()
            window = build_smoke_test_window()

            first = sync_calendar([window], state, calendar_client, "calendar-1")
            second = sync_calendar([window], state, calendar_client, "calendar-1")

            self.assertEqual(first.summary, {"create": 1, "update": 0, "keep": 0, "delete": 0})
            self.assertEqual(second.summary, {"create": 0, "update": 0, "keep": 1, "delete": 0})
            self.assertEqual(len(calendar_client.created), 1)
            self.assertEqual(state.get(window.source_key).google_event_id, "event-1")

    def test_sync_updates_changed_window(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            state = SyncState(Path(directory) / "sync.sqlite")
            calendar_client = FakeCalendarClient()
            original = build_smoke_test_window()
            changed = replace(original, title="Changed title")

            sync_calendar([original], state, calendar_client, "calendar-1")
            result = sync_calendar([changed], state, calendar_client, "calendar-1")

            self.assertEqual(result.summary, {"create": 0, "update": 1, "keep": 0, "delete": 0})
            self.assertEqual(calendar_client.updated[0][1], "event-1")
            self.assertEqual(state.get(original.source_key).content_hash, changed.content_hash())

    def test_sync_deletes_missing_window(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            state = SyncState(Path(directory) / "sync.sqlite")
            state.initialize()
            state.upsert(
                SyncedEvent(
                    source_key="loisirs-mtl|missing",
                    google_event_id="event-missing",
                    content_hash="old-hash",
                    last_seen_at="2026-05-17T10:00:00-04:00",
                )
            )
            calendar_client = FakeCalendarClient()

            result = sync_calendar([], state, calendar_client, "calendar-1")

            self.assertEqual(result.summary, {"create": 0, "update": 0, "keep": 0, "delete": 1})
            self.assertEqual(calendar_client.deleted, [("calendar-1", "event-missing")])
            self.assertEqual(state.get_all(), {})


if __name__ == "__main__":
    unittest.main()
