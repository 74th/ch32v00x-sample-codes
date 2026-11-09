# change `add-ch32v006-only-feature-samples` の実装記録

作業開始: 2026-11-09 08:54 JST（`date` の実測）。以後の時刻は、各節に書いたものを除き未記録。実機の段階は DUT=CH32V006 が必要で、作業開始時の DUT は CH32V002（change `extend-pico-fixture-measurement` の 7.1 のためユーザーが差し替え済み）。

## 1. 準備（タスク 1.1〜1.3）

### 1.1 既存の成果物のハッシュ（実測）

`git status` は作業開始時、前の change の未コミット変更のみ（この change のファイルはなし）。006 の WCH SDK の全例（15 個）を `make clean && make build` で build した `main.bin` の SHA-256（SDK 追加前）:

```
adc 57f2eea4224e39705cc2c9a77c6bb3fc672b586918a370c3fb216fefe7725dc4
adc_dma 7fee300170314929e9e798ceecd91324060edac9d3bd0b1aa61f73ea072d4e73
blink cb08ded31e5a56a1143b4d928623d79803281f0330af9cb3b53ea8484cf95043
blink_and_read 3f7eddf296ac9c599673036d4e003352d8a2a8d3ec15f8f43c1622a0d74050c6
i2c_master f889b04bf32bbff10c3054f4c9af891712064683362ff65b10a53025942dcbec
i2c_slave fb88ec24f3c825aa564b35ef2c79001693dea2606dcd0c4171432753d9ac88fd
pwm 92261b26a08a9b0db317259ce1d6779618189c8e939f86f986b7cbe9e4310405
sleep_wake 328751a2a7726ec0be0e46f266cc6591da5a73dcc0a49da1934eaeb15cf109fd
spi_master 8aa644111fb5df1d699656524647b6d5bfcbf861b92457d70421db181d960156
standby_wake e45cf2fad76769fb2d351da4a348ec936e2ad449a3e590b075cee391f5bb5d11
timer_blink b9a04eadbff2cbc3aa108e91c14bfa9f182b935c11ff6ceb05497cf75c490b2a
timer_dma aee88f28a8f125870f4631fe3acc623e1ab18a32121083c65be9b12ea2420a1e
uart 980bdd6035f84249d84919fd944d8862e3453e4a86329b320efe3cbbecdf40d7
watchdog cf3130657348f303404fd6ce9e7d4042a5204aa754e89ae831f88bff02ecf82d
wwdg fe5f71f338ef4fd86e5e13398aba0cd17f7d616b1f591d7764c2e4fd9980d960
```

`i2c_slave` と `standby_wake` は直前のログ（2026-11-08-2237、`fb88ec24…`、`e45cf2fa…`）と一致。

### 1.2 資料の確認（`xprivate/` の変換物。本文は転載せず、確認した要点のみ）

- USART2（RM 第14章、V005/006/007/M007 のみ）: AFIO_PCFR1 の USART2_RM[2:0]（RM Table 7-11）。**011 = TX/PD2、RX/PD3、CTS/PA0、RTS/PA1**。SDK の定義は `GPIO_PartialRemap3_USART2`。DS のピン表で PD2 は TSSOP20 の 19 番（固定配線の PD2→GP14 と同じ）。RX の PD3 は未配線。PA2（リマップ 2）と PC4（リマップ 5）は設計どおり使わない。
- OPA（RM 第17章）: 006 のピン表で OPA_P0 = PA2、OPA_N0 = PA1。EVT の PGA の例は CHP0 = PA2、出力 OUT0 = PD4（ADC_IN7 と共用）。PGA の利得は SDK の列挙で 4／8／16／32 倍（`CHN_PGA_4xIN` など）。**OPA の出力を ADC の内部チャネルへ出す記述は、EVT の例にもヘッダにもなく、PD4 の ADC_IN7 で読む方法（EVT と同じ）を使う**（設計 Risks の代替案）。
- SLTM（RM 第13章、V006/007/M007 のみ）: TIM3 は 16 ビットで**分周なし**（CK_INT = HB クロックをそのまま数える）、CH1/CH2 は出力比較、CH3/CH4 は DMA 要求のみ、出力ピンなし、TIM1 との連携（ITR0 = TIM1）。**RM Table 8-1 の注: 006/007 では TIM3 の CH3 イベントは DMA1 のチャネル 1 だけを起動できる**（M007 は 1〜3）。EVT の SLTIM_DMA も 006 ではチャネル 1 のみ使う。
- TKEY（RM 第10章）: ADC の外部チャネルを使い、EVT は `ADC_TKeyCmd`、`TKey1->IDATAR1`（充電時間）、`TKey1->RDATAR`（放電時間と結果）。SDK のヘッダでは `TKey1` は `ADC1_BASE` の別名。
- CMP の食い違い（記録のみ、実装しない）: RM 第17章は CMP を V007/M007 のみとするが、006 のデータシートの機能一覧は「OPA/PGA/CMP」と書く（DS 内の図の注に「CH32V005 no TouchKey,TIM3」の記述もあり、CMP は 006 に載るか資料から決められない）。EVT の `OPA/OPA_PGA` はリセットを含む `OPA_CMP_*` を呼ぶが、本サンプルは使わない。

