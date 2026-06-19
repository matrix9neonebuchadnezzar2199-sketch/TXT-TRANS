import sys
import os
import threading
from pathlib import Path


def _ensure_project_venv() -> None:
    """Re-exec with repo-root .venv when bare ``python`` lacks dependencies."""
    import importlib.util

    repo_root = Path(__file__).resolve().parent.parent
    venv_python = repo_root / ".venv" / "Scripts" / "python.exe"
    if importlib.util.find_spec("flet") is not None:
        return
    if venv_python.is_file():
        os.execv(str(venv_python), [str(venv_python), *sys.argv])


if not getattr(sys, "frozen", False):
    _ensure_project_venv()

IS_FROZEN = getattr(sys, "frozen", False)
GUI_ROOT = Path(__file__).resolve().parent
if IS_FROZEN:
    _BUNDLE_ROOT = Path(getattr(sys, "_MEIPASS", GUI_ROOT))
    REPO_ROOT = _BUNDLE_ROOT
    SRC_DIR = _BUNDLE_ROOT / "src" if (_BUNDLE_ROOT / "src").is_dir() else _BUNDLE_ROOT
else:
    REPO_ROOT = GUI_ROOT.parent
    SRC_DIR = REPO_ROOT / "src"

if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

import flet as ft
import yaml

from chunker import chunk_text, join_chunks
from languages import dropdown_options
from path_helpers import default_model_dir, list_input_txt_files, output_path_for
from translator import NllbTranslator

UI_STRINGS = {
    "ja": {
        "title": "TXT-TRANS",
        "pick_file": "ファイル選択",
        "pick_folder": "フォルダ選択",
        "paste": "クリップボード",
        "source": "原文の言語",
        "target": "訳文の言語",
        "start": "翻訳開始",
        "cancel": "キャンセル",
        "source_preview": "原文",
        "target_preview": "訳文",
        "loading_model": "モデル読み込み中…",
        "ready": "準備完了",
        "progress": "段落 {done}/{total}",
        "done": "翻訳完了: {path}",
        "cancelled": "キャンセルしました ({done}/{total})",
        "no_input": "入力ファイルを選択してください",
        "same_lang": "原文と訳文の言語が同じです",
        "exists": "出力ファイルが既にあります: {path}",
        "error": "エラー: {msg}",
    },
    "en": {
        "title": "TXT-TRANS",
        "pick_file": "Pick file",
        "pick_folder": "Pick folder",
        "paste": "Clipboard",
        "source": "Source language",
        "target": "Target language",
        "start": "Translate",
        "cancel": "Cancel",
        "source_preview": "Source",
        "target_preview": "Translation",
        "loading_model": "Loading model…",
        "ready": "Ready",
        "progress": "Chunk {done}/{total}",
        "done": "Saved: {path}",
        "cancelled": "Cancelled ({done}/{total})",
        "no_input": "Select an input file",
        "same_lang": "Source and target language are the same",
        "exists": "Output already exists: {path}",
        "error": "Error: {msg}",
    },
}


def userconf_path() -> Path:
    """GUI settings path (AppData when frozen)."""
    if IS_FROZEN:
        state_dir = (
            Path(os.environ.get("LOCALAPPDATA", str(Path.home() / "AppData" / "Local")))
            / "TXT-TRANS"
        )
        state_dir.mkdir(parents=True, exist_ok=True)
        return state_dir / "userconf.yaml"
    return GUI_ROOT / "userconf.yaml"


def load_config() -> dict:
    """Load or create default user configuration."""
    path = userconf_path()
    defaults = {"langcode": "ja", "source_lang": "ja", "target_lang": "en"}
    if not path.is_file():
        return defaults
    try:
        with path.open(encoding="utf-8") as handle:
            data = yaml.safe_load(handle) or {}
        return {**defaults, **data}
    except (OSError, yaml.YAMLError):
        return defaults


