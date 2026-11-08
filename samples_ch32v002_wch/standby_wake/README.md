# standby_wake（公式WCH SDK、CH32V002）

CH32V003版（[../../samples_ch32v003_wch/standby_wake/README.md](../../samples_ch32v003_wch/standby_wake/README.md)）をCH32V002専用の公式SDK（`../sdk`、PROVENANCE参照）へ移植したもの。
ビルド結果（WCH GCC 15.2.0、`-DCH32V002`、Flash 16 KB／RAM 4 KB、スタック512 B）: Flash 7,592 B／RAM 952 B。

## 003版との差分
- 機械的な置換: `RCC_APB2Periph_*`→`RCC_PB2Periph_*`、`RCC_APB1Periph_*`→`RCC_PB1Periph_*`、`RCC_AHBPeriph_*`→`RCC_HBPeriph_*`（002 SDKのAPI名）、`GPIO_Speed_10MHz/50MHz`→`GPIO_Speed_30MHz`（002 SDKは30 MHzのみ）。インクルードは`ch32v00x.h`のまま（`../sdk/Compat`が002の`ch32v00X.h`へ橋渡し）。
- このサンプル固有: 起床後の `SystemInit()` の直後に `Delay_Ms(10)` を追加（書籍にはない）。待ちなしでは起床直後の先頭約14バイトが毎回化け、10 ms・100 ms の待ちで 1〜2 バイトに減った（各3回×3起床、[ログ](../../okf/log/2026-11-08-2137-fix-ch32v00x-sample-findings.md)）。
- 003との行差分（`+`/`-`の行数）: `main.c` 6行。

## 観測状態（CH32V002実機で観測済み）
**hil-verified**。CH32V002（`0x1ffff704`=0x002、minichlinkが`Detected CH32V002`）に書き込み・全量読み戻しのうえ`tests/hil/wch/test_standby_wake.py`が成功（`--hil-device ch32v002 --hil-framework wch`）。判定基準は003と同じ（`hil/matrix_ch32v002_wch.json`）。003の結果は継承せず002で再観測した。数値の詳細は[ログ](../../okf/log/2026-11-08-0802-wch-sdk-ch32v002-hil.md)。
注意: 待ちを入れる前は、wake直後の先頭約14バイトが毎回同じ内容で文字化け（UARTフレーミングエラー）になっていた（003では先頭1バイト程度）。10 msの待ちの後も先頭1〜2バイトの化けは残り、原因は未特定。判定は従来どおり`up: N `以降の連番とwake間隔で行う。
