"""Platform-neutral application services shared by Tkinter and browser clients."""

from __future__ import annotations

import io
import json
import os
import tempfile
from pathlib import Path
from typing import Any, Callable

import Super
from app_info import APP_NAME, APP_VERSION, CALCULATION_ENGINE_VERSION
from criteria_info import criteria_metadata
import super_batch
import super_dxf
import super_exports
import super_landxml
from super_lane import lane_profile_points, parse_slope_percent, slope_at_station, slope_matches
import super_pdf
import super_project


DEFAULT_INPUTS = {
    "curve_direction": "left",
    "facility": "centerline",
    "area": "rural",
    "lane_width": "12",
    "lanes_rotated": "2",
    "normal_crown": "0.02",
    "station_format": True,
}


def application_manifest() -> dict[str, Any]:
    return {
        "name": APP_NAME,
        "application_version": APP_VERSION,
        "calculation_engine_version": CALCULATION_ENGINE_VERSION,
        "project_schema_version": super_project.PROJECT_VERSION,
        "criteria": criteria_metadata(),
        "defaults": dict(DEFAULT_INPUTS),
        "options": {
            "curve_direction": ["left", "right"],
            "facility": ["centerline", "outside edge"],
            "area": ["rural", "urban", "local"],
            "speed": [str(value) for value in range(15, 85, 5)],
            "coordinate_systems": list(super_dxf.MDOT_COORDINATE_SYSTEMS),
        },
    }


def _station_equations(value: Any) -> list[dict]:
    if isinstance(value, list):
        return value
    equations: list[dict] = []
    for entry in str(value or "").split(";"):
        entry = entry.strip()
        if not entry:
            continue
        if "=" not in entry:
            raise ValueError("Manual station equations must use Back=Ahead format.")
        back, ahead = (part.strip() for part in entry.split("=", 1))
        equations.append({"staBack": str(Super.parse_station(back)), "staAhead": str(Super.parse_station(ahead))})
    return equations


def _station_range(value: Any) -> tuple[float, float] | None:
    if value in (None, "", []):
        return None
    if isinstance(value, (list, tuple)) and len(value) == 2:
        start, end = float(value[0]), float(value[1])
    else:
        text = str(value)
        if "," not in text:
            raise ValueError("Internal alignment range must use Start,End format.")
        start_text, end_text = (part.strip() for part in text.split(",", 1))
        start, end = Super.parse_station(start_text), Super.parse_station(end_text)
    if end < start:
        raise ValueError("Internal alignment range end must be greater than its start.")
    return start, end


def calculate_curve(inputs: dict[str, Any]) -> dict[str, Any]:
    """Calculate one curve and return structured presentation data."""
    values = {**DEFAULT_INPUTS, **(inputs or {})}
    area = str(values.get("area", "rural"))
    facility = "centerline" if area.lower().startswith("local") else str(values.get("facility", "centerline"))
    arguments = (
        str(values.get("pc", "")),
        str(values.get("pt", "")),
        str(values.get("speed", "")),
        str(values.get("radius", "")),
        facility,
        area,
        str(values.get("lane_width", "12")),
        str(values.get("lanes_rotated", "2")),
        str(values.get("e_manual", "")),
        str(values.get("friction", "")),
        str(values.get("rel_grad", "")),
        str(values.get("normal_crown", "0.02")),
        str(values.get("Lr_manual", "")),
        str(values.get("Lt_manual", "")),
        _station_equations(values.get("station_equations")),
        _station_range(values.get("alignment_station_range")),
    )
    results = Super.calculate_superelevation(*arguments)
    baseline_arguments = list(arguments)
    for index in (8, 9, 10, 12, 13):
        baseline_arguments[index] = ""
    try:
        baseline = Super.calculate_superelevation(*baseline_arguments)
    except ValueError:
        baseline = results
    direction = str(values.get("curve_direction", "left") or "left")
    station_format = bool(values.get("station_format", True))
    left_rows, right_rows = super_exports.build_lane_rows(results, direction, station_format)
    return {
        "results": results,
        "baseline": baseline,
        "formatted_results": Super.format_results(results, station_format),
        "lanes": {"left": left_rows, "right": right_rows},
    }


def present_results(results: dict, direction: str = "left", station_format: bool = True) -> dict[str, Any]:
    left_rows, right_rows = super_exports.build_lane_rows(results, direction, station_format)
    return {
        "results": results,
        "baseline": results,
        "formatted_results": Super.format_results(results, station_format),
        "lanes": {"left": left_rows, "right": right_rows},
    }


def parse_landxml(content: str, filename: str = "alignment.xml") -> dict[str, Any]:
    data = super_landxml.parse_landxml_text(content, filename)
    source = super_project.make_landxml_source(filename, content)
    return {
        "source": source,
        "summary": {
            "filename": source["filename"],
            "alignment_name": data.alignment_name,
            "start_station": data.start_station,
            "alignment_length": data.alignment_length,
            "linear_unit": data.linear_unit,
            "station_equation_count": len(data.station_equations),
            "curve_count": len(data.curves),
            "warnings": list(data.warnings),
        },
        "curve_presets": data.curve_records(),
    }


def build_all_landxml_curves(content: str, filename: str, shared_inputs: dict[str, Any]) -> list[dict]:
    data = super_landxml.parse_landxml_text(content, filename)
    normalized = {key: str(value) for key, value in shared_inputs.items()}
    return super_batch.build_curves_from_presets(data.curve_records(), normalized)


