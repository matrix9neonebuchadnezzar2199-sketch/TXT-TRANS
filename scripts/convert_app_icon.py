"""Convert the TXT-TRANS mascot image to ``gui/assets/icon.ico`` for Windows."""

from __future__ import annotations

import sys
from pathlib import Path

from PIL import Image

REPO_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_SOURCE = REPO_ROOT / "image" / "8P6yIyDS.jpg"
OUTPUT = REPO_ROOT / "gui" / "assets" / "icon.ico"
ICO_SIZES = (16, 32, 48, 64, 128, 256)


def convert_icon(source: Path, output: Path) -> None:
    """Crop to square and write a multi-resolution Windows ICO file.

    Args:
        source: Source raster image (JPEG/PNG).
        output: Destination ``.ico`` path.

    Raises:
        FileNotFoundError: If ``source`` is missing.
    """
    if not source.is_file():
        raise FileNotFoundError(f"Icon source not found: {source}")

    output.parent.mkdir(parents=True, exist_ok=True)
    image = Image.open(source).convert("RGBA")
    width, height = image.size
    side = min(width, height)
    left = (width - side) // 2
    top = (height - side) // 2
    square = image.crop((left, top, left + side, top + side))
    square.save(output, format="ICO", sizes=[(size, size) for size in ICO_SIZES])
    print(f"Wrote {output} ({output.stat().st_size} bytes)")


def main(argv: list[str] | None = None) -> int:
    """CLI entry."""
    args = argv if argv is not None else sys.argv[1:]
    source = Path(args[0]) if args else DEFAULT_SOURCE
    output = Path(args[1]) if len(args) > 1 else OUTPUT
    try:
        convert_icon(source, output)
    except FileNotFoundError as exc:
        print(exc, file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
