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
        results.pop("reverse_curve_coordination", None)


def coordinate_reverse_curve_transitions(curves: Iterable[dict], enabled: bool = True) -> list[dict]:
    """Coordinate eligible MDOT reverse curves without tangent runout.

    Each curve retains its MDOT 30/70 runoff placement.  The available tangent
    must therefore be at least ``0.7Lr_exit + 0.7Lr_entry``.  Any surplus is a
    level (0%) segment between the two prescribed runoff endpoints.  A short
    tangent is recorded as a blocking check; runoff is never stretched or
    shifted to make it fit.
    """
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

        prior_pt = prior_results.get("pt_ft")
        following_pc = following_results.get("pc_ft")
        if prior_pt is None or following_pc is None:
            continue
        prior_pt = float(prior_pt)
        following_pc = float(following_pc)
        prior_runoff = float(prior_results.get("Lr", 0.0) or 0.0)
        following_runoff = float(following_results.get("Lr", 0.0) or 0.0)
        if prior_runoff <= 0.0 or following_runoff <= 0.0:
            continue

        available = following_pc - prior_pt
        required = 0.7 * prior_runoff + 0.7 * following_runoff
        check = {
            "paired_curve_indexes": [prior_index, prior_index + 1],
            "tangent_start_ft": prior_pt,
            "tangent_end_ft": following_pc,
            "available_tangent_ft": available,
            "minimum_tangent_ft": required,
            "deficit_ft": max(0.0, required - available),
            "rule": "Tmin = 0.7Lr(exit) + 0.7Lr(entry)",
            "status": "coordinated" if available + 1e-7 >= required else "short_tangent",
        }
        prior_coordination = prior_results.setdefault("reverse_curve_coordination", {"checks": []})
        following_coordination = following_results.setdefault("reverse_curve_coordination", {"checks": []})
        prior_coordination.setdefault("checks", []).append(copy.deepcopy(check))
        following_coordination.setdefault("checks", []).append(copy.deepcopy(check))
        if check["status"] == "short_tangent":
            continue

        exit_zero = prior_pt + 0.7 * prior_runoff
        entry_zero = following_pc - 0.7 * following_runoff
        prior_exit = {
            "paired_curve_index": prior_index + 1,
            "zero_station_ft": exit_zero,
            "plateau_end_ft": entry_zero,
            "runoff_length_ft": prior_runoff,
        }
        following_entry = {
            "paired_curve_index": prior_index,
            "zero_station_ft": entry_zero,
            "plateau_start_ft": exit_zero,
            "runoff_length_ft": following_runoff,
        }
        prior_coordination["exit"] = prior_exit
        following_coordination["entry"] = following_entry
        prior_results["reverse_curve_exit_zero_ft"] = exit_zero
        following_results["reverse_curve_entry_zero_ft"] = entry_zero
        prior_results.setdefault("reverse_curve_transitions", []).append({"role": "exit", **prior_exit})
        following_results.setdefault("reverse_curve_transitions", []).append({"role": "entry", **following_entry})

    for curve in coordinated:
        coordination = (curve.get("results", {}) or {}).get("reverse_curve_coordination")
        if not coordination:
            continue
        statuses = {check.get("status") for check in coordination.get("checks", [])}
        if "short_tangent" in statuses and "coordinated" in statuses:
            coordination["status"] = "partial"
        elif "short_tangent" in statuses:
            coordination["status"] = "short_tangent"
        else:
            coordination["status"] = "coordinated"
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
