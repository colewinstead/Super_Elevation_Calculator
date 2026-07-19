from __future__ import annotations

import json
import unittest
from pathlib import Path

from commercial_entitlements import (
    Capability,
    EntitlementRequiredError,
    LocalDevelopmentEntitlementProvider,
    Plan,
    commercial_manifest,
    require_capability,
)
from criteria_info import criteria_profiles
import super_service


ROOT = Path(__file__).parent
FIXTURE = ROOT / "tests" / "fixtures" / "sr82_synthetic.xml"


class CommercialEntitlementTests(unittest.TestCase):
    def snapshot(self, plan: Plan, status: str = "active") -> dict:
        return LocalDevelopmentEntitlementProvider(plan, status).snapshot().as_dict()

    def mdot_inputs(self) -> dict:
        return {
            "criteria_profile": "mdot-rdsd-2026-04-22",
            "pc": "100+00",
            "pt": "",
            "speed": "45",
            "radius": "2000",
            "facility": "centerline",
            "area": "rural",
            "lane_width": "12",
            "lanes_rotated": "2",
            "normal_crown": "0.02",
            "curve_direction": "left",
        }

    def test_plan_capability_matrix_is_complete_and_monotonic(self):
        manifest = commercial_manifest()
        free = set(manifest["plans"]["free"]["capabilities"])
        pro = set(manifest["plans"]["pro"]["capabilities"])
        team = set(manifest["plans"]["team"]["capabilities"])
        self.assertEqual(
            free,
            {
                "manual_single_curve",
                "basic_results",
                "lane_diagram",
                "standards_provenance",
                "sample_calculations",
            },
        )
        self.assertTrue(free < pro < team)
        self.assertEqual(team, {capability.value for capability in Capability})
        self.assertEqual(team - pro, {"team_seat_administration"})

    def test_free_denial_and_pro_team_grants_are_explicit(self):
        free = LocalDevelopmentEntitlementProvider(Plan.FREE).snapshot()
        with self.assertRaisesRegex(EntitlementRequiredError, "LandXML corridor workflows requires Pro"):
            require_capability(free, Capability.LANDXML_WORKFLOWS)
        for plan in (Plan.PRO, Plan.TEAM):
            snapshot = LocalDevelopmentEntitlementProvider(plan).snapshot()
            require_capability(snapshot, Capability.LANDXML_WORKFLOWS)
            require_capability(snapshot, Capability.PDF_REPORTS)

    def test_unavailable_service_falls_back_to_free_and_grace_retains_pro(self):
        unavailable = LocalDevelopmentEntitlementProvider(Plan.PRO, "unavailable").snapshot()
        self.assertEqual(unavailable.plan, Plan.FREE)
        self.assertEqual(unavailable.status, "unavailable")
        self.assertTrue(unavailable.allows(Capability.MANUAL_SINGLE_CURVE))
        self.assertFalse(unavailable.allows(Capability.PROJECT_FILES))

        grace = LocalDevelopmentEntitlementProvider(Plan.PRO, "grace").snapshot()
        self.assertEqual(grace.plan, Plan.PRO)
        self.assertEqual(grace.status, "grace")
        self.assertTrue(grace.allows(Capability.PROJECT_FILES))
        self.assertEqual(grace.browser_grace_days, 7)
        self.assertEqual(grace.desktop_grace_days, 30)

    def test_entitlement_state_cannot_change_authorized_calculation_results(self):
        results = []
        for plan in (Plan.FREE, Plan.PRO, Plan.TEAM):
            payload = {"inputs": self.mdot_inputs(), "entitlement": self.snapshot(plan)}
            results.append(super_service.dispatch("calculate", json.dumps(payload)))
        self.assertEqual(results[0], results[1])
        self.assertEqual(results[1], results[2])

    def test_free_tdot_request_is_denied_without_fallback_or_payload_mutation(self):
        inputs = {
            **self.mdot_inputs(),
            "criteria_profile": "tdot-rd11-2026-04-30",
            "facility": "undivided",
            "area": "rural",
            "speed": "50",
            "radius": "2280",
        }
        original = dict(inputs)
        denied = super_service.dispatch_safe(
            "calculate", json.dumps({"inputs": inputs, "entitlement": self.snapshot(Plan.FREE)})
        )
        self.assertFalse(denied["ok"])
        self.assertEqual(denied["error"]["type"], "EntitlementRequiredError")
        self.assertEqual(inputs, original)

        allowed = super_service.dispatch(
            "calculate", json.dumps({"inputs": inputs, "entitlement": self.snapshot(Plan.PRO)})
        )
        self.assertEqual(
            allowed["results"]["calculation_metadata"]["criteria"]["profile_id"],
            "tdot-rd11-2026-04-30",
        )

    def test_professional_dispatch_is_gated_before_file_processing(self):
        content = FIXTURE.read_text(encoding="utf-8")
        free = super_service.dispatch_safe(
            "parse_landxml",
            json.dumps({"content": content, "filename": FIXTURE.name, "entitlement": self.snapshot(Plan.FREE)}),
        )
        self.assertFalse(free["ok"])
        self.assertEqual(free["error"]["type"], "EntitlementRequiredError")
        pro = super_service.dispatch(
            "parse_landxml",
            json.dumps({"content": content, "filename": FIXTURE.name, "entitlement": self.snapshot(Plan.PRO)}),
        )
        self.assertGreater(pro["summary"]["curve_count"], 0)

    def test_generated_browser_catalog_matches_python_registries(self):
        generated_profiles = json.loads(
            (ROOT / "web" / "app" / "generated" / "criteria-profiles.json").read_text(encoding="utf-8")
        )
        generated_commercial = json.loads(
            (ROOT / "web" / "app" / "generated" / "commercial-manifest.json").read_text(encoding="utf-8")
        )
        self.assertEqual(
            [profile["profile_id"] for profile in generated_profiles],
            [profile["profile_id"] for profile in criteria_profiles()],
        )
        self.assertEqual(generated_commercial, commercial_manifest())


if __name__ == "__main__":
    unittest.main()
