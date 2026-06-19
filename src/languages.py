"""Language definitions for NLLB translation (FLORES-200)."""

from __future__ import annotations

import json
import sys
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

_CATALOG_FILENAME = "nllb_languages.json"


def _catalog_path() -> Path:
    """Resolve the language catalog for dev and PyInstaller one-folder builds.

    PyInstaller places data files under ``_MEIPASS/src/`` while the compiled
    ``languages`` module may live directly under ``_MEIPASS/``.
    """
    module_dir = Path(__file__).resolve().parent
    candidates: list[Path] = [module_dir / _CATALOG_FILENAME]

    if getattr(sys, "frozen", False):
        bundle_root = Path(getattr(sys, "_MEIPASS", module_dir))
        candidates.extend(
            [
                bundle_root / _CATALOG_FILENAME,
                bundle_root / "src" / _CATALOG_FILENAME,
            ]
        )
    elif module_dir.name != "src":
        candidates.append(module_dir / "src" / _CATALOG_FILENAME)

    for path in candidates:
        if path.is_file():
            return path

    searched = ", ".join(str(path) for path in candidates)
    raise FileNotFoundError(f"Language catalog not found. Tried: {searched}")


@dataclass(frozen=True)
class Language:
    """UI labels, NLLB FLORES code, and optional legacy filename suffix."""

    nllb_code: str
    name_en: str
    name_ja: str
    flag: str
    favorite: bool
    legacy_suffix: str | None

    @property
    def suffix(self) -> str:
        """Filename suffix (legacy short code for favorites, else NLLB code)."""
        return self.legacy_suffix or self.nllb_code

    @property
    def label_ja(self) -> str:
        """Backward-compatible Japanese label."""
        return self.name_ja

    @property
    def label_en(self) -> str:
        """Backward-compatible English label."""
        return self.name_en

    def display_label(self, ui_lang: str) -> str:
        """Build dropdown label: flag + language name."""
        name = self.name_ja if ui_lang == "ja" else self.name_en
        return f"{self.flag} {name}"


@lru_cache(maxsize=1)
def _catalog() -> dict[str, object]:
    """Load bundled language catalog once."""
    raw = json.loads(_catalog_path().read_text(encoding="utf-8"))
    languages: list[Language] = []
    by_code: dict[str, Language] = {}
    by_suffix: dict[str, Language] = {}

    for item in raw["languages"]:
        lang = Language(
            nllb_code=item["nllb_code"],
            name_en=item["name_en"],
            name_ja=item["name_ja"],
            flag=item["flag"],
            favorite=bool(item.get("favorite")),
            legacy_suffix=item.get("legacy_suffix"),
        )
        languages.append(lang)
        by_code[lang.nllb_code] = lang
        by_suffix[lang.suffix] = lang
        if lang.legacy_suffix:
            by_suffix[lang.legacy_suffix] = lang

    favorite_codes: tuple[str, ...] = tuple(raw["favorite_codes"])
    favorites = tuple(by_code[code] for code in favorite_codes if code in by_code)
    others = tuple(lang for lang in languages if not lang.favorite)

    return {
        "languages": tuple(languages),
        "by_code": by_code,
        "by_suffix": by_suffix,
        "favorites": favorites,
        "others": others,
        "favorite_codes": favorite_codes,
        "default_source": raw.get("default_source", "eng_Latn"),
        "default_target": raw.get("default_target", "jpn_Jpan"),
        "count": int(raw.get("count", len(languages))),
    }


def language_count() -> int:
    """Return the number of supported NLLB language codes."""
    return int(_catalog()["count"])


def all_languages() -> tuple[Language, ...]:
    """Return every supported language in catalog order."""
    return _catalog()["languages"]  # type: ignore[return-value]


def favorite_languages() -> tuple[Language, ...]:
    """Return the six frequently used languages."""
    return _catalog()["favorites"]  # type: ignore[return-value]


def language_by_code(nllb_code: str) -> Language:
    """Resolve an NLLB FLORES code such as ``eng_Latn``.

    Raises:
        KeyError: If ``nllb_code`` is unknown.
    """
    try:
        return _catalog()["by_code"][nllb_code]  # type: ignore[index]
    except KeyError as exc:
        raise KeyError(f"Unknown NLLB language code: {nllb_code}") from exc


def language_by_suffix(suffix: str) -> Language:
    """Resolve a legacy suffix (``ja``) or full NLLB code.

    Raises:
        KeyError: If ``suffix`` is unknown.
    """
    try:
        return _catalog()["by_suffix"][suffix]  # type: ignore[index]
    except KeyError as exc:
        raise KeyError(f"Unknown language suffix or code: {suffix}") from exc


def resolve_language(value: str) -> Language:
    """Resolve CLI/GUI value (legacy suffix or NLLB code)."""
    catalog = _catalog()
    by_code = catalog["by_code"]
    by_suffix = catalog["by_suffix"]
    if value in by_code:
        return by_code[value]  # type: ignore[index]
    if value in by_suffix:
        return by_suffix[value]  # type: ignore[index]
    raise KeyError(f"Unknown language: {value}")


def normalize_config_code(stored: str, *, fallback: str) -> str:
    """Map saved userconf value to an NLLB code (supports legacy suffixes)."""
    catalog = _catalog()
    by_code = catalog["by_code"]
    by_suffix = catalog["by_suffix"]
    if stored in by_code:
        return stored
    if stored in by_suffix:
        return by_suffix[stored].nllb_code  # type: ignore[index]
    return fallback


def default_source_code() -> str:
    """Default source language NLLB code."""
    return str(_catalog()["default_source"])


def default_target_code() -> str:
    """Default target language NLLB code."""
    return str(_catalog()["default_target"])


def _init_exports() -> tuple[
    tuple[Language, ...],
    frozenset[str],
    dict[str, Language],
    dict[str, Language],
]:
    langs = all_languages()
    return (
        langs,
        frozenset(lang.suffix for lang in langs),
        {lang.suffix: lang for lang in langs},
        {lang.nllb_code: lang for lang in langs},
    )


LANGUAGES, TRANSLATION_SUFFIXES, SUFFIX_TO_LANGUAGE, NLLB_TO_LANGUAGE = _init_exports()


def dropdown_options(ui_lang: str) -> list[tuple[str, str]]:
    """Build dropdown rows: favorites first, then all others.

    Returns:
        ``(nllb_code, label)`` pairs. Separator rows use key ``__header__:…``.
    """
    favorites = favorite_languages()
    others = tuple(lang for lang in all_languages() if not lang.favorite)
    header = "── よく使う言語 ──" if ui_lang == "ja" else "── Frequently used ──"
    options: list[tuple[str, str]] = [(f"__header__:{header}", header)]
    options.extend((lang.nllb_code, lang.display_label(ui_lang)) for lang in favorites)
    divider = "── すべての言語 ──" if ui_lang == "ja" else "── All languages ──"
    options.append((f"__header__:{divider}", divider))
    options.extend((lang.nllb_code, lang.display_label(ui_lang)) for lang in others)
    return options


def build_flet_dropdown_options(ui_lang: str) -> list:
    """Return Flet ``DropdownOption`` list with flags in labels."""
    import flet as ft

    options: list[ft.dropdown.Option] = []
    for key, label in dropdown_options(ui_lang):
        if key.startswith("__header__"):
            options.append(ft.dropdown.Option(key=key, text=label, disabled=True))
            continue
        options.append(ft.dropdown.Option(key=key, text=label))
    return options
