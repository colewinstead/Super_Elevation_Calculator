"""Canonical MDOT lane-transition profiles.

This module owns the station/slope geometry used by the browser, engineering
lookup, QA, and every export.  Criteria lookup remains in :mod:`Super`; this
module only turns the recorded rate, runoff, runout, PC, and PT into piecewise
linear lane profiles.
"""

from __future__ import annotations

from typing import Any


EPSILON = 1e-9


def outside_lane(direction: str) -> str:
    return "left" if str(direction).strip().lower().startswith("r") else "right"


def _event(label: str, station_ft: float, slope_pct: float, note: str, event_type: str) -> dict[str, Any]:
    return {
        "label": label,
        "station_ft": float(station_ft),
        "slope_pct": float(slope_pct),
        "note": note,
        "event_type": event_type,
    }


def _linear_value(station: float, start_station: float, start_value: float, end_station: float, end_value: float) -> float:
    if end_station <= start_station + EPSILON:
        return float(end_value)
    fraction = max(0.0, min(1.0, (station - start_station) / (end_station - start_station)))
    return float(start_value) + fraction * (float(end_value) - float(start_value))


def _full_super_slopes(results: dict, direction: str) -> dict[str, float]:
    nc_pct = abs(float(results.get("inputs", {}).get("normal_crown", 0.02) or 0.02) * 100.0)
    e_pct = abs(float(results.get("e", 0.0) or 0.0) * 100.0)
    reverse_crown = str(results.get("crown_state", "")).lower().startswith("reverse")
    magnitude = nc_pct if reverse_crown else e_pct
    outside = outside_lane(direction)
    return {
        "left": magnitude if outside == "left" else -magnitude,
        "right": magnitude if outside == "right" else -magnitude,
    }


def _append_entry(
    rows: list[dict[str, Any]],
    results: dict,
    side: str,
    target_slope: float,
    coordinated: dict | None,
) -> None:
    pc = float(results["pc_ft"])
    full = float(results["full_super_ft"])
    runoff = float(results.get("Lr", 0.0) or 0.0)
    runout = float(results.get("Lt", 0.0) or 0.0)
    zero = float(results.get("reverse_crown_ft", pc - 0.7 * runoff))
    nc_pct = abs(float(results.get("inputs", {}).get("normal_crown", 0.02) or 0.02) * 100.0)
    outside = outside_lane(str(results.get("curve_direction", "left")))

    if coordinated:
        zero = float(coordinated["zero_station_ft"])
        rows.append(_event("0%", zero, 0.0, "Shared reverse-curve transition meeting point", "Reverse curve zero"))
        pc_slope = _linear_value(pc, zero, 0.0, full, target_slope)
        rows.append(_event("PC", pc, pc_slope, "Linear slope on coordinated reverse-curve transition", "PC reverse-curve runoff"))
        rows.append(_event("FULL SUPER", full, target_slope, "PC + 0.3Lr", "Full super"))
        return

    pnc = float(results.get("pnc_ft", zero - runout))
    rows.append(_event("NC", pnc, -nc_pct, "Start of tangent runout", "Normal crown"))
    if side == outside:
        rows.append(_event("0%", zero, 0.0, "End of tangent runout; start of runoff", "Reverse crown"))
        pc_slope = _linear_value(pc, zero, 0.0, full, target_slope)
    else:
        target_magnitude = abs(target_slope)
        if target_magnitude <= nc_pct + EPSILON:
            rotation_start = full
        else:
            rotation_start = zero + runoff * nc_pct / target_magnitude
        rows.append(_event("BEGIN ROTATION", rotation_start, -nc_pct, "MDOT SE-3A X1 = Lr(NC/e)", "Inside-lane rotation"))
        pc_slope = _linear_value(pc, rotation_start, -nc_pct, full, target_slope)
    rows.append(_event("PC", pc, pc_slope, "70% of runoff occurs before PC", "PC 70% runoff"))
    rows.append(_event("FULL SUPER", full, target_slope, "PC + 0.3Lr", "Full super"))


