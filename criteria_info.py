"""Versioned criteria-profile registry and calculation traceability metadata."""

from __future__ import annotations

from copy import deepcopy
from typing import Any

from tdot_criteria import TDOT_PROFILE_ID


MDOT_PROFILE_ID = "mdot-rdsd-2026-04-22"

_MDOT_CRITERIA_METADATA = {
    "profile_id": MDOT_PROFILE_ID,
    "profile_name": "MDOT superelevation criteria",
    "revision": "2020 manual / standard drawings compilation revised 2026-04-22",
    "source_status": (
        "ISSUED SOURCES IDENTIFIED; VALUE-BY-VALUE VERIFICATION AND ENGINEER APPROVAL REQUIRED "
        "BEFORE PAID PILOT"
    ),
    "governing_authority": "Mississippi Department of Transportation",
    "source_documents": [
        {
            "title": "2020 Roadway Design Manual",
            "edition": "2020",
            "applicable_sections": ["3-4.0", "14-2.04"],
            "url": (
                "https://mdot.ms.gov/documents/Roadway%20Design/Standards/Manuals/"
                "2020%20Roadway%20Design%20Manual.pdf"
            ),
        },
        {
            "title": "Roadway Design Standard Drawings",
            "issue_date": "2017-08-01",
            "compilation_revision": "2026-04-22",
            "applicable_sheets": [
                "SE-1",
                "SE-2A",
                "SE-2B",
                "SE-2C",
                "SE-2D",
                "SE-2E",
                "SE-3A",
                "SE-3B",
            ],
            "url": (
                "https://mdot.ms.gov/documents/Roadway%20Design/Standards/Drawings/"
                "Roadway%20Design%20Standard%20Drawings.pdf"
            ),
        },
    ],
    "referenced_identifiers": [
        "Table 3-4-A",
        "Table 3-4-B",
        "Table 3-4-C",
        "Equation 3-4-1",
        "SE-1",
        "SE-2A",
        "SE-2B",
        "SE-2C",
        "SE-2D",
        "SE-2E",
        "SE-3A",
        "SE-3B",
    ],
    "implementation_module": "Super.py",
    "engineering_change_notice": (
        "This source identification does not validate the embedded values, formulas, interpolation, or "
        "branching rules. A qualified roadway engineer must complete the criteria matrix, independently "
        "check transcription, and approve golden calculations."
    ),
}


_TDOT_STANDARD_ROOT = (
    "https://www.tn.gov/content/dam/tn/tdot/engineering-production-support/documents/"
    "standard-drawings/roadway-standard-drawings/current/roadway-design-standards/"
)

_TDOT_TYPICAL_SECTION_SHEETS = [
    "RD11-TS-1",
    "RD11-TS-1A",
    "RD11-TS-2",
    "RD11-TS-2A",
    "RD11-TS-2B",
    "RD11-TS-3",
    "RD11-TS-3A",
    "RD11-TS-3B",
    "RD11-TS-3C",
    "RD11-TS-4",
    "RD11-TS-5",
    "RD11-TS-5B",
    "RD11-TS-5W",
    "RD11-TS-6",
    "RD11-TS-6A",
    "RD11-TS-6B",
    "RD11-TS-6C",
    "RD11-TS-7",
    "RD11-TS-7A",
    "RD11-TS-7B",
]