def lookup(results: dict, direction: str, station_text: str = "", slope_text: str = "") -> dict[str, Any]:
    if not station_text.strip() and not slope_text.strip():
        raise ValueError("Enter a station, a super value, or both.")
    points = lane_profile_points(results, direction)
    response: dict[str, Any] = {"station": None, "slope": None, "lanes": {}}
    reference = float(results.get("reverse_crown_ft", 0.0))
    if station_text.strip():
        station = Super.civil_to_internal_station(
            Super.parse_station(station_text), results.get("station_equations"), results.get("alignment_station_range")
        )
        reference = station
        response["station"] = {
            "label": Super.format_result_station(results, station, True),
            "internal_ft": station,
            "slopes": {
                lane: {
                    "percent": slope_at_station(points[lane], station),
                    "label": super_exports.format_slope_label(slope_at_station(points[lane], station)),
                }
                for lane in ("left", "right")
            },
        }
    if slope_text.strip():
        target = parse_slope_percent(slope_text)
        response["slope"] = {"percent": target, "label": super_exports.format_slope_label(target)}
        for lane in ("left", "right"):
            matches = slope_matches(points[lane], target)
            rendered = []
            nearest = None
            if station_text.strip() and matches:
                nearest = min(
                    range(len(matches)),
                    key=lambda index: _distance_to_range(matches[index], reference),
                )
            for index, (start, end) in enumerate(matches):
                rendered.append(
                    {
                        "start": Super.format_result_station(results, start, True),
                        "end": Super.format_result_station(results, end, True),
                        "is_range": end - start > 1e-6,
                        "nearest": index == nearest,
                    }
                )
            response["lanes"][lane] = rendered
    return response


def _distance_to_range(station_range: tuple[float, float], station: float) -> float:
    start, end = station_range
    if start <= station <= end:
        return 0.0
    return min(abs(station - start), abs(station - end))


def project_load(content: str) -> dict[str, Any]:
    data = super_project.loads_project(content)
    source = data.get("landxml_source")
    landxml = parse_landxml(source["content"], source["filename"]) if source else None
    return {"project": data, "landxml": landxml}


def project_save(data: dict[str, Any]) -> str:
    return super_project.dumps_project(data)


def export_ord_csv(curves: list[dict]) -> dict[str, Any]:
    handle = io.StringIO(newline="")
    warnings = super_exports.write_ord_csv(handle, curves)
    return {"content": handle.getvalue(), "warnings": warnings}


def _temporary_export(suffix: str, exporter: Callable[[str], Any]) -> tuple[bytes, list[str]]:
    path = ""
    try:
        with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as handle:
            path = handle.name
        result = exporter(path)
        warnings = result if isinstance(result, list) else []
        return Path(path).read_bytes(), warnings
    finally:
        if path and os.path.exists(path):
            os.unlink(path)


def export_pdf(curves: list[dict]) -> dict[str, Any]:
    content, warnings = _temporary_export(".pdf", lambda path: super_pdf.export_pdf(path, curves))
    return {"content": content, "warnings": warnings}


def export_detail_dxf(curves: list[dict]) -> dict[str, Any]:
    content, warnings = _temporary_export(".dxf", lambda path: super_dxf.export_detail_dxf(path, curves))
    return {"content": content, "warnings": warnings}


def export_overlay_dxf(
    curves: list[dict], landxml_source: dict[str, str], coordinate_config: dict[str, Any]
) -> dict[str, Any]:
    source = super_project.normalize_landxml_source(landxml_source)
    if not source:
        raise ValueError("Select LandXML before exporting an overlay DXF.")
    data = super_landxml.parse_landxml_text(source["content"], source["filename"])
    errors, diagnostic_warnings = super_dxf.overlay_export_issues(curves, data)
    if errors:
        raise ValueError("\n".join(errors))
    content, warnings = _temporary_export(
        ".dxf", lambda path: super_dxf.export_overlay_dxf(path, curves, data, coordinate_config)
    )
    return {"content": content, "warnings": list(dict.fromkeys(diagnostic_warnings + warnings))}


def dispatch(operation: str, payload_json: str = "{}") -> Any:
    """Stable JSON bridge invoked by the Pyodide worker."""
    payload = json.loads(payload_json or "{}")
    operations: dict[str, Callable[..., Any]] = {
        "manifest": lambda: application_manifest(),
        "calculate": lambda: calculate_curve(payload.get("inputs", payload)),
        "present_results": lambda: present_results(
            payload["results"], payload.get("direction", "left"), bool(payload.get("station_format", True))
        ),
        "parse_landxml": lambda: parse_landxml(payload["content"], payload.get("filename", "alignment.xml")),
        "build_all_landxml_curves": lambda: build_all_landxml_curves(
            payload["content"], payload.get("filename", "alignment.xml"), payload.get("shared_inputs", {})
        ),
        "lookup": lambda: lookup(
            payload["results"], payload.get("direction", "left"), payload.get("station", ""), payload.get("slope", "")
        ),
        "project_load": lambda: project_load(payload["content"]),
        "project_save": lambda: project_save(payload["project"]),
        "export_ord_csv": lambda: export_ord_csv(payload["curves"]),
        "export_pdf": lambda: export_pdf(payload["curves"]),
        "export_detail_dxf": lambda: export_detail_dxf(payload["curves"]),
        "export_overlay_dxf": lambda: export_overlay_dxf(
            payload["curves"], payload["landxml_source"], payload.get("coordinate_config", {})
        ),
    }
    try:
        handler = operations[operation]
    except KeyError as exc:
        raise ValueError(f"Unsupported browser operation: {operation}") from exc
    return handler()
