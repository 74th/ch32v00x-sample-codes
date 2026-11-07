# 実機の見えない環境での既定テスト

- 作業・記録日時: 2026-11-07 16:57 JST（開始時刻は未記録）。
- 目的: HIL を明示しない pytest が、USB 機器の見えない環境で実行できることを確認する。
- 条件: Pico と WCH-LinkE はホストに接続されていたが、bubblewrap の `--dev /dev` で子プロセスには新しい最小 `/dev` を提供し、`--unshare-net` と読み取り専用ルートを使用。uv の既存同期済み Python 環境、pytest 8.4.2、pyserial 3.5。物理的な取り外しではない。
- コマンド: `bwrap --ro-bind / / --dev /dev --proc /proc --tmpfs /tmp --unshare-net /usr/bin/env UV_NO_SYNC=1 UV_CACHE_DIR=/tmp/uv-cache PYTHONDONTWRITEBYTECODE=1 uv run --no-sync pytest -q -p no:cacheprovider`。
- 実測: 57 passed、3 skipped（いずれも `--hil` 未指定）。一方、通常の `uv run pytest` に対する USB/serial デバイスアクセスの strace 確認は `2026-11-07-1644-default-test-isolation.md` に記録。
- 失敗: 初回は読み取り専用の既定 uv キャッシュに一時ファイルを作れず失敗。`UV_CACHE_DIR=/tmp/uv-cache` に変更して成功。
- 未確認: 依存環境を新規にダウンロード・同期する操作は実行していない。実機への通信・書き込みや HIL の結果を意味しない。
