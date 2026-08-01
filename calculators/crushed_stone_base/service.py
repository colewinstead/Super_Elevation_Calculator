"""JSON-safe browser service for crushed stone base quantities."""

from __future__ import annotations

import json
from typing import Any

from .engine import DEFAULT_TONS_PER_CUBIC_YARD, DEFAULT_WASTE_PERCENT, ENGINE_VERSION, calculate


def application_manifest() -> dict[str, Any]:
    return {
        "name": "Crushed Stone Base Tonnage Calculator",
        "calculation_engine_version": ENGINE_VERSION,
        "defaults": {
            "tons_per_cubic_yard": DEFAULT_TONS_PER_CUBIC_YARD,
            "waste_percent": DEFAULT_WASTE_PERCENT,
        },
    }


def dispatch(operation: str, payload_json: str = "{}") -> Any:
    payload = json.loads(payload_json or "{}")
    if operation == "manifest":
        return application_manifest()
    if operation == "calculate":
        return calculate(
            payload.get("segments", []),
            payload.get("tons_per_cubic_yard", DEFAULT_TONS_PER_CUBIC_YARD),
            payload.get("waste_percent", DEFAULT_WASTE_PERCENT),
        )
    raise ValueError(f"Unsupported crushed stone base operation: {operation}")


def dispatch_safe(operation: str, payload_json: str = "{}") -> dict[str, Any]:
    try:
        return {"ok": True, "result": dispatch(operation, payload_json)}
    except Exception as exc:
        return {
            "ok": False,
            "error": {"type": type(exc).__name__, "message": str(exc) or "Operation failed."},
        }
