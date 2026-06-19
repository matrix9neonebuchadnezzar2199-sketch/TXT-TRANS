# TXT-TRANS Architecture

## Overview

Offline desktop translator for `.txt` files. Engine: **NLLB-200-distilled-600M** via **CTranslate2** (int8, CPU).

## Layers

| Layer | Path | Role |
|-------|------|------|
| GUI | `gui/main.py` | Flet UI, file pickers, background worker |
| CLI | `src/translate.py` | Batch / automation |
| Chunker | `src/chunker.py` | Paragraph and sentence splitting (~400 chars) |
| Translator | `src/translator.py` | Lazy-loaded CTranslate2 + Hugging Face tokenizer |
| Languages | `src/languages.py` | UI labels and NLLB FLORES codes |
| Paths | `src/path_helpers.py` | `report.txt` → `report.en.txt` |

## Data flow

```
input.txt → chunk_text → translate_chunks (NLLB) → join_chunks → report.en.txt
```

GUI runs translation on a **background thread** and updates the UI via `page.run_task` (no UI-thread blocking).

## Model

- Path: `models/nllb-200-distilled-600M-ct2/`
- Setup: `scripts/setup_model.ps1` (HF download + `ct2-transformers-converter --quantization int8`)
- Git: LFS tracked under `models/**`

## Frozen layout

PyInstaller bundles `models/` and Flet desktop client. User settings: `%LOCALAPPDATA%/TXT-TRANS/userconf.yaml`.

## PDF-SCAN integration

No code dependency. Workflow: PDF-SCAN → `report.txt` → open in TXT-TRANS → `report.en.txt`.
