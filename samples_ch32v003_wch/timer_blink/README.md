# timer_blink（公式WCH SDK、CH32V003）

書籍`timer_blink-wch_sdk`の移植。タイマ更新割り込みでLEDをトグルする。公式`TIM_TimeBaseInit`/`TIM_ITConfig`/`TIM_GetITStatus`/`NVIC_Init`と、`WCH-Interrupt-fast`属性の割り込みハンドラ。
- `USE_TIM1=1`（既定・書籍どおり）: TIM1、分周48000-1（1 kHz）、周期100 ms、リピートカウンタ5-1 → `TIM1_UP`が**500 msごと**。`1sec event`を出力（書籍の文言。実際の間隔は500 ms）。
- `USE_TIM1=0`: TIM2、周期500 ms。`500ms event`を出力。
どちらも割り込みごとにLEDをトグルするので500 ms/500 msで点滅する。Flash 7,092 B（TIM1）／5,040 B未満の別構成はなし、RAM 700 B。
TIM2版のビルド: `make clean && make build EXTRA_CFLAGS=-DUSE_TIM1=0`（HILが自動で両方を作る）。

## 書籍との差
- LEDは**PC0**（治具のBLINK→GP5）。書籍のPC1は治具のI2C SDA。
- `USE_TIM1`をコンパイラ引数で与えられるようにした。
- 起動時のレジスタダンプのうち`NVIC->IPRIOR[TIM1_UP_IRQn]`/`NVIC->IENR[…]`の2行は省いた（このSDKの`NVIC_Type`は配列長8で、書籍の添字35は範囲外）。TIM1レジスタのダンプは書籍のまま。

## 観測（HIL、実測）
`uv run pytest --hil --hil-framework wch tests/hil/wch/test_timer_blink.py`（`tim1`と`tim2`の両方。毎回`make clean`してから該当構成を書き込み）
- PC0（GP5）: 両構成とも500/500 ms（±100 ms）。
- UART（PD5）: TIM1は`1sec event`、TIM2は`500ms event`が2回以上、他方の文言は出ない。
- 割り込み属性（ELFの静的確認）: `TIM1_UP_IRQHandler`はベクタ35番、`TIM2_IRQHandler`は38番に入り、どちらも`mret`で戻る（既定ハンドラではない）。
- 起動時のレジスタダンプは32 Bを超えるため、先頭32 Bしか捕捉していない（レジスタ値そのものは未確認）。