def save_config(config: dict) -> None:
    """Persist GUI language and last-used translation pair."""
    path = userconf_path()
    try:
        with path.open("w", encoding="utf-8") as handle:
            yaml.safe_dump(config, handle, allow_unicode=True, sort_keys=False)
    except OSError:
        pass


def main(page: ft.Page) -> None:
    """Build and run the TXT-TRANS Flet UI."""
    config = load_config()
    langcode = config.get("langcode", "ja")

    def L(key: str, **kwargs: str) -> str:
        text = UI_STRINGS.get(langcode, UI_STRINGS["en"]).get(key, key)
        return text.format(**kwargs) if kwargs else text

    page.title = L("title")
    page.window.width = 900
    page.window.height = 720
    page.padding = 16

    model_dir = default_model_dir(REPO_ROOT)
    translator_holder: dict[str, NllbTranslator | None] = {"instance": None}
    cancel_event = threading.Event()
    worker: dict[str, threading.Thread | None] = {"thread": None}

    selected_input = ft.TextField(label="Input", read_only=True, expand=True)
    source_preview = ft.TextField(
        label=L("source_preview"),
        multiline=True,
        min_lines=8,
        max_lines=12,
        read_only=True,
        expand=True,
    )
    target_preview = ft.TextField(
        label=L("target_preview"),
        multiline=True,
        min_lines=8,
        max_lines=12,
        read_only=True,
        expand=True,
    )
    progress_bar = ft.ProgressBar(value=0, width=400)
    status_text = ft.Text(L("ready"))
    start_btn = ft.ElevatedButton(L("start"))
    cancel_btn = ft.OutlinedButton(L("cancel"), disabled=True)

    lang_options = dropdown_options(langcode)
    source_dd = ft.Dropdown(
        label=L("source"),
        options=[ft.dropdown.Option(key=s, text=label) for s, label in lang_options],
        value=config.get("source_lang", "ja"),
        width=200,
    )
    target_dd = ft.Dropdown(
        label=L("target"),
        options=[ft.dropdown.Option(key=s, text=label) for s, label in lang_options],
        value=config.get("target_lang", "en"),
        width=200,
    )

    input_files: list[Path] = []

    def set_busy(busy: bool) -> None:
        start_btn.disabled = busy
        cancel_btn.disabled = not busy
        page.update()

    def update_status(message: str) -> None:
        status_text.value = message
        page.update()

    def on_progress(done: int, total: int) -> None:
        progress_bar.value = done / max(total, 1)
        update_status(L("progress", done=str(done), total=str(total)))

    def load_input_file(path: Path) -> None:
        input_files.clear()
        input_files.append(path)
        selected_input.value = str(path)
        try:
            source_preview.value = path.read_text(encoding="utf-8")
        except OSError as exc:
            source_preview.value = ""
            update_status(L("error", msg=str(exc)))
            return
        target_preview.value = ""
        page.update()

    def pick_files_result(event: ft.FilePickerResultEvent) -> None:
        if event.files:
            load_input_file(Path(event.files[0].path))

    def pick_folder_result(event: ft.FilePickerResultEvent) -> None:
        if event.path:
            folder = Path(event.path)
            files = list_input_txt_files(folder)
            if files:
                load_input_file(files[0])
                input_files.clear()
                input_files.extend(files)

    file_picker = ft.FilePicker(on_result=pick_files_result)
    folder_picker = ft.FilePicker(on_result=pick_folder_result)
    page.overlay.extend([file_picker, folder_picker])

    def paste_clipboard(_event: ft.ControlEvent) -> None:
        try:
            import tkinter as tk

            root = tk.Tk()
            root.withdraw()
            clip = root.clipboard_get()
            root.destroy()
        except (tk.TclError, ImportError):
            update_status(L("error", msg="Clipboard unavailable"))
            return
        source_preview.value = clip
        input_files.clear()
        selected_input.value = "(clipboard)"
        target_preview.value = ""
        page.update()

    def get_translator() -> NllbTranslator:
        if translator_holder["instance"] is None:
            update_status(L("loading_model"))
            translator_holder["instance"] = NllbTranslator(model_dir)
        return translator_holder["instance"]

    def translate_worker() -> None:
        src = source_dd.value or "ja"
        tgt = target_dd.value or "en"
        config["source_lang"] = src
        config["target_lang"] = tgt
        save_config(config)

        try:
            engine = get_translator()

            def progress_cb(done: int, total: int) -> None:
                page.run_task(lambda: on_progress(done, total))

            if input_files:
                last_output = ""
                for input_path in input_files:
                    if cancel_event.is_set():
                        break
                    text = input_path.read_text(encoding="utf-8")
                    chunks = chunk_text(text)
                    translated_chunks = engine.translate_chunks(
                        chunks,
                        src,
                        tgt,
                        on_progress=progress_cb,
                        cancel_event=cancel_event,
                    )
                    result = join_chunks(translated_chunks, text)
                    out_path = output_path_for(input_path, tgt)
                    if out_path.exists():
                        page.run_task(
                            lambda p=out_path: update_status(L("exists", path=str(p)))
                        )
                        continue
                    out_path.write_text(result, encoding="utf-8")
                    last_output = str(out_path)
                    page.run_task(lambda r=result: setattr(target_preview, "value", r))
                    page.run_task(page.update)
                if cancel_event.is_set():
                    page.run_task(lambda: update_status(L("cancelled", done="?", total="?")))
                elif last_output:
                    page.run_task(lambda: update_status(L("done", path=last_output)))
            else:
                clip_text = source_preview.value or ""
                if not clip_text.strip():
                    page.run_task(lambda: update_status(L("no_input")))
                    return
                chunks = chunk_text(clip_text)
                translated_chunks = engine.translate_chunks(
                    chunks,
                    src,
                    tgt,
                    on_progress=progress_cb,
                    cancel_event=cancel_event,
                )
                result = join_chunks(translated_chunks, clip_text)
                page.run_task(lambda r=result: setattr(target_preview, "value", r))
                page.run_task(page.update)
                page.run_task(lambda: update_status(L("ready")))

        except RuntimeError as exc:
            if "cancelled" in str(exc).lower():
                page.run_task(lambda: update_status(L("cancelled", done="?", total="?")))
            else:
                page.run_task(lambda e=exc: update_status(L("error", msg=str(e))))
        except (OSError, FileNotFoundError) as exc:
            page.run_task(lambda e=exc: update_status(L("error", msg=str(e))))
        finally:
            cancel_event.clear()
            page.run_task(lambda: set_busy(False))
            page.run_task(lambda: setattr(progress_bar, "value", 0))
            page.run_task(page.update)

    def start_translate(_event: ft.ControlEvent) -> None:
        if source_dd.value == target_dd.value:
            update_status(L("same_lang"))
            return
        if not input_files and not (source_preview.value or "").strip():
            update_status(L("no_input"))
            return
        if worker["thread"] is not None and worker["thread"].is_alive():
            return
        cancel_event.clear()
        progress_bar.value = 0
        set_busy(True)
        worker["thread"] = threading.Thread(target=translate_worker, daemon=True)
        worker["thread"].start()

    def request_cancel(_event: ft.ControlEvent) -> None:
        cancel_event.set()

    start_btn.on_click = start_translate
    cancel_btn.on_click = request_cancel

    page.add(
        ft.Row(
            [
                ft.ElevatedButton(L("pick_file"), on_click=lambda _: file_picker.pick_files(allow_multiple=False, allowed_extensions=["txt"])),
                ft.ElevatedButton(L("pick_folder"), on_click=lambda _: folder_picker.get_directory_path()),
                ft.OutlinedButton(L("paste"), on_click=paste_clipboard),
            ]
        ),
        selected_input,
        ft.Row([source_dd, ft.Text("→"), target_dd]),
        ft.Row([source_preview, target_preview], expand=True),
        ft.Row([progress_bar, status_text], alignment=ft.MainAxisAlignment.START),
        ft.Row([start_btn, cancel_btn]),
    )


if __name__ == "__main__":
    ft.app(target=main)
