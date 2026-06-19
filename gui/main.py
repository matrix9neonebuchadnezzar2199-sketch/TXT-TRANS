import os
import sys
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
from languages import (
    build_flet_dropdown_options,
    default_source_code,
    default_target_code,
    language_by_code,
    normalize_config_code,
)
from path_helpers import default_model_dir
from translator import NllbTranslator

UI_STRINGS = {
    "ja": {
        "title": "TXT-TRANS",
        "source": "原文の言語",
        "target": "訳文の言語",
        "start": "翻訳開始",
        "stop": "停止",
        "source_preview": "原文（ここに貼り付け）",
        "target_preview": "訳文",
        "loading_model": "モデルをロード中です…",
        "ready": "準備完了",
        "progress": "段落 {done}/{total}",
        "done": "翻訳完了",
        "cancelled": "停止しました",
        "load_cancelled": "モデル読み込みを停止しました",
        "no_input": "原文にテキストを入力してください",
        "same_lang": "原文と訳文の言語が同じです",
        "pick_lang": "言語を選択してください",
        "error": "エラー: {msg}",
        "wait_model": "モデルのロード完了をお待ちください",
        "lang_section": "言語設定",
        "input_section": "INPUT",
        "output_section": "OUTPUT",
        "paste_hint": "Ctrl+V で貼り付け",
        "stop_ack": "停止を受け付けました…",
        "stop_idle": "停止できる処理は実行されていません",
        "stop_translate_done": "翻訳を停止しました（段落 {done}/{total}）",
        "stop_load_done": "モデル読み込みを停止しました",
        "help_tooltip": "ヘルプ",
        "help_title": "TXT-TRANS ヘルプ",
        "help_close": "閉じる",
        "help_body": (
            "【翻訳エンジン】\n"
            "Meta NLLB-200-distilled-600M（No Language Left Behind）を\n"
            "CTranslate2（int8 量子化）で CPU 実行しています。\n\n"
            "・完全オフライン（インターネット不要）\n"
            "・対応言語: NLLB-200（202言語、日英中韓露は上部に固定表示）\n"
            "・段落単位で翻訳（長文は自動分割）\n"
            "・専門用語は文脈によって誤訳する場合があります\n\n"
            "【使い方】\n"
            "1. 原文欄（青枠）にテキストを貼り付け\n"
            "2. 原文・訳文の言語を選択\n"
            "3. 「翻訳開始」を押す\n\n"
            "「停止」を押すと処理を中断します。\n"
            "停止後に再度翻訳する場合は、モデルを再ロードしてから翻訳します。\n\n"
            "製作者：OK"
        ),
    },
    "en": {
        "title": "TXT-TRANS",
        "source": "Source language",
        "target": "Target language",
        "start": "Translate",
        "stop": "Stop",
        "source_preview": "Source (paste here)",
        "target_preview": "Translation",
        "loading_model": "Loading model…",
        "ready": "Ready",
        "progress": "Chunk {done}/{total}",
        "done": "Translation complete",
        "cancelled": "Stopped",
        "load_cancelled": "Model loading stopped",
        "no_input": "Paste source text first",
        "same_lang": "Source and target language are the same",
        "pick_lang": "Select a language",
        "error": "Error: {msg}",
        "wait_model": "Wait for model loading to finish",
        "lang_section": "Languages",
        "input_section": "INPUT",
        "output_section": "OUTPUT",
        "paste_hint": "Paste with Ctrl+V",
        "stop_ack": "Stop requested…",
        "stop_idle": "Nothing is running to stop",
        "stop_translate_done": "Translation stopped (chunk {done}/{total})",
        "stop_load_done": "Model loading stopped",
        "help_tooltip": "Help",
        "help_title": "TXT-TRANS Help",
        "help_close": "Close",
        "help_body": (
            "【Translation engine】\n"
            "Runs Meta NLLB-200-distilled-600M (No Language Left Behind)\n"
            "via CTranslate2 (int8) on CPU.\n\n"
            "・Fully offline\n"
            "・Languages: NLLB-200 (202; JA/EN/ZH/KO/RU pinned at top)\n"
            "・Paragraph-based chunking for long text\n\n"
            "【How to use】\n"
            "1. Paste text into the blue INPUT box\n"
            "2. Choose source and target languages\n"
            "3. Click Translate\n\n"
            "Stop interrupts the current job. The next run reloads the model first.\n\n"
            "Author: OK"
        ),
    },
}


