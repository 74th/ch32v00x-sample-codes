# adc（公式WCH SDK、CH32V002）

CH32V003版（[../../samples_ch32v003_wch/adc/README.md](../../samples_ch32v003_wch/adc/README.md)）をCH32V002専用の公式SDK（`../sdk`、PROVENANCE参照）へ移植したもの。
ビルド結果（WCH GCC 15.2.0、`-DCH32V002`、Flash 16 KB／RAM 4 KB、スタック512 B）: Flash 7,556 B／RAM 952 B。

## 003版との差分
- 機械的な置換: `RCC_APB2Periph_*`→`RCC_PB2Periph_*`、`RCC_APB1Periph_*`→`RCC_PB1Periph_*`、`RCC_AHBPeriph_*`→`RCC_HBPeriph_*`（002 SDKのAPI名）、`GPIO_Speed_10MHz/50MHz`→`GPIO_Speed_30MHz`（002 SDKは30 MHzのみ）。インクルードは`ch32v00x.h`のまま（`../sdk/Compat`が002の`ch32v00X.h`へ橋渡し）。
- このサンプル固有: ADC: 12-bit。002 SDKにADC校正APIが無いため校正（`ADC_Calibration_Vol`/`ADC_ResetCalibration`/`ADC_StartCalibration`）を省略。サンプル時間は`ADC_SampleTime_CyclesMode7`（239.5サイクル、003の241サイクルに最も近い）。公式002例に倣い`RCC_ADCCLKConfig(RCC_PCLK2_Div8)`を追加。
- 003との行差分（`+`/`-`の行数）: `main.c` 10行。

## 観測状態（CH32V002実機で観測済み）
**hil-verified**。CH32V002（`0x1ffff704`=0x002、minichlinkが`Detected CH32V002`）に書き込み・全量読み戻しのうえ`tests/hil/wch/test_adc.py`が成功（`--hil-device ch32v002 --hil-framework wch`）。判定基準は003と同じ（`hil/matrix_ch32v002_wch.json`）。003の結果は継承せず002で再観測した。数値の詳細は[ログ](../../okf/log/2026-11-08-0802-wch-sdk-ch32v002-hil.md)。
