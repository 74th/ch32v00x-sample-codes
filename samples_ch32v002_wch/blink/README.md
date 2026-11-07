# blink（公式WCH SDK、CH32V002）

CH32V003版`blink`（公式`Delay_Ms`、PC0を500 msごとに点滅）の002 SDK版。Flash 1,796 B／RAM 524 B（スタック512 B込み）。
`wch.mk`、`-DCH32V002`、16K/4K、ISAなどの設定は[../README.md](../README.md)。003版からの変更は機械的な置換（`RCC_PB2Periph_GPIOC`、`GPIO_Speed_30MHz`）のみ。
**CH32V002実機で観測済み**（`uv run python scripts/wch-sdk.py flash/observe --device ch32v002 --sample blink`: 書き込み・全量読み戻し後、PC0→Pico GP5が50サンプル(10 ms間隔)ずつのHigh/Low＝500 ms周期、完全な半周期を4回以上、400..600 ms）。ログ: [2026-11-08-0802](../../okf/log/2026-11-08-0802-wch-sdk-ch32v002-hil.md)。
