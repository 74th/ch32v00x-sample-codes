# i2c_slave（Arduino Core CH32、CH32V002F4P6）

- ソース: `samples_ch32v003_arduino/i2c_slave/i2c_slave.ino` と同じ（出典と変更点はそちらの README）。
- ボード: 公式 `WCH:ch32v` 1.0.6 の CH32VM00X / CH32V006K8 を流用し、`../arduino.mk` で Flash/RAM サイズとスタック・ヒープの位置を上書きする（[調査](../../okf/log/2026-11-07-2125-arduino-ch32v002-survey.md)）。
- 配線・HIL は CH32V003 版と同じ（`--hil-device ch32v002 --hil-framework arduino`）。
