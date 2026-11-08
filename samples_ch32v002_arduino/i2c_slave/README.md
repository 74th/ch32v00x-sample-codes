# i2c_slave（Arduino Core CH32、CH32V002F4P6）

- ソース: `samples_ch32v003_arduino/i2c_slave/i2c_slave.ino` を元にし、`on_request` の範囲判定だけを直した（下記。出典とその他の変更点は 003 版の README）。
- ボード: 公式 `WCH:ch32v` 1.0.6 の CH32VM00X / CH32V006K8 を流用し、`../arduino.mk` で Flash/RAM サイズとスタック・ヒープの位置を上書きする（[調査](../../okf/log/2026-11-07-2125-arduino-ch32v002-survey.md)）。
- 配線・HIL は CH32V003 版と同じ（`--hil-device ch32v002 --hil-framework arduino`）。

## 書籍のコードとの差（範囲判定）
- `on_request` は書籍（003 版と同じソース）では `position + (i - 1)` で判定して `position + i` を読むため、ポインタが末尾（0x2D〜0x2F）のとき配列の外を1バイト読みえた。実際に読む添字（`position + i`）で判定し、範囲外は `0xFF` を返すように直した（書籍は `0x00`）。`on_receive` は判定と書き込みが同じ添字なので変えていない。
- このため、ソースは CH32V003 版と同一ではなくなった（差は `on_request` のみ）。
- 002 での確認（実測）: ポインタ 0x2E から4バイト読むと `00 00 ff ff`（3回とも）。Wire slave の既知の断続的な固着は、この修正では解決していない（[ログ](../../okf/log/2026-11-08-2137-fix-ch32v00x-sample-findings.md)）。
