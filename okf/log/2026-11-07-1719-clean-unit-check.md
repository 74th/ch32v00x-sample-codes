# クリーン環境での単体テストと設定照合

- 作業・記録日時: 2026-11-07 17:19 JST（開始時刻未記録）。
- 目的: 新規の依存環境から通常の単体テスト、配線設定照合、OpenSpec 検証を実行する。
- 条件: `UV_PROJECT_ENVIRONMENT=/tmp/ch32-hil-clean-venv` で新規仮想環境を作成、既存の uv キャッシュを `--offline --locked` で利用。実機 HIL は指定せず、USB・プログラマー書き込みを行っていない。ホストの物理的な実機接続状態は本操作では確認していない。
- コマンド: `UV_PROJECT_ENVIRONMENT=/tmp/ch32-hil-clean-venv uv sync --locked --offline`、`UV_PROJECT_ENVIRONMENT=/tmp/ch32-hil-clean-venv uv run --locked --offline pytest -q`、`UV_PROJECT_ENVIRONMENT=/tmp/ch32-hil-clean-venv uv run --locked --offline python -m ch32hil.wiring`、`openspec validate automate-ch32v003-ch32fun-hil --strict`。
- 結果: 依存同期成功。単体テスト 73 passed、実機 HIL 9 skipped。配線のピンと文書化された部品値の機械照合成功（電源、方向、実配線等は人間レビューが必要）。OpenSpec strict 検証成功。
- 失敗: なし。uv がハードリンクできずコピーへフォールバックした警告あり。未確認: ネットワークからの新規依存取得。実機動作の成否はこの結果に含まない。
