from __future__ import annotations

import csv
from dataclasses import dataclass
from typing import Iterable, TextIO

import Super


ORD_HEADERS = [
    "SuperelevationLane",
    "Station",
    "CrossSlope",
    "PivotAbout",
    "PointType",
    "TransitionType",
    "NonLinearCurveLength",
]

@dataclass(frozen=True)
class ExportWarning:
    message: str


def format_slope_value(value: float, precision: int = 2) -> str:
    rounded = round(float(value), precision)
    if rounded > 0:
        return f"+{rounded:.{precision}f}"
    return f"{rounded:.{precision}f}"


def format_slope_label(value: float, precision: int = 2) -> str:
    return f"{format_slope_value(value, precision)}%"


def slope_decimal(value: float, precision: int = 4) -> str:
    return format_slope_value(float(value) / 100.0, precision)


def outside_lane(direction: str) -> str:
    return "left" if str(direction).strip().lower().startswith("r") else "right"


def inside_lane(direction: str) -> str:
    return "right" if outside_lane(direction) == "left" else "left"


def pivot_about_for_side(side: str) -> str:
    return "RS" if side == "left" else "LS"


def lane_name_for_side(side: str, curve: dict) -> str:
    meta = curve.get("meta", {}) or {}
    key = f"{side}_lane_name"
    if str(meta.get(key, "")).strip():
        return str(meta[key]).strip()
    return f"{side.title()} Lane"


def _format_station(value: float | None, station_format: bool) -> str:
    if value is None:
        return "n/a"
    return Super.format_station(value, station_format)


def _make_row(
    label: str,
    station: float | None,
    slope_pct: float,
    note: str,
    event_type: str,
    station_format: bool,
) -> dict:
    return {
        "label": label,
        "station": _format_station(station, station_format),
        "station_ft": station,
        "slope": format_slope_value(slope_pct),
        "slope_pct": float(slope_pct),
        "slope_decimal": float(slope_pct) / 100.0,
        "slope_label": format_slope_label(slope_pct),
        "note": note,
        "event_type": event_type,
    }


