# TXT-TRANS

オフライン・CPU のみでテキストファイルを翻訳する Windows 向けデスクトップツールです。  
PDF-SCAN の OCR 出力（`.txt`）を想定していますが、任意の UTF-8 テキストに使えます。

## 対応言語

日本語 / 英語 / 中国語（簡体・繁体） / 韓国語 / ロシア語（NLLB-200-distilled-600M）

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

モデルは `models/nllb-200-distilled-600M-ct2/` に配置され、Git LFS で管理します。

## CLI

```powershell
.\.venv\Scripts\python.exe src\translate.py --input sample.txt --from ja --to en
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
