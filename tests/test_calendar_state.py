import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from calendar_state import CalendarSyncState


class FakeCalendarClient:
    def __init__(self, events):
        self.events = events
        self.calls = []

    def list_managed_events(self, calendar_id, time_min=None):
        self.calls.append((calendar_id, time_min))
        return self.events


class CalendarSyncStateTest(unittest.TestCase):
    def test_reads_synced_events_from_calendar_extended_properties(self) -> None:
        calendar_client = FakeCalendarClient(
            [
                {
                    "id": "event-1",
                    "updated": "2026-05-17T10:00:00Z",
                    "extendedProperties": {
                        "private": {
                            "source": "loisirs-montreal",
                            "source_key": "loisirs-mtl|1",
                            "content_hash": "hash-1",
                        }
                    },
                },
                {
                    "id": "event-2",
                    "extendedProperties": {"private": {"source": "loisirs-montreal"}},
                },
            ]
        )
        state = CalendarSyncState(calendar_client, "calendar-1", "2026-05-17T00:00:00-04:00")

        synced_events = state.get_all()

        self.assertEqual(list(synced_events.keys()), ["loisirs-mtl|1"])
        self.assertEqual(synced_events["loisirs-mtl|1"].google_event_id, "event-1")
        self.assertEqual(synced_events["loisirs-mtl|1"].content_hash, "hash-1")
        self.assertEqual(calendar_client.calls, [("calendar-1", "2026-05-17T00:00:00-04:00")])


if __name__ == "__main__":
    unittest.main()
