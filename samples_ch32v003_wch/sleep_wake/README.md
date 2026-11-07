# sleep_wake（公式WCH SDK、CH32V003）

書籍`sleep_mode_blink-wch_sdk`の移植。Sleepモード（`__WFI()`）をTIM1更新割り込みで復帰する。
TIM1は1 kHz（分周48000-1）、周期100 ms、リピートカウンタ20-1 → **2秒ごと**に`TIM1_UP`割り込み。メインループは「LEDトグル → `sleep`出力 → `__WFI()`」、
`TIM1_UP_IRQHandler`（`WCH-Interrupt-fast`）は`tim`を出力して復帰させ、ループが`awake`を出力する。1周期（2秒）のUARTは`tim`→`awake`→`sleep`（19 B）。
書籍の`MODE_NOUSE_SLEEP`（スリープせず割り込み内でLEDをトグル）も残してある。Flash 5,196 B／RAM 716 B。
公式の`__WFI`は`WFE`関数（`core_riscv.c`の`.highcode`）を呼ぶため、`sdk/Core/core_riscv.c`もコピーして共通ビルドに加えた（PROVENANCE参照）。

## 書籍との差
LEDを**PC0**（治具BLINK→GP5。書籍のPC1は治具のI2C SDA）。NMI/HardFault/TIM2の宣言と空ハンドラを省いた（公式Startupの既定）。それ以外は書籍のコード。

## 観測（HIL、実測）
`uv run pytest --hil --hil-framework wch tests/hil/wch/test_sleep_wake.py`（3回連続成功）
- ELFに`wfi`命令がある（静的確認）。
- UARTの行順序が`tim → awake → sleep`の循環（例: `awake, sleep, tim, awake`）で、32 Bの受信に約3.1秒（WFIが即戻るなら`tim`が出ず、即座に連続出力になる）。
- PC0（GP5）が約2.0秒ごとにトグル（半周期2.05, 2.0, 2.0, 2.0, 2.0, 2.0 s、判定は1.6〜2.4 s）。
- **消費電力は測定していない**。割り込みを待っていることは分かるが、コアのクロックが止まっていること（実際に低消費電力であること）は示せていない。
