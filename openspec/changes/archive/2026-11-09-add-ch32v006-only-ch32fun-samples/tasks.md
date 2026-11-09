# Tasks

## 1. 準備

- [x] 1.1 `git status` を確認し、作業ログ（`okf/log/`）を開始する。共通配置の ch32fun の既存サンプルを 002 と 006 で build し、成果物の SHA-256 を記録する（追加で既存の成果物が変わらないことの確認用）。
- [x] 1.2 固定 ch32fun が CH32V006 のときに定義するマクロ（`#error` の判定に使う）、`printf` の出力先の設定、`ch32x00xhw.h` の USART2・OPA・ADC（TKEY）の定義と、`ALTM_TypeDef` が未定義であることを確かめて記録する。

## 2. USART2

- [x] 2.1 `samples_ch32v00x_ch32fun/usart2/`: レジスタ操作で USART2 の TX をリマップ 3（PD2）に出し、WCH SDK 版と同じ `usart2 0123456789\r\n` を 200 ms ごとに送る。CH32V002 では `#error`。README に出典と WCH SDK 版との対応を書く。
- [x] 2.2 006 で build し、002 の build が理由付きのエラーで止まることを確かめる。

## 3. TIM3

- [x] 3.1 `samples_ch32v00x_ch32fun/tim3/`: RM 第13章のレジスタの並びでサンプル内に構造体を定義し、TIM3 の CC3 の DMA 要求（DMA1 チャネル 1）で PC0 を反転する（ATRLR 47999、500 Hz）。`ALTM_TypeDef` が固定 ch32fun で未定義であることと根拠をコメントに書く。
- [x] 3.2 006 で build し、逆アセンブルで TIM3（0x40000800）と DMA1 チャネル 1 への書き込みがあることを確かめる。002 の build が止まることを確かめる。

## 4. OPA

- [x] 4.1 WCH SDK の `OPA_Unlock`、`OPA_Init`、`OPA_Cmd` と RM 第17章を読み、PGA 4 倍・8 倍、P0=PA2、OUT0=PD4 の設定で書くレジスタと値を決めて記録する（SDK と ch32fun の `OPA_TypeDef` の並びも比べる）。
- [x] 4.2 `samples_ch32v00x_ch32fun/opa/`: 上の値をレジスタに直接書き、ADC で PA2（ch0）と PD4（ch7）を読んで、WCH SDK 版と同じ形式で USART1 に出す。`-DOPA_GAIN=4|8`。
- [x] 4.3 006 で build し、WCH SDK 版の build と比べて同じレジスタに同じ値を書いていることを（逆アセンブルまたは静的な値で）確かめる。002 の build が止まることを確かめる。

## 5. TKEY

- [x] 5.1 `samples_ch32v00x_ch32fun/tkey/`: レジスタ操作で ADC の TKEY を有効にし、PD4（ch7）と PA2（ch0）の値を WCH SDK 版と同じ形式で USART1 に出す（充電・放電時間は同じ値）。
- [x] 5.2 006 で build し、002 の build が止まることを確かめる。

## 6. HIL 試験とマトリクス

- [x] 6.1 WCH SDK 版の試験の流れを共通の関数にまとめ、ch32fun 用の `tests/hil/test_v006_only_ch32fun.py`（`usart2`、`tim3`、`opa` 4 倍・8 倍、`tkey`）を作る。CH32V006 以外では skip。WCH SDK 版の試験が変わらず動くことを確かめる。
- [x] 6.2 `hil/matrix_ch32v006.json` に 4 行を `additional-not-in-book`、状態 `build-only` で追加する。必要なら `matrix_ch32v002.json` に `excluded` で載せ、マトリクスの単体テストを 006 だけの行に対応させる。`uv run pytest` が通ることを確かめる。

## 7. 実機での確認（DUT=CH32V006）

- [x] 7.1 DUT が CH32V006 であることを `./scripts/ch32fun.sh flash ch32v006` の検出で確かめてから、`usart2`、`tim3`、`opa` の試験を実行し、測った値を WCH SDK 版と並べて記録する。
- [x] 7.2 `tkey` の試験を実行し、PD4 の 1 kΩ のリードを指で触る手作業の観測（ユーザーが触る）を 1 回行って記録する。
- [x] 7.3 実機で通ったもの（`usart2`、`tim3`、`opa`）だけマトリクスを `hil-verified` にする。`tkey` は `build-only` のまま観測を note に書く。

## 8. 記録

- [x] 8.1 `okf/peripherals/ch32v006-port-differences.md` の 006 だけの機能の節に ch32fun 版の結果と、固定 ch32fun の `ALTM_TypeDef` の未定義を追記する。`okf/open-questions/ch32v00x-unverified.md` の C4 を更新する。
