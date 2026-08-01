"""Pure crushed stone base quantity calculations."""

from __future__ import annotations

import math
from typing import Any


ENGINE_VERSION = "1.1.0"
DEFAULT_TONS_PER_CUBIC_YARD = 1.6875
DEFAULT_WASTE_PERCENT = 0.0


def _finite_number(value: Any, label: str, *, positive: bool = False) -> float:
    if isinstance(value, bool):
        raise ValueError(f"{label} must be a number.")
    try:
        number = float(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{label} must be a number.") from exc
    if not math.isfinite(number):
        raise ValueError(f"{label} must be finite.")
    if positive and number <= 0:
        raise ValueError(f"{label} must be greater than zero.")
    return number


def _nonnegative_number(value: Any, label: str) -> float:
    number = _finite_number(value, label)
    if number < 0:
        raise ValueError(f"{label} must be zero or greater.")
    return number


def calculate(
    segments: list[dict[str, Any]],
    tons_per_cubic_yard: Any = DEFAULT_TONS_PER_CUBIC_YARD,
    waste_percent: Any = DEFAULT_WASTE_PERCENT,
) -> dict[str, Any]:
    """Calculate segment and total compacted base quantities using US customary units."""
    if not isinstance(segments, list) or not segments:
        raise ValueError("Add at least one roadway segment.")

    density = _finite_number(tons_per_cubic_yard, "Tons per cubic yard", positive=True)
    waste = _finite_number(waste_percent, "Waste percentage")
    if waste < 0 or waste > 100:
        raise ValueError("Waste percentage must be between 0 and 100.")

    calculated_segments: list[dict[str, Any]] = []
    total_cubic_feet = 0.0
    total_cubic_yards = 0.0
    total_base_tons = 0.0

    for index, segment in enumerate(segments, start=1):
        if not isinstance(segment, dict):
            raise ValueError(f"Segment {index} must be an object.")
        length = _finite_number(segment.get("length_ft"), f"Segment {index} length", positive=True)
        pavement_width = _finite_number(
            segment.get("pavement_width_ft"), f"Segment {index} pavement width", positive=True
        )
        shoulder_width = _nonnegative_number(
            segment.get("shoulder_width_ft"), f"Segment {index} shoulder width"
        )
        shoulder_slope_percent = _nonnegative_number(
            segment.get("shoulder_slope_percent"), f"Segment {index} shoulder slope"
        )
        side_slope_h_to_v = _finite_number(
            segment.get("side_slope_h_to_v"), f"Segment {index} side slope", positive=True
        )
        thickness = _finite_number(
            segment.get("thickness_in"), f"Segment {index} compacted thickness", positive=True
        )
        thickness_ft = thickness / 12.0
        shoulder_slope = shoulder_slope_percent / 100.0
        side_slope = 1.0 / side_slope_h_to_v
        if side_slope <= shoulder_slope:
            raise ValueError(
                f"Segment {index} side slope must be steeper than the shoulder slope "
                "so the outside base keyout closes."
            )

        keyout_run_per_side = thickness_ft / (side_slope - shoulder_slope)
        triangle_area_per_side = 0.5 * thickness_ft * keyout_run_per_side
        equivalent_width_per_side = triangle_area_per_side / thickness_ft
        equivalent_width_both_sides = 2.0 * equivalent_width_per_side
        rectangular_width = pavement_width + 2.0 * shoulder_width
        effective_base_width = rectangular_width + equivalent_width_both_sides
        cross_section_area = thickness_ft * rectangular_width + 2.0 * triangle_area_per_side
        cubic_feet = length * cross_section_area
        cubic_yards = cubic_feet / 27.0
        base_tons = cubic_yards * density
        calculated_segments.append(
            {
                "name": str(segment.get("name", "")).strip(),
                "length_ft": length,
                "pavement_width_ft": pavement_width,
                "shoulder_width_ft": shoulder_width,
                "shoulder_slope_percent": shoulder_slope_percent,
                "side_slope_h_to_v": side_slope_h_to_v,
                "thickness_in": thickness,
                "keyout_run_per_side_ft": keyout_run_per_side,
                "triangle_area_per_side_sq_ft": triangle_area_per_side,
                "equivalent_width_per_side_ft": equivalent_width_per_side,
                "equivalent_width_both_sides_ft": equivalent_width_both_sides,
                "effective_base_width_ft": effective_base_width,
                "cross_section_area_sq_ft": cross_section_area,
                "cubic_feet": cubic_feet,
                "cubic_yards": cubic_yards,
                "base_tons": base_tons,
            }
        )
        total_cubic_feet += cubic_feet
        total_cubic_yards += cubic_yards
        total_base_tons += base_tons

    waste_tons = total_base_tons * waste / 100.0
    return {
        "segments": calculated_segments,
        "totals": {
            "cubic_feet": total_cubic_feet,
            "cubic_yards": total_cubic_yards,
            "base_tons": total_base_tons,
            "waste_tons": waste_tons,
            "order_tons": total_base_tons + waste_tons,
        },
        "assumptions": {
            "tons_per_cubic_yard": density,
            "waste_percent": waste,
            "thickness_basis": "Compacted plan thickness",
            "shoulder_count": 2,
            "keyout_basis": "Two identical outside keyout triangles; base bottom follows the shoulder slope",
            "units": "US customary",
        },
        "engine_version": ENGINE_VERSION,
    }
