# usart2（公式WCH SDK、CH32V006のみ）

USART2 の送信（TX）を確認するサンプル。**書籍にない内容**で、CH32V002 にはない周辺機能（USART2、RM 第14章）。種別は `additional-not-in-book`（`hil/matrix_ch32v006_wch.json`）。

出典: 公式 EVT `EXAM/USART`（`externals/ch32v002_004_005_006_007`、調査用）。EVT の例は USART1 のみで USART2 の例はないため、USART2 の初期化は自作（構造体の設定項目は EVT の USART1 の例と同じ）。

## 動作
USART2 の TX をリマップ 3（`AFIO_PCFR1` の USART2_RM = 011、`GPIO_PartialRemap3_USART2`）で **PD2**（TSSOP20 の 19 番、固定配線で GP14）に出し、`usart2 0123456789\r\n` を 200 ms ごとに送る（115200 8N1）。USART1（PD5、115200）には設定を 1 回出力する。

## EVT からの変更点
- USART2、TX のみ、リマップ 3（RX の PD3 は固定配線にないので扱わない）。割り込みと DMA は使わない。
- ログは `USART_Printf_Init`（USART1、PD5）。

## 観測状態
**hil-verified（TX のみ）**（CH32V006 実機）。PD2→GP14 の PIO UART 受信で `usart2 0123456789\r\n` を 1.2 s に 6 回受信（`tests/hil/wch/test_v006_only.py::test_wch_usart2`、記録は `../../okf/log/2026-11-09-0854-ch32v006-only-feature-samples.md`）。RX は未配線で未確認。