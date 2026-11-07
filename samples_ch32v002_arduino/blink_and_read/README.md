# blink_and_read（Arduino Core CH32、CH32V002F4P6）

- 出典: `externals/ch32v003-book-code/blink_and_read-arduino_core_ch32`（book-code 4ce0a1b, CC0 1.0）。`samples_ch32v003_arduino/blink_and_read/blink_and_read.ino` と同じソース。
- ボード定義: 公式配布 `WCH:ch32v` 1.0.6 には CH32V002 の定義がないため、同系列の `CH32VM00X_EVT`（`pnum=CH32V006K8`）を流用する。
- 流用時の上書き（`../arduino.mk`）: Flash 16 KB / RAM 4 KB のサイズ検査、`_eusrstack=0x20001000`（SP の初期値）、`_heap_end=0x20000e00`（`_sbrk` の上限）。CH32V006K8 の `Link.ld` は MEMORY を 62K/8K に固定しており、上書きしないと SP が 0x20002000（V002 の RAM の外）になる。根拠と判定は [調査ログ](../../okf/log/2026-11-07-2125-arduino-ch32v002-survey.md)。
- 配線・期待値は CH32V003 版と同じ（固定配線は CH32V002F4P6 でもそのまま成立）。
- ビルド: `make -C samples_ch32v002_arduino/blink_and_read build`。書き込みは固定 minichlink で、識別領域 `0x1ffff704` が `0x002` であることを確認してから行う（`ch32hil`）。
