"""Traceability metadata for the unchanged legacy engineering criteria."""

from __future__ import annotations

from copy import deepcopy
from typing import Any


_CRITERIA_METADATA = {
    "profile_id": "mdot-legacy-unverified",
    "profile_name": "MDOT-oriented legacy superelevation criteria",
    "revision": "unverified",
    "source_status": "SOURCE VERIFICATION REQUIRED BEFORE PAID PILOT",
    "governing_authority": (
        "Mississippi Department of Transportation (attribution from the legacy implementation; "
        "governing publication and revision have not been verified)"
    ),
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
        "This metadata does not validate the embedded values or formulas. A qualified roadway engineer "
        "must trace each criterion to the governing signed/issued source and approve golden calculations."
    ),
}


def criteria_metadata() -> dict:
    """Return an isolated copy suitable for results, projects, and reports."""
    return deepcopy(_CRITERIA_METADATA)


def applicable_standard_drawings(results: dict[str, Any]) -> list[str]:
    """Return the MDOT standard drawings associated with the recorded road classification."""
    inputs = results.get("inputs", {}) or {}
    area = str(inputs.get("area_type", results.get("area_type", ""))).lower()
    facility = str(inputs.get("facility", results.get("facility", ""))).lower()
    try:
        speed = float(inputs.get("speed_mph", 0))
    except (TypeError, ValueError):
        speed = 0.0

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
    metadata = results.get("calculation_metadata", {}) or {}
    overrides = metadata.get("manual_overrides", {}) or {}
    area = str(inputs.get("area_type", results.get("area_type", ""))).lower()
    facility = str(inputs.get("facility", results.get("facility", ""))).lower()
    try:
        speed = float(inputs.get("speed_mph", 0))
    except (TypeError, ValueError):
        speed = 0.0
    normal_crown_only = bool(results.get("normal_crown_only"))

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
    return " / ".join(str(item) for item in drawings) if drawings else "No mapped MDOT standard drawing"


def calculation_sources_label(criteria: dict[str, Any]) -> str:
    sources = criteria.get("calculation_sources", []) or []
    return "; ".join(
        f"{source.get('component', 'Source')} - {source.get('reference', 'unknown')}"
        for source in sources
        if isinstance(source, dict)
    )
