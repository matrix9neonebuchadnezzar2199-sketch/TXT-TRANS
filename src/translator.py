"""NLLB-200 CTranslate2 translation wrapper."""

from __future__ import annotations

import logging
import threading
from collections.abc import Callable
from pathlib import Path

import ctranslate2
from transformers import AutoTokenizer

from chunker import chunk_text, join_chunks
from languages import language_by_suffix

logger = logging.getLogger(__name__)


class NllbTranslator:
    """Offline translator using a local CTranslate2 NLLB model."""

    def __init__(
        self,
        model_dir: Path,
        *,
        device: str = "cpu",
        compute_type: str = "int8",
    ) -> None:
        """Store model location; weights load lazily on first translate.

        Args:
            model_dir: Directory produced by ``ct2-transformers-converter``.
            device: CTranslate2 device (``cpu`` only for v1).
            compute_type: Quantization mode (``int8`` recommended).
        """
        self.model_dir = Path(model_dir)
        self.device = device
        self.compute_type = compute_type
        self._translator: ctranslate2.Translator | None = None
        self._tokenizer: AutoTokenizer | None = None
        self._load_lock = threading.Lock()

    def _ensure_loaded(self) -> None:
        if self._translator is not None:
            return
        with self._load_lock:
            if self._translator is not None:
                return
            if not self.model_dir.is_dir():
                raise FileNotFoundError(
                    f"Model directory not found: {self.model_dir}. "
                    "Run scripts/setup_model.ps1 first."
                )
            logger.info("Loading NLLB model from %s", self.model_dir)
            self._translator = ctranslate2.Translator(
                str(self.model_dir),
                device=self.device,
                compute_type=self.compute_type,
            )
            self._tokenizer = AutoTokenizer.from_pretrained(str(self.model_dir))

    def translate(self, text: str, src_suffix: str, tgt_suffix: str) -> str:
        """Translate a single text block.

        Args:
            text: Source text.
            src_suffix: Source language suffix (``ja``, ``en``, ...).
            tgt_suffix: Target language suffix.

        Returns:
            Translated text with paragraph structure preserved.
        """
        chunks = chunk_text(text)
        if not chunks:
            return ""
        translated = self.translate_chunks(chunks, src_suffix, tgt_suffix)
        return join_chunks(translated, text)

    def translate_chunks(
        self,
        chunks: list[str],
        src_suffix: str,
        tgt_suffix: str,
        *,
        on_progress: Callable[[int, int], None] | None = None,
        cancel_event: threading.Event | None = None,
    ) -> list[str]:
        """Translate pre-split chunks with optional progress and cancel.

        Args:
            chunks: Non-empty strings from ``chunk_text``.
            src_suffix: Source language suffix.
            tgt_suffix: Target language suffix.
            on_progress: Called as ``(completed, total)`` after each chunk.
            cancel_event: When set, stop before the next chunk.

        Returns:
            Translated chunks in order.

        Raises:
            RuntimeError: If translation is cancelled mid-run.
        """
        self._ensure_loaded()
        assert self._translator is not None
        assert self._tokenizer is not None

        src_lang = language_by_suffix(src_suffix)
        tgt_lang = language_by_suffix(tgt_suffix)
        tokenizer = self._tokenizer
        translator = self._translator

        tokenizer.src_lang = src_lang.nllb_code
        if hasattr(tokenizer, "lang_code_to_token"):
            target_prefix = [tokenizer.lang_code_to_token[tgt_lang.nllb_code]]
        else:
            target_prefix = [tgt_lang.nllb_code]

        results: list[str] = []
        total = len(chunks)

        for index, chunk in enumerate(chunks):
            if cancel_event is not None and cancel_event.is_set():
                raise RuntimeError("Translation cancelled")

            token_ids = tokenizer.encode(chunk)
            source_tokens = tokenizer.convert_ids_to_tokens(token_ids)
            batch_result = translator.translate_batch(
                [source_tokens],
                target_prefix=[target_prefix],
                beam_size=1,
                max_decoding_length=512,
            )
            hypothesis = batch_result[0].hypotheses[0]
            output_ids = tokenizer.convert_tokens_to_ids(hypothesis)
            results.append(tokenizer.decode(output_ids, skip_special_tokens=True))

            if on_progress is not None:
                on_progress(index + 1, total)

        return results
