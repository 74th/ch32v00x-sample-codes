# timer_dma（公式WCH SDK、CH32V003）

書籍`timer_dma-wch_sdk`の移植。4桁7セグメントのダイナミック点灯を、タイマ要求のDMAだけで行う。
TIM1（約100 kHzで10カウント＝約100 µsごと）がCC1/CC2/CC3のDMA要求を出し、DMA1のch2/ch3/ch6が要求ごとに4要素のcircularバッファから1ワードを
GPIOA/GPIOC/GPIOD->BSHRへ書く。約100 µsごとに次の桁（カソードSEL1〜4）とセグメントパターンへ切り替わり、全桁の走査は約400 µs。表示パターンは桁0〜3で「0123」。
公式`DMA_Init`/`DMA_Cmd`/`TIM_TimeBaseInit`/`TIM_OC1Init`/`TIM_DMACmd`を使用。Flash 2,640 B／RAM 468 B。バッファ・桁/セグメント表・TIM1/DMA設定は書籍のまま。

## 書籍との差
- `printf`をすべて削除。書籍はSDI printfだが、このビルドではSDI出力を有効にしておらず（`SDI_PRINT`はCLOSE）、USART printfだとPD5を使うがPD5は表示のSEL2。
  `SDI_PRINT`がCLOSEのままUSART1未初期化で`printf`を呼ぶと書き込みがブロックし得るため、呼び出し自体を除いた。他の差はない。
- ピン使用は書籍と同じ: SA〜SG=PC4 PC3 PD3 PD2 PC7 PC5 PC6、SDP=PA1、SEL1〜4=PD6 PD5 PD4 PC0。

## 観測（HIL、実測）
`uv run pytest --hil --hil-framework wch tests/hil/wch/test_timer_dma.py`（最終条件で11回連続成功）
Picoは1コマンド1ピン、最小間隔1 msで、100 µsの桁切替は時間分解できない。そこで各ピンのHigh比率（300点、1.17 ms間隔）を、桁0〜3の期待パターンから求めた値と比較する。
- SEL1(PD6)/SEL2(PD5)/SEL4(PC0): 0.75（自桁の間だけLow）、SA(PC4)/SD(PD2): 0.75、SE(PC7)/SG(PC6): 0.5、SF(PC5): 0.25。許容±0.10、実測は期待値から約0.02以内。
- 静的なピンなら0または1になるため、比率が揃うことでタイマ要求DMAがBSHRを時分割で書いていることを示す。ELFに`DMA_Init`/`DMA_Cmd`/`TIM_DMACmd`/`TIM_OC1Init`があることも確認。
- 初回は1 ms間隔でエイリアシング（PC7が2 run＝ほぼ固定値）、また起動直後の測定でPD6が低めに出た（起動後約100 msまで走査が始まらないため。1秒待つと解消）。
- **観測できないもの**: SB(PC3)、SC(PD3)、SEL3(PD4)、SDP(PA1。10 kΩ+1 µFのADC網経由)、実際の4桁表示。そのため表示が「0123」になることと、各桁でカソードとセグメントが同期して切り替わること（桁ごとの組み合わせ）は未確認。
- DMAチャネル設定はコード上とELFシンボルの確認で、レジスタの実測値は読んでいない。