### 1.3 公式 EVT の例（`EXAM/OPA/OPA_PGA`、`EXAM/TIM/SLTIM_DMA`、`EXAM/TOUCHKEY/TKEY`、`EXAM/USART/*`）の読解と方針

- `EXAM/USART` の例はいずれも USART1（`USART_DMA`、`USART_Interrupt` など）で、USART2 の例はない。サンプルは USART2 の初期化を TX のみ・リマップ 3 に自作（USART1 の例の設定項目と同じ構造体を使う）。
- `OPA_PGA`: 元は差動（`PGA_Dif`）で `OPA_CMP_Cmd` を使う。ここでは単端（`PGA_No_Dif`）に限り、CMP のバイアスは使わず、ADC で PA2 と PD4 の両方を読む。
- `SLTIM_DMA`: 元は TIM1 の ATRLR を RAM に DMA する。ここでは DMA の転送先を GPIOC の BSHR にして PC0 を反転（`timer_dma` サンプルと同じ方式）、CH3 比較の DMA 要求（チャネル 1）を使う。TIM1 は使わない。
- `TKEY`: 元は PC4（チャネル 2）。本個体は PC4 の経路が通らない（2026-11-08-2237 の 6.1）ので、PD4（ch7、未配線）と PA2（ch0、10 kΩ＋1 µF の付いた負荷）にする。

## 2. SDK へのドライバの追加（タスク 2.1、2.2）

- `ch32v00X_opa.{h,c}` を EVT から `samples_ch32v006_wch/sdk/Peripheral/{inc,src}/` へ無改変でコピー（SHA-256 `96f297b4…`、`78bedd24…`）。`sdk/System/ch32v00X_conf.h` に `#include <ch32v00X_opa.h>` を追加、`PROVENANCE.md` に 2 行を追加。`tim`、`dma` は既存。
- 再 build（15 例）の `main.bin` の SHA-256 は 1.1 と**完全に一致**（実測、差分なし）。

## 3. サンプルの追加（タスク 3.1〜3.5）

`samples_ch32v006_wch/{usart2,opa,tim3,tkey}/`（`Makefile`、`main.c`）。いずれも `make build` が通る（警告は既存の `debug.c:287` の unused parameter のみ）。

| サンプル | 構成 | 出力 | FLASH／RAM |
|---|---|---|---|
| `usart2` | USART2 TX をリマップ 3 で PD2。`usart2 0123456789\r\n` を 200 ms ごとに送信、115200 8N1。USART1 に設定を 1 回出力 | PD2→GP14 | 7136 B／952 B |
| `opa` | PA2→OPA→PD4（PGA 4 倍、`-DOPA_GAIN=8` で 8 倍、変更時は `make clean`）。ADC で ch0（PA2）と ch7（PD4）を連続読みし、`opa gain=<g> in=<raw> out=<raw>` を 200 ms ごとに USART1 へ | USART1（PD5→GP9） | 7648 B／952 B |
| `tim3` | TIM3（分周なし、ATRLR=47999）の CC3 DMA 要求で DMA1 ch1 が BSHR に PC0 の set/reset を交互に書く。PC0 は 500 Hz（半周期 1 ms、周期 2 ms）。CPU は動かさない | PC0→GP5 | 7692 B／960 B |
| `tkey` | ADC の TKEY で ch7（PD4、未配線）と ch0（PA2、10 kΩ＋1 µF）を読み、`tkey pd4=<n> pa2=<n>` を 500 ms ごとに USART1 へ | USART1 | 7508 B／952 B |