# Dark-theme panel colors (input vs output vs selectors).
UI = {
    "page_bg": "#1a2332",
    "panel_border": "#4a6fa5",
    "text": "#e8eef7",
    "muted": "#9eb0c8",
    "select_bg": "#243044",
    "select_border": "#6b8fc7",
    "input_bg": "#1a3352",
    "input_border": "#5eb3ff",
    "input_focus": "#7ec8ff",
    "output_bg": "#1a3328",
    "output_border": "#5ecf8a",
    "accent": "#5eb3ff",
    "output_accent": "#6bcf8a",
    "warn": "#ffb020",
    "error": "#ff6b6b",
}


def _section_label(text: str, color: str) -> ft.Text:
    return ft.Text(text, size=13, weight=ft.FontWeight.W_600, color=color)


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
    defaults = {
        "langcode": "ja",
        "source_lang": default_source_code(),
        "target_lang": default_target_code(),
    }
    if not path.is_file():
        return defaults
    try:
        with path.open(encoding="utf-8") as handle:
            data = yaml.safe_load(handle) or {}
        merged = {**defaults, **data}
        merged["source_lang"] = normalize_config_code(
            str(merged.get("source_lang", defaults["source_lang"])),
            fallback=defaults["source_lang"],
        )
        merged["target_lang"] = normalize_config_code(
            str(merged.get("target_lang", defaults["target_lang"])),
            fallback=defaults["target_lang"],
        )
        return merged
    except (OSError, yaml.YAMLError):
        return defaults