_TDOT_CRITERIA_METADATA = {
    "profile_id": TDOT_PROFILE_ID,
    "profile_name": "TDOT RD11 superelevation criteria",
    "revision": "Roadway Design Guidelines revised 2026-04-30 / RD11 drawings issue 2019-01-01",
    "source_status": (
        "ISSUED TDOT SOURCES TRANSCRIBED; INDEPENDENT ENGINEERING REVIEW AND GOLDEN-CALCULATION "
        "APPROVAL REQUIRED BEFORE PRODUCTION USE"
    ),
    "governing_authority": "Tennessee Department of Transportation",
    "source_documents": [
        {
            "title": "TDOT Roadway Design Standards library",
            "library_revision": "2026-04-30",
            "applicable_anchors": ["RD11TYP05", "RD11SLP06"],
            "url": (
                "https://www.tn.gov/tdot/state-engineering-technical-training/production-support/"
                "standard-drawings-library/standard-roadway-drawings/roadway-design-standards.html"
            ),
        },
        {
            "title": "Roadway Design Guidelines, Chapter 2",
            "revision": "2026-04-30",
            "applicable_topic": "Urban 4% and rural 8% desirable maximum superelevation",
            "url": (
                "https://www.tn.gov/content/dam/tn/tdot/engineering-production-support/documents/"
                "design-standards/design-guidelines---pdn/Chapter%202%20RDG%20-%20%20PDN.pdf"
            ),
        },
        {
            "title": "Superelevation Design Guide",
            "file_revision": "2026-01-15",
            "applicable_topic": "RD11-LR rate selection, transition length, and simple-curve placement",
            "url": (
                "https://www.tn.gov/content/dam/tn/tdot/engineering-production-support/documents/"
                "design-standards/additional-resources/Superelevation%20Design%20Guide.pdf"
            ),
        },
        {
            "title": "RD11 superelevation and runoff standard drawings",
            "issue_date": "2019-01-01",
            "applicable_sheets": [
                "RD11-SE-1",
                "RD11-SE-2",
                "RD11-SE-2A",
                "RD11-SE-3",
                "RD11-SE-3A",
                "RD11-LR-1",
                "RD11-LR-2",
            ],
            "url": _TDOT_STANDARD_ROOT,
        },
        {
            "title": "RD11 typical sections and design criteria catalog",
            "scope": (
                "Supporting roadway-classification, width, grade, sight-distance, and maximum-"
                "superelevation checks; only superelevation fields are consumed by this calculator"
            ),
            "applicable_sheets": _TDOT_TYPICAL_SECTION_SHEETS,
            "url": (
                "https://www.tn.gov/tdot/state-engineering-technical-training/production-support/"
                "standard-drawings-library/standard-roadway-drawings/roadway-design-standards.html#RD11TYP05"
            ),
        },
    ],
    "referenced_identifiers": [
        "RD11-SE-1",
        "RD11-SE-2",
        "RD11-SE-2A",
        "RD11-SE-3",
        "RD11-SE-3A",
        "RD11-LR-1",
        "RD11-LR-2",
        *_TDOT_TYPICAL_SECTION_SHEETS,
    ],
    "active_table_policy": {
        "urban": "RD11-LR-1, 4% desirable maximum",
        "rural": "RD11-LR-2, 8% desirable maximum",
        "allowable_6_percent": (
            "Recorded as a supporting typical-section criterion; never selected automatically"
        ),
    },
    "implementation_modules": ["tdot_criteria.py", "Super.py"],
    "engineering_change_notice": (
        "TDOT states that its standard drawings are intended for TDOT projects. Confirm project "
        "applicability, roadway classification, design exceptions, and current revisions before use."
    ),
}


_PROFILE_METADATA = {
    MDOT_PROFILE_ID: _MDOT_CRITERIA_METADATA,
    TDOT_PROFILE_ID: _TDOT_CRITERIA_METADATA,
}


def normalize_profile_id(profile_id: str | None) -> str:
    value = str(profile_id or MDOT_PROFILE_ID).strip().lower()
    aliases = {"mdot": MDOT_PROFILE_ID, "tdot": TDOT_PROFILE_ID}
    value = aliases.get(value, value)
    if value not in _PROFILE_METADATA:
        choices = ", ".join(sorted(_PROFILE_METADATA))
        raise ValueError(f"Unknown criteria profile '{profile_id}'. Available profiles: {choices}.")
    return value


def criteria_profiles() -> list[dict[str, Any]]:
    """Return selector-safe profile summaries."""
    return [
        {
            "profile_id": profile_id,
            "profile_name": metadata["profile_name"],
            "governing_authority": metadata["governing_authority"],
            "revision": metadata["revision"],
        }
        for profile_id, metadata in _PROFILE_METADATA.items()
    ]


def criteria_metadata(profile_id: str | None = None) -> dict:
    """Return an isolated copy suitable for results, projects, and reports."""
    return deepcopy(_PROFILE_METADATA[normalize_profile_id(profile_id)])


def applicable_standard_drawings(results: dict[str, Any]) -> list[str]:
    """Return standard drawings associated with the recorded criteria profile."""
    inputs = results.get("inputs", {}) or {}
    profile_id = _result_profile_id(results)
    area = str(inputs.get("area_type", results.get("area_type", ""))).lower()
    facility = str(inputs.get("facility", results.get("facility", ""))).lower()
    try:
        speed = float(inputs.get("speed_mph", 0))
    except (TypeError, ValueError):
        speed = 0.0

    if profile_id == TDOT_PROFILE_ID:
        rate_drawing = "RD11-LR-1" if area.startswith("urban") else "RD11-LR-2"
        transition_drawings = ["RD11-SE-3", "RD11-SE-3A"] if (
            facility.startswith("divided") or "edge" in facility
        ) else ["RD11-SE-2", "RD11-SE-2A"]
        return [f"TDOT STD. DWG {drawing}" for drawing in [rate_drawing, "RD11-SE-1", *transition_drawings]]

    drawings: list[str] = []
    if area.startswith("local"):
        drawings = ["SE-1"]
    elif area.startswith("rural"):
        drawings = ["SE-2B", "SE-3B"] if "edge" in facility else ["SE-2A", "SE-3A"]
    elif area.startswith("urban"):
        if speed <= 45 and "center" in facility:
            drawings = ["SE-2E"]
        elif speed == 50 and "center" in facility:
            drawings = ["SE-2C"]
        elif speed == 50 and "edge" in facility:
            drawings = ["SE-2D"]
    return [f"MDOT STD. DWG {drawing}" for drawing in drawings]