- 3.5（build の確認、実測）: `nm` に `OPA_Init`/`OPA_Cmd`/`OPA_Unlock`（opa）、`GPIO_PinRemapConfig`/`USART_Init`（usart2）、`TIM_Cmd`/`TIM_DMACmd`/`DMA_Init`（tim3）、`ADC_TKeyCmd`/`ADC_BufferCmd`（tkey）が入る。逆アセンブルに、USART2 のベース `0x40004400`（`lui 0x40004`）、OPA の `0x40024000`（`lui 0x40024`）、TIM3 `0x40000800` と DMA1 `0x40020000`、`TKey1`（= ADC1、`0x40022400`）を読み書きする命令がある。**これは build とコードの確認であり、動作の確認ではない**。
- 各サンプルに `README.md`（出典、動作、EVT からの変更点、観測状態＝build のみ）を追加。

## 4. HIL 試験とホスト単体テスト（タスク 4.1〜4.3）、マトリクス（5.1）

- `tests/hil/wch/test_v006_only.py`（`test_wch_tim3`、`test_wch_usart2`、`test_wch_opa[gain4|gain8]`、`test_wch_tkey`）。`hil_device.name != "ch32v006"` では理由付きで skip（002 では実行しない）。実機の実行は未実施（この時点の DUT は CH32V002）。
  - `tim3`: PC0→GP5 を `EDGE_MEASURE` の繰り返し（`pwm_edge_survey`）で測り、500 Hz（`48 MHz/(47999+1)/2`）±3 %、duty 50 %（±20000 ppm）で判定。
  - `usart2`: PD2→GP14 を PIO の UART 受信（background の `CAPTURE_START UART 14 115200`）で 1.2 s 取り込み、固定文字列 `usart2 0123456789\r\n` が 2 回以上届くかを判定（change `extend-pico-fixture-measurement` の機能。同 change は実装済み）。
  - `opa`: `ADC_OBSERVE`（Pico が GP13 に 10 kHz PWM を出して PA2 の RC に印加）を刺激として使い、その間の DUT のログ（PD5→GP9）を background の UART 取り込みで受ける。`ADC_OBSERVE` 自身の報告の解析は本の形式（3 桁 hex）でないため `ERR TIMEOUT adc_report` で終わる想定で、それ以外の応答なら失敗にする。判定は `out/in` の中央値が利得（4 倍、8 倍）の窓に入るか。許容幅は仮の ±15 %（設計 Open Questions のとおり、**最初の実測と資料で決め、根拠を記録する**）。入力が低すぎる読み（in<150）と出力が満スケールの 90 % 超（飽和）の読みは判定から外し、飽和は別に記録する。duty は利得 4 が 10/20 %（判定）と 60 %（飽和の記録）、利得 8 が 10 %（判定）と 40 %（飽和の記録）。
  - `tkey`: `tkey pd4=<n> pa2=<n>` を取り込み、値を記録する（値の合否は付けない。ログが取れなければ失敗）。
- ホスト側の判定は `ch32hil/v006_only.py`（`tim3_expected_hz`、`parse_opa`、`judge_opa`、`saturation_record`、`parse_tkey`、`tkey_record`、`judge_usart2`）。`tests/unit/test_v006_only.py`（6 件。比の窓、閾値の外の読みの扱い、利得の食い違い、TIM3 の期待周波数、TKEY が値で失敗しないこと、USART2 の文字列の回数とデータ欠落）。
- マトリクス（5.1）: `hil/matrix_ch32v006_wch.json` に `usart2`、`opa`、`tim3`、`tkey` の 4 行を、種別 `additional-not-in-book`、状態 `build-only` で追加（`hil_tests` は上の試験。実機で通るまで `hil-verified` にしない）。単体テストの前提「002 と 006 の WCH の行が同じ並び」を書籍由来の行に限るよう直し（`tests/unit/test_config_matrix.py`）、`wwdg` の追跡テストは 006 の WCH のみ 4 行の追加を許すようにした。`uv run pytest`（実機なし）: **404 passed、57 skipped**。

## 5. CH32V006 での実機試験（タスク 6.1〜6.3。DUT=CH32V006、ユーザー申告で差し替え済み）

- 書き込み前の確認（実測）: `./scripts/ch32fun.sh flash ch32v006` → `Part Type: 00-63-06-20`、識別領域の上位型番 0x006 の照合を通過、読み戻し一致。治具は `extend-pico-fixture-measurement` の UF2（`3fbbcdcc…`）、`uv run pytest --hil --hil-device ch32v006 --hil-framework wch tests/hil/wch/test_v006_only.py`（run dir `xprivate/runs/2026-11-09-1200-…`、`1215-…`、`1230-…`。書き込み・全量読み戻しは各試験の中で実行）。
- **試験の修正（試験側の誤り、サンプルの不具合ではない）**: 初回は 5 本中 4 本が失敗: (a) `tim3` と `opa` は `Run.phase()` にキーワード引数を渡して `TypeError`（`lambda` に修正）、(b) `tkey` は `UART_XFER` の受信数 96 が上限 32 を超えて `ERR INVALID uart_arguments`（background の UART 取り込みに変更）、(c) `opa` は `ADC_OBSERVE` が `ERR UART uart_errors=0x8`（Pico 側の UART の overrun。DUT のログが連続するため）で終わり、想定していた `TIMEOUT` ではなかった（PWM は全期間出ているので `TIMEOUT` か `UART` のどちらでも刺激としては成立、と判定条件を直した）。直した後の再実行で通った。

