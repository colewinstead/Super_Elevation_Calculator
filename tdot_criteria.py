"""Versioned TDOT RD11 superelevation criteria and table lookups.

The numeric radius tables below are transcribed from TDOT standard drawings
RD11-LR-1 and RD11-LR-2 (issue date 2019-01-01).  The active profile uses
the desirable 4 percent urban and 8 percent rural tables identified by the
current TDOT Roadway Design Guidelines, Chapter 2 (revision 2026-04-30).
"""

from __future__ import annotations

from math import floor, isclose


TDOT_PROFILE_ID = "tdot-rd11-2026-04-30"

# RD11-SE-1, Table 1. Values are decimal relative gradients.
RELATIVE_GRADIENTS = {
    20: 0.0074,
    25: 0.0070,
    30: 0.0066,
    35: 0.0062,
    40: 0.0058,
    45: 0.0054,
    50: 0.0050,
    55: 0.0047,
    60: 0.0045,
    65: 0.0043,
    70: 0.0040,
}

# RD11-SE-1, Table 2. The drawing expresses roadway lanes as the equivalent
# number of lanes rotated (n1) and a lane adjustment factor (b).
LANE_FACTORS = {
    2: (1.0, 1.00),
    3: (1.5, 0.83),
    4: (2.0, 0.75),
    5: (2.5, 0.70),
    6: (3.0, 0.67),
}

URBAN_SPEEDS = (20, 25, 30, 35, 40, 45, 50, 55, 60)
RURAL_SPEEDS = (20, 25, 30, 35, 40, 45, 50, 55, 60, 65, 70)

# Rows are (superelevation rate, minimum radii by speed).  A None rate is the
# normal-crown boundary. Rates are decimal ft/ft.
URBAN_EMAX_4_ROWS = (
    (None, (107, 198, 333, 510, 762, 1039, 7220, 8650, 10300)),
    (0.020, (92, 167, 273, 408, 593, 794, 4940, 5950, 7080)),
    (0.022, (91, 165, 270, 404, 586, 785, 4280, 5180, 6190)),
    (0.024, (91, 164, 268, 400, 580, 776, 3690, 4500, 5410)),
    (0.026, (90, 163, 265, 396, 573, 767, 3130, 3870, 4700)),
    (0.028, (89, 162, 263, 393, 567, 758, 2660, 3310, 4060)),
    (0.030, (89, 160, 261, 389, 561, 750, 2290, 2860, 3530)),
    (0.032, (88, 159, 259, 385, 556, 742, 1980, 2490, 3090)),
    (0.034, (88, 158, 256, 382, 550, 734, 1720, 2170, 2700)),
    (0.036, (87, 157, 254, 378, 544, 726, 1480, 1880, 2350)),
    (0.038, (87, 155, 252, 375, 539, 718, 1260, 1600, 2010)),
    (0.040, (86, 154, 250, 371, 533, 711, 926, 1190, 1500)),
)

RURAL_EMAX_8_ROWS = (
    (None, (1640, 2370, 3240, 4260, 5410, 6710, 8150, 9720, 11500, 12900, 14500)),
    (0.020, (1190, 1720, 2370, 3120, 3970, 4930, 5990, 7150, 8440, 9510, 10700)),
    (0.022, (1070, 1550, 2130, 2800, 3570, 4440, 5400, 6450, 7620, 8600, 9660)),
    (0.024, (959, 1400, 1930, 2540, 3240, 4030, 4910, 5870, 6930, 7830, 8810)),
    (0.026, (872, 1280, 1760, 2320, 2960, 3690, 4490, 5370, 6350, 7180, 8090)),
    (0.028, (796, 1170, 1610, 2130, 2720, 3390, 4130, 4950, 5850, 6630, 7470)),
    (0.030, (730, 1070, 1480, 1960, 2510, 3130, 3820, 4580, 5420, 6140, 6930)),
    (0.032, (672, 985, 1370, 1820, 2330, 2900, 3550, 4250, 5040, 5720, 6460)),
    (0.034, (620, 911, 1270, 1690, 2170, 2700, 3300, 3970, 4700, 5350, 6050)),
    (0.036, (572, 845, 1180, 1570, 2020, 2520, 3090, 3710, 4400, 5010, 5680)),
    (0.038, (530, 784, 1100, 1470, 1890, 2360, 2890, 3480, 4140, 4710, 5350)),
    (0.040, (490, 729, 1030, 1370, 1770, 2220, 2720, 3270, 3890, 4450, 5050)),
    (0.042, (453, 678, 955, 1280, 1660, 2080, 2560, 3080, 3670, 4200, 4780)),
    (0.044, (418, 630, 893, 1200, 1560, 1960, 2410, 2910, 3470, 3980, 4540)),
    (0.046, (384, 585, 834, 1130, 1470, 1850, 2280, 2750, 3290, 3770, 4310)),
    (0.048, (349, 542, 779, 1060, 1390, 1750, 2160, 2610, 3120, 3590, 4100)),
    (0.050, (314, 499, 727, 991, 1310, 1650, 2040, 2470, 2960, 3410, 3910)),
    (0.052, (284, 457, 676, 929, 1230, 1560, 1930, 2350, 2820, 3250, 3740)),
    (0.054, (258, 420, 627, 870, 1160, 1480, 1830, 2230, 2680, 3110, 3570)),
    (0.056, (236, 387, 582, 813, 1090, 1390, 1740, 2120, 2550, 2970, 3420)),
    (0.058, (216, 358, 542, 761, 1030, 1320, 1650, 2010, 2430, 2840, 3280)),
    (0.060, (199, 332, 506, 713, 965, 1250, 1560, 1920, 2320, 2710, 3150)),
    (0.062, (184, 308, 472, 669, 909, 1180, 1480, 1820, 2210, 2600, 3020)),
    (0.064, (170, 287, 442, 628, 857, 1110, 1400, 1730, 2110, 2490, 2910)),
    (0.066, (157, 267, 413, 590, 808, 1050, 1330, 1650, 2010, 2380, 2790)),
    (0.068, (146, 248, 386, 553, 761, 990, 1260, 1560, 1910, 2280, 2690)),
    (0.070, (135, 231, 360, 518, 716, 933, 1190, 1480, 1820, 2180, 2580)),
    (0.072, (125, 214, 336, 485, 672, 878, 1120, 1400, 1720, 2070, 2470)),
    (0.074, (115, 198, 312, 451, 628, 822, 1060, 1320, 1630, 1970, 2350)),
    (0.076, (105, 182, 287, 417, 583, 765, 980, 1230, 1530, 1850, 2230)),
    (0.078, (94, 164, 261, 380, 533, 701, 901, 1140, 1410, 1720, 2090)),
    (0.080, (76, 134, 214, 314, 444, 587, 758, 960, 1200, 1480, 1810)),
)


