import json
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from parser import (
    FIGURE_SKATING,
    PRIMARY,
    PUBLIC_SKATE,
    SECONDARY,
    parse_skating_windows,
    parse_untimed_activities,
)


class ParserTest(unittest.TestCase):
    def test_parse_timed_windows_and_skip_untimed_activity(self) -> None:
        fixture = ROOT / "tests" / "fixtures" / "loisirs_response.json"
        response = json.loads(fixture.read_text(encoding="utf-8"))

        windows = parse_skating_windows(response)

        self.assertEqual(len(windows), 5)
        window = windows[0]
        self.assertEqual(window.activity_id, 185408)
        self.assertEqual(window.kind, PUBLIC_SKATE)
        self.assertEqual(window.importance, SECONDARY)
        self.assertEqual(window.start, "2026-05-20T12:00:00-04:00")
        self.assertEqual(window.end, "2026-05-20T14:00:00-04:00")
        self.assertEqual(
            window.source_key,
            "loisirs-mtl|185408|2026-05-20|12:00:00|14:00:00|Auditorium de Verdun",
        )
        self.assertIn("Loisirs Montréal", window.description)

    def test_classifies_figure_skating_as_primary(self) -> None:
        fixture = ROOT / "tests" / "fixtures" / "loisirs_response.json"
        response = json.loads(fixture.read_text(encoding="utf-8"))

        windows = parse_skating_windows(response)
        window = next(window for window in windows if window.activity_id == 190000)

        self.assertEqual(window.kind, FIGURE_SKATING)
        self.assertEqual(window.importance, PRIMARY)

    def test_expands_weekly_recurring_schedule(self) -> None:
        fixture = ROOT / "tests" / "fixtures" / "loisirs_response.json"
        response = json.loads(fixture.read_text(encoding="utf-8"))

        windows = [
            window for window in parse_skating_windows(response)
            if window.activity_id == 190001
        ]

        self.assertEqual([window.start[:10] for window in windows], ["2026-06-05", "2026-06-12", "2026-06-19"])

    def test_keeps_untimed_figure_skating_activity_visible(self) -> None:
        fixture = ROOT / "tests" / "fixtures" / "loisirs_response.json"
        response = json.loads(fixture.read_text(encoding="utf-8"))

        activities = parse_untimed_activities(response)
        activity = next(activity for activity in activities if activity.activity_id == 182078)

        self.assertEqual(activity.kind, FIGURE_SKATING)
        self.assertEqual(activity.importance, PRIMARY)
        self.assertEqual(activity.start_date, "2026-03-21")
        self.assertEqual(activity.end_date, "2026-05-31")


if __name__ == "__main__":
    unittest.main()
