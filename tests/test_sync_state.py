import sys
import tempfile
import unittest
from dataclasses import replace
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from calendar_client import build_smoke_test_window
from sync_state import SyncState, SyncedEvent, plan_sync, summarize_actions


class SyncStateTest(unittest.TestCase):
    def test_stores_updates_and_deletes_synced_events(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            db_path = Path(directory) / "sync.sqlite"
            state = SyncState(db_path)
            state.initialize()

            event = SyncedEvent(
                source_key="loisirs-mtl|1",
                google_event_id="google-1",
                content_hash="hash-1",
                last_seen_at="2026-05-17T10:00:00-04:00",
            )
            state.upsert(event)

            self.assertEqual(state.get("loisirs-mtl|1"), event)

            updated = SyncedEvent(
                source_key="loisirs-mtl|1",
                google_event_id="google-1",
                content_hash="hash-2",
                last_seen_at="2026-05-17T11:00:00-04:00",
            )
            state.upsert(updated)
            self.assertEqual(state.get_all(), {"loisirs-mtl|1": updated})

            state.mark_seen("loisirs-mtl|1", "2026-05-17T12:00:00-04:00")
            self.assertEqual(state.get("loisirs-mtl|1").last_seen_at, "2026-05-17T12:00:00-04:00")

            state.delete("loisirs-mtl|1")
            self.assertEqual(state.get_all(), {})

    def test_plan_sync_compares_current_windows_to_saved_state(self) -> None:
        current = build_smoke_test_window()
        changed = replace(current, source_key="loisirs-mtl|changed", title="Changed title")
        removed = SyncedEvent(
            source_key="loisirs-mtl|removed",
            google_event_id="google-removed",
            content_hash="old-hash",
            last_seen_at="2026-05-17T10:00:00-04:00",
        )

        synced_events = {
            current.source_key: SyncedEvent(
                source_key=current.source_key,
                google_event_id="google-current",
                content_hash=current.content_hash(),
                last_seen_at="2026-05-17T10:00:00-04:00",
            ),
            changed.source_key: SyncedEvent(
                source_key=changed.source_key,
                google_event_id="google-changed",
                content_hash="old-hash",
                last_seen_at="2026-05-17T10:00:00-04:00",
            ),
            removed.source_key: removed,
        }

        actions = plan_sync([current, changed], synced_events)

        self.assertEqual(summarize_actions(actions), {"create": 0, "update": 1, "keep": 1, "delete": 1})

    def test_plan_sync_finds_new_window(self) -> None:
        current = build_smoke_test_window()

        actions = plan_sync([current], {})

        self.assertEqual(summarize_actions(actions), {"create": 1, "update": 0, "keep": 0, "delete": 0})


if __name__ == "__main__":
    unittest.main()