def _source(component: str, reference: str, mode: str = "automatic") -> dict[str, str]:
    return {"component": component, "reference": reference, "mode": mode}


def calculation_sources(results: dict[str, Any]) -> list[dict[str, str]]:
    """Describe the tables, drawings, formulas, and overrides that produced a result."""
    inputs = results.get("inputs", {}) or {}
    profile_id = _result_profile_id(results)
    metadata = results.get("calculation_metadata", {}) or {}
    overrides = metadata.get("manual_overrides", {}) or {}
    area = str(inputs.get("area_type", results.get("area_type", ""))).lower()
    facility = str(inputs.get("facility", results.get("facility", ""))).lower()
    try:
        speed = float(inputs.get("speed_mph", 0))
    except (TypeError, ValueError):
        speed = 0.0
    normal_crown_only = bool(results.get("normal_crown_only"))

    if profile_id == TDOT_PROFILE_ID:
        return _tdot_calculation_sources(results, overrides, area, facility, normal_crown_only)

    sources = [_source("Crown thresholds", "MDOT Table 3-4-A")]

    if overrides.get("superelevation_rate") or inputs.get("e_manual") is not None:
        sources.append(_source("Superelevation rate", "USER OVERRIDE: superelevation rate", "user_override"))
    elif area.startswith("local"):
        sources.append(_source("Superelevation rate", "MDOT STD. DWG SE-1"))
    elif area.startswith("rural"):
        drawing = "SE-2B" if "edge" in facility else "SE-2A"
        sources.append(_source("Superelevation rate", f"MDOT STD. DWG {drawing}"))
    elif area.startswith("urban") and speed <= 45 and "center" in facility:
        sources.append(_source("Superelevation rate", "MDOT STD. DWG SE-2E"))
    elif area.startswith("urban") and speed == 50 and "center" in facility:
        sources.append(_source("Superelevation rate", "MDOT STD. DWG SE-2C"))
    elif area.startswith("urban") and speed == 50 and "edge" in facility:
        sources.append(_source("Superelevation rate", "MDOT STD. DWG SE-2D"))
    else:
        if overrides.get("side_friction") or str(inputs.get("friction_input", "")).strip():
            sources.append(_source("Side friction", "USER OVERRIDE: side friction", "user_override"))
        else:
            sources.append(_source("Side friction", "Speed-based friction table (0.24 scale)", "formula"))
        sources.append(_source("Superelevation rate", "V^2/(15R) - f formula", "formula"))

    if area.startswith("local"):
        sources.append(_source("Curve widening", "MDOT STD. DWG SE-1"))

    if normal_crown_only:
        sources.append(_source("Transition", "Normal crown - no transition required"))
        return sources

    if overrides.get("runoff_length") or inputs.get("Lr_manual") is not None:
        sources.append(_source("Runoff length", "USER OVERRIDE: runoff length", "user_override"))
    elif area.startswith("local") or (area.startswith("rural") and "center" in facility):
        sources.append(_source("Runoff length", "MDOT STD. DWG SE-3A"))
    elif area.startswith("urban") and speed <= 45 and "center" in facility:
        sources.append(_source("Runoff length", "MDOT STD. DWG SE-2E"))
    elif area.startswith("urban") and speed == 50 and "center" in facility:
        sources.append(_source("Runoff length", "MDOT STD. DWG SE-2C"))
    elif area.startswith("urban") and speed == 50 and "edge" in facility:
        sources.append(_source("Runoff length", "MDOT STD. DWG SE-2D"))
    else:
        sources.extend(_equation_sources("Runoff length", results, "MDOT Equation 3-4-1"))

    if overrides.get("tangent_runout") or inputs.get("Lt_manual") is not None:
        sources.append(_source("Tangent runout", "USER OVERRIDE: tangent runout", "user_override"))
    elif area.startswith("local") or (area.startswith("rural") and "center" in facility):
        sources.append(_source("Tangent runout", "MDOT STD. DWG SE-3A"))
    elif area.startswith("urban") and speed <= 45 and "center" in facility:
        sources.append(_source("Tangent runout", "MDOT STD. DWG SE-2E"))
    else:
        sources.extend(_equation_sources("Tangent runout", results, "Tangent runout formula"))
    return sources