def build_lane_rows(results: dict, direction: str, station_format: bool = True) -> tuple[list[dict], list[dict]]:
    direction_text = (direction or "left").strip().lower() or "left"
    outside = outside_lane(direction_text)

    L = float(results.get("Lr", 0.0) or 0.0)
    Lt = float(results.get("Lt", 0.0) or 0.0)
    e = float(results.get("e", 0.0) or 0.0)
    normal_crown = float(results.get("inputs", {}).get("normal_crown", 0.02) or 0.02)
    reverse_crown = float(results.get("reverse_crown_ft", 0.0) or 0.0)
    reverse_crown_out = results.get("reverse_crown_out_ft")
    reverse_crown_out = None if reverse_crown_out is None else float(reverse_crown_out)

    pc = reverse_crown + 0.7 * L
    full_super_pc = float(results.get("full_super_ft", 0.0) or 0.0)
    full_super_pt = results.get("full_super_out_ft")
    full_super_pt = None if full_super_pt is None else float(full_super_pt)
    pt = reverse_crown_out - 0.7 * L if reverse_crown_out is not None else None

    nc_pct = normal_crown * 100.0
    e_pct = e * 100.0
    e70_pct = e_pct * 0.7

    reverse_crown_case = (
        str(results.get("crown_state", "")).lower().startswith("reverse")
        or str(results.get("e_source", "")).lower().startswith("reverse")
    )
    normal_crown_only = bool(results.get("normal_crown_only"))

    def finish(rows: list[dict]) -> list[dict]:
        for row in rows:
            row["station"] = Super.format_result_station(results, row.get("station_ft"), station_format)
        return rows

    def lane_rows(side: str) -> list[dict]:
        final_sign = 1.0 if side == outside else -1.0
        rows: list[dict] = []

        if normal_crown_only:
            rows.append(
                _make_row(
                    "NC",
                    pc,
                    -nc_pct,
                    "Normal crown maintained; no superelevation transition required",
                    "Normal crown",
                    station_format,
                )
            )
            if pt is not None and pt != pc:
                rows.append(
                    _make_row(
                        "NC",
                        pt,
                        -nc_pct,
                        "Normal crown maintained through curve",
                        "Normal crown",
                        station_format,
                    )
                )
            return finish(rows)

        if reverse_crown_case:
            start_station = reverse_crown - Lt
            end_station = reverse_crown_out + Lt if reverse_crown_out is not None else None
            if side == outside:
                rows.append(_make_row("NC", start_station, -nc_pct, "Sta = PC - 0.7L - Lt", "Normal crown", station_format))
                rows.append(_make_row("0%", reverse_crown, 0.0, "Sta = PC - 0.7L", "Reverse crown", station_format))
                rows.append(_make_row("PC", pc, final_sign * nc_pct * 0.7, "70% super", "PC 70% super", station_format))
                rows.append(
                    _make_row("FULL SUPER", full_super_pc, final_sign * nc_pct, "Sta = PC + 0.3L", "Full super", station_format)
                )
                if pt is not None and full_super_pt is not None and reverse_crown_out is not None:
                    rows.append(
                        _make_row(
                            "FULL SUPER",
                            full_super_pt,
                            final_sign * nc_pct,
                            "Sta = PT - 0.3L",
                            "End full super",
                            station_format,
                        )
                    )
                    rows.append(_make_row("PT", pt, final_sign * nc_pct * 0.7, "70% super", "PT 70% super", station_format))
                    rows.append(_make_row("0%", reverse_crown_out, 0.0, "Sta = PT + 0.7L", "End runoff", station_format))
                if end_station is not None:
                    rows.append(_make_row("NC", end_station, -nc_pct, "0% + runout", "Back to normal crown", station_format))
            else:
                rows.append(_make_row("NC", start_station, -nc_pct, "Sta = PC - 0.7L - Lt", "Normal crown", station_format))
                rows.append(_make_row("PC", pc, -nc_pct * 0.7, "70% super", "PC 70% super", station_format))
                rows.append(
                    _make_row("FULL SUPER", full_super_pc, -nc_pct, "Sta = PC + 0.3L", "Full super", station_format)
                )
                if pt is not None and full_super_pt is not None:
                    rows.append(
                        _make_row("FULL SUPER", full_super_pt, -nc_pct, "Sta = PT - 0.3L", "End full super", station_format)
                    )
                    rows.append(_make_row("PT", pt, -nc_pct * 0.7, "70% super", "PT 70% super", station_format))
                if end_station is not None:
                    rows.append(_make_row("NC", end_station, -nc_pct, "Sta = PT + 0.7L + Lt", "Back to normal crown", station_format))
            return finish(rows)

        if side == outside:
            rows.append(_make_row("NC", reverse_crown - Lt, -nc_pct, "Sta = PC - 0.7L - Lt", "Normal crown", station_format))
            rows.append(_make_row("0%", reverse_crown, 0.0, "Sta = PC - 0.7L", "Reverse crown", station_format))
            rows.append(_make_row("2%", reverse_crown + Lt, nc_pct, "Sta = PC - 0.7L + Lt", "Begin runoff", station_format))
        else:
            rows.append(_make_row("NC", reverse_crown + Lt, -nc_pct, "Sta = PC - 0.7L + Lt", "Normal crown", station_format))

        rows.append(_make_row("PC", pc, final_sign * e70_pct, "70% super", "PC 70% super", station_format))
        rows.append(_make_row("FULL SUPER", full_super_pc, final_sign * e_pct, "Sta = PC + 0.3L", "Full super", station_format))
        if pt is not None and full_super_pt is not None and reverse_crown_out is not None:
            rows.append(_make_row("FULL SUPER", full_super_pt, final_sign * e_pct, "Sta = PT - 0.3L", "End full super", station_format))
            rows.append(_make_row("PT", pt, final_sign * e70_pct, "70% super", "PT 70% super", station_format))
            if side == outside:
                rows.append(_make_row("0%", reverse_crown_out, 0.0, "Sta = PT + 0.7L", "End runoff", station_format))
                rows.append(_make_row("NC", reverse_crown_out + Lt, -nc_pct, "0% + runout", "Back to normal crown", station_format))
            else:
                rows.append(_make_row("NC", reverse_crown_out - Lt, -nc_pct, "Sta = PT + 0.7L - Lt", "Back to normal crown", station_format))
        return rows

    return finish(lane_rows("left")), finish(lane_rows("right"))


