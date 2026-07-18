"""Validate that APP_VERSION can identify a new immutable GitHub release."""

from __future__ import annotations

import argparse
import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

import sys

sys.path.insert(0, str(ROOT))

from app_info import APP_VERSION  # noqa: E402


VERSION_PATTERN = re.compile(r"^(\d+)\.(\d+)\.(\d+)$")
TAG_PATTERN = re.compile(r"^[vV](\d+)\.(\d+)\.(\d+)$")


def parse_version(value: str) -> tuple[int, int, int]:
    match = VERSION_PATTERN.fullmatch(value)
    if not match:
        raise ValueError(f"Version '{value}' must use numeric MAJOR.MINOR.PATCH format.")
    return tuple(int(part) for part in match.groups())


def release_tags(values: list[str]) -> dict[str, tuple[int, int, int]]:
    parsed: dict[str, tuple[int, int, int]] = {}
    for value in values:
        match = TAG_PATTERN.fullmatch(value.strip())
        if match:
            parsed[value.strip()] = tuple(int(part) for part in match.groups())
    return parsed


def git(*args: str) -> str:
    return subprocess.check_output(
        ["git", *args], cwd=ROOT, text=True, stderr=subprocess.STDOUT
    ).strip()


def validate(*, allow_current_tag: bool = False) -> str:
    current = parse_version(APP_VERSION)
    tags = release_tags(git("tag", "--list").splitlines())
    matching = [tag for tag, version in tags.items() if version == current]

    if matching:
        head = git("rev-parse", "HEAD")
        for tag in matching:
            if allow_current_tag and git("rev-list", "-n", "1", tag) == head:
                return tag
        raise ValueError(
            f"APP_VERSION {APP_VERSION} already has release tag {matching[0]}. "
            "Increase APP_VERSION before merging to main."
        )

    if tags:
        latest_tag, latest = max(tags.items(), key=lambda item: item[1])
        if current <= latest:
            raise ValueError(
                f"APP_VERSION {APP_VERSION} must be newer than {latest_tag}. "
                "Increase APP_VERSION before merging to main."
            )

    return f"v{APP_VERSION}"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--allow-current-tag",
        action="store_true",
        help="Allow a matching tag only when it already points to HEAD.",
    )
    args = parser.parse_args()
    try:
        tag = validate(allow_current_tag=args.allow_current_tag)
    except (ValueError, subprocess.CalledProcessError) as exc:
        raise SystemExit(str(exc)) from exc
    print(f"Release version {APP_VERSION} is valid ({tag}).")


if __name__ == "__main__":
    main()
