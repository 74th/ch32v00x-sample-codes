# Pico GPIO 出力・周期測定試作

- 記録日時: 2026-11-07 16:28 JST。作業開始時刻は記録していない。実行は記録日時より前。
- 目的: v2 プロトコルへ期限付き GPIO 出力、loopback 観測、周期・duty 測定を追加し、DUT 接続ピンを駆動せずに要求の拒否と受動測定を確認する。
- 条件: CH32V003 の PC0→Pico GP5、PC1→GP10 等は `2026-11-07-1506-gpio-wiring-observation.md` の配線。DUT は既存 blink。GP16/GP17 の loopback は未確認・未使用。Pico SDK 2.2.0 `a1438dff1d38bd9c65dbd693f0e5db4b9ae91779`、TinyUSB `86ad6e56c1700e85f1c5678607a762cfe3aa2f47`、arm-none-eabi-gcc 14.2.1、picotool 2.1.1。電源と信号電圧は今回測定していない。
- コマンド: `cmake --build hardware/pico-tester/build`、`picotool load -f -v -x hardware/pico-tester/build/pico_gpio_tester.uf2`（能力表示修正前後の2回、どちらも verify OK）。書換後 `hardware/pico-tester/measure.py` の `discover(30)` で再認識を待ち、pyserial で CAPS、GPIO_DRIVE、GPIO_LOOPBACK、GPIO_PULSE、RESET_SAFE を送信。`uv run pytest -q tests/unit/test_pico_client.py` は9件成功。
- 実測: 最終 firmware の CAPS に `drive_pins=16,17`、GPIO_PULSE ほかを確認。`GPIO_DRIVE 5 1 20` は `ERR UNSUPPORTED drive_pin`、`GPIO_LOOPBACK 16 16 1 20` は `ERR CONFLICT same_pin`、`GPIO_PULSE 10 100` は `ERR TIMEOUT pulse_edges`。`GPIO_PULSE 5 3000` は period 1002243 µs、high 501050 µs、duty 499928 ppm。RESET_SAFE は OK。前ビルドでは期間 2001 ms を INVALID と拒否した。Pico や DUT の GPIO は今回の試験では出力させていない。
- 失敗: 予期しないエラーなし。上記の ERR は意図的な負の要求。
- 未確認: 独立 loopback、GPIO 出力の電気的波形、境界時間、USB 切断中の出力停止、実際の safe state、測定精度・速度範囲、DUT への刺激。GP16/17 接続確認後に自己検証を行う。Pico は v2 GPIO 試作のまま。
