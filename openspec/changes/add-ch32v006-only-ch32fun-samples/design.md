# Design

## Context

動機は `proposal.md` を参照。設計に関わる事実（固定 ch32fun `b28d285` と前の change の結果）は次のとおり。

- 固定 ch32fun は、CH32V002/CH32V006 を `CH32V00x` として扱い、ヘッダ `ch32x00xhw.h` を使う。USART2（`USART2`、`RCC_USART2EN`、`AFIO_PCFR1_USART2_RM`）、OPA（`OPA_TypeDef`：`CFGR1`、`CTLR1`、`CFGR2`、`CTLR2`、`OPA_KEY`、`CMP_KEY`、`POLL_KEY`）、ADC の `IDATAR1`/`RDATAR`、`ADC_TKENABLE` は定義されている。
- **`TIM3` は `((ALTM_TypeDef *)TIM3_BASE)` と宣言されているが、`ALTM_TypeDef` はどのヘッダにも定義がない**。そのため、固定 ch32fun のまま `TIM3->…` と書くとコンパイルできない。
- 共通配置のビルド（`target.mk`）は `TARGET_MCU` に CH32V002/CH32V006 を受け付ける。ch32fun の HIL 試験は `hil_dut(<sample>)` で `samples_ch32v00x_ch32fun/<sample>` を選ぶ。マトリクスの単体テストは、002/006 の ch32fun マトリクスと共通配置のサンプルの対応を検査する（実装時に、006 だけの行を許すよう調整が要るかを確かめる）。
- WCH SDK 版の結果（CH32V006）: USART2 は文字列を 6 回受信、TIM3 は 496.6 Hz、OPA の比は 4 倍で 3.92〜3.99、8 倍で 7.81、TKEY は PD4≈4087（触ると 1300〜2650）、PA2≈51。判定は `ch32hil/v006_only.py`。

## Goals / Non-Goals

**Goals:**
- WCH SDK 版と同じ動作を、固定 ch32fun とレジスタ操作だけで再現し、同じ判定で確かめる。
- SDK の関数が書くレジスタの値を、ch32fun 版のソースで明示する（書籍の 4 章の「レジスタで書く」方針に合わせる）。

**Non-Goals:**
- 固定 ch32fun の変更（`ALTM_TypeDef` の追加など）や上流への提案。
- CH32V002 での実行、Arduino 版。

## Decisions

### 1. 作る順番と、各サンプルの出力は WCH SDK 版にそろえる

順番は USART2 → TIM3 → OPA → TKEY（ユーザーの指示。TKEY は最後）。出力の文字列・周期・ピンを WCH SDK 版と同じにして、HIL の判定（`ch32hil/v006_only.py`、`judge.judge_pwm_survey`）をそのまま使う。ログの出力は ch32fun の `printf`（USART1、PD5、115200。ch32fun の既定のデバッグ出力の設定に合わせ、`funconfig.h` で UART の printf を選ぶ）。

### 2. TIM3 は、サンプルの中でレジスタの構造体を定義する

固定 ch32fun に `ALTM_TypeDef` がないため、サンプルの中で RM 第13章の Table 13-2 のとおりの構造体（16 ビットのレジスタが 4 バイト間隔：`CTLR`、`DMAINTENR`、`CNT`、`ATRLR`、`CH1CVR`〜`CH4CVR`）を定義し、`TIM3_BASE`（固定 ch32fun の定義、0x40000800）に当てて使う。ヘッダの `TIM3` マクロは使わない（名前がぶつかるので別名にする）。根拠と、固定 ch32fun で `ALTM_TypeDef` が未定義であることをソースのコメントに書く。
代替案の「固定 ch32fun を直す」は、固定の方針（AGENTS.md）に反するので採らない。

### 3. OPA は、SDK の `OPA_Init` が書く値を、RM と照らしてレジスタに書く

`ch32v00X_opa.c` の `OPA_Unlock`（キーの書き込み）、`OPA_Init`（`CFGR1`/`CTLR1` へのビットの組み立て）、`OPA_Cmd` を読み、同じ値を ch32fun の `OPA->…` へ直接書く。値は WCH SDK 版の build の逆アセンブル、または実機の DUT の読み戻し（必要なら診断用のビルドでレジスタを printf する）で照合する。SDK と ch32fun でレジスタの並び（`OPA_TypeDef`）が違う場合は、RM 第17章のオフセットを正とし、違いをログに記録する。

### 4. CH32V002 では、build を `#error` で止める

各サンプルの `main.c` で、`TARGET_MCU` が CH32V006 以外のとき（ch32fun の `CH32V006` の定義の有無で判定。実装時に固定 ch32fun が定義するマクロを確かめる）`#error` で止め、「CH32V002 にはこの周辺機能がない」と書く。マトリクスは `matrix_ch32v006.json` に `additional-not-in-book` で追加する。`matrix_ch32v002.json` には、単体テストが共通配置の全サンプルの記載を求める場合だけ、状態 `excluded`（理由: 機能がない）で載せる。

### 5. HIL は ch32fun のフレームワークで、WCH SDK 版の試験の流れを再利用する

`tests/hil/test_v006_only.py`（ch32fun 用）を作り、`tests/hil/wch/test_v006_only.py` の流れ（刺激、取り込み、判定）を共通の関数にまとめて両方から使う。CH32V006 以外では skip する。マトリクスの単体テスト（`tests/hil/*.py` の各試験がマトリクスに載っていること）を満たすよう、006 の追加行の `hil_tests` に載せる。

### 6. TKEY の扱いは WCH SDK 版と同じ

値の記録だけで合否を付けない（`build-only` のまま）。PD4 の 1 kΩ のリードを指で触る手作業の観測は、WCH SDK 版と同じ手順で 1 回行い、ログに記録する。

## Risks / Trade-offs

- [OPA のレジスタの意味を読み違える] → SDK のソースと RM を両方見て、実機の比で確かめる。WCH SDK 版と比が大きく違えば、レジスタの値を比べ直す。
- [`ALTM_TypeDef` の扱いが固定 ch32fun の更新で変わる] → 固定 revision を前提にし、更新時に見直す旨をコメントに書く。
- [ch32fun の起動処理（クロック、割り込み）が SDK と違い、TIM3 の周期や TKEY の値が変わる] → 測った値を WCH SDK 版と並べて記録し、違いは差として残す（ch32fun の HCLK は 48 MHz の想定）。
- [マトリクスの単体テストが「002 と 006 で同じ共通サンプル」を前提にしている] → 006 だけの追加行を許すよう、書籍由来の行に限る形にテストを直す（前の change の WCH と同じ方針）。

## Open Questions

なし（PGA の許容幅は WCH SDK 版と同じ ±10 % を使う）。