def _ord_point_type(event_type: str, side: str, direction: str) -> str:
    outside = outside_lane(direction)
    suffix = "OUT" if side == outside else "IN"
    if event_type in {"Normal crown", "Back to normal crown"}:
        return f"NC{suffix}"
    if event_type in {"Reverse crown", "End runoff"}:
        return f"RC{suffix}"
    if event_type in {"Full super", "End full super"}:
        return f"FS{suffix}"
    return "U"


def _station_region(station: float, equations: list[dict] | None) -> int:
    """Return ORD station region number (R1 before equations, then R2, R3...)."""
    region = 1
    for equation in sorted(equations or [], key=lambda item: float(item.get("internal", item.get("staInternal", 0.0)))):
        internal = float(equation.get("internal", equation.get("staInternal", 0.0)))
        if station + 1e-9 >= internal:
            region += 1
        else:
            break
    return region


def build_normalized_rows(curves: Iterable[dict], station_format: bool = True) -> list[dict]:
    rows: list[dict] = []
    for curve in curves:
        results = curve.get("results") or {}
        meta = curve.get("meta", {}) or {}
        direction = meta.get("curve_direction", "left")
        left_rows, right_rows = build_lane_rows(results, direction, station_format)

        for side, lane_rows in (("left", left_rows), ("right", right_rows)):
            lane_name = lane_name_for_side(side, curve)
            for row in lane_rows:
                station_ft = row.get("station_ft")
                if station_ft is None:
                    continue
                rows.append(
                    {
                        "project_name": str(meta.get("project_name", "") or ""),
                        "route_name": str(meta.get("route_name", "") or ""),
                        "alignment_name": str(meta.get("alignment_name", "") or ""),
                        "curve_name": str(meta.get("curve_name", "") or ""),
                        "curve_direction": str(direction or ""),
                        "station": station_ft,
                        "station_label": row["station"],
                        "side": side,
                        "lane_name": lane_name,
                        "slope_percent": float(row["slope_pct"]),
                        "slope_decimal": float(row["slope_decimal"]),
                        "slope_label": row["slope_label"],
                        "event_type": row["event_type"],
                        "notes": row["note"] if not curve.get("notes") else f"{row['note']}; {curve['notes']}",
                        "station_region": _station_region(float(station_ft), results.get("station_equations")),
                    }
                )
    return rows


def write_ord_csv(handle: TextIO, curves: Iterable[dict]) -> list[str]:
    warnings = [
        "ORD CSV format follows Bentley Import Superelevation documentation. Verify lane names match existing ORD superelevation lanes before import.",
        "Stations after alignment equations use ORD region suffixes R2, R3, and so on.",
        "This export is schema-confirmed but still needs real in-ORD round-trip validation.",
    ]
    writer = csv.DictWriter(handle, fieldnames=ORD_HEADERS)
    writer.writeheader()
    for row in build_normalized_rows(curves):
        if not row["station_label"] or row["station_label"] == "n/a":
            continue
        station_label = str(row["station_label"])
        station_region = int(row.get("station_region", 1) or 1)
        if station_region > 1:
            station_label = f"{station_label}R{station_region}"
        writer.writerow(
            {
                "SuperelevationLane": row["lane_name"],
                "Station": station_label,
                "CrossSlope": slope_decimal(row["slope_percent"]),
                "PivotAbout": pivot_about_for_side(str(row["side"])),
                "PointType": _ord_point_type(str(row["event_type"]), str(row["side"]), str(row["curve_direction"])),
                "TransitionType": "L",
                "NonLinearCurveLength": "0",
            }
        )
    return warnings
