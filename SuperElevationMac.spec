# -*- mode: python ; coding: utf-8 -*-

import os

from PyInstaller.utils.hooks import collect_data_files

from app_info import APP_VERSION


pyproj_datas = collect_data_files("pyproj", includes=["proj_dir/share/proj/**"])
target_arch = os.environ.get("SUPERELEVATION_TARGET_ARCH") or None

a = Analysis(
    ["super_app.py"],
    pathex=[],
    binaries=[],
    datas=pyproj_datas,
    hiddenimports=["ezdxf", "pyproj", "super_ui"],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="Superelevation Calculator",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=target_arch,
    codesign_identity=None,
    entitlements_file=None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=False,
    upx_exclude=[],
    name="Superelevation Calculator",
)

app = BUNDLE(
    coll,
    name="Superelevation Calculator.app",
    icon=None,
    bundle_identifier="com.colewinstead.superelevationcalculator",
    info_plist={
        "CFBundleDisplayName": "Superelevation Calculator",
        "CFBundleShortVersionString": APP_VERSION,
        "CFBundleVersion": APP_VERSION,
        "LSMinimumSystemVersion": "15.0",
        "NSHighResolutionCapable": True,
    },
)
