from __future__ import annotations

import json
from pathlib import Path
from typing import Any


PROJECT_VERSION = 2


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
    version = int(data.get("version", 1) or 1)
    vars_data = data.get("vars", {}) if isinstance(data.get("vars", {}), dict) else {}
    curves = []
    for curve in data.get("curves", []) or []:
        if not isinstance(curve, dict):
            continue
        curves.append(
            {
                "results": curve.get("results"),
                "meta": curve.get("meta", {}) or {},
                "notes": curve.get("notes", ""),
            }
        )
    return {
        "version": PROJECT_VERSION,
        "source_version": version,
        "vars": vars_data,
        "curves": curves,
        "last_results": data.get("last_results"),
        "last_meta": data.get("last_meta", {}) or {},
        "project_notes": data.get("project_notes", ""),
    }


def load_project(path: str | Path) -> dict[str, Any]:
    with Path(path).open("r", encoding="utf-8") as handle:
        return normalize_project(json.load(handle))


def save_project(path: str | Path, data: dict[str, Any]) -> None:
    payload = normalize_project(data)
    payload["source_version"] = PROJECT_VERSION
    with Path(path).open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2)
