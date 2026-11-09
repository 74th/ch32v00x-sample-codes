# opa（公式WCH SDK、CH32V006のみ）

OPA（オペアンプ）を PGA として使うサンプル。**書籍にない内容**。CH32V002 にはない周辺機能（RM 第17章）。種別は `additional-not-in-book`。

出典: 公式 EVT `EXAM/OPA/OPA_PGA`（調査用）。ドライバ `ch32v00X_opa.{c,h}` を `../sdk` にコピーした（出所は `../PROVENANCE.md`）。

## 動作
OPA の正入力 CHP0 = PA2、負入力は内部（利得 4 倍、`make clean && make EXTRA_CFLAGS=-DOPA_GAIN=8` で 8 倍）、出力 OUT0 = PD4。ADC で PA2（ADC_IN0）と PD4（ADC_IN7）を続けて読み、USART1（PD5、115200）に `opa gain=<g> in=<生値> out=<生値>` を 200 ms ごとに出す。起動時に `init opa gain=<g>`。

## EVT からの変更点
- 単端のみ（EVT の差動モードと CMP のバイアス設定は使わない）。ADC は入力と出力の両方を読む。
- 利得をビルド時に切り替える。ログは固定の 1 行形式。
- 出力を ADC の内部チャネルへ出す方法は資料・EVT に記述がないので、PD4（ADC_IN7）で読む。

## 観測状態
**hil-verified**（CH32V006 実機）。PA2 に低い入力を与えたときの out/in の中央値が、利得 4 で 3.92〜3.99、利得 8 で 7.81（許容幅 ±10 %）。高入力は飽和。電圧は未校正、オフセット・ノイズ・帯域・差動・CMP は未確認（`test_wch_opa`、同ログ）。