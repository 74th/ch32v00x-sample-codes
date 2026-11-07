# adc（公式WCH SDK、CH32V003）

書籍`adc-wch_sdk`の移植。PA1（ADC1 ch1、x）とPA2（ch0、y）を単発変換で読み、200 msごとに`x: <n>, y: <n>`をUSART1 TX（PD5）へ出す。
10-bit・右詰め・サンプル時間241サイクル、起動時に公式`ADC_ResetCalibration`/`ADC_StartCalibration`で校正。Flash 6,964 B／RAM 696 B。
ADC設定は書籍と同一で、省いたのはNMI/HardFaultの宣言だけ（公式Startupの既定ハンドラを使う）。

## 観測（HIL、実測）
`uv run pytest --hil --hil-framework wch tests/hil/wch/test_adc.py`
RC（10 kΩ・1 µF、τ=10 ms）をPico GP12/GP13の`GPIO_DRIVE`で充放電し、解放後に保持された電圧をDUTが読む。
- 粗い確認: High駆動のチャネル≧700、Low駆動≦300。2チャネルを独立に確認。結果: x=997/y=0、x=0/y=995、両方0。
- 単調性: 完全放電後に10 msのパルスを3回累積。x: 604→821→917、y: 604→822→922（理論63/86/95 %に近く、各段≧20増）。
外部基準で電圧を測っていないため、変換値の絶対精度は未確認（校正はサンプル内で実行）。ADC_OBSERVE（PWM刺激）はch32funのhex出力専用のため使っていない。
