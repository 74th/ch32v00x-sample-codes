# watchdog（公式WCH SDK、CH32V006）

`../../samples_ch32v002_wch/watchdog/` と同じソース・Makefile（書籍 `*-wch_sdk` 由来）を、CH32V006用の維持SDK（`../sdk`、PROVENANCE参照）で `-DCH32V006`・公式LD（Flash 62 KB／RAM 8 KB）でビルドする。
観測状態は `hil/matrix_ch32v006_wch.json` と `okf/log/` の実測ログを参照（002/003 の結果は継承しない）。

## 観測状態（CH32V006 実機、機能のみ）
**hil-verified**（`--hil-device ch32v006 --hil-framework wch`）。IWDG（reload 2000）は 006 では約 2.3〜3.1 s 無給電でリセットされるため、PA1 の保持を 3.5 s にして確認（リセット要因は IWDGRSTF）。タイムアウトの精度は未確認。002/003 の結果は継承せず 006 で観測した。[ログ](../../okf/log/2026-11-08-1656-ch32v006-wch-batch3-timer-dma-sleep-watchdog.md)

## IWDG の時間の追加調査（2026-11-08）
同じ設定（/128、reload 2000）の診断ファームで、フィードをやめてからのリセットは約 2.3〜2.4 s（3 回、002 と同じ）、PSCR/RLDR は設定どおり読み戻せた。AWU の起床間隔から LSI は約 115.6 kHz と推定（公称 128 kHz、Pico の時計基準で未校正）。上の「2.3〜3.1 s」は、PA1 を Low にし始める時点と最後のフィードとの間の幅（0〜0.5 s）を含む測り方による、と考える。3.5 s の保持は余裕のある値として変えていない。LED2（PC4）は 006 の PC4 の経路が通らないため観測できない。[ログ](../../okf/log/2026-11-08-2237-ch32v006-sample-findings.md)
