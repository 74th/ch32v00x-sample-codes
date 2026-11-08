# i2c_oled（Arduino Core CH32、CH32V006F8P6）

CH32V002 版と同じソース。OLED ライブラリ `OLED SSD1306 - SH1106` 1.0.7 を `sketch.yaml` で固定。006 は RAM 8 KiB のため、CH32V003 で起きる `malloc(512)` 失敗はない。
- 観測: 006 実機で Pico の SSD1306 模擬の内容がホスト描画と一致（[ログ](../../okf/log/2026-11-08-1636-ch32v006-arduino-batch2.md)）。**実 OLED の表示は未確認**。
