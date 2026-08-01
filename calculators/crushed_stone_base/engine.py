"""Pure crushed stone base quantity calculations."""

from __future__ import annotations

import math
from typing import Any


ENGINE_VERSION = "1.0.0"
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
        width = _finite_number(segment.get("width_ft"), f"Segment {index} base width", positive=True)
        thickness = _finite_number(
            segment.get("thickness_in"), f"Segment {index} compacted thickness", positive=True
        )
        cubic_feet = length * width * thickness / 12.0
        cubic_yards = cubic_feet / 27.0
        base_tons = cubic_yards * density
        calculated_segments.append(
            {
                "name": str(segment.get("name", "")).strip(),
                "length_ft": length,
                "width_ft": width,
                "thickness_in": thickness,
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
            "units": "US customary",
        },
        "engine_version": ENGINE_VERSION,
    }