def _result_profile_id(results: dict[str, Any]) -> str:
    inputs = results.get("inputs", {}) or {}
    stored = ((results.get("calculation_metadata", {}) or {}).get("criteria", {}) or {})
    requested = stored.get("profile_id") or inputs.get("criteria_profile") or MDOT_PROFILE_ID
    try:
        return normalize_profile_id(str(requested))
    except ValueError:
        return str(requested)


def _tdot_calculation_sources(
    results: dict[str, Any],
    overrides: dict[str, Any],
    area: str,
    facility: str,
    normal_crown_only: bool,
) -> list[dict[str, str]]:
    inputs = results.get("inputs", {}) or {}
    rate_drawing = "RD11-LR-1 (4% desirable)" if area.startswith("urban") else "RD11-LR-2 (8% desirable)"
    sources = [_source("Criteria profile", "TDOT Roadway Design Guidelines, Chapter 2")]
    if overrides.get("superelevation_rate") or inputs.get("e_manual") is not None:
        sources.append(_source("Superelevation rate", "USER OVERRIDE: superelevation rate", "user_override"))
    else:
        sources.append(_source("Superelevation rate", f"TDOT STD. DWG {rate_drawing}"))
    if normal_crown_only:
        sources.append(_source("Transition", "Normal crown - no transition required"))
        return sources
    if overrides.get("runoff_length") or inputs.get("Lr_manual") is not None:
        sources.append(_source("Runoff length", "USER OVERRIDE: runoff length", "user_override"))
    else:
        sources.extend(
            [
                _source("Relative gradient", "TDOT STD. DWG RD11-SE-1, Table 1"),
                _source("Lane adjustment", "TDOT STD. DWG RD11-SE-1, Table 2"),
                _source("Runoff length", "TDOT STD. DWG RD11-SE-1 runoff equation", "formula"),
            ]
        )
    if overrides.get("tangent_runout") or inputs.get("Lt_manual") is not None:
        sources.append(_source("Tangent runout", "USER OVERRIDE: tangent runout", "user_override"))
    else:
        sources.append(_source("Tangent runout", "TDOT STD. DWG RD11-SE-1, LT = LR(NC/e)", "formula"))
    placement = "RD11-SE-3/3A" if (facility.startswith("divided") or "edge" in facility) else "RD11-SE-2/2A"
    sources.append(_source("Transition placement", f"TDOT STD. DWG {placement}"))
    sources.append(
        _source(
            "Supporting criteria",
            "TDOT RD11-TS typical-section catalog recorded; no roadway-class sheet selected",
        )
    )
    return sources


def _equation_sources(component: str, results: dict[str, Any], formula: str) -> list[dict[str, str]]:
    inputs = results.get("inputs", {}) or {}
    metadata = results.get("calculation_metadata", {}) or {}
    overrides = metadata.get("manual_overrides", {}) or {}
    sources = [_source(component, "MDOT Table 3-4-B")]
    if overrides.get("relative_gradient") or str(inputs.get("relative_gradient_input", "")).strip():
        sources.append(_source(component, "USER OVERRIDE: relative gradient", "user_override"))
    else:
        sources.append(_source(component, "MDOT Table 3-4-C"))
    sources.append(_source(component, formula, "formula"))
    if overrides.get("normal_crown") and component == "Tangent runout":
        sources.append(_source(component, "USER OVERRIDE: normal crown", "user_override"))
    return sources


def criteria_for_result(results: dict[str, Any]) -> dict[str, Any]:
    """Return stored criteria metadata enriched with result-specific display provenance."""
    stored = ((results.get("calculation_metadata", {}) or {}).get("criteria", {}) or {})
    if stored:
        metadata = deepcopy(stored)
    else:
        metadata = {
            "profile_id": "legacy-unversioned",
            "profile_name": "Legacy calculation criteria",
            "revision": "unknown",
            "source_status": "SOURCE UNKNOWN: recalculate only after reviewing current criteria",
        }
    metadata["applicable_standard_drawings"] = applicable_standard_drawings(results)
    metadata["calculation_sources"] = calculation_sources(results)
    return metadata


def applicable_drawings_label(criteria: dict[str, Any]) -> str:
    drawings = criteria.get("applicable_standard_drawings", []) or []
    if drawings:
        return " / ".join(str(item) for item in drawings)
    if str(criteria.get("profile_id", "")).startswith("mdot"):
        return "No mapped MDOT standard drawing"
    return "No mapped standard drawing"


def calculation_sources_label(criteria: dict[str, Any]) -> str:
    sources = criteria.get("calculation_sources", []) or []
    return "; ".join(
        f"{source.get('component', 'Source')} - {source.get('reference', 'unknown')}"
        for source in sources
        if isinstance(source, dict)
    )
