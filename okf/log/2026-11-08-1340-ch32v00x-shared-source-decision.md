# CH32V002 の同一ソース再実行と CH32V002/CH32V006 共通化の判定

- 作業日時: 2026-11-08 13:37〜13:39 JST（`date` で 13:37:29 と 13:38:45 を確認）。記録は 13:40 JST。
- 対象 change: `verify-ch32v006-shared-ch32fun` のタスク 5.1。
- 対象: 開発ボードを CH32V002F4P6 に差し替え済み（ユーザー申告）。同じブレッドボード・固定配線の Pico 治具。識別領域の読取（実測）は `1ffff704: 20 06 20 00`（上位型番 `0x002`）、Flash 16 kB。電圧は今回は未測定。
- ソース: HEAD `b06efd8` ＋ 未コミットの本 change 変更。CH32V006 の実行（[ログ](2026-11-08-1335-ch32v006-hil.md)）と今回の間に、アプリケーションソース（各 `main.c`・`funconfig.h`・Makefile）は変更していない（文書とマトリクス JSON のみ変更）。

## 実行コマンドと結果（実測）
```sh
uv run pytest --hil --hil-device ch32v002 --hil-framework ch32fun -m 'hil and gpio' tests/hil --hil-port=<Pico> --hil-run-dir=<dir>
uv run pytest --hil --hil-device ch32v002 --hil-framework ch32fun -m 'hil and not gpio' tests/hil --hil-port=<Pico>
```
- GPIO: 3 passed。run.json: device=ch32v002、build_target=CH32V002、blink_and_read の sha256=`92edb7948e42…c9342`、chip_id=`0x00200620`、全段階 pass。
- その他: 11 passed、1 xfailed（SSD1306 `helper_1mhz`、既存の xfail マーカー。CH32V006 でも同じ結果）。passed の内訳は ADC、i2c_slave_helper、ssd1306 100 kHz、ws2812、I2C 2 方向、PWM、SPI、UART、watchdog、sleep_wake。

## 共通化の判定（5.1）: 成立
- ソース無分岐: 12 サンプルはいずれも CH32V002/CH32V006 で同一の `main.c`・`funconfig.h` を使い、デバイス別の分岐を追加していない（`TARGET_MCU` はビルド設定、起動表示は共通表記に直した）。
- 両ターゲット build: 全 12 サンプル×2 が成功（[ログ](2026-11-08-1315-ch32v006-host-foundation.md)）。
- 両実機の必須 HIL: CH32V006 が 3+8+3（helper 必須）、CH32V002 が 3+11（helper 必須 3 を含む）で合格。判定の基準にした必須試験はいずれも失敗なし。
- 判定の範囲: 機能確認のみ。ADC の精度・時間校正・消費電流、実 OLED/LED、規格適合は未確認。`gpio_input` は両機とも HIL 対象外。SSD1306 1 MHz は両機とも参考（XFAIL）。CH32V006F8P6 は F8P7 と同一ダイという申告に基づく仮定。
- 差分の阻害要因: なし。ADC_CLK_MODE と sleep の差分（判定 B の 2 件）も結果として問題は観測されなかった（原因解析はしていない）。
- よって `samples_ch32v002_ch32fun/` → `samples_ch32v00x_ch32fun/` への移行条件は成立（タスク 5.2 へ）。CH32V005/007 や他パッケージは未検証のまま。
