# 既定テストの実機アクセス確認

- 作業・記録日時: 2026-11-07 16:44 JST（開始時刻は未記録）。
- 目的: 既定 pytest が HIL を選択せず実機へアクセスしないことと、旧 GPIO v1 の終了コード分類を確認する。
- 条件: Pico と WCH-LinkE は USB に接続中。実機を物理的に外した試験は実施していない。pytest 8.4.2、pyserial 3.5 は `uv` のロック済み環境。書き込みコマンドは指定していない。
- コマンド: `strace -f -e trace=openat,open,ioctl -o /tmp/hil-default-strace.log uv run pytest -q`、`rg -n '/dev/(bus/usb|ttyACM|ttyUSB|hidraw)' /tmp/hil-default-strace.log`、`uv run pytest -q tests/unit/test_measure.py`。
- 結果: trace 付き既定実行は 47 passed / HIL 1 skipped。指定デバイスパスへの open は trace に見つからなかった。旧6ケースを維持し、モックを使った PASS=0、MISMATCH=1、不正応答=3 のテストを追加して同ファイル7件成功。timeout=2 は既存テストで確認。これらは実機動作を主張しない。
- 失敗: なし。未確認: 実機を物理的に外したホストでの再実行。trace の検索は列挙した USB・シリアル・hidraw パスを対象とする。
