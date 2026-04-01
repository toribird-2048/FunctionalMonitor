# FunctionalMonitor

## 概要

FunctionalMonitorは、Notionを利用して「課題」や「持ち物」など情報を自動取得し、Pygameを使った全画面インフォメーションボードとして表示するアプリケーションです。学校や自宅のディスプレイ・サイネージ端末向け情報表示モニターに最適です。

## 主な機能

- **Notion API連携**  
  指定したNotionデータベースから、「明日までの持ち物」や「課題」を自動取得します。
- **多彩な情報表示UI**  
  時計・課題・TODO・翌日の持ち物リストなど、複数のUI表示に切替対応。キーボードで表示を切り替え可能。
- **日本語対応・カスタムフォント**  
  日本語フォント（NotoSansJP）が同梱され、日本語���報もきれいに表示。
- **フルスクリーン表示**  
  デジタルサイネージ用途に十分な1920x1280での全画面描画。

## 必要な環境

- Python 3.10以降推奨
- 必須ライブラリ: `pygame`, `notion_client`, `python-dotenv`
- Notion API用インテグレーショントークン、及びデータベースID（いずれも環境変数設定が必要）

## インストール

```bash
git clone https://github.com/toribird-2048/FunctionalMonitor.git
cd FunctionalMonitor
uv sync
```

### .env ファイル例

```
NOTION_API_KEY=xxxxxxxxxxxxxxxxxxxxxxxx
NOTION_DATA_SOURCE_ID=xxxxxxxxxxxxxxxxxxxxxxxx
```

## 使い方

```bash
uv run main.py
```
起動すると全画面で時計や課題・持ち物リストなどが表示されます。  
（キー操作で画面表示の切り替えが可能です）

- Ctrl+Eで終了

## カスタマイズ・注意

- Notionデータベースの構造は、「期日」「課題」「種別」「完了」「終了」など所定のプロパティ名を使う前提です。  
- プロパティ名等を変更する場合は `get_items_data.py` などを修正してください。
