"""Download and extract the Flet Windows desktop client for PyInstaller bundling."""

from __future__ import annotations

import sys
import urllib.request
import zipfile
from pathlib import Path

import flet_desktop.version

REPO_ROOT = Path(__file__).resolve().parent.parent
STAGE_DIR = REPO_ROOT / ".build" / "flet-client"
FLET_EXE = STAGE_DIR / "flet" / "flet.exe"


def main() -> int:
    """Stage flet.exe under ``.build/flet-client`` if not already present."""
    if FLET_EXE.is_file():
        print(f"Flet client already staged: {FLET_EXE}")
        return 0

    version = flet_desktop.version.version
    if not version:
        import flet.version
        from flet.version import update_version

        version = flet.version.version or update_version()

    zip_name = "flet-windows.zip"
    url = f"https://github.com/flet-dev/flet/releases/download/v{version}/{zip_name}"
    STAGE_DIR.mkdir(parents=True, exist_ok=True)
    zip_path = STAGE_DIR / zip_name

    print(f"Downloading Flet v{version} from {url}")
    urllib.request.urlretrieve(url, zip_path)

    print(f"Extracting to {STAGE_DIR}")
    with zipfile.ZipFile(zip_path, "r") as archive:
        archive.extractall(STAGE_DIR)

    if not FLET_EXE.is_file():
        print(f"[ERROR] flet.exe not found after extract: {FLET_EXE}", file=sys.stderr)
        return 1

    print(f"Staged Flet client: {FLET_EXE}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
