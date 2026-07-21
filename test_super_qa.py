from __future__ import annotations

import copy
import unittest
from pathlib import Path
from unittest import mock

import super_service
import super_batch
import super_exports


FIXTURE = Path(__file__).parent / "tests" / "fixtures" / "sr82_synthetic.xml"
CW_FIXTURE = Path(__file__).parent / "tests" / "fixtures" / "cw_reverse_curve.xml"


class CorridorQATests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.content = FIXTURE.read_text(encoding="utf-8")

    def curves(self) -> list[dict]:
        return super_service.build_all_landxml_curves(
            self.content,
            FIXTURE.name,
            {
                "speed": "45",
                "facility": "centerline",
                "area": "rural",
                "lane_width": "12",
                "lanes_rotated": "2",
                "normal_crown": "0.02",
            },
        )

    def test_curve_diagram_contains_profiles_markers_and_criteria(self):
        curve = self.curves()[0]
        diagram = super_service.curve_diagram(curve["results"], curve["meta"]["curve_direction"])
        self.assertTrue(diagram["profiles"]["left"])
        self.assertTrue(diagram["profiles"]["right"])
        self.assertIn("PC", {marker["kind"] for marker in diagram["markers"]})
        self.assertIn("PC", {label for point in diagram["snap_points"] for label in point["labels"]})
        self.assertIn("Runoff length", {item["component"] for item in diagram["intervals"]["left"]})

        station = diagram["profiles"]["left"][2]["station_ft"]
        lookup = super_service.diagram_lookup(curve["results"], curve["meta"]["curve_direction"], station)
        self.assertEqual(lookup["station_ft"], station)
        self.assertIn("reference", lookup["lanes"]["left"]["criterion"])

    def test_diagram_includes_station_equations(self):
        curve = copy.deepcopy(self.curves()[0])
        curve["results"]["station_equations"] = [{"staInternal": "18000", "staBack": "18000", "staAhead": "18100"}]
        diagram = super_service.curve_diagram(curve["results"], curve["meta"]["curve_direction"])
        equation = next(marker for marker in diagram["markers"] if marker["kind"] == "STATION EQUATION")
        self.assertEqual(equation["station_ft"], 18000.0)
        self.assertIn("180+00.000", equation["label"])

    def test_corridor_diagram_contains_every_curve_and_global_domain(self):
        curves = self.curves()
        diagram = super_service.corridor_diagram(curves)
        self.assertEqual(diagram["curve_count"], len(curves))
        self.assertEqual([item["curve_name"] for item in diagram["curves"]], [
            curve["meta"]["curve_name"] for curve in curves
        ])
        self.assertEqual(diagram["domain"]["start_ft"], min(
            item["domain"]["start_ft"] for item in diagram["curves"]
        ))
        self.assertEqual(diagram["domain"]["end_ft"], max(
            item["domain"]["end_ft"] for item in diagram["curves"]
        ))

    def test_plan_view_uses_overlay_dxf_entities(self):
        preview = super_service.plan_view(self.content, FIXTURE.name, self.curves())
        self.assertEqual(preview["background"], "#101010")
        self.assertEqual(preview["layers"]["ALI_DESIGN_ML_CURVES"]["color"], 8)
        self.assertIn("LINE", {entity["type"] for entity in preview["entities"]})
        self.assertIn("TEXT", {entity["type"] for entity in preview["entities"]})
        self.assertTrue(any(
            entity["type"] == "TEXT" and entity["text"].startswith("R=")
            for entity in preview["entities"]
        ))
        self.assertNotIn("curve_paths", preview)
        self.assertNotIn("events", preview)
        self.assertLess(preview["bounds"]["min_x"], preview["bounds"]["max_x"])
        self.assertLess(preview["bounds"]["min_y"], preview["bounds"]["max_y"])
        callout = next(entity for entity in preview["entities"] if (entity.get("preview") or {}).get("event_type"))
        self.assertRegex(callout["preview"]["group_id"], r"^curve-\d+-row-\d+$")
        self.assertIn("curve_index", callout["preview"])
        self.assertIn("curve_name", callout["preview"])
        self.assertIn("station", callout["preview"])
        self.assertIn("station_ft", callout["preview"])
        self.assertIn(callout["preview"]["side"], {"left", "right"})
        self.assertIn("slope", callout["preview"])

    def test_normal_crown_only_curve_has_stable_profiles(self):
        inputs = {
            "pc": "10+00", "pt": "12+00", "speed": "30", "radius": "100000",
            "facility": "centerline", "area": "rural", "lane_width": "12",
            "lanes_rotated": "2", "normal_crown": "0.02", "curve_direction": "left",
        }
        response = super_service.calculate_curve(inputs)
        self.assertTrue(response["results"]["normal_crown_only"])
        diagram = super_service.curve_diagram(response["results"], "left")
        self.assertGreaterEqual(len(diagram["profiles"]["left"]), 2)

    def test_complete_synthetic_corridor_passes(self):
        report = super_service.corridor_qa(self.content, FIXTURE.name, self.curves())
        self.assertEqual(report["status"], "pass")
        self.assertEqual(report["counts"], {"pass": 2, "review": 0, "block": 0})

    def test_missing_calculation_blocks_corridor(self):
        report = super_service.corridor_qa(self.content, FIXTURE.name, self.curves()[:1])
        self.assertEqual(report["status"], "block")
        self.assertIn("UNCALCULATED_CURVE", {finding["code"] for finding in report["findings"]})

    def test_intentionally_excluded_curve_is_not_reported_as_uncalculated(self):
        curves = self.curves()
        report = super_service.corridor_qa(self.content, FIXTURE.name, curves[:1], [1])
        self.assertNotIn("UNCALCULATED_CURVE", {finding["code"] for finding in report["findings"]})
        self.assertEqual(report["curve_count"], 1)
        self.assertEqual(report["source_curve_count"], 2)
        self.assertEqual(report["excluded_count"], 1)
        self.assertEqual(report["curve_statuses"][1]["status"], "excluded")

    def test_inconsistent_speed_and_overrides_require_review(self):
        curves = copy.deepcopy(self.curves())
        curves[1]["results"]["inputs"]["speed_mph"] = 50.0
        curves[1]["results"]["calculation_metadata"]["manual_overrides"]["runoff_length"] = True
        report = super_service.corridor_qa(self.content, FIXTURE.name, curves)
        codes = {finding["code"] for finding in report["findings"]}
        self.assertIn("INCONSISTENT_SPEED", codes)
        self.assertIn("MIXED_OVERRIDES", codes)
        self.assertEqual(report["status"], "review")

    def test_reverse_curve_uses_zero_to_zero_demand(self):
        curves = copy.deepcopy(self.curves())
        next_entry_zero = curves[1]["results"]["reverse_crown_ft"]
        curves[0]["results"]["reverse_crown_out_ft"] = next_entry_zero + 25.0
        report = super_service.corridor_qa(self.content, FIXTURE.name, curves)
        finding = next(item for item in report["findings"] if item["code"] == "SHORT_TANGENT")
        self.assertIn("zero-slope reverse-curve recovery", finding["message"])

    def test_reverse_curve_coordination_preserves_runoff_and_removes_runout(self):
        curves = super_service.build_all_landxml_curves(
            self.content,
            FIXTURE.name,
            {
                "speed": "45", "facility": "centerline", "area": "rural",
                "lane_width": "12", "lanes_rotated": "2", "normal_crown": "0.02",
                "coordinate_reverse_curves": "true",
            },
        )
        prior, following = curves[:2]
        prior_results = prior["results"]
        following_results = following["results"]
        exit_zero = prior_results["pt_ft"] + 0.7 * prior_results["Lr"]
        entry_zero = following_results["pc_ft"] - 0.7 * following_results["Lr"]
        self.assertAlmostEqual(prior_results["reverse_curve_exit_zero_ft"], exit_zero)
        self.assertAlmostEqual(following_results["reverse_curve_entry_zero_ft"], entry_zero)
        self.assertAlmostEqual(prior_results["full_super_out_ft"], prior_results["pt_ft"] - 0.3 * prior_results["Lr"])
        self.assertAlmostEqual(following_results["full_super_ft"], following_results["pc_ft"] + 0.3 * following_results["Lr"])
        self.assertLessEqual(exit_zero, entry_zero)

        check = prior_results["reverse_curve_coordination"]["checks"][0]
        self.assertEqual(check["status"], "coordinated")
        self.assertAlmostEqual(
            check["minimum_tangent_ft"],
            0.7 * prior_results["Lr"] + 0.7 * following_results["Lr"],
        )

        for curve in (prior, following):
            left_rows, right_rows = super_exports.build_lane_rows(
                curve["results"], curve["meta"]["curve_direction"], station_format=False,
            )
            for rows in (left_rows, right_rows):
                zeros = {
                    row["station_ft"] for row in rows
                    if row["slope_pct"] == 0.0 and exit_zero - 1e-6 <= row["station_ft"] <= entry_zero + 1e-6
                }
                self.assertEqual(zeros, {exit_zero, entry_zero})

        report = super_service.corridor_qa(self.content, FIXTURE.name, curves)
        codes = {finding["code"] for finding in report["findings"]}
        self.assertNotIn("SHORT_TANGENT", codes)
        self.assertNotIn("SHORT_REVERSE_TANGENT", codes)

        restored = super_batch.coordinate_reverse_curve_transitions(curves, enabled=False)
        self.assertNotIn("reverse_curve_exit_zero_ft", restored[0]["results"])
        self.assertNotIn("reverse_curve_entry_zero_ft", restored[1]["results"])
        self.assertNotIn("reverse_curve_coordination", restored[0]["results"])
        self.assertAlmostEqual(restored[0]["results"]["full_super_out_ft"], prior_results["full_super_out_ft"])

    def test_latest_cw_reverse_curve_uses_prescribed_runoffs_and_level_surplus(self):
        content = CW_FIXTURE.read_text(encoding="utf-8")
        curves = super_service.build_all_landxml_curves(
            content,
            CW_FIXTURE.name,
            {
                "speed": "65", "facility": "centerline", "area": "rural",
                "lane_width": "12", "lanes_rotated": "2", "normal_crown": "0.02",
                "coordinate_reverse_curves": "true",
            },
        )
        self.assertEqual(len(curves), 2)
        prior, following = curves
        check = prior["results"]["reverse_curve_coordination"]["checks"][0]
        self.assertEqual(check["status"], "coordinated")
        self.assertAlmostEqual(check["available_tangent_ft"], 123.0, places=3)
        self.assertAlmostEqual(check["minimum_tangent_ft"], 86.1, places=3)
        self.assertAlmostEqual(
            following["results"]["reverse_curve_entry_zero_ft"]
            - prior["results"]["reverse_curve_exit_zero_ft"],
            36.9,
            places=3,
        )

        left_rows, right_rows = super_exports.build_lane_rows(
            following["results"], following["meta"]["curve_direction"], station_format=False,
        )
        for rows in (left_rows, right_rows):
            entry_labels = {row["label"] for row in rows if row["station_ft"] < following["results"]["full_super_ft"]}
            self.assertNotIn("NC", entry_labels)
            self.assertNotIn("BEGIN ROTATION", entry_labels)
        pc_slopes = [abs(next(row for row in rows if row["label"] == "PC")["slope_pct"]) for rows in (left_rows, right_rows)]
        self.assertTrue(all(abs(slope - 1.68) < 1e-9 for slope in pc_slopes))

    def test_short_reverse_tangent_blocks_without_moving_runoff(self):
        curves = self.curves()
        prior, following = curves[:2]
        following["results"]["pc_ft"] = prior["results"]["pt_ft"] + 10.0
        following["results"]["full_super_ft"] = following["results"]["pc_ft"] + 0.3 * following["results"]["Lr"]
        coordinated = super_batch.coordinate_reverse_curve_transitions(curves)
        self.assertNotIn("exit", coordinated[0]["results"]["reverse_curve_coordination"])
        self.assertNotIn("entry", coordinated[1]["results"]["reverse_curve_coordination"])
        self.assertNotIn("reverse_curve_exit_zero_ft", coordinated[0]["results"])
        self.assertNotIn("reverse_curve_entry_zero_ft", coordinated[1]["results"])
        report = super_service.corridor_qa(self.content, FIXTURE.name, coordinated)
        finding = next(item for item in report["findings"] if item["code"] == "SHORT_REVERSE_TANGENT")
        self.assertEqual(finding["severity"], "block")
        self.assertIn("0.7Lr(exit) + 0.7Lr(entry)", finding["details"])

    def test_normal_crown_curve_does_not_require_transition_recovery_events(self):
        curves = copy.deepcopy(self.curves())
        curves[0]["results"]["normal_crown_only"] = True
        with mock.patch("super_qa._zero_event", return_value=None) as zero_event:
            report = super_service.corridor_qa(self.content, FIXTURE.name, curves)
        self.assertNotIn("MISSING_TRANSITION_DEMAND", {finding["code"] for finding in report["findings"]})
        zero_event.assert_not_called()

    def test_spiral_geometry_blocks_corridor(self):
        spiral = '<Spiral length="100"><Start>1453411.9250950934 993735.04373338632 0</Start><End>1453411.9250950934 993835.04373338632 0</End></Spiral>'
        content = self.content.replace("<Curve crvType=", f"{spiral}<Curve crvType=", 1)
        report = super_service.corridor_qa(content, "spiral.xml", [])
        self.assertEqual(report["status"], "block")
        self.assertIn("UNSUPPORTED_SPIRAL", {finding["code"] for finding in report["findings"]})

    def test_out_of_alignment_transition_blocks_corridor(self):
        curves = copy.deepcopy(self.curves())
        curves[0]["results"]["reverse_crown_ft"] = 9000.0
        report = super_service.corridor_qa(self.content, FIXTURE.name, curves)
        self.assertIn("OUT_OF_ALIGNMENT", {finding["code"] for finding in report["findings"]})

    def test_zero_length_geometry_blocks_corridor(self):
        content = self.content.replace('length="7407.4478297109072"', 'length="0"', 1)
        report = super_service.corridor_qa(content, "invalid.xml", [])
        self.assertIn("INVALID_GEOMETRY", {finding["code"] for finding in report["findings"]})


if __name__ == "__main__":
    unittest.main()
