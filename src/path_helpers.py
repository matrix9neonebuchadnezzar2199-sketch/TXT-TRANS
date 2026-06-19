"""Output path resolution and input file discovery."""

from __future__ import annotations

from pathlib import Path

from languages import resolve_language


def default_model_dir(repo_root: Path) -> Path:
    """Return the bundled NLLB CTranslate2 model directory."""
    return repo_root / "models" / "nllb-200-distilled-600M-ct2"


def _language_tag_from_name(filename: str) -> str | None:
    """Return the language tag from ``stem.lang.txt`` if recognized."""
    if not filename.lower().endswith(".txt"):
        return None
    base = filename[:-4]
    dot = base.rfind(".")
    if dot <= 0:
        return None
    tag = base[dot + 1 :]
    try:
        resolve_language(tag)
    except KeyError:
        return None
    return tag


def output_path_for(input_path: Path, target_tag: str) -> Path:
    """Build ``stem.{target}.txt`` beside the input file.

    Args:
        input_path: Source ``.txt`` file.
        target_tag: Target language suffix or NLLB code.

    Returns:
        Output path in the same directory as ``input_path``.
    """
    target_lang = resolve_language(target_tag)
    stem = input_path.stem
    existing_tag = _language_tag_from_name(input_path.name)
    if existing_tag is not None:
        stem = input_path.name[: -(len(existing_tag) + 5)]
    return input_path.parent / f"{stem}.{target_lang.suffix}.txt"


def is_translated_txt(path: Path) -> bool:
    """Return True if ``path`` looks like a generated translation file."""
    return _language_tag_from_name(path.name) is not None


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
    from languages import LANGUAGES

    return tuple(lang.suffix for lang in LANGUAGES)
