"""Traceability metadata for the unchanged legacy engineering criteria."""

from __future__ import annotations

from copy import deepcopy


_CRITERIA_METADATA = {
    "profile_id": "mdot-legacy-unverified",
    "profile_name": "MDOT-oriented legacy superelevation criteria",
    "revision": "unverified",
    "source_status": "SOURCE VERIFICATION REQUIRED BEFORE PAID PILOT",
    "governing_authority": (
        "Mississippi Department of Transportation (attribution from the legacy implementation; "
        "governing publication and revision have not been verified)"
    ),
    "referenced_identifiers": [
        "Table 3-4-A",
        "Table 3-4-B",
        "Table 3-4-C",
        "Equation 3-4-1",
        "SE-1",
        "SE-2A",
        "SE-2B",
        "SE-2C",
        "SE-2D",
        "SE-2E",
        "SE-3A",
        "SE-3B",
    ],
    "implementation_module": "Super.py",
    "engineering_change_notice": (
        "This metadata does not validate the embedded values or formulas. A qualified roadway engineer "
        "must trace each criterion to the governing signed/issued source and approve golden calculations."
    ),
}


def criteria_metadata() -> dict:
    """Return an isolated copy suitable for results, projects, and reports."""
    return deepcopy(_CRITERIA_METADATA)
