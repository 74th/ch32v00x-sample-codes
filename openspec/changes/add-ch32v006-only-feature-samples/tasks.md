# Tasks

## 1. 準備と資料の照合

- [ ] 1.1 `git status` を確認し、作業ログ（`okf/log/`）を開始する。006 の WCH SDK の全例を build して `.bin` の SHA-256 を記録する（SDK の追加で既存の成果物が変わらないことの確認用）。
- [ ] 1.2 RM の USART2（第14章）、OPA（第17章、内部チャネルと ADC のチャネル番号）、SLTM（第13章、TIM3 の DMA 要求の割当）、TKEY（第10章）と、006 のデータシートのピン表を読み、TSSOP20 のピン（USART2 のリマップ3の PD2/PD3、OPA の P0/N0/OUT0）と使い方を記録する。CMP の資料の食い違い（DS と RM）も記録する。
- [ ] 1.3 公式 EVT の `EXAM/USART`、`EXAM/OPA/OPA_PGA`、`EXAM/TIM/SLTIM_DMA`、`EXAM/TOUCHKEY/TKEY` を読み、サンプルの元にする部分と変える部分を決めて記録する。

## 2. SDK へのドライバの追加

- [ ] 2.1 `ch32v00X_opa.{c,h}` など必要なドライバを EVT から `samples_ch32v006_wch/sdk/` にコピーし、`PROVENANCE.md` と `ch32v00X_conf.h` を更新する。
- [ ] 2.2 006 の WCH SDK の全例を build し、`.bin` の SHA-256 が 1.1 と一致することを確かめる。

## 3. サンプルの実装

- [ ] 3.1 `samples_ch32v006_wch/usart2/`: USART2 の TX をリマップ3で PD2 に出し、既知の文字列を一定間隔で送る。USART1（PD5）に設定を出す。出典と変更点を README に書く。
- [ ] 3.2 `samples_ch32v006_wch/opa/`: OPA を単端の PGA（`-D` で 4 倍・8 倍を切り替え）にし、PA2 の入力と OPA の出力を ADC で読んで USART1 に出す。
- [ ] 3.3 `samples_ch32v006_wch/tim3/`: TIM3 の DMA 要求で PC0 を反転する（使えなければ CPU で TIM3 の CNT を見て反転し、その旨を記録する）。
- [ ] 3.4 `samples_ch32v006_wch/tkey/`: 負荷の違う2つのチャネルの TKEY の値を USART1 に出す。
- [ ] 3.5 4 つのサンプルを build し、map と逆アセンブルで、使う周辺機能のレジスタへの設定が含まれることを確かめる。

## 4. HIL 試験

- [ ] 4.1 `tests/hil/wch/` に、`opa`（Pico が PA2 を既知のレベルにし、比を判定）、`tim3`（PC0 の周期を判定）、`tkey`（値の差を記録）の試験を作る。各試験は 006 でだけ実行する（002 では skip）。
- [ ] 4.2 `usart2` の試験を作る。change `extend-pico-fixture-measurement` の UART 受信（GP14）が使えるときは、受けた文字列を判定する。使えないときは、理由を付けて skip する。
- [ ] 4.3 試験のホスト単体テスト（比と周期の期待値の計算、許容範囲）を追加する。

## 5. マトリクスと単体テスト

- [ ] 5.1 `hil/matrix_ch32v006_wch.json` に 4 つの行を、書籍由来でない種別（`additional-not-in-book`、`add-wwdg-sample` と共通）で、状態 `build-only` として追加する。マトリクスの単体テストの前提（002 と 006 の WCH の行が同じ並び）を、書籍由来の行に限るように直す。`uv run pytest` が通ることを確かめる。

## 6. 実機での確認

- [ ] 6.1 DUT を CH32V006 にして（差し替えはユーザーが行う）、`opa`、`tim3`、`tkey` の試験を実行し、測った値（比、周期、TKEY の値）を記録する。PGA の許容範囲は、最初の実測と資料を見て決め、根拠を記録する。
- [ ] 6.2 治具の UART 受信が使えるようになっていれば、`usart2` の試験を実行して記録する。使えなければ保留と記録する。
- [ ] 6.3 実機で通ったものだけ、マトリクスの状態を `hil-verified` に更新する。

## 7. 記録

- [ ] 7.1 `okf/open-questions/ch32v00x-unverified.md` の C4、U5 を更新し、CMP（資料の食い違い）、TKEY のタッチ、USART2 の受信、2 線の SDI など対象外としたものを、理由と必要なものとともに記載する。
- [ ] 7.2 `okf/peripherals/ch32v006-port-differences.md` に、006 だけの機能の節（資料、ピン、実機の結果）を追加する。
