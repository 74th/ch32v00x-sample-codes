# blink_and_read（公式WCH SDK、CH32V003）

書籍`blink_and_read-wch_sdk`の移植。PC0のLEDを500 msごとに点滅し、PA1（内部プルアップ入力）がLowの間は点滅せず1秒待つ。
公式の`GPIO_Init`/`GPIO_ReadInputDataBit`/`Delay_Ms`を使用。ビルドは`PERIPH := misc`（`NVIC_PriorityGroupConfig`）。Flash 6,356 B／RAM 696 B（printf込み）。

書籍との差: ログはSDI printfではなくUSART1 TX（PD5）の`USART_Printf_Init(115200)`。治具のPico（GP9）で観測できるようにするため。
SDI_PRINT/wlinkは使わない。

## 観測（HIL、実測）
`uv run pytest --hil --hil-framework wch tests/hil/wch/test_blink_and_read.py`
- 起動文字列`init/start/loop 0/loop 1`と連番、UARTエラー0
- PC0（GP5）が500/500 ms（±100 ms）
- PA1をGP12→RCでLowにすると3 s間点滅停止（high=0）、解放後に点滅再開
再開確認は、1秒の`Delay_Ms`が残る分を待ってから300点（3 s）をサンプルする。精密な電圧・周期測定ではない。
