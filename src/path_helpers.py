"""Output path resolution and input file discovery."""

from __future__ import annotations

import re
from pathlib import Path

from languages import LANGUAGES, TRANSLATION_SUFFIXES, language_by_suffix

# report.en.txt -> stem report, suffix en
_TRANSLATED_NAME = re.compile(
    r"^(.+)\.(" + "|".join(re.escape(s) for s in sorted(TRANSLATION_SUFFIXES, key=len, reverse=True)) + r")\.txt$",
    re.IGNORECASE,
)


def default_model_dir(repo_root: Path) -> Path:
    """Return the bundled NLLB CTranslate2 model directory."""
    return repo_root / "models" / "nllb-200-distilled-600M-ct2"


def output_path_for(input_path: Path, target_suffix: str) -> Path:
    """Build ``stem.{target}.txt`` beside the input file.

    Args:
        input_path: Source ``.txt`` file.
        target_suffix: Target language suffix such as ``en``.

    Returns:
        Output path in the same directory as ``input_path``.
    """
    language_by_suffix(target_suffix)
    stem = input_path.stem
    # Strip an existing language suffix from inputs like report.ja.txt
    match = _TRANSLATED_NAME.match(input_path.name)
    if match:
        stem = match.group(1)
    return input_path.parent / f"{stem}.{target_suffix}.txt"


def is_translated_txt(path: Path) -> bool:
    """Return True if ``path`` looks like a generated translation file."""
    return _TRANSLATED_NAME.match(path.name) is not None


def list_input_txt_files(directory: Path) -> list[Path]:
    """List ``*.txt`` files in ``directory``, excluding translation outputs.

    Args:
        directory: Folder to scan.

    Returns:
        Sorted list of source text files.
    """
    files = [
        path
        for path in directory.glob("*.txt")
        if path.is_file() and not is_translated_txt(path)
    ]
    return sorted(files)


def all_language_suffixes() -> tuple[str, ...]:
    """Return every supported output suffix."""
    return tuple(lang.suffix for lang in LANGUAGES)
