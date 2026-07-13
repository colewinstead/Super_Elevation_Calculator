from __future__ import annotations

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


def station_for_slope(
    point_list: list[tuple[float, float]],
    target: float,
    reference_station: float,
) -> float | None:
    candidates: list[float] = []
    for (x0, y0), (x1, y1) in zip(point_list, point_list[1:]):
        if y0 == y1 == target:
            candidates.extend([x0, x1])
        elif (target - y0) * (target - y1) <= 0 and y0 != y1:
            t = (target - y0) / (y1 - y0)
            candidates.append(x0 + t * (x1 - x0))
    if not candidates:
        return None
    return min(candidates, key=lambda value: abs(value - reference_station))
