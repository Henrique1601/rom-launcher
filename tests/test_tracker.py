"""Testes unitários para o Playtime Tracker e Scraper."""

import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from rom_cli.core.tracker import PlaytimeTracker
from rom_cli.core.scraper import sanitize_filename_for_url, get_cover_path


class TestTrackerAndScraper(unittest.TestCase):
    def test_tracker_record_session(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            f = Path(tmp_dir) / "playtime.json"
            tracker = PlaytimeTracker(storage_file=f)

            tracker.record_session("Super Mario World", 3600)  # 1 hora
            stats = tracker.get_stats("Super Mario World")

            self.assertEqual(stats["total_seconds"], 3600)
            self.assertEqual(stats["sessions_count"], 1)
            self.assertEqual(tracker.format_playtime("Super Mario World"), "1h 0m")

    def test_sanitize_filename_for_url(self):
        raw = "Pokemon - FireRed Version (USA, Europe) [v1.1]"
        cleaned = sanitize_filename_for_url(raw)
        self.assertEqual(cleaned, "Pokemon - FireRed Version")

    def test_get_cover_path(self):
        p = get_cover_path("Zelda: Breath of the Wild", "switch")
        self.assertTrue(str(p).endswith(".png"))
        self.assertNotIn(":", p.name)


if __name__ == "__main__":
    unittest.main()
