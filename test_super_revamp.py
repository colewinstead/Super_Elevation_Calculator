import tempfile
import unittest
from pathlib import Path

import Super
import super_pdf
import super_project
from super_lane import build_lane_rows, lane_profile_points, slope_at_station


class SuperRevampTests(unittest.TestCase):
    def sample_results(self):
        return Super.calculate_superelevation(
            "10+00",
            "12+00",
            "45",
            "1200",
            "centerline",
            "rural",
            "12",
            "2",
            "",
            "",
            "",
            "0.02",
            "",
            "",
        )

    def test_station_round_trip(self):
        self.assertEqual(Super.parse_station("10+50.25"), 1050.25)
        self.assertEqual(Super.format_station(1050.25), "10+50.250")

    def test_lane_rows_and_profile_are_shared(self):
        results = self.sample_results()
        left_rows, right_rows = build_lane_rows(results, "left")
        self.assertTrue(left_rows)
        self.assertTrue(right_rows)
        points = lane_profile_points(results, "left")
        self.assertIn("left", points)
        self.assertIsInstance(slope_at_station(points["left"], Super.parse_station("10+00")), float)

    def test_stamp_selection_preserved(self):
        rural = self.sample_results()
        self.assertEqual(super_pdf.select_stamps(rural), ["SE-2A", "SE-3A"])
        local = Super.calculate_superelevation(
            "10+00", "", "35", "700", "centerline", "local", "12", "2", "", "", "", "0.02", "", ""
        )
        self.assertEqual(super_pdf.select_stamps(local), ["SE-1"])

    def test_project_v1_loads_and_saves_v2(self):
        data = {
            "version": 1,
            "vars": {"pc": "10+00"},
            "curves": [{"results": self.sample_results(), "meta": {"curve_name": "A"}}],
        }
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "project.json"
            super_project.save_project(path, data)
            loaded = super_project.load_project(path)
        self.assertEqual(loaded["version"], 2)
        self.assertEqual(len(loaded["curves"]), 1)


if __name__ == "__main__":
    unittest.main()
