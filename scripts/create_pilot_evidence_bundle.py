"""Create an unapproved private paid-pilot evidence workspace outside the repository."""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


def _git_value(*args: str) -> str:
    completed = subprocess.run(
        ["git", *args],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    return completed.stdout.strip()


def _release_identity() -> dict[str, Any]:
    from app_info import APP_NAME, APP_VERSION, CALCULATION_ENGINE_VERSION
    from criteria_info import criteria_profiles
    from super_project import PROJECT_VERSION

    return {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "product": APP_NAME,
        "application_version": APP_VERSION,
        "calculation_engine_version": CALCULATION_ENGINE_VERSION,
        "project_schema_version": PROJECT_VERSION,
        "commit_sha": _git_value("rev-parse", "HEAD"),
        "branch": _git_value("branch", "--show-current"),
        "tracked_worktree_clean": not bool(
            _git_value("status", "--porcelain", "--untracked-files=no")
        ),
        "untracked_files_present": bool(
            _git_value("ls-files", "--others", "--exclude-standard")
        ),
        "criteria_profiles": criteria_profiles(),
        "approval_status": "unapproved",
    }


def create_bundle(output: Path) -> Path:
    output = output.expanduser().resolve()
    try:
        output.relative_to(ROOT.resolve())
    except ValueError:
        pass
    else:
        raise ValueError("Private pilot evidence must be created outside the public repository.")

    if output.exists() and any(output.iterdir()):
        raise FileExistsError(f"Evidence directory is not empty: {output}")
    output.mkdir(parents=True, exist_ok=True)

    templates = ROOT / "docs" / "templates"
    shutil.copy2(templates / "PRIVATE_PE_VALIDATION_RECORD.md", output / "01-private-pe-validation-record.md")
    shutil.copy2(templates / "PILOT_ACCEPTANCE_RECORD.md", output / "02-pilot-acceptance-record.md")
    for directory in (
        "03-automated-tests",
        "04-clean-machine",
        "05-engineering-acceptance",
        "06-legal-approvals",
        "07-support-and-onboarding",
        "08-release-and-rollback",
    ):
        (output / directory).mkdir()

    identity = _release_identity()
    (output / "release-identity.json").write_text(
        json.dumps(identity, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    (output / "README.md").write_text(
        "# Private paid-pilot evidence\n\n"
        "This workspace was generated outside the public repository. Its records start unapproved. "
        "Retain signatures, confidential vectors, customer-file approvals, legal advice, and acceptance evidence here. "
        "Do not copy completed records, signing keys, credentials, or customer engineering files into source control.\n",
        encoding="utf-8",
    )
    return output


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", required=True, type=Path, help="New or empty directory outside the repository")
    args = parser.parse_args()
    created = create_bundle(args.output)
    print(f"Created unapproved private evidence workspace: {created}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
