import math
import unittest

from calculators.catalog import browser_runtime_manifest, calculator_catalog
from calculators.crushed_stone_base.engine import ENGINE_VERSION, calculate
from calculators.crushed_stone_base.service import dispatch_safe


class CrushedStoneBaseTests(unittest.TestCase):
    def test_baseline_segment(self):
        result = calculate(
            [{
                "name": "Mainline", "length_ft": 100, "pavement_width_ft": 20,
                "shoulder_width_ft": 5, "shoulder_slope_percent": 0,
                "side_slope_h_to_v": 4, "thickness_in": 6,
            }],
            1.6875,
            0,
        )
        segment = result["segments"][0]
        self.assertEqual(segment["keyout_run_per_side_ft"], 2.0)
        self.assertEqual(segment["equivalent_width_per_side_ft"], 1.0)
        self.assertEqual(segment["equivalent_width_both_sides_ft"], 2.0)
        self.assertEqual(segment["effective_base_width_ft"], 32.0)
        self.assertEqual(result["totals"]["cubic_feet"], 1600.0)
        self.assertEqual(result["totals"]["base_tons"], 100.0)
        self.assertEqual(result["totals"]["order_tons"], 100.0)

    def test_realistic_four_percent_shoulder_and_six_to_one_side_slope(self):
        result = calculate([{
            "length_ft": 100, "pavement_width_ft": 20, "shoulder_width_ft": 6,
            "shoulder_slope_percent": 4, "side_slope_h_to_v": 6, "thickness_in": 6,
        }])
        segment = result["segments"][0]
        expected_run = 0.5 / (1.0 / 6.0 - 0.04)
        self.assertTrue(math.isclose(segment["keyout_run_per_side_ft"], expected_run))
        self.assertTrue(math.isclose(segment["equivalent_width_per_side_ft"], expected_run / 2.0))
        self.assertTrue(math.isclose(segment["effective_base_width_ft"], 32.0 + expected_run))

    def test_multiple_segments_and_waste(self):
        result = calculate(
            [
                {"name": "A", "length_ft": 100.5, "pavement_width_ft": 20, "shoulder_width_ft": 5, "shoulder_slope_percent": 0, "side_slope_h_to_v": 4, "thickness_in": 6},
                {"name": "B", "length_ft": 50, "pavement_width_ft": 12.5, "shoulder_width_ft": 4, "shoulder_slope_percent": 0, "side_slope_h_to_v": 4, "thickness_in": 8},
            ],
            1.6875,
            5,
        )
        expected_cf = 100.5 * 32 * 6 / 12 + 50 * (12.5 + 8 + 8 / 3) * 8 / 12
        expected_tons = expected_cf / 27 * 1.6875
        self.assertTrue(math.isclose(result["totals"]["cubic_feet"], expected_cf))
        self.assertTrue(math.isclose(result["totals"]["base_tons"], expected_tons))
        self.assertTrue(math.isclose(result["totals"]["waste_tons"], expected_tons * 0.05))
        self.assertTrue(math.isclose(result["totals"]["order_tons"], expected_tons * 1.05))

    def test_service_returns_json_safe_result(self):
        response = dispatch_safe(
            "calculate",
            '{"segments":[{"length_ft":100,"pavement_width_ft":20,"shoulder_width_ft":5,"shoulder_slope_percent":0,"side_slope_h_to_v":4,"thickness_in":6}],"tons_per_cubic_yard":1.6875,"waste_percent":0}',
        )
        self.assertTrue(response["ok"])
        self.assertEqual(response["result"]["totals"]["base_tons"], 100.0)

    def test_invalid_values_are_rejected(self):
        valid = [{"length_ft": 100, "pavement_width_ft": 20, "shoulder_width_ft": 5, "shoulder_slope_percent": 4, "side_slope_h_to_v": 6, "thickness_in": 6}]
        invalid_cases = [
            ([], 1.6875, 0),
            ([{**valid[0], "length_ft": 0}], 1.6875, 0),
            ([{**valid[0], "pavement_width_ft": -1}], 1.6875, 0),
            ([{**valid[0], "shoulder_width_ft": -1}], 1.6875, 0),
            ([{**valid[0], "shoulder_slope_percent": -1}], 1.6875, 0),
            ([{**valid[0], "side_slope_h_to_v": 25}], 1.6875, 0),
            ([{**valid[0], "thickness_in": "nan"}], 1.6875, 0),
            (valid, 0, 0),
            (valid, float("inf"), 0),
            (valid, 1.6875, -1),
            (valid, 1.6875, 101),
        ]
        for segments, density, waste in invalid_cases:
            with self.subTest(segments=segments, density=density, waste=waste):
                with self.assertRaises(ValueError):
                    calculate(segments, density, waste)

    def test_catalog_drives_public_routes_and_runtime_bundles(self):
        catalog = {item["id"]: item for item in calculator_catalog()}
        runtime = browser_runtime_manifest()["calculators"]
        self.assertEqual(catalog["crushed_stone_base"]["route"], "/calculators/crushed-stone-base")
        self.assertEqual(catalog["crushed_stone_base"]["access"], "Free")
        self.assertEqual(catalog["crushed_stone_base"]["engine_version"], ENGINE_VERSION)
        self.assertEqual(runtime["crushed_stone_base"]["pyodide_packages"], [])
        self.assertEqual(runtime["crushed_stone_base"]["micropip_packages"], [])
        self.assertIn("super_service.py", runtime["superelevation"]["modules"])


if __name__ == "__main__":
    unittest.main()
