### [Notes]
- このプロジェクトは個人用です。
- このプログラムが実行されているのはラズパイ3です。
- このプログラムはユーザーのデスクにおいてある、1920x1280解像度のディスプレイに表示されています。

### [Technical_Decisions]
- **Alert Check Frequency:** `UiController.check_alerts` における毎ループの `json.load` は、Raspberry Pi 3 のリソース上、実用上のパフォーマンス低下が認められないため、実装のシンプルさとリアルタイム性を優先し、キャッシュロジック（timedelta）を導入しない。