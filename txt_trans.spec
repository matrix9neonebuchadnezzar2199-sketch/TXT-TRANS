# -*- mode: python ; coding: utf-8 -*-
"""PyInstaller spec for TXT-TRANS (one-folder, model bundled)."""

import os

from PyInstaller.utils.hooks import collect_all

ENTRY_SCRIPT = os.path.join("gui", "main.py")
APP_NAME = "TXT-TRANS"
SRC_DIR = "src"
GUI_DIR = "gui"
MODEL_DIR = os.path.join("models", "nllb-200-distilled-600M-ct2")
BUILD_DIR = ".build"
FLET_CLIENT_DIR = os.path.join(BUILD_DIR, "flet-client", "flet")
ONEFILE = False

datas = []
binaries = []
hiddenimports = []

if os.path.isdir(MODEL_DIR):
    datas.append((MODEL_DIR, MODEL_DIR))
else:
    print(f"[WARN] Model dir missing: {MODEL_DIR!r}; run scripts/setup_model.ps1")

_gui_assets = os.path.join(GUI_DIR, "assets")
if os.path.isdir(_gui_assets):
    datas.append((_gui_assets, "assets"))

if os.path.isdir(FLET_CLIENT_DIR):
    datas.append((FLET_CLIENT_DIR, os.path.join("flet_desktop", "app", "flet")))
else:
    print(
        f"[WARN] Flet client not staged at {FLET_CLIENT_DIR!r}; "
        "run scripts/prepare_flet_client.py before building."
    )

for package_name in ("ctranslate2", "transformers", "sentencepiece", "yaml"):
    try:
        pkg_datas, pkg_binaries, pkg_hiddenimports = collect_all(package_name)
        datas += pkg_datas
        binaries += pkg_binaries
        hiddenimports += pkg_hiddenimports
    except Exception as exc:
        print(f"[WARN] collect_all({package_name!r}) failed: {exc}")

hiddenimports += ["flet", "flet_desktop", "ctranslate2", "transformers", "sentencepiece"]

try:
    flet_datas, flet_binaries, flet_hiddenimports = collect_all("flet")
    datas += flet_datas
    binaries += flet_binaries
    hiddenimports += flet_hiddenimports
except Exception as exc:
    print(f"[WARN] collect_all('flet') failed: {exc}")

try:
    fd_datas, fd_binaries, fd_hiddenimports = collect_all("flet_desktop")
    datas += fd_datas
    binaries += fd_binaries
    hiddenimports += fd_hiddenimports
except Exception as exc:
    print(f"[WARN] collect_all('flet_desktop') failed: {exc}")

block_cipher = None

a = Analysis(
    [ENTRY_SCRIPT],
    pathex=[SRC_DIR, GUI_DIR],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

_icon = os.path.join(GUI_DIR, "assets", "icon.ico")
_icon_arg = _icon if os.path.isfile(_icon) else None

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name=APP_NAME,
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=False,
    disable_windowed_traceback=False,
    icon=_icon_arg,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=False,
    name=APP_NAME,
)
