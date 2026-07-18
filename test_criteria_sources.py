import unittest

import Super
from criteria_info import applicable_drawings_label, criteria_for_result


class CriteriaSourceTests(unittest.TestCase):
    def calculate(
        self,
        *,
        area: str,
        facility: str,
        speed: str = "45",
        radius: str = "1200",
        e_manual: str = "",
        rel_grad: str = "",
        normal_crown: str = "0.02",
        lr_manual: str = "",
        lt_manual: str = "",
    ) -> dict:
        return Super.calculate_superelevation(
            "120+00",
            "140+00",
            speed,
            radius,
            facility,
            area,
            "12",
            "2",
            e_manual,
            "",
            rel_grad,
            normal_crown,
            lr_manual,
            lt_manual,
        )

    def references(self, result: dict) -> set[str]:
        criteria = criteria_for_result(result)
        return {source["reference"] for source in criteria["calculation_sources"]}

    def test_road_classification_maps_to_applicable_mdot_drawings(self):
        cases = [
            ("local", "outside edge", "45", ["MDOT STD. DWG SE-1"]),
            ("rural", "centerline", "45", ["MDOT STD. DWG SE-2A", "MDOT STD. DWG SE-3A"]),
            ("rural", "outside edge", "45", ["MDOT STD. DWG SE-2B", "MDOT STD. DWG SE-3B"]),
            ("urban", "centerline", "45", ["MDOT STD. DWG SE-2E"]),
            ("urban", "centerline", "50", ["MDOT STD. DWG SE-2C"]),
            ("urban", "outside edge", "50", ["MDOT STD. DWG SE-2D"]),
        ]
        for area, facility, speed, expected in cases:
            with self.subTest(area=area, facility=facility, speed=speed):
                result = self.calculate(area=area, facility=facility, speed=speed)
                self.assertEqual(
                    result["calculation_metadata"]["criteria"]["applicable_standard_drawings"],
                    expected,
                )

    def test_local_sources_identify_se1_and_se3a(self):
        references = self.references(self.calculate(area="local", facility="centerline"))
        self.assertIn("MDOT STD. DWG SE-1", references)
        self.assertIn("MDOT STD. DWG SE-3A", references)
        self.assertIn("MDOT Table 3-4-A", references)

    def test_rural_edge_sources_identify_drawing_and_equation_tables(self):
        references = self.references(self.calculate(area="rural", facility="outside edge"))
        self.assertIn("MDOT STD. DWG SE-2B", references)
        self.assertIn("MDOT Table 3-4-B", references)
        self.assertIn("MDOT Table 3-4-C", references)
        self.assertIn("MDOT Equation 3-4-1", references)

    def test_unmapped_urban_path_reports_formula_sources_without_inventing_a_drawing(self):
        result = self.calculate(area="urban", facility="centerline", speed="60")
        criteria = criteria_for_result(result)
        references = self.references(result)
        self.assertEqual(criteria["applicable_standard_drawings"], [])
        self.assertEqual(applicable_drawings_label(criteria), "No mapped MDOT standard drawing")
        self.assertIn("V^2/(15R) - f formula", references)
        self.assertIn("MDOT Table 3-4-B", references)
        self.assertIn("MDOT Table 3-4-C", references)

    def test_manual_overrides_replace_automatic_component_sources(self):
        result = self.calculate(
            area="rural",
            facility="outside edge",
            e_manual="0.04",
            rel_grad="0.005",
            normal_crown="0.03",
            lr_manual="100",
            lt_manual="50",
        )
        criteria = criteria_for_result(result)
        sources = {(source["component"], source["reference"], source["mode"]) for source in criteria["calculation_sources"]}
        self.assertIn(("Superelevation rate", "USER OVERRIDE: superelevation rate", "user_override"), sources)
        self.assertIn(("Runoff length", "USER OVERRIDE: runoff length", "user_override"), sources)
        self.assertIn(("Tangent runout", "USER OVERRIDE: tangent runout", "user_override"), sources)
        self.assertNotIn("MDOT Equation 3-4-1", {source[1] for source in sources})

    def test_legacy_result_gets_display_fallback_without_rewriting_profile(self):
        result = self.calculate(area="rural", facility="centerline")
        result["calculation_metadata"].pop("criteria")
        criteria = criteria_for_result(result)
        self.assertEqual(criteria["profile_id"], "legacy-unversioned")
        self.assertEqual(criteria["applicable_standard_drawings"], ["MDOT STD. DWG SE-2A", "MDOT STD. DWG SE-3A"])
        self.assertIn("SOURCE UNKNOWN", criteria["source_status"])


if __name__ == "__main__":
    unittest.main()
