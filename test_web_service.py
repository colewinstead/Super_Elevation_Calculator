from __future__ import annotations

import json
import unittest
from pathlib import Path

import super_project
import super_service
from commercial_entitlements import LocalDevelopmentEntitlementProvider, Plan


FIXTURE = Path(__file__).parent / "tests" / "fixtures" / "sr82_synthetic.xml"


class WebServiceTests(unittest.TestCase):
    def pro_payload(self, payload: dict) -> dict:
        return {
            **payload,
            "entitlement": LocalDevelopmentEntitlementProvider(Plan.PRO).snapshot().as_dict(),
        }

    def inputs(self) -> dict:
        return {
            "pc": "10+00",
            "pt": "12+00",
            "speed": "45",
            "radius": "1000",
            "facility": "centerline",
            "area": "rural",
            "lane_width": "12",
            "lanes_rotated": "2",
            "normal_crown": "0.02",
            "curve_direction": "right",
        }

    def test_browser_calculation_uses_shared_engine_and_lane_rows(self):
        response = super_service.calculate_curve(self.inputs())
        self.assertEqual(response["results"]["inputs"]["speed_mph"], 45.0)
        self.assertTrue(response["lanes"]["left"])
        self.assertTrue(response["lanes"]["right"])
        self.assertEqual(
            response["results"]["calculation_metadata"]["engine_version"],
            super_service.CALCULATION_ENGINE_VERSION,
        )

    def test_landxml_is_embedded_with_integrity_hash(self):
        content = FIXTURE.read_text(encoding="utf-8")
        parsed = super_service.parse_landxml(content, FIXTURE.name)
        self.assertEqual(parsed["source"]["filename"], FIXTURE.name)
        self.assertEqual(len(parsed["source"]["sha256"]), 64)
        self.assertGreater(parsed["summary"]["curve_count"], 0)
        self.assertEqual(parsed["summary"]["coordinate_system"]["status"], "recognized")
        self.assertEqual(parsed["summary"]["coordinate_system"]["code"], "6507")
        self.assertTrue(parsed["summary"]["coordinate_system"]["preserve_xy"])

    def test_schema_v5_project_round_trip_embeds_landxml_and_pairs(self):
        content = FIXTURE.read_text(encoding="utf-8")
        source = super_project.make_landxml_source(FIXTURE.name, content)
        serialized = super_service.project_save({
            "version": 5,
            "vars": self.inputs(),
            "landxml_source": source,
            "excluded_landxml_curve_indexes": [1],
            "curves": [{}, {}],
            "reverse_curve_pairs": [[0, 1]],
        })
        loaded = super_service.project_load(serialized)
        self.assertEqual(loaded["project"]["version"], 5)
        self.assertEqual(loaded["project"]["landxml_source"]["sha256"], source["sha256"])
        self.assertEqual(loaded["landxml"]["source"]["content"], content)
        self.assertEqual(loaded["project"]["excluded_landxml_curve_indexes"], [1])
        self.assertEqual(loaded["project"]["reverse_curve_pairs"], [[0, 1]])

    def test_embedded_landxml_hash_mismatch_is_refused(self):
        with self.assertRaisesRegex(super_project.ProjectFormatError, "integrity"):
            super_project.normalize_project({
                "version": 5,
                "landxml_source": {"filename": "a.xml", "encoding": "utf-8", "sha256": "0" * 64, "content": "<LandXML />"},
            })

    def test_schema_v4_infers_disjoint_pairs_without_recalculating_results(self):
        recorded = {
            "calculation_metadata": {"engine_version": "1.2.1"},
            "reverse_curve_coordination": {
                "checks": [{"paired_curve_indexes": [0, 1], "status": "coordinated"}],
            },
        }
        loaded = super_project.normalize_project({
            "version": 4,
            "vars": {"coordinate_reverse_curves": True},
            "curves": [
                {"results": recorded},
                {"results": {"recorded_value": 123.456}},
            ],
        })
        self.assertEqual(loaded["version"], 5)
        self.assertEqual(loaded["source_version"], 4)
        self.assertEqual(loaded["reverse_curve_pairs"], [[0, 1]])
        self.assertNotIn("coordinate_reverse_curves", loaded["vars"])
        self.assertEqual(loaded["curves"][0]["results"], recorded)
        self.assertEqual(loaded["curves"][1]["results"]["recorded_value"], 123.456)

    def test_schema_v5_rejects_overlapping_pair_chain(self):
        with self.assertRaisesRegex(super_project.ProjectFormatError, "more than one"):
            super_project.normalize_project({
                "version": 5,
                "curves": [{}, {}, {}],
                "reverse_curve_pairs": [[0, 1], [1, 2]],
            })

    def test_safe_dispatch_returns_friendly_project_error_without_traceback(self):
        response = super_service.dispatch_safe("project_load", json.dumps(self.pro_payload({"content": ""})))
        self.assertFalse(response["ok"])
        self.assertEqual(response["error"]["type"], "ProjectFormatError")
        self.assertIn("not valid JSON", response["error"]["message"])
        self.assertNotIn("Traceback", response["error"]["message"])

    def test_browser_exports_are_generated_in_memory(self):
        response = super_service.calculate_curve(self.inputs())
        curve = {"results": response["results"], "meta": {"curve_direction": "right"}, "notes": ""}
        csv_result = super_service.export_ord_csv([curve])
        pdf_result = super_service.export_pdf([curve])
        dxf_result = super_service.export_detail_dxf([curve])
        self.assertIn("SuperelevationLane", csv_result["content"])
        self.assertTrue(pdf_result["content"].startswith(b"%PDF"))
        self.assertIn(b"SECTION", dxf_result["content"])

    def test_lookup_returns_descriptive_display_labels(self):
        results = super_service.calculate_curve(self.inputs())["results"]
        station = super_service.lookup(results, "right", "10+50", "")
        slope = super_service.lookup(results, "right", "", str(results["e"] * 100))
        self.assertIn("decimal", station["station"]["slopes"]["left"])
        self.assertEqual(slope["slope"]["decimal"], "+0.0800")
        self.assertEqual(slope["lanes"]["left"][0]["label"], "Full-super range")

    def test_browser_dispatch_exposes_diagram_and_corridor_qa(self):
        content = FIXTURE.read_text(encoding="utf-8")
        curves = super_service.build_all_landxml_curves(content, FIXTURE.name, self.inputs())
        diagram = super_service.dispatch("curve_diagram", json.dumps({
            "results": curves[0]["results"], "direction": curves[0]["meta"]["curve_direction"],
        }))
        qa = super_service.dispatch(
            "corridor_qa",
            json.dumps(self.pro_payload({"content": content, "filename": FIXTURE.name, "curves": curves})),
        )
        self.assertTrue(diagram["profiles"]["left"])
        self.assertEqual(qa["status"], "pass")

    def test_present_results_accepts_pyodide_omitted_optional_values(self):
        results = self.calculate_results_without_none_values()
        presented = super_service.present_results(results, "right")
        self.assertTrue(presented["lanes"]["left"])

    def calculate_results_without_none_values(self) -> dict:
        results = super_service.calculate_curve(self.inputs())["results"]
        return {key: value for key, value in results.items() if value is not None}


if __name__ == "__main__":
    unittest.main()
