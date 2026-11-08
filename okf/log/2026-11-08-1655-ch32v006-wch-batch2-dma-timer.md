# CH32V006 WCH 公式SDK: adc_dma / timer_blink の HIL（タスク 5.2）

- 作業日時: 2026-11-08 16:55:50〜16:56:17 JST（`date` で確認）。記録は 17:00 JST 頃。
- 対象: CH32V006F8P6（ユーザー申告）。固定配線、電圧未測定。ツール・ソース・識別（`chip_id=0x00630620`）・全量 readback は [前ログ](2026-11-08-1651-ch32v006-wch-batch1.md)と同じ。ソースは 002 版と同一（変更なし）。

## 静的根拠（実測）
- adc_dma: ELF に `ADC_DMACmd`・`DMA_Init`・`DMA_Cmd` があり、`ADC_GetConversionValue`（CPU による読み取り）は含まれない。コードが DMA1 のレジスタブロック（0x40020xxx）を参照。サンプルは DMA1 チャネル 1 に ADC1 の RDATAR（HalfWord、Circular、VeryHigh）を割り当て、リファレンスマニュアル（CH32V00x、DMA 要求表）の「チャネル 1 のハードウェア要求は ADC1」と一致（資料確認）。ポーリングへの代替はしていない。
- timer_blink: SDK ヘッダ（`-DCH32V002` と `-DCH32V006` のプリプロセッサ出力）で `TIM1_UP_IRQn=35`・`TIM2_IRQn=38` が同一。ELF で `TIM1_UP_IRQHandler`（0x21a）がベクタのスロット 35、`TIM2_IRQHandler`（0x1f6）がスロット 38 にあり、`mret` で戻る割り込み属性の関数（`check_irq_handler`）。
- 不備の修正: `test_adc_dma.py` の静的確認が、どの機種でも `samples_ch32v003_wch/adc_dma/main.elf`（003 の成果物）を見ていた。判定対象の機種のビルド成果物（`dut.sample_dir/main.elf`）を見るよう直した。003/002 の過去の結果の静的確認は 003 の ELF を見ていた可能性がある（002 の結果自体は ADC の読みで判定しているので機能の判定は変わらない。過去ログは未変更）。

## 実行（実測）
```sh
uv run pytest --hil --hil-device ch32v006 --hil-framework wch -m 'hil and wch' tests/hil/wch/test_adc_dma.py tests/hil/wch/test_timer_blink.py --hil-port=<Pico> --hil-run-dir=<run>
```
- **3 passed**（27.5 s）: `test_wch_adc_dma`（x_high_y_low=(3780, 14) など。判定は未校正の粗い比率）、`test_wch_timer_blink[tim1]`（PC0 500/500 ms、「1sec event」×2、TIM1_UP ハンドラ）、`test_wch_timer_blink[tim2]`（「500ms event」×2、TIM2 ハンドラ）。
- 機能確認のみ。ADC の精度・校正・時間精度は未確認。
