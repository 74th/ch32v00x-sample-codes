# adc_dma（公式WCH SDK、CH32V006）

`../../samples_ch32v002_wch/adc_dma/` と同じソース・Makefile（書籍 `*-wch_sdk` 由来）を、CH32V006用の維持SDK（`../sdk`、PROVENANCE参照）で `-DCH32V006`・公式LD（Flash 62 KB／RAM 8 KB）でビルドする。
観測状態は `hil/matrix_ch32v006_wch.json` と `okf/log/` の実測ログを参照（002/003 の結果は継承しない）。

## 観測状態（CH32V006 実機、機能のみ）
**hil-verified**（`--hil-device ch32v006 --hil-framework wch`）。ADC1 から DMA1 チャネル 1（資料の DMA 要求表と一致）経由で値が読めることを確認。CPU による変換値の読み取りはリンクされていない。002/003 の結果は継承せず 006 で観測した。[ログ](../../okf/log/2026-11-08-1655-ch32v006-wch-batch2-dma-timer.md)
