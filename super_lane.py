from __future__ import annotations

import math

import super_exports


def build_lane_rows(
    results: dict,
    direction: str,
    station_format: bool = True,
) -> tuple[list[dict], list[dict]]:
    return super_exports.build_lane_rows(results, direction, station_format)


def lane_profile_points(results: dict, direction: str) -> dict[str, list[tuple[float, float]]]:
    left_rows, right_rows = build_lane_rows(results, direction, station_format=False)

    def to_points(rows: list[dict]) -> list[tuple[float, float]]:
        points = [
            (float(row["station_ft"]), float(row["slope_pct"]))
            for row in rows
            if row.get("station_ft") is not None
        ]
        points.sort(key=lambda item: item[0])
        return points

    return {"left": to_points(left_rows), "right": to_points(right_rows)}


def slope_at_station(point_list: list[tuple[float, float]], station: float) -> float:
    if not point_list:
        return 0.0
    if station <= point_list[0][0]:
        return point_list[0][1]
    if station >= point_list[-1][0]:
        return point_list[-1][1]
    for (x0, y0), (x1, y1) in zip(point_list, point_list[1:]):
        if x0 <= station <= x1 or x1 <= station <= x0:
            if x1 == x0:
                return y1
            t = (station - x0) / (x1 - x0)
            return y0 + (y1 - y0) * t
    return point_list[-1][1]


def parse_slope_percent(value: str) -> float:
    text = value.strip()
    if not text:
        raise ValueError("Superelevation value is required.")
    explicit_percent = text.endswith("%")
    if explicit_percent:
        text = text[:-1].strip()
    try:
        raw = float(text)
    except ValueError as exc:
        raise ValueError("Invalid superelevation value.") from exc
    if not math.isfinite(raw):
        raise ValueError("Invalid superelevation value.")
    if explicit_percent or abs(raw) > 0.2:
        return raw
    return raw * 100.0


def slope_matches(
    point_list: list[tuple[float, float]],
    target: float,
    tolerance: float = 1e-9,
) -> list[tuple[float, float]]:
    matches: list[tuple[float, float]] = []
    for (x0, y0), (x1, y1) in zip(point_list, point_list[1:]):
        y0_matches = math.isclose(y0, target, abs_tol=tolerance)
        y1_matches = math.isclose(y1, target, abs_tol=tolerance)
        if y0_matches and y1_matches:
            matches.append((min(x0, x1), max(x0, x1)))
            continue
        if min(y0, y1) - tolerance <= target <= max(y0, y1) + tolerance and not math.isclose(
            y0, y1, abs_tol=tolerance
        ):
            if y0_matches:
                station = x0
            elif y1_matches:
                station = x1
            else:
                fraction = (target - y0) / (y1 - y0)
                station = x0 + fraction * (x1 - x0)
            matches.append((station, station))

    merged: list[tuple[float, float]] = []
    for start, end in sorted(matches):
        if not merged:
            merged.append((start, end))
            continue
        prior_start, prior_end = merged[-1]
        same_point = math.isclose(prior_start, prior_end, abs_tol=tolerance) and math.isclose(
            start, end, abs_tol=tolerance
        )
        if start <= prior_end + tolerance and (
            not same_point or math.isclose(prior_start, start, abs_tol=tolerance)
        ):
            merged[-1] = (prior_start, max(prior_end, end))
        else:
            merged.append((start, end))
    return merged


def station_for_slope(
    point_list: list[tuple[float, float]],
    target: float,
    reference_station: float,
) -> float | None:
    matches = slope_matches(point_list, target)
    if not matches:
        return None

    def nearest_station(match: tuple[float, float]) -> float:
        start, end = match
        return min(max(reference_station, start), end)

    return min(
        (nearest_station(match) for match in matches),
        key=lambda station: abs(station - reference_station),
    )
