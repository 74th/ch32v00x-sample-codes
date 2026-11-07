# adc_dma（公式WCH SDK、CH32V003）

書籍`adc_dma-wch_sdk`の移植。ADC1をscan＋連続変換（PA1=ch1→PA2=ch0の順、241サイクル）で動かし、DMA1チャネル1（周辺→メモリ、circular、half-word×2）で`adc_buf[2]`へ転送する。
メインループは変換起動もADCデータレジスタの読み出しもせず、`adc_buf[0]`（x=PA1）と`adc_buf[1]`（y=PA2）を200 msごとにUSART1 TX（PD5）へ出すだけ。
Flash 7,340 B／RAM 696 B。公式`ADC_*`/`DMA_*`/`ADC_DMACmd`を使用。

書籍との差: `adc_buf`を`volatile`にした（DMAが書き込むため。非volatileだとコンパイラが読み出しを最適化し得る）。NMI/HardFault宣言は省略。

## 観測
`uv run pytest --hil --hil-framework wch tests/hil/wch/test_adc_dma.py`（実測）
- 静的: `main.elf`に`ADC_DMACmd`/`DMA_Init`/`DMA_Cmd`があり`ADC_GetConversionValue`が無い（CPUによる変換値読み出しなし）。
- 順序・継続更新: DUTを再起動せず、PA1だけHigh、PA2だけHigh、両方Lowと刺激を変えて、PA1がx、PA2がyに現れ、値が更新され続けることを確認。
  結果: x=810/y=43、x=205/y=950、両方0。解放後の保持電圧が単発版（adc）より低いのは、連続変換中のリーク・取得が効いた可能性があるが原因は未調査。判定は粗い閾値（High≧700、Low≦300）。
- 単調性: 10 msパルス3段で x: 583→767→843、y: 580→767→849。
DMAレジスタをデバッガから直接読む確認は、minichlinkのメモリ読み出しが周辺レジスタに対して0を返したため行っていない（DMA使用はコードと静的確認、刺激への追従による）。
