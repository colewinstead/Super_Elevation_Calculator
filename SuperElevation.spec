# -*- mode: python ; coding: utf-8 -*-

from pathlib import Path

from PyInstaller.utils.hooks import collect_data_files

pyproj_datas = collect_data_files('pyproj', includes=['proj_dir/share/proj/**'])
version_file = Path('build/windows_version_info.txt')
if not version_file.exists():
    raise SystemExit('Run scripts/build_windows.ps1 so Windows version metadata is generated first.')


a = Analysis(
    ['super_app.py'],
    pathex=[],
    binaries=[],
    datas=pyproj_datas,
    hiddenimports=['ezdxf', 'pyproj', 'super_ui'],
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
    a.binaries,
    a.datas,
    [],
    name='SuperElevation',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    version=str(version_file),
)
