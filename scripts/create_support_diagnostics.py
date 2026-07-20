"""Create a local, redacted support bundle without engineering files."""

from __future__ import annotations

import argparse
import json
import platform
import re
import sys
import zipfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
FORBIDDEN_ENGINEERING_SUFFIXES = {".json", ".xml", ".landxml", ".pdf", ".csv", ".dxf", ".dgn"}
ALLOWED_ENTITLEMENT_STATUSES = {"unknown", "active", "grace", "expired", "unavailable"}


def redact_log(text: str) -> str:
    text = re.sub(r"(?i)\b[\w.+-]+@[\w.-]+\.[a-z]{2,}\b", "[EMAIL]", text)
    text = re.sub(r"(?i)\b(bearer\s+)[a-z0-9._~-]+", r"\1[TOKEN]", text)
    text = re.sub(r"(?i)\b(api[_-]?key|token|secret|password)\s*[:=]\s*\S+", r"\1=[REDACTED]", text)
    text = re.sub(r"(?i)(?:[a-z]:\\|/Users/|/home/)[^\r\n\t\"']+", "[LOCAL_PATH]", text)
    return text


def diagnostic_manifest(entitlement_status: str) -> dict[str, Any]:
    from app_info import APP_NAME, APP_VERSION, CALCULATION_ENGINE_VERSION
    from criteria_info import criteria_profiles

    return {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "product": APP_NAME,
        "application_version": APP_VERSION,
        "calculation_engine_version": CALCULATION_ENGINE_VERSION,
        "criteria_profiles": [
            {
                "profile_id": profile["profile_id"],
                "revision": profile["revision"],
            }
            for profile in criteria_profiles()
        ],
        "entitlement_status": entitlement_status,
        "operating_system": platform.platform(),
        "python_version": platform.python_version(),
        "engineering_files_included": False,
        "notice": "No project, LandXML, calculation, PDF, CSV, DXF, or DGN file is collected automatically.",
    }


def create_diagnostics(output: Path, entitlement_status: str, log_path: Path | None = None) -> Path:
    output = output.expanduser().resolve()
    try:
        output.relative_to(ROOT.resolve())
    except ValueError:
        pass
    else:
        raise ValueError("Support diagnostics must be created outside the public repository.")
    if output.suffix.lower() != ".zip":
        raise ValueError("Support diagnostic output must use a .zip extension.")
    if output.exists():
        raise FileExistsError(f"Refusing to overwrite existing support bundle: {output}")
    entitlement_status = entitlement_status.strip().lower()
    if entitlement_status not in ALLOWED_ENTITLEMENT_STATUSES:
        choices = ", ".join(sorted(ALLOWED_ENTITLEMENT_STATUSES))
        raise ValueError(f"Entitlement status must be one of: {choices}.")

    redacted_log: str | None = None
    if log_path is not None:
        log_path = log_path.expanduser().resolve()
        if log_path.suffix.lower() in FORBIDDEN_ENGINEERING_SUFFIXES or log_path.suffix.lower() != ".log":
            raise ValueError("Only an explicitly selected application .log file can be included.")
        redacted_log = redact_log(log_path.read_text(encoding="utf-8", errors="replace"))

    output.parent.mkdir(parents=True, exist_ok=True)
    manifest = diagnostic_manifest(entitlement_status)
    manifest["user_selected_log_included"] = redacted_log is not None
    with zipfile.ZipFile(output, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        archive.writestr("diagnostics.json", json.dumps(manifest, indent=2, sort_keys=True) + "\n")
        if redacted_log is not None:
            archive.writestr("application-redacted.log", redacted_log)
    return output


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--entitlement-status", default="unknown")
    parser.add_argument("--include-log", type=Path, help="Explicit application .log file to redact and include")
    args = parser.parse_args()
    try:
        created = create_diagnostics(args.output, args.entitlement_status, args.include_log)
    except (OSError, ValueError) as error:
        print(str(error), file=sys.stderr)
        return 2
    print(f"Created local support bundle: {created}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
