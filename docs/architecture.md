# TXT-TRANS Architecture

## Overview

Offline desktop translator for `.txt` files. Engine: **NLLB-200-distilled-600M** via **CTranslate2** (int8, CPU).

## Layers

| Layer | Path | Role |
|-------|------|------|
| GUI | `gui/main.py` | Flet UI, paste workflow, stop/reload, help dialog |
| CLI | `src/translate.py` | Batch / automation |
| Chunker | `src/chunker.py` | Paragraph and sentence splitting (~400 chars) |
| Translator | `src/translator.py` | CTranslate2 + Hugging Face tokenizer (`load`/`unload`, cancellable) |
| Languages | `src/languages.py` | UI labels and NLLB FLORES codes |
| Paths | `src/path_helpers.py` | `report.txt` → `report.en.txt` |

## Data flow

```
input.txt → chunk_text → translate_chunks (NLLB) → join_chunks → report.en.txt
```

GUI runs model load and translation on a **background thread** and updates the UI via `page.run_task` (Flet 0.27 requires async callbacks). Startup eagerly loads the model; **Stop** sets a cancel event, unloads weights, and the next translate reloads. Status line shows stop acknowledgement and chunk progress (`done/total`).

## Model

- Path: `models/nllb-200-distilled-600M-ct2/`
- Setup: `scripts/setup_model.ps1` (HF download + `ct2-transformers-converter --quantization int8`)
- Git: LFS tracked under `models/**`

## Frozen layout

PyInstaller bundles `models/` and Flet desktop client. User settings: `%LOCALAPPDATA%/TXT-TRANS/userconf.yaml`.

## PDF-SCAN integration

No code dependency. Workflow: PDF-SCAN → `report.txt` → open in TXT-TRANS → `report.en.txt`.
