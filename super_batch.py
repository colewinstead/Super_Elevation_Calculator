from __future__ import annotations

from typing import Iterable

import Super


def build_curve_from_preset(preset: dict, shared_inputs: dict[str, str]) -> dict:
    results = Super.calculate_superelevation(
        str(preset["pc_station_label"]),
        str(preset.get("pt_station_label", "") or ""),
        str(shared_inputs.get("speed", "")),
        str(preset["radius_ft"]),
        str(shared_inputs.get("facility", "centerline")),
        str(shared_inputs.get("area", "rural")),
        str(shared_inputs.get("lane_width", "12")),
        str(shared_inputs.get("lanes_rotated", "2")),
        str(shared_inputs.get("e_manual", "")),
        str(shared_inputs.get("friction", "")),
        str(shared_inputs.get("rel_grad", "")),
        str(shared_inputs.get("normal_crown", "0.02")),
        str(shared_inputs.get("Lr_manual", "")),
        str(shared_inputs.get("Lt_manual", "")),
        preset.get("station_equations"),
        preset.get("alignment_station_range"),
        str(shared_inputs.get("criteria_profile", "mdot-rdsd-2026-04-22")),
    )
    return {
        "results": results,
        "meta": {
            "project_name": str(shared_inputs.get("project_name", "") or ""),
            "route_name": str(shared_inputs.get("route_name", "") or ""),
            "alignment_name": str(preset.get("alignment_name", "") or ""),
            "curve_name": str(preset.get("curve_name", "") or ""),
            "curve_direction": str(preset.get("curve_direction", "left") or "left"),
        },
        "notes": str(shared_inputs.get("curve_notes", "") or ""),
    }


def build_curves_from_presets(presets: Iterable[dict], shared_inputs: dict[str, str]) -> list[dict]:
    return [build_curve_from_preset(preset, shared_inputs) for preset in presets]
