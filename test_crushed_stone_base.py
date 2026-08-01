import math
import unittest

from calculators.catalog import browser_runtime_manifest, calculator_catalog
from calculators.crushed_stone_base.engine import calculate
from calculators.crushed_stone_base.service import dispatch_safe


class CrushedStoneBaseTests(unittest.TestCase):
    def test_baseline_segment(self):
        result = calculate(
            [{"name": "Mainline", "length_ft": 100, "width_ft": 20, "thickness_in": 6}],
            1.6875,
            0,
        )
        self.assertEqual(result["totals"]["cubic_feet"], 1000.0)
        self.assertTrue(math.isclose(result["totals"]["cubic_yards"], 1000.0 / 27.0))
        self.assertEqual(result["totals"]["base_tons"], 62.5)
        self.assertEqual(result["totals"]["order_tons"], 62.5)

    def test_multiple_segments_and_waste(self):
        result = calculate(
            [
                {"name": "A", "length_ft": 100.5, "width_ft": 20, "thickness_in": 6},
                {"name": "B", "length_ft": 50, "width_ft": 12.5, "thickness_in": 8},
            ],
            1.6875,
            5,
        )
        expected_cf = 100.5 * 20 * 6 / 12 + 50 * 12.5 * 8 / 12
        expected_tons = expected_cf / 27 * 1.6875
        self.assertTrue(math.isclose(result["totals"]["cubic_feet"], expected_cf))
        self.assertTrue(math.isclose(result["totals"]["base_tons"], expected_tons))
        self.assertTrue(math.isclose(result["totals"]["waste_tons"], expected_tons * 0.05))
        self.assertTrue(math.isclose(result["totals"]["order_tons"], expected_tons * 1.05))

    def test_service_returns_json_safe_result(self):
        response = dispatch_safe(
            "calculate",
            '{"segments":[{"length_ft":100,"width_ft":20,"thickness_in":6}],"tons_per_cubic_yard":1.6875,"waste_percent":0}',
        )
        self.assertTrue(response["ok"])
        self.assertEqual(response["result"]["totals"]["base_tons"], 62.5)

    def test_invalid_values_are_rejected(self):
        valid = [{"length_ft": 100, "width_ft": 20, "thickness_in": 6}]
        invalid_cases = [
            ([], 1.6875, 0),
            ([{"length_ft": 0, "width_ft": 20, "thickness_in": 6}], 1.6875, 0),
            ([{"length_ft": 100, "width_ft": -1, "thickness_in": 6}], 1.6875, 0),
            ([{"length_ft": 100, "width_ft": 20, "thickness_in": "nan"}], 1.6875, 0),
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
        self.assertEqual(runtime["crushed_stone_base"]["pyodide_packages"], [])
        self.assertEqual(runtime["crushed_stone_base"]["micropip_packages"], [])
        self.assertIn("super_service.py", runtime["superelevation"]["modules"])


if __name__ == "__main__":
    unittest.main()
