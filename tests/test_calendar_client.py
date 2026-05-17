import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from calendar_client import build_smoke_test_window, window_to_event


class CalendarClientTest(unittest.TestCase):
    def test_window_to_event_adds_calendar_metadata(self) -> None:
        window = build_smoke_test_window()

        event = window_to_event(window)

        self.assertEqual(event["summary"], "Test - Patinage Montréal sync")
        self.assertEqual(event["start"]["timeZone"], "America/Toronto")
        private = event["extendedProperties"]["private"]
        self.assertEqual(private["source"], "loisirs-montreal")
        self.assertEqual(private["source_key"], window.source_key)
        self.assertEqual(len(private["content_hash"]), 64)


if __name__ == "__main__":
    unittest.main()