### 結果（実測）

| 試験 | 結果 | 値 |
|---|---|---|
| `test_wch_usart2` | PASSED | 1.2 s の取り込みで `usart2 0123456789\r\n` を 6 回（114 バイト）、overflow・frame error なし |
| `test_wch_tim3` | PASSED | 8 回の測定で平均周期 2013.7 µs（496.6 Hz、期待 500 Hz に対し −0.68 %）、duty 500 005〜500 026 ppm（8/8 が ±2 点内）。HSI の誤差と整合 |
| `test_wch_opa[gain4]` | PASSED | duty 10 %: 入力 ADC 356、出力 1401、out/in の中央値 3.924（3.861〜3.961、19 読み）。duty 20 %: 入力 763、出力 3040、3.986（3.950〜4.017）。duty 60 %: 19 読みすべて出力 4095（飽和、記録のみ） |
| `test_wch_opa[gain8]` | PASSED | duty 10 %: 入力 356、出力 2777、7.809（7.712〜7.94）。duty 40 %: 19 読みすべて 4095（飽和、記録のみ） |
| `test_wch_tkey` | PASSED（記録） | 5 読み: PD4（未配線）4086〜4087（中央値 4087）、PA2（10 kΩ＋1 µF）50〜52（中央値 51）。差 −4036。値の合否は付けていない |

- PGA の許容幅（設計の未決事項）: 実測の偏差は利得 4 で −1.5〜−0.4 %、利得 8 で −2.4 % で、いずれも約 2 % 以内。資料に利得の誤差の数値は見つけられなかったため、**窓は ±10 %（実測偏差の約 5 倍の余裕）に決めた**（仮の ±15 % から変更）。電圧は未校正で、比だけで判定。なお、offset の影響は入力が高い側（duty 20 %）のほうが比が 4 に近く、低入力で比が小さいのは偏りがあることを示すが、原因は未確認。
- 刺激について: Pico の PWM は `ADC_OBSERVE` のもの（10 kHz、duty 10〜90 %）を使い、DUT のログ（`opa gain=… in=… out=…`）は同時に background の UART 取り込みで受けた（change `extend-pico-fixture-measurement` の機能）。
- tkey: PD4（浮いたピン）が 4087 近くに張り付き、PA2（1 µF）は小さい値。TKEY の値は負荷（容量）が大きいほど小さく読まれる、というのがこの 1 台での観測。EVT のチャネル 2（PC4）では試していない（本個体は PC4 の経路が通らない）。タッチは模擬できない。

### マトリクスと文書（6.3、7.1、7.2）

- `hil/matrix_ch32v006_wch.json`: `usart2`、`opa`、`tim3` を `hil-verified`（evidence は本ログ）に更新。`tkey` は値に合否がない参考の観測なので `build-only` のままにし、note に観測値を追記。`uv run pytest`（実機なし）: **404 passed、57 skipped**。
- `okf/open-questions/ch32v00x-unverified.md`: C4 を「一部（実機で確認）」、U5 を「一部（TX のみ確認）」に更新し、対象外と必要なもの（CMP の資料の食い違い、TKEY のタッチ＝実物のパッド、USART2 の受信＝PD3 の配線、OPA のオフセット・ノイズ・帯域・差動、2 線の SDI・PB ポート＝TSSOP20 にピンなし）を記載。
- `okf/peripherals/ch32v006-port-differences.md`: 006 だけの機能の節（資料、ピン、実機の結果）を追加。各サンプルの README の「観測状態」も更新。

### 未確認・残件

- 1 台の CH32V006（個体）での 1 回ずつの結果。TKEY を hil-verified にしていない。USART2 の RX、OPA の差動・他の利得（16/32 倍）、TIM3 と TIM1 の連携は未試験。
- ログの時刻は、各節の記載（08:54 開始）と、スクリプトの時計・ユーザー側の時刻の記録に差があるかもしれない。厳密な時刻は run dir 名を参照。
