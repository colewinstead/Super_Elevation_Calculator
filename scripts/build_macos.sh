#!/usr/bin/env bash

set -euo pipefail

skip_install=false
python_path="${PYTHON_PATH:-python3}"

while (($#)); do
  case "$1" in
    --skip-install)
      skip_install=true
      ;;
    --python)
      shift
      python_path="$1"
      ;;
    *)
      echo "Unknown argument: $1" >&2
      exit 2
      ;;
  esac
  shift
done

if [[ "$(uname -s)" != "Darwin" ]]; then
  echo "The macOS release must be built on macOS." >&2
  exit 1
fi

case "$(uname -m)" in
  arm64)
    target_arch="arm64"
    release_arch="Apple-Silicon"
    ;;
  x86_64)
    target_arch="x86_64"
    release_arch="Intel"
    ;;
  *)
    echo "Unsupported Mac architecture: $(uname -m)" >&2
    exit 1
    ;;
esac

root="$(cd "$(dirname "$0")/.." && pwd)"
cd "$root"

if [[ "$skip_install" != true ]]; then
  "$python_path" -m pip install -r requirements-lock.txt "pyinstaller>=6.0,<7.0"
fi

version="$($python_path -c 'from app_info import APP_VERSION; print(APP_VERSION)')"
app_name="Superelevation Calculator.app"
dmg_name="SuperelevationCalculator-macOS-${release_arch}.dmg"
checksum_name="SHA256SUMS-macOS-${release_arch}.txt"

rm -rf build/macos-work build/macos-dist
rm -f "dist/$dmg_name" "dist/$checksum_name"
mkdir -p dist
SUPERELEVATION_TARGET_ARCH="$target_arch" \
  "$python_path" -m PyInstaller \
    --clean \
    --noconfirm \
    --workpath build/macos-work \
    --distpath build/macos-dist \
    SuperElevationMac.spec

app_path="build/macos-dist/$app_name"
executable="$app_path/Contents/MacOS/Superelevation Calculator"
test -d "$app_path"
test -x "$executable"
test "$(/usr/libexec/PlistBuddy -c 'Print :CFBundleShortVersionString' "$app_path/Contents/Info.plist")" = "$version"
test "$(/usr/libexec/PlistBuddy -c 'Print :CFBundleIdentifier' "$app_path/Contents/Info.plist")" = "com.colewinstead.superelevationcalculator"
lipo "$executable" -verify_arch "$target_arch"
"$executable" --version >/dev/null

staging_dir="$(mktemp -d)"
mount_dir="$(mktemp -d)"
cleanup() {
  hdiutil detach "$mount_dir" -quiet 2>/dev/null || true
  rm -rf "$staging_dir" "$mount_dir"
}
trap cleanup EXIT

cp -R "$app_path" "$staging_dir/"
ln -s /Applications "$staging_dir/Applications"
hdiutil create \
  -volname "Superelevation Calculator $version" \
  -srcfolder "$staging_dir" \
  -format UDZO \
  -ov \
  "dist/$dmg_name"
hdiutil verify "dist/$dmg_name"
hdiutil attach "dist/$dmg_name" -mountpoint "$mount_dir" -nobrowse -readonly -quiet
test -d "$mount_dir/$app_name"
test -L "$mount_dir/Applications"
hdiutil detach "$mount_dir" -quiet

(cd dist && shasum -a 256 "$dmg_name" > "$checksum_name")
echo "Built dist/$dmg_name and dist/$checksum_name"
