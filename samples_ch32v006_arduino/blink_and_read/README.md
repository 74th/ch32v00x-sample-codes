# blink_and_read（Arduino Core CH32、CH32V006F8P6）

- 出典: `samples_ch32v002_arduino/blink_and_read/blink_and_read.ino`（元は `externals/ch32v003-book-code/blink_and_read-arduino_core_ch32`、book-code 4ce0a1b, CC0 1.0）と同じソース。
- ボード定義: 公式配布 `WCH:ch32v` 1.0.6 の `CH32VM00X_EVT`（`pnum=CH32V006K8`、48 MHz HSI）をそのまま使う。Flash 62 KiB / RAM 8 KiB。CH32V002 用の `upload.maximum_*`・`_eusrstack`・`_heap_end` の上書きは行わない（`../arduino.mk`）。
- 依存条件: arduino-cli 1.5.1、`WCH:ch32v` 1.0.6、`riscv-wch-gcc` 15.2.0（`scripts/arduino.sh` が固定導入）。
- ビルド: `make -C samples_ch32v006_arduino/blink_and_read build`。成果物は `main.bin` / `main.elf`、キャッシュは `.arduino/build/samples_ch32v006_arduino/` で 002/003 と分離。
- 書き込み・実機観測は別段階。書き込みは固定 minichlink で、識別領域 `0x1ffff704` の上位型番が `0x006` であることを確認してから行う（`ch32hil`）。
- F8P6 は資料上の F8P7 と同一ダイとして扱う前 change のユーザー判断を引き継いでいる（独立には未検証）。
