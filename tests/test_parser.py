import json
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from parser import parse_skating_windows


class ParserTest(unittest.TestCase):
    def test_parse_timed_windows_and_skip_untimed_activity(self) -> None:
        fixture = ROOT / "tests" / "fixtures" / "loisirs_response.json"
        response = json.loads(fixture.read_text(encoding="utf-8"))

        windows = parse_skating_windows(response)

        self.assertEqual(len(windows), 1)
        window = windows[0]
        self.assertEqual(window.activity_id, 185408)
        self.assertEqual(window.start, "2026-05-20T12:00:00-04:00")
        self.assertEqual(window.end, "2026-05-20T14:00:00-04:00")
        self.assertEqual(
            window.source_key,
            "loisirs-mtl|185408|2026-05-20|12:00:00|14:00:00|Auditorium de Verdun",
        )
        self.assertIn("Loisirs Montréal", window.description)


if __name__ == "__main__":
    unittest.main()

