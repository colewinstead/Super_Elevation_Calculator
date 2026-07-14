import tempfile
import unittest
from pathlib import Path

import Super
from super_app import ModernSuperElevationUI
import super_pdf
import super_project
from super_lane import (
    build_lane_rows,
    lane_profile_points,
    parse_slope_percent,
    slope_at_station,
    slope_matches,
    station_for_slope,
)


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

    def test_lookup_slope_accepts_percent_and_decimal_inputs(self):
        self.assertEqual(parse_slope_percent("2"), 2.0)
        self.assertEqual(parse_slope_percent("2%"), 2.0)
        self.assertEqual(parse_slope_percent("0.02"), 2.0)
        self.assertEqual(parse_slope_percent("1"), 1.0)
        self.assertEqual(parse_slope_percent("0.5"), 0.5)

    def test_lookup_finds_calculated_rate_despite_float_noise(self):
        results = self.sample_results()
        points = lane_profile_points(results, "left")
        station = station_for_slope(points["right"], results["e"] * 100.0, results["reverse_crown_ft"])
        self.assertAlmostEqual(station, results["full_super_ft"])

    def test_lookup_returns_entering_and_exiting_slope_stations(self):
        results = self.sample_results()
        points = lane_profile_points(results, "left")
        matches = slope_matches(points["right"], 2.0)

        self.assertEqual(len(matches), 2)
        self.assertAlmostEqual(matches[0][0], matches[0][1])
        self.assertAlmostEqual(matches[1][0], matches[1][1])
        self.assertLess(matches[0][0], results["full_super_ft"])
        self.assertGreater(matches[1][0], results["full_super_out_ft"])
        self.assertAlmostEqual(slope_at_station(points["right"], matches[0][0]), 2.0)
        self.assertAlmostEqual(slope_at_station(points["right"], matches[1][0]), 2.0)

    def test_lookup_returns_full_super_station_range(self):
        results = self.sample_results()
        points = lane_profile_points(results, "left")
        matches = slope_matches(points["right"], results["e"] * 100.0)

        self.assertEqual(len(matches), 1)
        self.assertAlmostEqual(matches[0][0], results["full_super_ft"])
        self.assertAlmostEqual(matches[0][1], results["full_super_out_ft"])

    def test_nearest_lookup_can_select_exiting_occurrence(self):
        results = self.sample_results()
        points = lane_profile_points(results, "left")
        matches = slope_matches(points["right"], 2.0)
        station = station_for_slope(points["right"], 2.0, results["pnc_out_ft"])

        self.assertAlmostEqual(station, matches[-1][0])

    def test_calculation_preserves_alignment_range_for_lookup(self):
        station_range = (1000.0, 2000.0)
        equations = [{"staInternal": 1000.0, "staBack": 1000.0, "staAhead": 500.0}]
        results = Super.calculate_superelevation(
            "5+50", "7+50", "45", "1200", "centerline", "rural", "12", "2", "", "", "", "0.02", "", "",
            station_equations=equations,
            alignment_station_range=station_range,
        )
        self.assertEqual(results["alignment_station_range"], station_range)
        self.assertEqual(
            Super.civil_to_internal_station(
                Super.parse_station("5+50"), results["station_equations"], results["alignment_station_range"]
            ),
            1050.0,
        )

    def test_advanced_settings_validation_accepts_supported_values(self):
        ModernSuperElevationUI._validate_advanced_values(
            {
                "station_equations": "15+43.52=12+33.15;20+00=18+50",
                "alignment_station_range": "14+17.36,15+70.52",
                "e_manual": "0.06",
                "Lr_manual": "180",
                "Lt_manual": "60",
                "rel_grad": "0.005",
                "friction": "0.03",
                "normal_crown": "0.02",
            }
        )

    def test_advanced_settings_validation_rejects_invalid_values(self):
        with self.assertRaisesRegex(ValueError, "Relative gradient must be greater than zero"):
            ModernSuperElevationUI._validate_advanced_values({"rel_grad": "0"})
        with self.assertRaisesRegex(ValueError, "Station equations must use Back=Ahead format"):
            ModernSuperElevationUI._validate_advanced_values({"station_equations": "15+00 to 12+00"})
        with self.assertRaisesRegex(ValueError, "range end must be greater"):
            ModernSuperElevationUI._validate_advanced_values({"alignment_station_range": "20+00,10+00"})

    def test_landxml_stationing_skips_hidden_manual_validation(self):
        ModernSuperElevationUI._validate_advanced_values(
            {"station_equations": "unused invalid value", "alignment_station_range": "also unused"},
            validate_equations=False,
            validate_range=False,
        )

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
