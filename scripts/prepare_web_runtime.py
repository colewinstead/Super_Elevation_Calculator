"""Stage the shared Python modules for the browser build without duplicating source."""

from __future__ import annotations

import json
import shutil
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
TARGET = ROOT / "web" / "public" / "python"
GENERATED = ROOT / "web" / "app" / "generated"
sys.path.insert(0, str(ROOT))

from commercial_entitlements import commercial_manifest  # noqa: E402
from criteria_info import criteria_metadata, criteria_profiles  # noqa: E402
from app_info import APP_VERSION, CALCULATION_ENGINE_VERSION  # noqa: E402

MODULES = [
    "Super.py",
    "app_info.py",
    "commercial_entitlements.py",
    "criteria_info.py",
    "tdot_criteria.py",
    "super_batch.py",
    "super_dxf.py",
    "super_exports.py",
    "super_landxml.py",
    "super_lane.py",
    "super_pdf.py",
    "super_project.py",
    "super_qa.py",
    "super_service.py",
    "super_transition.py",
    "super_ui.py",
]


def main() -> None:
    TARGET.mkdir(parents=True, exist_ok=True)
    for name in MODULES:
        shutil.copy2(ROOT / name, TARGET / name)
    (TARGET / "manifest.json").write_text(json.dumps({"modules": MODULES}, indent=2) + "\n", encoding="utf-8")
    GENERATED.mkdir(parents=True, exist_ok=True)
    supported_profiles = []
    for profile in criteria_profiles():
        metadata = criteria_metadata(profile["profile_id"])
        supported_profiles.append(
            {
                **profile,
                "source_status": metadata["source_status"],
                "engineering_change_notice": metadata["engineering_change_notice"],
            }
        )
    (GENERATED / "criteria-profiles.json").write_text(
        json.dumps(supported_profiles, indent=2) + "\n", encoding="utf-8"
    )
    (GENERATED / "commercial-manifest.json").write_text(
        json.dumps(commercial_manifest(), indent=2) + "\n", encoding="utf-8"
    )
    (GENERATED / "release-info.json").write_text(
        json.dumps(
            {
                "application_version": APP_VERSION,
                "calculation_engine_version": CALCULATION_ENGINE_VERSION,
            },
            indent=2,
        ) + "\n",
        encoding="utf-8",
    )
    print(f"Staged {len(MODULES)} shared Python modules for the browser runtime.")


if __name__ == "__main__":
    main()
