"""Commercial capability policy kept separate from engineering calculations."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any, Protocol

from criteria_info import MDOT_PROFILE_ID


class Plan(str, Enum):
    FREE = "free"
    PRO = "pro"
    TEAM = "team"


class Capability(str, Enum):
    MANUAL_SINGLE_CURVE = "manual_single_curve"
    BASIC_RESULTS = "basic_results"
    LANE_DIAGRAM = "lane_diagram"
    STANDARDS_PROVENANCE = "standards_provenance"
    SAMPLE_CALCULATIONS = "sample_calculations"
    LANDXML_WORKFLOWS = "landxml_workflows"
    MULTI_CURVE_PROJECTS = "multi_curve_projects"
    ALL_DOT_PROFILES = "all_dot_profiles"
    PROJECT_FILES = "project_files"
    PDF_REPORTS = "pdf_reports"
    ORD_CSV_EXPORT = "ord_csv_export"
    OVERLAY_DXF_EXPORT = "overlay_dxf_export"
    PROVENANCE_EXPORT = "provenance_export"
    PRIORITY_SUPPORT = "priority_support"
    DESKTOP_EDITION = "desktop_edition"
    TEAM_SEAT_ADMINISTRATION = "team_seat_administration"


_CAPABILITY_DETAILS: dict[Capability, tuple[str, str, Plan]] = {
    Capability.MANUAL_SINGLE_CURVE: ("Manual single-curve calculations", "Enter one curve and calculate locally.", Plan.FREE),
    Capability.BASIC_RESULTS: ("Basic results", "Review calculated transition values and lane events.", Plan.FREE),
    Capability.LANE_DIAGRAM: ("Lane diagram", "Inspect station-aware lane slopes.", Plan.FREE),
    Capability.STANDARDS_PROVENANCE: ("Standards and provenance", "See criteria sources, revisions, and engine identity.", Plan.FREE),
    Capability.SAMPLE_CALCULATIONS: ("Sample calculations", "Load a synthetic manual example.", Plan.FREE),
    Capability.LANDXML_WORKFLOWS: ("LandXML corridor workflows", "Read local alignment geometry without uploading it.", Plan.PRO),
    Capability.MULTI_CURVE_PROJECTS: ("Multi-curve projects", "Build and review combined curve sets.", Plan.PRO),
    Capability.ALL_DOT_PROFILES: ("All supported DOT profiles", "Use every available versioned criteria profile.", Plan.PRO),
    Capability.PROJECT_FILES: ("Project save and open", "Store and reopen local project JSON files.", Plan.PRO),
    Capability.PDF_REPORTS: ("PDF reports", "Create calculation reports locally.", Plan.PRO),
    Capability.ORD_CSV_EXPORT: ("ORD CSV exports", "Create OpenRoads-compatible CSV deliverables.", Plan.PRO),
    Capability.OVERLAY_DXF_EXPORT: ("Overlay DXF exports", "Create coordinate-aware CAD overlays.", Plan.PRO),
    Capability.PROVENANCE_EXPORT: ("Versioned calculation provenance", "Include formal version and criteria traceability in deliverables.", Plan.PRO),
    Capability.PRIORITY_SUPPORT: ("Priority support", "Receive prioritized pilot support.", Plan.PRO),
    Capability.DESKTOP_EDITION: ("Optional desktop edition", "Use the offline desktop benefit when licensed.", Plan.PRO),
    Capability.TEAM_SEAT_ADMINISTRATION: ("Team seat administration", "Assign named users within an organization.", Plan.TEAM),
}

_FREE_CAPABILITIES = frozenset(
    {
        Capability.MANUAL_SINGLE_CURVE,
        Capability.BASIC_RESULTS,
        Capability.LANE_DIAGRAM,
        Capability.STANDARDS_PROVENANCE,
        Capability.SAMPLE_CALCULATIONS,
    }
)
_PRO_CAPABILITIES = frozenset(capability for capability in Capability if capability is not Capability.TEAM_SEAT_ADMINISTRATION)
_TEAM_CAPABILITIES = frozenset(Capability)
_PLAN_CAPABILITIES = {
    Plan.FREE: _FREE_CAPABILITIES,
    Plan.PRO: _PRO_CAPABILITIES,
    Plan.TEAM: _TEAM_CAPABILITIES,
}


class EntitlementRequiredError(PermissionError):
    """Raised before a professional workflow reaches engineering services."""

    def __init__(self, capability: Capability):
        self.capability = capability
        feature_name = _CAPABILITY_DETAILS[capability][0]
        super().__init__(
            f"{feature_name} requires Pro. Your current inputs, results, and project state are unchanged."
        )


@dataclass(frozen=True)
class EntitlementSnapshot:
    plan: Plan
    capabilities: tuple[Capability, ...]
    source: str = "local-development"
    status: str = "active"
    browser_grace_days: int = 7
    desktop_grace_days: int = 30

    def allows(self, capability: Capability | str) -> bool:
        normalized = capability if isinstance(capability, Capability) else Capability(capability)
        return normalized in self.capabilities

    def as_dict(self) -> dict[str, Any]:
        return {
            "plan": self.plan.value,
            "capabilities": [capability.value for capability in self.capabilities],
            "source": self.source,
            "status": self.status,
            "browser_grace_days": self.browser_grace_days,
            "desktop_grace_days": self.desktop_grace_days,
        }


class EntitlementProvider(Protocol):
    def snapshot(self) -> EntitlementSnapshot: ...


class LocalDevelopmentEntitlementProvider:
    """Deterministic provider for tests and localhost-only UI development."""

    def __init__(self, plan: Plan | str = Plan.FREE, status: str = "active") -> None:
        self.plan = plan if isinstance(plan, Plan) else Plan(str(plan).lower())
        if status not in {"active", "grace", "unavailable"}:
            raise ValueError("Local entitlement status must be active, grace, or unavailable.")
        self.status = status

    def snapshot(self) -> EntitlementSnapshot:
        if self.status == "unavailable":
            return EntitlementSnapshot(
                plan=Plan.FREE,
                capabilities=_ordered_capabilities(_PLAN_CAPABILITIES[Plan.FREE]),
                status="unavailable",
            )
        return EntitlementSnapshot(
            plan=self.plan,
            capabilities=_ordered_capabilities(_PLAN_CAPABILITIES[self.plan]),
            status=self.status,
        )


def _ordered_capabilities(capabilities: frozenset[Capability]) -> tuple[Capability, ...]:
    return tuple(capability for capability in Capability if capability in capabilities)


def snapshot_from_payload(value: Any) -> EntitlementSnapshot:
    """Normalize an unsigned development snapshot; production will replace this provider."""
    if not isinstance(value, dict):
        return LocalDevelopmentEntitlementProvider().snapshot()
    try:
        plan = Plan(str(value.get("plan", Plan.FREE.value)).lower())
        status = str(value.get("status", "active")).lower()
        return LocalDevelopmentEntitlementProvider(plan, status).snapshot()
    except (TypeError, ValueError):
        return LocalDevelopmentEntitlementProvider(status="unavailable").snapshot()


def require_capability(snapshot: EntitlementSnapshot, capability: Capability) -> None:
    if not snapshot.allows(capability):
        raise EntitlementRequiredError(capability)


def require_profile_access(snapshot: EntitlementSnapshot, profile_id: str) -> None:
    if profile_id != MDOT_PROFILE_ID:
        require_capability(snapshot, Capability.ALL_DOT_PROFILES)


def commercial_manifest() -> dict[str, Any]:
    return {
        "policy_version": 1,
        "production_default_plan": Plan.FREE.value,
        "free_criteria_profile": MDOT_PROFILE_ID,
        "browser_grace_days": 7,
        "desktop_grace_days": 30,
        "plans": {
            plan.value: {
                "name": plan.value.title(),
                "capabilities": [capability.value for capability in _ordered_capabilities(capabilities)],
            }
            for plan, capabilities in _PLAN_CAPABILITIES.items()
        },
        "capabilities": {
            capability.value: {
                "name": details[0],
                "description": details[1],
                "minimum_plan": details[2].value,
            }
            for capability, details in _CAPABILITY_DETAILS.items()
        },
    }
