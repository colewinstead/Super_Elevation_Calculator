from __future__ import annotations

import copy
from typing import Iterable

import Super


_ENTRY_TRANSITION_KEYS = ("pnc_ft", "reverse_crown_ft", "full_super_ft")
_EXIT_TRANSITION_KEYS = ("full_super_out_ft", "reverse_crown_out_ft", "pnc_out_ft")


def _enabled(value: object) -> bool:
    return str(value or "").strip().lower() in {"1", "true", "yes", "on"}


def _restore_reverse_curve_transitions(curves: list[dict]) -> None:
    for curve in curves:
        results = curve.get("results", {}) or {}
        originals = results.pop("uncoordinated_reverse_curve_transition", {}) or {}
        for key, value in originals.get("entry", {}).items():
            results[key] = value
        for key, value in originals.get("exit", {}).items():
            results[key] = value
        results.pop("reverse_curve_entry_zero_ft", None)
        results.pop("reverse_curve_exit_zero_ft", None)
        results.pop("reverse_curve_transitions", None)


def coordinate_reverse_curve_transitions(curves: Iterable[dict], enabled: bool = True) -> list[dict]:
    """Coordinate consecutive opposite-direction MDOT curves through a tangent midpoint."""
    coordinated = copy.deepcopy(list(curves))
    _restore_reverse_curve_transitions(coordinated)
    if not enabled:
        return coordinated

    for prior_index, (prior, following) in enumerate(zip(coordinated, coordinated[1:])):
        prior_results = prior.get("results", {}) or {}
        following_results = following.get("results", {}) or {}
        prior_profile = str(prior_results.get("calculation_metadata", {}).get("criteria", {}).get("profile_id", ""))
        following_profile = str(following_results.get("calculation_metadata", {}).get("criteria", {}).get("profile_id", ""))
        prior_direction = str(prior.get("meta", {}).get("curve_direction", "left")).lower()
        following_direction = str(following.get("meta", {}).get("curve_direction", "left")).lower()
        if not prior_profile.startswith("mdot") or not following_profile.startswith("mdot"):
            continue
        if prior_direction == following_direction:
            continue
        if prior_results.get("normal_crown_only") or following_results.get("normal_crown_only"):
            continue
        if str(prior_results.get("crown_state", "")).lower().startswith("reverse"):
            continue
        if str(following_results.get("crown_state", "")).lower().startswith("reverse"):
            continue

        prior_pt = prior_results.get("pt_ft")
        following_pc = following_results.get("pc_ft")
        if prior_pt is None or following_pc is None:
            continue
        prior_pt = float(prior_pt)
        following_pc = float(following_pc)
        if following_pc < prior_pt:
            continue

        midpoint = (prior_pt + following_pc) / 2.0
        prior_originals = prior_results.setdefault("uncoordinated_reverse_curve_transition", {})
        prior_originals["exit"] = {key: prior_results.get(key) for key in _EXIT_TRANSITION_KEYS}
        following_originals = following_results.setdefault("uncoordinated_reverse_curve_transition", {})
        following_originals["entry"] = {key: following_results.get(key) for key in _ENTRY_TRANSITION_KEYS}

        prior_results["full_super_out_ft"] = midpoint - float(prior_results.get("Lr", 0.0) or 0.0)
        prior_results["reverse_crown_out_ft"] = midpoint
        prior_results["pnc_out_ft"] = None
        prior_results["reverse_curve_exit_zero_ft"] = midpoint
        prior_results.setdefault("reverse_curve_transitions", []).append({
            "role": "exit",
            "paired_curve_index": prior_index + 1,
            "tangent_start_ft": prior_pt,
            "tangent_end_ft": following_pc,
            "zero_slope_ft": midpoint,
        })

        following_results["pnc_ft"] = None
        following_results["reverse_crown_ft"] = midpoint
        following_results["full_super_ft"] = midpoint + float(following_results.get("Lr", 0.0) or 0.0)
        following_results["reverse_curve_entry_zero_ft"] = midpoint
        following_results.setdefault("reverse_curve_transitions", []).append({
            "role": "entry",
            "paired_curve_index": prior_index,
            "tangent_start_ft": prior_pt,
            "tangent_end_ft": following_pc,
            "zero_slope_ft": midpoint,
        })
    return coordinated


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
            "landxml_curve_index": preset.get("landxml_curve_index"),
            "landxml_curve_id": str(preset.get("landxml_curve_id", "") or ""),
            "project_name": str(shared_inputs.get("project_name", "") or ""),
            "route_name": str(shared_inputs.get("route_name", "") or ""),
            "alignment_name": str(preset.get("alignment_name", "") or ""),
            "curve_name": str(preset.get("curve_name", "") or ""),
            "curve_direction": str(preset.get("curve_direction", "left") or "left"),
        },
        "notes": str(shared_inputs.get("curve_notes", "") or ""),
    }


def build_curves_from_presets(presets: Iterable[dict], shared_inputs: dict[str, str]) -> list[dict]:
    curves = [build_curve_from_preset(preset, shared_inputs) for preset in presets]
    return coordinate_reverse_curve_transitions(
        curves,
        enabled=_enabled(shared_inputs.get("coordinate_reverse_curves")),
    )