def save_config(config: dict) -> None:
    """Persist last-used translation language pair."""
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
    page.bgcolor = UI["page_bg"]
    page.theme = ft.Theme(
        color_scheme_seed=UI["accent"],
        visual_density=ft.VisualDensity.COMFORTABLE,
    )
    page.theme_mode = ft.ThemeMode.DARK

    model_dir = default_model_dir(REPO_ROOT)

    translator_holder: dict[str, NllbTranslator | None] = {"instance": None}
    model_ready = {"value": False}
    model_loading = {"value": False}
    reload_needed = {"value": False}
    stop_event = threading.Event()
    worker: dict[str, threading.Thread | None] = {"thread": None}

    source_preview = ft.TextField(
        label=L("source_preview"),
        multiline=True,
        min_lines=10,
        max_lines=16,
        expand=True,
        disabled=True,
        bgcolor=UI["input_bg"],
        border_color=UI["input_border"],
        focused_border_color=UI["input_focus"],
        border_width=2,
        focused_border_width=2,
        cursor_color=UI["input_focus"],
        text_style=ft.TextStyle(color=UI["text"]),
        label_style=ft.TextStyle(color=UI["accent"], weight=ft.FontWeight.W_600),
        hint_text=L("paste_hint"),
        hint_style=ft.TextStyle(color=UI["muted"], italic=True),
    )
    target_preview = ft.TextField(
        label=L("target_preview"),
        multiline=True,
        min_lines=10,
        max_lines=16,
        read_only=True,
        expand=True,
        disabled=True,
        bgcolor=UI["output_bg"],
        border_color=UI["output_border"],
        border_width=2,
        text_style=ft.TextStyle(color=UI["text"]),
        label_style=ft.TextStyle(color=UI["output_accent"], weight=ft.FontWeight.W_600),
    )
    progress_bar = ft.ProgressBar(value=None, width=400, color=UI["accent"], bgcolor=UI["select_bg"])
    status_text = ft.Text(L("loading_model"), color=UI["muted"], size=14, weight=ft.FontWeight.W_500)
    status_icon = ft.Icon(ft.Icons.INFO_OUTLINE, color=UI["muted"], size=20)
    progress_state = {"done": 0, "total": 0}
    stop_pending = {"value": False}
    start_btn = ft.ElevatedButton(
        L("start"),
        disabled=True,
        bgcolor=UI["accent"],
        color=UI["page_bg"],
    )
    stop_btn = ft.OutlinedButton(L("stop"), style=ft.ButtonStyle(color=UI["muted"]))

    lang_options = build_flet_dropdown_options(langcode)
    dropdown_style = dict(
        bgcolor=UI["select_bg"],
        border_color=UI["select_border"],
        focused_border_color=UI["input_focus"],
        border_width=1,
        focused_border_width=2,
        label_style=ft.TextStyle(color=UI["muted"]),
        text_style=ft.TextStyle(color=UI["text"], weight=ft.FontWeight.W_500),
    )
    source_dd = ft.Dropdown(
        label=L("source"),
        options=lang_options,
        value=config.get("source_lang", default_source_code()),
        width=300,
        disabled=True,
        enable_filter=True,
        filter_on_change=True,
        **dropdown_style,
    )
    target_dd = ft.Dropdown(
        label=L("target"),
        options=lang_options,
        value=config.get("target_lang", default_target_code()),
        width=300,
        disabled=True,
        enable_filter=True,
        filter_on_change=True,
        **dropdown_style,
    )

    lang_panel = ft.Container(
        content=ft.Column(
            [
                _section_label(L("lang_section"), UI["muted"]),
                ft.Row(
                    [
                        source_dd,
                        ft.Icon(ft.Icons.ARROW_FORWARD, color=UI["accent"], size=28),
                        target_dd,
                    ],
                    alignment=ft.MainAxisAlignment.CENTER,
                    spacing=16,
                ),
            ],
            spacing=8,
        ),
        padding=16,
        border_radius=12,
        border=ft.border.all(1, UI["select_border"]),
        bgcolor=UI["select_bg"],
    )

    source_panel = ft.Container(
        content=ft.Column(
            [
                _section_label(L("input_section"), UI["accent"]),
                source_preview,
            ],
            spacing=4,
            expand=True,
        ),
        padding=12,
        border_radius=12,
        border=ft.border.all(2, UI["input_border"]),
        bgcolor=ft.Colors.with_opacity(0.35, UI["input_bg"]),
        expand=True,
    )

    target_panel = ft.Container(
        content=ft.Column(
            [
                _section_label(L("output_section"), UI["output_accent"]),
                target_preview,
            ],
            spacing=4,
            expand=True,
        ),
        padding=12,
        border_radius=12,
        border=ft.border.all(2, UI["output_border"]),
        bgcolor=ft.Colors.with_opacity(0.35, UI["output_bg"]),
        expand=True,
    )

    load_overlay = ft.Container(
        content=ft.Column(
            [
                ft.Text(L("loading_model"), size=18, weight=ft.FontWeight.BOLD),
                ft.ProgressBar(width=360, value=None),
            ],
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            alignment=ft.MainAxisAlignment.CENTER,
            spacing=16,
        ),
        alignment=ft.alignment.center,
        expand=True,
        bgcolor=ft.Colors.with_opacity(0.85, ft.Colors.SURFACE),
        visible=True,
    )

    def schedule_ui(callback, *args, **kwargs) -> None:
        """Run a sync UI callback on the Flet event loop (requires async wrapper)."""

        async def _task() -> None:
            callback(*args, **kwargs)

        page.run_task(_task)

    def set_work_ui_enabled(enabled: bool) -> None:
        source_preview.disabled = not enabled
        source_dd.disabled = not enabled
        target_dd.disabled = not enabled
        start_btn.disabled = not enabled
        target_preview.disabled = not enabled

    def show_loading_overlay(show: bool) -> None:
        load_overlay.visible = show
        page.update()

    def set_status(message: str, kind: str = "normal") -> None:
        colors = {
            "normal": UI["muted"],
            "warn": UI["warn"],
            "ok": UI["output_accent"],
            "error": UI["error"],
            "progress": UI["accent"],
        }
        icons = {
            "normal": ft.Icons.INFO_OUTLINE,
            "warn": ft.Icons.PAUSE_CIRCLE_OUTLINE,
            "ok": ft.Icons.CHECK_CIRCLE_OUTLINE,
            "error": ft.Icons.ERROR_OUTLINE,
            "progress": ft.Icons.HOURGLASS_TOP,
        }
        status_text.value = message
        status_text.color = colors.get(kind, UI["muted"])
        status_icon.name = icons.get(kind, ft.Icons.INFO_OUTLINE)
        status_icon.color = colors.get(kind, UI["muted"])
        page.update()

    def update_status(message: str) -> None:
        set_status(message, "normal")

    def on_model_load_failed(exc: BaseException) -> None:
        model_loading["value"] = False
        model_ready["value"] = False
        translator_holder["instance"] = None
        reload_needed["value"] = True
        show_loading_overlay(False)
        set_work_ui_enabled(True)
        start_btn.disabled = False
        stop_btn.disabled = False
        if "cancelled" in str(exc).lower():
            set_status(L("stop_load_done"), "warn")
        else:
            set_status(L("error", msg=str(exc)), "error")

    def start_model_load(on_success=None) -> None:
        """Show load overlay and load NLLB; optionally run *on_success* on UI thread."""
        if worker["thread"] is not None and worker["thread"].is_alive():
            return
        model_loading["value"] = True
        model_ready["value"] = False
        old_engine = translator_holder["instance"]
        if old_engine is not None:
            old_engine.unload()
        translator_holder["instance"] = None
        show_loading_overlay(True)
        update_status(L("loading_model"))
        set_work_ui_enabled(False)
        stop_btn.disabled = False
        stop_event.clear()

        def _load_worker() -> None:
            try:
                engine = NllbTranslator(model_dir)
                engine.load(cancel_event=stop_event)
                if stop_event.is_set():
                    raise RuntimeError("Load cancelled")
                translator_holder["instance"] = engine

                def _on_ready() -> None:
                    model_ready["value"] = True
                    model_loading["value"] = False
                    show_loading_overlay(False)
                    if on_success is not None and not stop_event.is_set():
                        on_success()
                    else:
                        set_work_ui_enabled(True)
                        progress_bar.value = 0
                        set_status(L("ready"), "ok")

                schedule_ui(_on_ready)
            except Exception as exc:
                schedule_ui(on_model_load_failed, exc)

        worker["thread"] = threading.Thread(target=_load_worker, daemon=True)
        worker["thread"].start()

    def on_progress(done: int, total: int) -> None:
        progress_state["done"] = done
        progress_state["total"] = total
        progress_bar.value = done / max(total, 1)
        set_status(L("progress", done=str(done), total=str(total)), "progress")

    def translate_worker() -> None:
        src = source_dd.value or default_source_code()
        tgt = target_dd.value or default_target_code()
        if src.startswith("__header__") or tgt.startswith("__header__"):
            schedule_ui(set_status, L("pick_lang"), "warn")
            return
        config["source_lang"] = src
        config["target_lang"] = tgt
        save_config(config)

        try:
            src_lang = language_by_code(src)
            tgt_lang = language_by_code(tgt)
            engine = translator_holder["instance"]
            if engine is None:
                schedule_ui(set_status, L("wait_model"), "warn")
                return

            clip_text = source_preview.value or ""
            if not clip_text.strip():
                schedule_ui(set_status, L("no_input"), "warn")
                return

            def progress_cb(done: int, total: int) -> None:
                schedule_ui(on_progress, done, total)

            chunks = chunk_text(clip_text)
            translated_chunks = engine.translate_chunks(
                chunks,
                src_lang.suffix,
                tgt_lang.suffix,
                on_progress=progress_cb,
                cancel_event=stop_event,
            )
            result = join_chunks(translated_chunks, clip_text)

            def apply_result(translated: str) -> None:
                target_preview.value = translated
                page.update()

            schedule_ui(apply_result, result)
            if stop_event.is_set():
                done = progress_state["done"]
                total = progress_state["total"]
                schedule_ui(
                    set_status,
                    L("stop_translate_done", done=str(done), total=str(total)),
                    "warn",
                )
            else:
                schedule_ui(set_status, L("done"), "ok")

        except RuntimeError as exc:
            if "cancelled" in str(exc).lower():
                done = progress_state["done"]
                total = progress_state["total"]
                schedule_ui(
                    set_status,
                    L("stop_translate_done", done=str(done), total=str(total)),
                    "warn",
                )
            else:
                schedule_ui(set_status, L("error", msg=str(exc)), "error")
        except (OSError, FileNotFoundError) as exc:
            schedule_ui(set_status, L("error", msg=str(exc)), "error")
        finally:
            if stop_event.is_set():
                reload_needed["value"] = True
                old_engine = translator_holder["instance"]
                if old_engine is not None:
                    old_engine.unload()
                translator_holder["instance"] = None
                model_ready["value"] = False
            stop_pending["value"] = False
            stop_event.clear()

            def finish_translate() -> None:
                set_work_ui_enabled(True)
                stop_btn.disabled = False
                progress_bar.value = 0
                page.update()

            schedule_ui(finish_translate)

    def begin_translate() -> None:
        """Run translation on a background thread (model must already be loaded)."""
        progress_state["done"] = 0
        progress_state["total"] = 0
        progress_bar.value = 0
        set_work_ui_enabled(False)
        stop_btn.disabled = False
        worker["thread"] = threading.Thread(target=translate_worker, daemon=True)
        worker["thread"].start()

    def start_translate(_event: ft.ControlEvent) -> None:
        if worker["thread"] is not None and worker["thread"].is_alive():
            return
        if source_dd.value == target_dd.value:
            set_status(L("same_lang"), "warn")
            return
        if not (source_preview.value or "").strip():
            set_status(L("no_input"), "warn")
            return

        if reload_needed["value"] or not model_ready["value"]:
            reload_needed["value"] = False

            def after_reload() -> None:
                begin_translate()

            start_model_load(on_success=after_reload)
            return

        stop_event.clear()
        begin_translate()

    def request_stop(_event: ft.ControlEvent) -> None:
        running = model_loading["value"] or (
            worker["thread"] is not None and worker["thread"].is_alive()
        )
        if not running:
            set_status(L("stop_idle"), "warn")
            return

        stop_pending["value"] = True
        stop_event.set()
        reload_needed["value"] = True
        old_engine = translator_holder["instance"]
        if old_engine is not None:
            old_engine.unload()
        translator_holder["instance"] = None
        model_ready["value"] = False
        if model_loading["value"]:
            set_status(L("stop_ack"), "warn")
        else:
            set_status(L("stop_ack"), "warn")

    help_dialog_ref: dict[str, ft.AlertDialog | None] = {"dlg": None}

    def open_help(_event: ft.ControlEvent) -> None:
        def close_help(_event: ft.ControlEvent) -> None:
            if help_dialog_ref["dlg"] is not None:
                help_dialog_ref["dlg"].open = False
                page.update()

        if help_dialog_ref["dlg"] is None:
            help_dialog_ref["dlg"] = ft.AlertDialog(
                modal=True,
                title=ft.Text(L("help_title")),
                content=ft.Container(
                    content=ft.Text(L("help_body"), selectable=True, size=14, color=UI["text"]),
                    width=520,
                    height=420,
                    padding=8,
                ),
                actions=[ft.TextButton(L("help_close"), on_click=close_help)],
                actions_alignment=ft.MainAxisAlignment.END,
            )
            page.overlay.append(help_dialog_ref["dlg"])
        help_dialog_ref["dlg"].open = True
        page.update()

    help_btn = ft.IconButton(
        icon=ft.Icons.MENU_BOOK,
        tooltip=L("help_tooltip"),
        icon_color=UI["accent"],
        on_click=open_help,
    )

    header_row = ft.Row(
        [
            ft.Text(L("title"), size=22, weight=ft.FontWeight.BOLD, color=UI["accent"]),
            ft.Container(expand=True),
            help_btn,
        ],
        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
    )

    status_row = ft.Row(
        [status_icon, status_text],
        spacing=8,
        vertical_alignment=ft.CrossAxisAlignment.CENTER,
    )

    start_btn.on_click = start_translate
    stop_btn.on_click = request_stop

    work_area = ft.Column(
        [
            header_row,
            lang_panel,
            ft.Row([source_panel, target_panel], expand=True, spacing=12),
            ft.Row([progress_bar, status_row], alignment=ft.MainAxisAlignment.START, spacing=12),
            ft.Row([start_btn, stop_btn]),
        ],
        expand=True,
        spacing=12,
    )

    page.add(
        ft.Stack(
            [
                work_area,
                load_overlay,
            ],
            expand=True,
        )
    )

    start_model_load()


if __name__ == "__main__":
    ft.app(target=main)
