"""Split long text into translation-friendly chunks."""

from __future__ import annotations

import re

# Sentence boundaries for CJK and Latin scripts.
_SENTENCE_END = re.compile(r"(?<=[。．.!?？])\s*")

MAX_CHUNK_CHARS = 400


def split_paragraphs(text: str) -> list[str]:
    """Split on blank lines while preserving paragraph boundaries.

    Args:
        text: Full source document.

    Returns:
        Non-empty paragraph strings.
    """
    paragraphs: list[str] = []
    for block in re.split(r"\n\s*\n", text):
        stripped = block.strip()
        if stripped:
            paragraphs.append(block.strip("\n"))
    if not paragraphs and text.strip():
        paragraphs.append(text.strip())
    return paragraphs


def split_long_paragraph(paragraph: str, max_chars: int = MAX_CHUNK_CHARS) -> list[str]:
    """Break an oversized paragraph at sentence boundaries.

    Args:
        paragraph: Single paragraph without inter-paragraph blank lines.
        max_chars: Soft maximum length per chunk.

    Returns:
        One or more chunks not exceeding ``max_chars`` when possible.
    """
    if len(paragraph) <= max_chars:
        return [paragraph]

    sentences = _SENTENCE_END.split(paragraph)
    chunks: list[str] = []
    current = ""

    for sentence in sentences:
        if not sentence:
            continue
        candidate = current + sentence if current else sentence
        if len(candidate) <= max_chars:
            current = candidate
            continue
        if current:
            chunks.append(current.strip())
        if len(sentence) <= max_chars:
            current = sentence
        else:
            # Hard split when a single sentence exceeds the limit.
            for offset in range(0, len(sentence), max_chars):
                piece = sentence[offset : offset + max_chars]
                if offset + max_chars < len(sentence):
                    chunks.append(piece)
                else:
                    current = piece
    if current:
        chunks.append(current.strip())
    return [chunk for chunk in chunks if chunk]


def chunk_text(text: str, max_chars: int = MAX_CHUNK_CHARS) -> list[str]:
    """Split text into paragraphs and sub-chunks for translation.

    Args:
        text: Source document.
        max_chars: Soft maximum characters per chunk.

    Returns:
        Ordered non-empty chunks.
    """
    result: list[str] = []
    for paragraph in split_paragraphs(text):
        for piece in split_long_paragraph(paragraph, max_chars=max_chars):
            if piece.strip():
                result.append(piece)
    return result


def join_chunks(chunks: list[str], original: str) -> str:
    """Reassemble translated chunks using the original paragraph structure.

    When the original used blank-line paragraph breaks, insert double newlines
    between translated paragraph groups. For single-paragraph inputs, join with
    newlines only.

    Args:
        chunks: Translated chunk strings (same count as ``chunk_text`` output).
        original: Original source text before chunking.

    Returns:
        Combined translated text.
    """
    if not chunks:
        return ""
    if "\n\n" in original:
        return "\n\n".join(chunks)
    return "\n".join(chunks)
