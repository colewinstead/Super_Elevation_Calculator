"""Silent, launch-time discovery of newer desktop application releases."""

from __future__ import annotations

from dataclasses import dataclass
import json
import platform
import re
import ssl
import sys
from typing import Any
from urllib.request import Request, urlopen

import certifi

from app_info import APP_NAME, APP_VERSION
import app_logging


REPOSITORY = "colewinstead/Super_Elevation_Calculator"
LATEST_RELEASE_API = f"https://api.github.com/repos/{REPOSITORY}/releases/latest"
RELEASE_URL_PREFIX = f"https://github.com/{REPOSITORY}/releases/"
REQUEST_TIMEOUT_SECONDS = 5.0
VERSION_PATTERN = re.compile(r"^[vV]?(\d+)\.(\d+)\.(\d+)$")
HTTPS_CONTEXT = ssl.create_default_context(cafile=certifi.where())


@dataclass(frozen=True)
class UpdateInfo:
    """A newer release and the safest available place to download it."""

    current_version: str
    latest_version: str
    download_url: str


def parse_version(value: str) -> tuple[int, int, int]:
    """Parse the application's numeric release format, with an optional v prefix."""
    match = VERSION_PATTERN.fullmatch(value.strip())
    if not match:
        raise ValueError(f"Invalid application version: {value!r}")
    return tuple(int(part) for part in match.groups())


def release_asset_name(*, platform_name: str | None = None, machine: str | None = None) -> str | None:
    """Return the published desktop asset for the current operating system."""
    platform_name = platform_name or sys.platform
    machine = (machine or platform.machine()).lower()
    if platform_name == "win32":
        return "SuperElevation.exe"
    if platform_name == "darwin":
        if machine in {"arm64", "aarch64"}:
            return "SuperelevationCalculator-macOS-Apple-Silicon.dmg"
        if machine in {"x86_64", "amd64"}:
            return "SuperelevationCalculator-macOS-Intel.dmg"
    return None


def update_from_release(
    release: dict[str, Any],
    current_version: str = APP_VERSION,
    *,
    platform_name: str | None = None,
    machine: str | None = None,
) -> UpdateInfo | None:
    """Evaluate a GitHub release response without performing network access."""
    if release.get("draft") or release.get("prerelease"):
        return None

    tag_name = release.get("tag_name")
    if not isinstance(tag_name, str):
        raise ValueError("Latest release did not contain a version tag.")
    current = parse_version(current_version)
    latest = parse_version(tag_name)
    if latest <= current:
        return None

    latest_version = ".".join(str(part) for part in latest)
    fallback_url = f"{RELEASE_URL_PREFIX}tag/v{latest_version}"
    download_url = fallback_url
    expected_name = release_asset_name(platform_name=platform_name, machine=machine)
    assets = release.get("assets", [])
    if not isinstance(assets, list):
        raise ValueError("Latest release assets were not a list.")
    if expected_name:
        for asset in assets:
            if not isinstance(asset, dict) or asset.get("name") != expected_name:
                continue
            candidate = asset.get("browser_download_url")
            if isinstance(candidate, str) and candidate.startswith(f"{RELEASE_URL_PREFIX}download/"):
                download_url = candidate
            break

    return UpdateInfo(
        current_version=current_version,
        latest_version=latest_version,
        download_url=download_url,
    )


def check_for_update(current_version: str = APP_VERSION) -> UpdateInfo | None:
    """Check GitHub once, returning no user-facing error when discovery fails."""
    request = Request(
        LATEST_RELEASE_API,
        headers={
            "Accept": "application/vnd.github+json",
            "User-Agent": f"{APP_NAME.replace(' ', '-')}/{current_version}",
            "X-GitHub-Api-Version": "2026-03-10",
        },
    )
    try:
        with urlopen(request, timeout=REQUEST_TIMEOUT_SECONDS, context=HTTPS_CONTEXT) as response:
            release = json.load(response)
        if not isinstance(release, dict):
            raise ValueError("Latest release response was not an object.")
        return update_from_release(release, current_version)
    except Exception as exc:
        app_logging.configure_logging().info(
            "update_check_unavailable exception_type=%s message=%s",
            type(exc).__name__,
            str(exc),
        )
        return None
