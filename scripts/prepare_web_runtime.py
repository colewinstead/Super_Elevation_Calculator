"""Stage the shared Python modules for the browser build without duplicating source."""

from __future__ import annotations

import json
import shutil
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
TARGET = ROOT / "web" / "public" / "python"
MODULES = [
    "Super.py",
    "app_info.py",
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
    "super_ui.py",
]


def main() -> None:
    TARGET.mkdir(parents=True, exist_ok=True)
    for name in MODULES:
        shutil.copy2(ROOT / name, TARGET / name)
    (TARGET / "manifest.json").write_text(json.dumps({"modules": MODULES}, indent=2) + "\n", encoding="utf-8")
    print(f"Staged {len(MODULES)} shared Python modules for the browser runtime.")


if __name__ == "__main__":
    main()