def _table(area_type: str):
    if str(area_type).strip().lower().startswith("urban"):
        return URBAN_SPEEDS, URBAN_EMAX_4_ROWS, "TDOT STD. DWG RD11-LR-1 (4% desirable)"
    return RURAL_SPEEDS, RURAL_EMAX_8_ROWS, "TDOT STD. DWG RD11-LR-2 (8% desirable)"


def validate_speed(speed_mph: float, area_type: str) -> int:
    """Return the exact TDOT table speed or raise a review-friendly error."""
    speeds, _, source = _table(area_type)
    rounded = int(round(speed_mph))
    if not isclose(speed_mph, rounded, abs_tol=1e-9) or rounded not in speeds:
        allowed = ", ".join(str(value) for value in speeds)
        raise ValueError(f"{source} supports these design speeds: {allowed} mph.")
    return rounded


def lookup_superelevation(speed_mph: float, radius_ft: float, area_type: str) -> dict:
    """Select the conservative tabulated rate for an exact TDOT speed row."""
    speeds, rows, source = _table(area_type)
    speed = validate_speed(speed_mph, area_type)
    column = speeds.index(speed)
    normal_radius = float(rows[0][1][column])
    reverse_radius = float(rows[1][1][column])
    if radius_ft >= normal_radius:
        return {
            "e": 0.0,
            "e_max": float(rows[-1][0]),
            "normal_radius": normal_radius,
            "reverse_radius": reverse_radius,
            "minimum_radius": float(rows[-1][1][column]),
            "crown_state": "Normal crown",
            "source": source,
            "note": "Radius meets the TDOT normal-crown threshold; no transition is required.",
        }

    selected_rate = float(rows[-1][0])
    selected_radius = float(rows[-1][1][column])
    for rate, radii in rows[1:]:
        if radius_ft >= radii[column]:
            selected_rate = float(rate)
            selected_radius = float(radii[column])
            break
    below_minimum = radius_ft < float(rows[-1][1][column])
    note = (
        f"Selected the larger tabulated rate when R={radius_ft:g} ft falls between TDOT radius rows."
    )
    if below_minimum:
        note = (
            f"Radius is below the {source} minimum of {rows[-1][1][column]:g} ft; "
            "the maximum tabulated rate is shown and a design exception/review is required."
        )
    return {
        "e": selected_rate,
        "e_max": float(rows[-1][0]),
        "normal_radius": normal_radius,
        "reverse_radius": reverse_radius,
        "minimum_radius": float(rows[-1][1][column]),
        "selected_row_radius": selected_radius,
        "crown_state": "See standard drawings",
        "source": source,
        "note": note,
        "below_minimum_radius": below_minimum,
    }


def relative_gradient(speed_mph: float) -> float:
    speed = validate_speed(speed_mph, "rural")
    return RELATIVE_GRADIENTS[speed]


def lane_factors(total_lanes: float) -> tuple[float, float, int]:
    rounded = int(round(total_lanes))
    if not isclose(total_lanes, rounded, abs_tol=1e-9) or rounded not in LANE_FACTORS:
        raise ValueError("TDOT RD11 runoff tables support a whole roadway lane count from 2 through 6.")
    n1, adjustment = LANE_FACTORS[rounded]
    return n1, adjustment, rounded


def round_half_up(value: float) -> float:
    """Round a positive design length to the nearest whole foot."""
    return float(floor(value + 0.5))


def runoff_length(
    lane_width_ft: float,
    total_lanes: float,
    e: float,
    gradient: float,
) -> tuple[float, float, float, int]:
    n1, adjustment, lanes = lane_factors(total_lanes)
    raw = lane_width_ft * n1 * e / gradient * adjustment
    return round_half_up(raw), n1, adjustment, lanes
