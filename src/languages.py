"""Language definitions for NLLB translation."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Language:
    """UI label, NLLB FLORES code, and output filename suffix."""

    label_ja: str
    label_en: str
    nllb_code: str
    suffix: str


LANGUAGES: tuple[Language, ...] = (
    Language("日本語", "Japanese", "jpn_Jpan", "ja"),
    Language("英語", "English", "eng_Latn", "en"),
    Language("中国語（簡体）", "Chinese (Simplified)", "zho_Hans", "zh-hans"),
    Language("中国語（繁体）", "Chinese (Traditional)", "zho_Hant", "zh-hant"),
    Language("韓国語", "Korean", "kor_Hang", "ko"),
    Language("ロシア語", "Russian", "rus_Cyrl", "ru"),
)

SUFFIX_TO_LANGUAGE: dict[str, Language] = {lang.suffix: lang for lang in LANGUAGES}
NLLB_TO_LANGUAGE: dict[str, Language] = {lang.nllb_code: lang for lang in LANGUAGES}

# All known translation output suffixes (for batch skip logic).
TRANSLATION_SUFFIXES: frozenset[str] = frozenset(lang.suffix for lang in LANGUAGES)


def language_by_suffix(suffix: str) -> Language:
    """Resolve a filename suffix to a ``Language``.

    Args:
        suffix: Short code such as ``ja`` or ``zh-hans``.

    Returns:
        Matching ``Language``.

    Raises:
        KeyError: If ``suffix`` is unknown.
    """
    return SUFFIX_TO_LANGUAGE[suffix]


def dropdown_options(langcode: str) -> list[tuple[str, str]]:
    """Build Flet dropdown options as ``(suffix, label)`` pairs."""
    if langcode == "ja":
        return [(lang.suffix, lang.label_ja) for lang in LANGUAGES]
    return [(lang.suffix, lang.label_en) for lang in LANGUAGES]
