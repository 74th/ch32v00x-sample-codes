# Proposal

## Why

CH32V006 だけの周辺機能（USART2、TIM3、OPA、TKEY）は、change `add-ch32v006-only-feature-samples` で WCH SDK 版のサンプルを作り、実機で確認した。書籍の ch32fun の章はレジスタを直接操作する書き方を説明しているが、これらの機能の ch32fun 版はない。ユーザーは ch32fun（レジスタ直接操作）でも確かめたい、と判断した。

## What Changes

- 標準 ch32fun（固定 `externals/ch32fun`、extralibs なし）で、レジスタを直接操作するサンプルを `samples_ch32v00x_ch32fun/` に追加する。作る順番は次のとおりで、TKEY は最後にする。
  1. `usart2`: USART2 の TX をリマップ 3 で PD2 に出し、WCH SDK 版と同じ文字列を送る。
  2. `tim3`: TIM3 の CC3 の DMA 要求で PC0 を反転する（WCH SDK 版と同じ 500 Hz）。
  3. `opa`: OPA を PGA（4 倍・8 倍）にし、PA2 の入力と PD4 の出力を ADC で読んで USART1 に出す。
  4. `tkey`: TKEY で PD4 と PA2 の値を USART1 に出す。
- 4 つのサンプルは CH32V006 専用とする。共通配置（`samples_ch32v00x_ch32fun/`）に置くが、CH32V002 を指定したビルドは、理由を示すコンパイルエラーで止める。
- レジスタの値は、WCH SDK 版の SDK のソース（`ch32v00X_opa.c` など）とリファレンスマニュアルから決め、WCH SDK 版の build（map、逆アセンブル）と比べて確かめる。
- HIL: WCH SDK 版と同じ判定（`ch32hil/v006_only.py`）を使う試験を、ch32fun のフレームワークで追加する。CH32V006 でだけ実行し、ほかのデバイスでは理由付きで skip する。
- マトリクス: `hil/matrix_ch32v006.json` に 4 行を種別 `additional-not-in-book` で追加する。CH32V002 の扱いは design で決める。

## Capabilities

### New Capabilities

なし。

### Modified Capabilities

- `ch32fun-sample-workflow`: 書籍にない、CH32V006 だけの周辺機能の ch32fun サンプル（片方のデバイス専用のサンプルを共通配置に置く場合の扱い）の要件を加える。

## Impact

- 追加するコード: `samples_ch32v00x_ch32fun/{usart2,tim3,opa,tkey}/`、`tests/hil/` の ch32fun 用の試験、`hil/matrix_ch32v006.json`（と必要なら `hil/matrix_ch32v002.json`）の行、ホスト単体テスト。
- 固定 `externals/ch32fun` は変更しない（ヘッダの不足はサンプル側で補う。design を参照）。
- 配線: 変更しない。TKEY の手作業の観測は、PD4 の 1 kΩ のリード（前の change で付けたもの）を使う。
- 対象外: CH32V002、Arduino、USART2 の受信、OPA の差動・16/32 倍、CMP、TIM3 と TIM1 の連携。書籍 16 章への ch32fun 版の節の追加は別作業。
