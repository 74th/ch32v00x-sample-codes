# Pico protocol v2 入力観測の初版

- 作業日時: 2026-11-07 15:10–15:12 JST。記録は作業後。
- 目的: request ID、能力照会、入力安全状態、エラーとタイムアウトの区別、および固定配線 PC0–GP5 の入力観測を確認する。
- 対象・配線: CH32V003F4P6 は WCH-LinkE、Pico は USB 接続。PC0–GP5 等の配線は `2026-11-07-1506-gpio-wiring-observation.md` の GPIO 観測に従う。電圧や抵抗は今回測定していない。DUT は `blink_and_read` を実行。Pico 実装は `hardware/pico-tester/main.c`, `fixture.c` と同時点の CMake 設定。
- ツール: Pico SDK 2.2.0 `a1438dff1d38bd9c65dbd693f0e5db4b9ae91779`、TinyUSB `86ad6e56c1700e85f1c5678607a762cfe3aa2f47`、arm-none-eabi-gcc 14.2.1、picotool 2.1.1、pyserial（`uv run`）。
- コマンド: `PICO_SDK_PATH=/home/nnyn/.pico-sdk/sdk/2.2.0 cmake -S hardware/pico-tester -B hardware/pico-tester/build -G Ninja -DPICO_BOARD=pico`、`cmake --build hardware/pico-tester/build`、`picotool load -f -v -x hardware/pico-tester/build/pico_gpio_tester.uf2`。数値パース修正後に再ビルド・再書込み。双方 picotool verify OK。各書き込み後 `hardware/pico-tester/measure.py` の `discover(30)` で再認識を待ち pyserial でコマンドを実行。`uv run pytest -q tests/unit/test_pico_client.py`。
- 実測: 最初のビルドで `1 CAPS` と `2 RESET_SAFE` が OK、`3 XYZ` が `ERR UNSUPPORTED`、非許可 GP25 と count 0 が `ERR INVALID`。`GPIO_SAMPLE 5 200 10000` は 200点中 High 101、Low 99、遷移4回。未完フレームを1秒以上放置し `0 ERR TIMEOUT incomplete_frame`、続く CAPS が成功。修正後の最終ビルドでは巨大な ID が `0 ERR INVALID request_id`、CAPS、GP5 200点で High/Low 両方、RESET_SAFE が成功。ホストの既存 Pico client 模擬試験は 9 passed。
- 失敗: 初回実装の数値変換は範囲超過を明示確認していなかったため修正し再ビルド・書き込みした。試験コマンドのエラー応答は意図した負のケース。
- 未確認: GPIO 出力・pin ownership・競合拒否、他周辺機能、独立 loopback、実機 USB 切断中のピン状態、意図的な異常時の電気的 safe state、全範囲の観測精度。入力のみのため能力全体を自己検証済みとしない。DUT は書き換えていない。Pico は v2 初版のまま、v1 `measure.py` とは互換でない。
