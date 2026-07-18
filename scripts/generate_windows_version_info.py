"""Generate PyInstaller Windows resources from the authoritative app version."""

from __future__ import annotations

from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from app_info import APP_NAME, APP_VERSION  # noqa: E402


def version_tuple(version: str) -> tuple[int, int, int, int]:
    parts = version.split(".")
    if len(parts) != 3 or not all(part.isdigit() for part in parts):
        raise ValueError("APP_VERSION must use numeric MAJOR.MINOR.PATCH format for Windows builds.")
    return int(parts[0]), int(parts[1]), int(parts[2]), 0


def generate(output: Path) -> None:
    version = version_tuple(APP_VERSION)
    comma_version = ", ".join(str(part) for part in version)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        f"""VSVersionInfo(
  ffi=FixedFileInfo(filevers=({comma_version}), prodvers=({comma_version}), mask=0x3f, flags=0x0, OS=0x40004, fileType=0x1, subtype=0x0, date=(0, 0)),
  kids=[StringFileInfo([StringTable('040904B0', [
    StringStruct('CompanyName', 'Superelevation Calculator'),
    StringStruct('FileDescription', '{APP_NAME}'),
    StringStruct('FileVersion', '{APP_VERSION}'),
    StringStruct('InternalName', 'SuperElevation'),
    StringStruct('OriginalFilename', 'SuperElevation.exe'),
    StringStruct('ProductName', '{APP_NAME}'),
    StringStruct('ProductVersion', '{APP_VERSION}')
  ])]), VarFileInfo([VarStruct('Translation', [1033, 1200])])]
)\n""",
        encoding="utf-8",
    )


if __name__ == "__main__":
    target = Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / "build" / "windows_version_info.txt"
    generate(target)
