from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path
from typing import Any

from app_info import APP_VERSION, CALCULATION_ENGINE_VERSION
from criteria_info import criteria_metadata


PROJECT_VERSION = 3


class ProjectFormatError(ValueError):
    """Raised when a project cannot be safely interpreted by this release."""


def calculation_provenance(curves: list[dict], last_results: dict | None = None) -> tuple[str, dict]:
    """Summarize the engines/criteria represented by saved calculation results."""
    results_list = [curve.get("results") for curve in curves if isinstance(curve, dict) and curve.get("results")]
    if not results_list and last_results:
        results_list = [last_results]
    if not results_list:
        return CALCULATION_ENGINE_VERSION, criteria_metadata()

    engines: set[str] = set()
    criteria_by_profile: dict[str, dict] = {}
    for results in results_list:
        metadata = results.get("calculation_metadata", {}) if isinstance(results, dict) else {}
        engine = str(metadata.get("engine_version") or "legacy-unversioned")
        criteria = metadata.get("criteria") if isinstance(metadata.get("criteria"), dict) else {}
        profile_id = str(criteria.get("profile_id") or "legacy-unversioned")
        engines.add(engine)
        criteria_by_profile.setdefault(
            profile_id,
            criteria or {"profile_id": profile_id, "source_status": "unknown"},
        )
    engine_summary = next(iter(engines)) if len(engines) == 1 else "mixed"
    if len(criteria_by_profile) == 1:
        criteria_summary = next(iter(criteria_by_profile.values()))
    else:
        criteria_summary = {
            "profile_id": "mixed",
            "profiles": sorted(criteria_by_profile),
            "source_status": "REVIEW REQUIRED: project contains calculations from multiple criteria profiles",
        }
    return engine_summary, criteria_summary


def curve_label(meta: dict, results: dict | None) -> str:
    alignment = meta.get("alignment_name", "Unnamed alignment")
    curve = meta.get("curve_name", "Unnamed curve")
    direction = meta.get("curve_direction", "left")
    inputs = (results or {}).get("inputs", {})
    pc = inputs.get("pc", "?")
    pt = inputs.get("pt", "?") or "n/a"
    speed = inputs.get("speed_mph", "?")
    radius = inputs.get("radius_ft", "?")
    if isinstance(speed, (int, float)) and float(speed).is_integer():
        speed = str(int(speed))
    if isinstance(radius, (int, float)) and float(radius).is_integer():
        radius = str(int(radius))
    return f"{alignment} | {curve} | {direction} | PC {pc} PT {pt} | V {speed} mph | R {radius} ft"


def normalize_project(data: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(data, dict):
        raise ProjectFormatError("Project root must be a JSON object.")
    try:
        version = int(data.get("version", 1) or 1)
    except (TypeError, ValueError) as exc:
        raise ProjectFormatError("Project schema version must be an integer.") from exc
    if version < 1:
        raise ProjectFormatError(f"Project schema version {version} is invalid.")
    if version > PROJECT_VERSION:
        raise ProjectFormatError(
            f"This project uses schema version {version}, but this application supports up to version "
            f"{PROJECT_VERSION}. Install a newer application release to open it safely."
        )

    vars_data = data.get("vars", {}) if isinstance(data.get("vars", {}), dict) else {}
    curves = []
    raw_curves = data.get("curves", []) or []
    if not isinstance(raw_curves, list):
        raise ProjectFormatError("Project 'curves' must be a list.")
    for curve in raw_curves:
        if not isinstance(curve, dict):
            continue
        curves.append(
            {
                "results": curve.get("results"),
                "meta": curve.get("meta", {}) or {},
                "notes": curve.get("notes", ""),
            }
        )

    legacy = version < PROJECT_VERSION
    return {
        "version": PROJECT_VERSION,
        "source_version": version,
        "application_version": data.get("application_version") or ("legacy-unversioned" if legacy else APP_VERSION),
        "calculation_engine_version": data.get("calculation_engine_version")
        or ("legacy-unversioned" if legacy else CALCULATION_ENGINE_VERSION),
        "criteria": data.get("criteria") or ({"profile_id": "legacy-unversioned", "source_status": "unknown"} if legacy else criteria_metadata()),
        "vars": vars_data,
        "curves": curves,
        "last_results": data.get("last_results"),
        "last_meta": data.get("last_meta", {}) or {},
        "project_notes": data.get("project_notes", ""),
    }


def load_project(path: str | Path) -> dict[str, Any]:
    file_path = Path(path)
    try:
        with file_path.open("r", encoding="utf-8") as handle:
            raw = json.load(handle)
    except json.JSONDecodeError as exc:
        raise ProjectFormatError(
            f"The project is not valid JSON (line {exc.lineno}, column {exc.colno})."
        ) from exc
    return normalize_project(raw)


def save_project(path: str | Path, data: dict[str, Any]) -> None:
    file_path = Path(path)
    payload = normalize_project(data)
    payload["source_version"] = PROJECT_VERSION
    file_path.parent.mkdir(parents=True, exist_ok=True)
    temp_name: str | None = None
    try:
        with tempfile.NamedTemporaryFile(
            "w", encoding="utf-8", dir=file_path.parent, prefix=f".{file_path.name}.", suffix=".tmp", delete=False
        ) as handle:
            temp_name = handle.name
            json.dump(payload, handle, indent=2)
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temp_name, file_path)
    finally:
        if temp_name and os.path.exists(temp_name):
            os.unlink(temp_name)
