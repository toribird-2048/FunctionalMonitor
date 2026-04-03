### [Notes]
- このプロジェクトは個人用です。
- このプログラムが実行されているのはラズパイ3です。
- このプログラムはユーザーのデスクにおいてある、1920x1280解像度のディスプレイに表示されています。
- essentials.jsonは基本的に一年に一回しか編集されません。
- essentials.json付近の構造は複雑化させる予定は全くありません。
- subprocess をリスト形式で使用している箇所（shell=False）において、shlex.quote の使用を推奨しないでください。それは引数の二重クォートを引き起こし、バグの原因となります。

### [Technical_Decisions]
- **Alert Check Frequency:** `UiController.check_alerts` における毎ループの `json.load` は、Raspberry Pi 3 のリソース上、実用上のパフォーマンス低下が認められないため、実装のシンプルさとリアルタイム性を優先し、キャッシュロジック（timedelta）を導入しない。
- **Exception Handling Strategy:** 実装の複雑化を避けるため、現在は各メソッド内での個別 `try-except` による最低限の保護に留めている。全体的なエラーハンドリング刷新は「大きな変更」と定義し、段階的に実施する。
- **essential items:** essential items、つまり時間割に応じた持ち物表は、変更時学年が上がることもあり全く原型を留めないため、編集時に前のessential.jsonを残しておく必要はない。

### [Pending_Tasks]
- **Robustness:** 異常終了時のユーザーフィードバック実装（Issue化済み）。
    - 現状、メインループ内での例外発生時にフリーズかクラッシュかの判別が困難。
    - 対策案：`try-except` でメインループを囲い、致命的エラー発生時に `BaseUi` の仕組みを利用して画面上にエラーメッセージ（トレースバック等）を巨大フォントで描画して停止する仕組みを検討中。

### [File_Relationships]
- `daily_essentials.json`: **[GENERATED]** `edit_daily_essentials.py` によって管理。
    - 手動編集は行わないため、重複記述によるヒューマンエラーの指摘は不要。
- `alerts.json`: **[EXTERNAL]** 外部API（Shortcuts/MacroDroid）から更新。
    - 構造の整合性は送信側で担保。
