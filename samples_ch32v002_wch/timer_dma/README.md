# timer_dma（公式WCH SDK、CH32V002）

CH32V003版（[../../samples_ch32v003_wch/timer_dma/README.md](../../samples_ch32v003_wch/timer_dma/README.md)）をCH32V002専用の公式SDK（`../sdk`、PROVENANCE参照）へ移植したもの。
ビルド結果（WCH GCC 15.2.0、`-DCH32V002`、Flash 16 KB／RAM 4 KB、スタック512 B）: Flash 3,624 B／RAM 724 B。

## 003版との差分
- 機械的な置換: `RCC_APB2Periph_*`→`RCC_PB2Periph_*`、`RCC_APB1Periph_*`→`RCC_PB1Periph_*`、`RCC_AHBPeriph_*`→`RCC_HBPeriph_*`（002 SDKのAPI名）、`GPIO_Speed_10MHz/50MHz`→`GPIO_Speed_30MHz`（002 SDKは30 MHzのみ）。インクルードは`ch32v00x.h`のまま（`../sdk/Compat`が002の`ch32v00X.h`へ橋渡し）。
- このサンプル固有: なし（上記の置換のみ）。DMAチャネル割当は003と同じ。
- 003との行差分（`+`/`-`の行数）: `main.c` 14行。

## 観測状態（CH32V002実機で観測済み）
**hil-verified**。CH32V002（`0x1ffff704`=0x002、minichlinkが`Detected CH32V002`）に書き込み・全量読み戻しのうえ`tests/hil/wch/test_timer_dma.py`が成功（`--hil-device ch32v002 --hil-framework wch`）。判定基準は003と同じ（`hil/matrix_ch32v002_wch.json`）。003の結果は継承せず002で再観測した。数値の詳細は[ログ](../../okf/log/2026-11-08-0802-wch-sdk-ch32v002-hil.md)。
未観測（003と同様）: SB,SC,SEL3,SDP,表示器。
