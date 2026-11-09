# tim3（公式WCH SDK、CH32V006のみ）

簡易タイマー TIM3（SLTM、RM 第13章）のサンプル。**書籍にない内容**。CH32V002 にはない周辺機能。種別は `additional-not-in-book`。

出典: 公式 EVT `EXAM/TIM/SLTIM_DMA`（調査用）。

## 動作
TIM3 は出力ピンを持たないので、CC3 の DMA 要求（006 では DMA1 のチャネル 1 だけ。RM Table 8-1）で、DMA が GPIOC の BSHR に PC0 の set/reset を交互に書く。TIM3 は HCLK（48 MHz）を分周なしで数え、`ATRLR = 47999` で 1 ms ごとに DMA 要求、PC0 は 500 Hz（周期 2 ms）の矩形波になる。CPU は何もしない（起動時に USART1 へ `init tim3 dma toggle pc0 half_period_us=1000`）。

## EVT からの変更点
- DMA の転送先を TIM1->ATRLR の RAM への取り込みから GPIOC->BSHR に変えた（`../timer_dma` と同じ方式）。TIM1 は使わない。割り込みなし。

## 観測状態
**hil-verified**（CH32V006 実機）。PC0 が 496.6 Hz（期待 500 Hz、−0.68 %）、duty 50 %（`test_wch_tim3`、同ログ）。