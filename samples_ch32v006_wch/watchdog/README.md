# watchdog（公式WCH SDK、CH32V006）

`../../samples_ch32v002_wch/watchdog/` と同じソース・Makefile（書籍 `*-wch_sdk` 由来）を、CH32V006用の維持SDK（`../sdk`、PROVENANCE参照）で `-DCH32V006`・公式LD（Flash 62 KB／RAM 8 KB）でビルドする。
観測状態は `hil/matrix_ch32v006_wch.json` と `okf/log/` の実測ログを参照（002/003 の結果は継承しない）。

## 観測状態（CH32V006 実機、機能のみ）
**hil-verified**（`--hil-device ch32v006 --hil-framework wch`）。IWDG（reload 2000）は 006 では約 2.3〜3.1 s 無給電でリセットされるため、PA1 の保持を 3.5 s にして確認（リセット要因は IWDGRSTF）。タイムアウトの精度は未確認。002/003 の結果は継承せず 006 で観測した。[ログ](../../okf/log/2026-11-08-1656-ch32v006-wch-batch3-timer-dma-sleep-watchdog.md)
