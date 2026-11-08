# blink_and_read（公式WCH SDK、CH32V006）

`../../samples_ch32v002_wch/blink_and_read` と同じ `main.c`・Makefile（書籍 `blink_and_read-wch_sdk` 由来）を、CH32V006用の維持SDK（`../sdk`、PROVENANCE参照）でビルドする。
ビルド結果（WCH GCC 15.2.0、`-DCH32V006`、Flash 62 KB／RAM 8 KB、スタック512 B）: Flash 7,084 B／RAM 952 B。

## 002版との差分
- ソース差分なし。002 SDKとCH32V006 SDK（同一revision）はAPI名が同じ。差は `wch.mk` の `-DCH32V006` とリンカスクリプト（公式62K/8K）のみ。

## 観測状態（CH32V006実機で観測済み、機能のみ）
**hil-verified**。CH32V006（`0x1ffff704` 上位型番 0x006、`Detected CH32V006`）へ書き込み・全量読み戻しのうえ `tests/hil/wch/test_blink_and_read.py` が成功（`--hil-device ch32v006 --hil-framework wch`）。判定基準は002/003と同じ。002・003の結果は継承せず006で観測した。詳細は[ログ](../../okf/log/2026-11-08-1549-ch32v006-wch-blink-hil.md)、マトリクスは `hil/matrix_ch32v006_wch.json`。