def _append_exit(
    rows: list[dict[str, Any]],
    results: dict,
    side: str,
    target_slope: float,
    coordinated: dict | None,
) -> None:
    pt_value = results.get("pt_ft")
    full_value = results.get("full_super_out_ft")
    if pt_value is None or full_value is None:
        return
    pt = float(pt_value)
    full = float(full_value)
    runoff = float(results.get("Lr", 0.0) or 0.0)
    runout = float(results.get("Lt", 0.0) or 0.0)
    zero = float(results.get("reverse_crown_out_ft", pt + 0.7 * runoff))
    nc_pct = abs(float(results.get("inputs", {}).get("normal_crown", 0.02) or 0.02) * 100.0)
    outside = outside_lane(str(results.get("curve_direction", "left")))

    rows.append(_event("FULL SUPER", full, target_slope, "PT - 0.3Lr", "End full super"))
    if coordinated:
        zero = float(coordinated["zero_station_ft"])
        pt_slope = _linear_value(pt, full, target_slope, zero, 0.0)
        rows.append(_event("PT", pt, pt_slope, "Linear slope on coordinated reverse-curve transition", "PT reverse-curve runoff"))
        rows.append(_event("0%", zero, 0.0, "Shared reverse-curve transition meeting point", "Reverse curve zero"))
        return

    if side == outside:
        rotation_end = zero
        end_slope = 0.0
    else:
        target_magnitude = abs(target_slope)
        if target_magnitude <= nc_pct + EPSILON:
            rotation_end = full
        else:
            rotation_end = zero - runoff * nc_pct / target_magnitude
        end_slope = -nc_pct
    pt_slope = _linear_value(pt, full, target_slope, rotation_end, end_slope)
    rows.append(_event("PT", pt, pt_slope, "70% of runoff occurs after PT", "PT 70% runoff"))
    if side == outside:
        rows.append(_event("0%", zero, 0.0, "End of runoff; start of tangent runout", "End runoff"))
    else:
        rows.append(_event("END ROTATION", rotation_end, -nc_pct, "MDOT SE-3A X1 = Lr(NC/e)", "Inside-lane rotation"))
    rows.append(_event("NC", zero + runout, -nc_pct, "End of tangent runout", "Back to normal crown"))


def build_mdot_lane_events(results: dict, direction: str) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """Build the canonical piecewise-linear MDOT lane profiles."""
    direction_text = (direction or "left").strip().lower() or "left"
    working = dict(results)
    working["curve_direction"] = direction_text
    pc = float(working.get("pc_ft", 0.0) or 0.0)
    pt_value = working.get("pt_ft")
    nc_pct = abs(float(working.get("inputs", {}).get("normal_crown", 0.02) or 0.02) * 100.0)

    if working.get("normal_crown_only"):
        left = [_event("NC", pc, -nc_pct, "Normal crown maintained", "Normal crown")]
        right = [_event("NC", pc, -nc_pct, "Normal crown maintained", "Normal crown")]
        if pt_value is not None and not abs(float(pt_value) - pc) <= EPSILON:
            left.append(_event("NC", float(pt_value), -nc_pct, "Normal crown maintained through curve", "Normal crown"))
            right.append(_event("NC", float(pt_value), -nc_pct, "Normal crown maintained through curve", "Normal crown"))
        return left, right

    coordination = working.get("reverse_curve_coordination", {}) or {}
    entry = coordination.get("entry")
    exit_transition = coordination.get("exit")
    targets = _full_super_slopes(working, direction_text)
    lane_rows: dict[str, list[dict[str, Any]]] = {"left": [], "right": []}
    for side in ("left", "right"):
        _append_entry(lane_rows[side], working, side, targets[side], entry)
        _append_exit(lane_rows[side], working, side, targets[side], exit_transition)
        lane_rows[side].sort(key=lambda item: (float(item["station_ft"]), item["label"]))
    return lane_rows["left"], lane_rows["right"]
