# TXT-TRANS

オフライン・CPU のみでテキストを翻訳する Windows 向けデスクトップツールです。  
PDF-SCAN の OCR 出力（`.txt`）を想定していますが、GUI では貼り付け、CLI ではファイル指定に対応します。

## 対応言語

日本語 / 英語 / 中国語（簡体・繁体） / 韓国語 / ロシア語ほか **NLLB-200 計 202 言語**（GUI ではよく使う 6 言語を先頭表示、国旗付き）

## 動作環境

| 項目 | 内容 |
|------|------|
| OS | Windows 10 / 11（64bit） |
| Python | 3.12（開発時） |
| RAM | 翻訳時おおよそ 1〜1.5 GB |
| GPU | 不要 |

## クイックスタート（開発）

```powershell
git clone https://github.com/matrix9neonebuchadnezzar2199-sketch/TXT-TRANS.git
cd TXT-TRANS
git lfs install
git lfs pull

# 初回: venv + モデル変換（Hugging Face から約 2.4GB 取得、ローカルに int8 化）
.\scripts\setup_model.ps1

# GUI
.\run-gui.ps1
```

起動時に NLLB モデルを自動ロードします（オーバーレイ表示）。完了後:

1. **INPUT**（青枠）に原文を貼り付け（Ctrl+V）
2. 原文・訳文の言語を選択（初期値: 英語 → 日本語。🔍 フィルタで 202 言語から検索可）
3. **翻訳開始** をクリック

| 機能 | 説明 |
|------|------|
| **停止** | モデル読込・翻訳を中断。受付直後・完了時にステータスで結果を表示 |
| **ヘルプ**（右上の本アイコン） | 使用モデル（NLLB-200-distilled-600M + CTranslate2）の解説と使い方 |
| **再翻訳** | 停止後は次回の翻訳開始時にモデルを再ロードしてから実行 |

モデルは `models/nllb-200-distilled-600M-ct2/` に配置され、Git LFS で管理します。

## CLI

```powershell
.\.venv\Scripts\python.exe src\translate.py --input sample.txt --from en --to ja
.\.venv\Scripts\python.exe src\translate.py --input sample.txt --from eng_Latn --to fra_Latn
.\.venv\Scripts\python.exe src\translate.py --input-dir .\docs --from ja --to en --force
```

出力は入力ファイルの横に `report.en.txt` の形式で保存されます。

## ビルド（配布用）

```powershell
.\build.ps1
```

生成物: `dist\TXT-TRANS\`（one-folder、モデル同梱、約 700 MB）

## リポジトリ構成

```
TXT-TRANS/
├── gui/main.py       # Flet GUI
├── src/              # 翻訳エンジン + CLI
├── models/           # NLLB CTranslate2 重み（LFS）
├── scripts/          # setup_model.ps1, prepare_flet_client.py
└── docs/             # アーキテクチャ
```

## ライセンス

MIT License — 詳細は [LICENCE](./LICENCE)。  
NLLB モデルは Meta のライセンスに従います（[facebook/nllb-200-distilled-600M](https://huggingface.co/facebook/nllb-200-distilled-600M)）。
