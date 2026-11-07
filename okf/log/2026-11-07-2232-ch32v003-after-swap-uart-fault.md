# CH32V003 へ差し替え後の HIL で UART が受信できない（調査中）

- 作業日時: 2026-11-07 22:32〜22:39 JST（コマンドの開始時刻は `date` の実測。記録 22:39 頃）
- 経緯: Pico の SSD1306 模擬を修正した後（[2026-11-07-2225](2026-11-07-2225-pico-ssd1306-model-arduino-oled.md)）、ユーザーが DUT を CH32V002 から CH32V003 に差し替えた（ユーザー申告。差し替え時の電圧値は報告なし）。
- 対象: CH32V003F4P6、Pico E661AC8863223539（修正後のファームウェア）、固定配線。

## 実行（実測）

| 開始 | 実行 | 結果 |
| --- | --- | --- |
| 22:32:38 | `./scripts/ch32fun.sh flash ch32v003` | `Detected CH32V003`、`Image written.`、`FLASH OK (runtime unverified)` |
| 22:32:51 | Arduino の全 HIL（`--hil-framework arduino`） | 5 failed, 4 passed, 1 xfailed |
| 22:34:32 | ch32fun の全 HIL | 2 failed, 231 passed（単体を含む）, 10 skipped, 1 xfailed |
| 22:36:15 | ch32fun の HIL のみ（Arduino を除外） | 2 failed（`test_uart.py::test_uart_echo`、`test_adc.py::test_adc_functional`）, 12 passed, 1 xfailed |

失敗の内容:
- ch32fun uart: `UART_XFER` が TIMEOUT、`received=2`、`uart_errors=0x5`、`rx=0000`。ch32fun adc: `ADC_OBSERVE` が `TIMEOUT adc_report`（DUT の UART 出力を受けられない）。
- Arduino blink_and_read / adc: Serial を 1 バイトも受信できない（errors 0x0）。
- Arduino i2c_slave（`read_0x12` で TIMEOUT）、i2c_oled（8 ページとも期待と不一致）、neopixel（`bad_pulses=9`、`t1h_ns=0`）も失敗。i2c_master、i2c_slave_test_master、pwm、spi_master は pass。
- 21:22 の CH32V003 と、22:29 の CH32V002（同じ修正後の Pico ファームウェア）では、UART を使うテストはすべて pass していた。

## 診断（22:38 頃、実測）

Arduino blink_and_read を書き込んでリセットし、1 秒後に観測した:
- GP5（PC0）: `1:50, 0:50` → DUT は動作して点滅している。
- GP9（DUT PD5 = USART1 TX）: 10 ms 間隔 100 点がすべて Low。UART の待機レベルは High で、スケッチは約 1 s ごとに出力するので、本来は大半が High のはず。
- 続けて `UART_XFER` で 3 s 受信 → 0 バイト。GP9 は入力・pull なし（`GPIO_STATE`）。

## 判断（推定）

- PD5（TSSOP20 の 2 番ピン）と Pico GP9 の間が導通していない可能性が高い（差し替え時の DUT の差し込みや配線の接触）。GP9 は pull なしの入力なので、線が浮いていると Low に読める。ファームウェアやコードの変更が原因なら CH32V002 でも失敗するはずで、CH32V002 では直前に通っている。
- i2c_slave、i2c_oled、neopixel の失敗が同じ原因（接触）か、CH32V003 固有の結果かは、接続を直してから再実行して切り分ける。

## 未確認

- 配線と差し込みの状態（ユーザーに確認を依頼）。電圧。
