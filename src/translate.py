"""CLI entry point for TXT-TRANS."""

from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

from languages import LANGUAGES, resolve_language
from path_helpers import default_model_dir, list_input_txt_files, output_path_for
from translator import NllbTranslator

REPO_ROOT = Path(__file__).resolve().parent.parent


def _build_parser() -> argparse.ArgumentParser:
    suffix_help = ", ".join(lang.suffix for lang in LANGUAGES[:6]) + ", … (202 NLLB codes)"
    parser = argparse.ArgumentParser(
        description="Offline text translator (NLLB-200 + CTranslate2)",
    )
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--input", type=Path, help="Single .txt file")
    group.add_argument("--input-dir", type=Path, help="Directory of .txt files")
    parser.add_argument(
        "--from",
        dest="src",
        required=True,
        help=f"Source language ({suffix_help}, e.g. en or eng_Latn)",
    )
    parser.add_argument(
        "--to",
        dest="tgt",
        required=True,
        help=f"Target language ({suffix_help}, e.g. ja or jpn_Jpan)",
    )
    parser.add_argument("--force", action="store_true", help="Overwrite existing outputs")
    parser.add_argument(
        "--model-dir",
        type=Path,
        default=None,
        help="Override bundled model path",
    )
    parser.add_argument("-v", "--verbose", action="store_true")
    return parser


def _translate_file(
    translator: NllbTranslator,
    input_path: Path,
    src: str,
    tgt: str,
    *,
    force: bool,
) -> Path:
    output_path = output_path_for(input_path, tgt)
    if output_path.exists() and not force:
        raise FileExistsError(f"Output exists (use --force): {output_path}")
    text = input_path.read_text(encoding="utf-8")
    translated = translator.translate(text, src, tgt)
    output_path.write_text(translated, encoding="utf-8")
    return output_path


def main(argv: list[str] | None = None) -> int:
    """Run the CLI translator.

    Args:
        argv: Optional argument list (defaults to ``sys.argv[1:]``).

    Returns:
        Process exit code.
    """
    parser = _build_parser()
    args = parser.parse_args(argv)
    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(levelname)s: %(message)s",
    )

    if args.src == args.tgt:
        parser.error("Source and target language must differ")

    try:
        src_lang = resolve_language(args.src)
        tgt_lang = resolve_language(args.tgt)
    except KeyError as exc:
        parser.error(str(exc))

    model_dir = args.model_dir or default_model_dir(REPO_ROOT)
    translator = NllbTranslator(model_dir)

    if args.input is not None:
        files = [args.input]
    else:
        files = list_input_txt_files(args.input_dir)

    if not files:
        logging.error("No input .txt files found")
        return 1

    for input_path in files:
        if not input_path.is_file():
            logging.error("Input not found: %s", input_path)
            return 1
        try:
            output_path = _translate_file(
                translator,
                input_path,
                src_lang.suffix,
                tgt_lang.suffix,
                force=args.force,
            )
            logging.info("%s -> %s", input_path, output_path)
        except FileExistsError as exc:
            logging.error("%s", exc)
            return 1
        except OSError as exc:
            logging.error("Failed to process %s: %s", input_path, exc)
            return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
