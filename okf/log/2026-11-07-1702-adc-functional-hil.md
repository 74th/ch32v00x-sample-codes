# CH32V003 ADC 機能 HIL（未校正）

- 作業日時: 2026-11-07 16:58–17:02 JST。記録は作業後。
- 目的: ユーザー指定に従い、電圧や ADC の精度ではなく、PWM 設定を変えたとき ADC の読みが変化する機能を確認する。
- 対象・配線: CH32V003 PA2 ADC A0–10 kΩ–Pico GP13、PA2–1 µF–GND、CH32 PD5 UART TX→Pico GP9 RX。固定配線をユーザーが準備し、GPIO 接続を `2026-11-07-1506-gpio-wiring-observation.md` で確認。抵抗・容量と電圧は今回独立測定していない。独立電圧計での校正はユーザーが不要と判断。
- ツール: WCH-LinkE 2.22、固定 ch32fun `b28d285460ce052a179dba8f4a22c6f73ff8e328`、Pico SDK 2.2.0 `a1438dff1d38bd9c65dbd693f0e5db4b9ae91779`、TinyUSB `86ad6e56c1700e85f1c5678607a762cfe3aa2f47`、picotool 2.1.1、pytest 8.4.2。
- ソース: 実験時は未コミット。最終実験後 SHA-256: Pico `main.c` `b9e3e5964b6f61f38612650072d2d9e782ffcd36424b3e3789d9bdcca7cf28b3`、`protocol.c` `4eb396110df11a6cb4d9e9c633d48baff3253fceb207bc15bbbfd9310c11281a`、`adc_fixture.c` `7768e6fffd8d95aade42faca13e266a56a52964bc513f28dc66f65d6ed1e6832`、`tests/hil/test_adc.py` `15bdd2b9419c7d783ce71c099618d973391e10eb2ba28147c20a6c939eec6669`。
- コマンド: `./scripts/ch32fun.sh flash ch32v003` で CH32V003 検出確認、`uv run pytest --hil -m 'hil and adc' tests/hil/test_adc.py -q -s --hil-port /dev/serial/by-id/usb-Raspberry_Pi_Pico_E661AC8863223539-if00`。Pico は picotool による書き込み・verify 成功後、`measure.discover(30)` で再認識。DUT build、flash、成果物サイズ readback 一致、reset は pytest の各段階で確認。
- 実測: 10 kHz PWM、安定待ち500 ms。duty 10/20/50/80/90% に対する DUT の10-bit ADC 出力は 82/183/489/798/900 で単調増加。成功後 GP13 は output=0、pull_up=0、pull_down=0。範囲外 duty 9/91%、settle 99 ms、timeout 299 ms は INVALID。電圧・絶対誤差・ADC 精度は測っていない。
- PWM 生成の別確認: I2C 自己試験用の Pico GP16–GP18 loopback を用い `GPIO_SELFTEST_PWM 16 18 <duty> 10000` を実行。10/50/90% で period 101/100/100 µs、high 10/49/90 µs。同一 Pico 時計での測定で独立校正ではなく、GP13 と RC 出力の電圧確認でもない。
- 失敗: 先行書込みの picotool は verify 出力がなく応答も得られず保留した（`2026-11-07-1649-pico-reflash-unconfirmed.md`）。ユーザーが BOOTSEL で再接続後、明示的に `picotool load -v -x` の書込み・verify OK を確認して復旧。
- 未確認: 電源電圧、RC の実電圧、settle の絶対精度、ADC の精度とリニアリティ、異なる構成での安全範囲、物理 USB 抜去時の波形。DUT は ADC sample、Pico は v2 firmware のまま。
