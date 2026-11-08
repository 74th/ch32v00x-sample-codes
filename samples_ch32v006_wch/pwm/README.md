# pwm（公式WCH SDK、CH32V006）

`../../samples_ch32v002_wch/pwm/` と同じソース・Makefile（書籍 `*-wch_sdk` 由来）を、CH32V006用の維持SDK（`../sdk`、PROVENANCE参照）で `-DCH32V006`・公式LD（Flash 62 KB／RAM 8 KB）でビルドする。
観測状態は `hil/matrix_ch32v006_wch.json` と `okf/log/` の実測ログを参照（002/003 の結果は継承しない）。

## 観測状態（CH32V006 実機、機能のみ）
**hil-verified**（`--hil-device ch32v006 --hil-framework wch`）。**書籍からの逸脱**: PC4（TIM1_CH4）が 006 で無信号のため、第 2 チャネルを TIM2_CH3 on PC0（`USE_PC0=1`、既定）にした。PD2＋PC0 で合格。PC4 版は `EXTRA_CFLAGS=-DUSE_PC0=0` でビルドでき、参考試験は XFAIL（原因未特定）。002/003 の結果は継承せず 006 で観測した。[ログ](../../okf/log/2026-11-08-1651-ch32v006-wch-batch1.md)
