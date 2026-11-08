# Tasks

## 1. 準備と資料の照合

- [x] 1.1 `git status` と固定 ch32fun のコミットを確認し、作業ログ（`okf/log/`）を開始する。変更前に、002/006 の WCH SDK 全例・ch32fun 全例・Arduino 3 例を build して `.bin` の SHA-256 を記録する（成果物が変わらないことの確認用）。
- [x] 1.2 RM 第5章（WWDG_CTLR、WWDG_CFGR、WWDG_STATR、窓の判定、リセット条件）と公式 EVT の `EXAM/WWDG`、`ch32v00X_wwdg.{c,h}` を読み、002/006 の資料上の差がないこと、窓の下限（0x3F か 0x40 か）の記述の食い違いを記録する。
- [x] 1.3 固定 ch32fun のヘッダ（`ch32x00xhw.h` の `WWDG_TypeDef`、`RCC_WWDGEN`、`RCC_WWDGRSTF`、`WWDG_IRQn`）を確かめ、ch32fun 版に必要な定義がそろっていることを記録する。

## 2. WCH SDK への WWDG ドライバの追加

- [x] 2.1 公式 EVT の `ch32v00X_wwdg.{c,h}` を、`samples_ch32v002_wch/sdk/` と `samples_ch32v006_wch/sdk/` の `Peripheral/{inc,src}/` にコピーし、`PROVENANCE.md`（002/006 それぞれ）にコピー元・SHA-256・変更の有無を追記する。`sdk/System/ch32v00X_conf.h` にヘッダを加える。
- [x] 2.2 追加後、既存のサンプル全例を build し、`.bin` の SHA-256 が 1.1 と一致することを確認する（一致しないものは原因を調べる）。

## 3. サンプルの実装

- [x] 3.1 WCH SDK `wwdg`（`samples_ch32v002_wch/wwdg/`）を実装する。起動時にリセット要因（`WWDGRSTF`、`IWDGRSTF`）を UART に出してフラグを消し、有効化の前に待ちを入れ、`-DWWDG_MODE`（0 = 窓の内側、1 = 窓より早い、2 = フィードしない）の3動作を実装する。窓は 0x5F、分周は /8、5 ms ごとのループで `.` を出す（design の決定 2〜5）。出典（公式 EVT）と変更点を冒頭のコメントと README に書く。
- [x] 3.2 `samples_ch32v006_wch/wwdg/` に、002 と同じソースと Makefile で 006 向けを作る（既存の 002/006 のサンプルと同じ構成）。
- [x] 3.3 ch32fun `wwdg`（`samples_ch32v00x_ch32fun/wwdg/`）を、固定 ch32fun のレジスタ定義を使って 002/006 共通のソースとして実装する（design の決定 8）。002/006 の両方で build する。
- [x] 3.4 3つの WCH SDK・ch32fun のサンプルを、各 `-DWWDG_MODE` で build し、逆アセンブルで WWDG のレジスタへの書き込みが期待どおり（モードごとに異なる）であることを確認する。

## 4. 治具の確認とHILの作成

- [x] 4.1 実機で WWDG の挙動を診断する。有効化の前の待ちの長さを決めるため、WWDG を有効にした後でデバッガが接続できるか（書き込み、読み戻し、リセット）を、002 で確かめる。接続できない場合の復旧手順（電源の入れ直しと既知のサンプルの書き込み）を先に用意する。
- [x] 4.2 `tests/hil/wch/test_wwdg.py` と、ch32fun 用の試験を作る。各ビルド（`make_args`）を書き込み・読み戻し・リセットし、UART の取得から、窓の内側（ループが続き、起動メッセージが繰り返されない）、窓より早い（点が1個で `cause=WWDG`）、フィードしない（点が9個で `cause=WWDG`）を判定する。各試験の最後に既知のサンプルを書き込んで復旧を確認する。
- [x] 4.3 試験のホスト単体テスト（実機なし）を追加し、判定の許容幅が `-DWWDG_MODE` ごとの期待と矛盾しないことを確かめる。

## 5. マトリクスと単体テストの更新

- [x] 5.1 `ch32hil/matrix.py` の `CLASSES` に `additional-not-in-book` を加え、`book_sample` が null の行を許す。WCH のマトリクスの単体テスト（書籍の13例の1対1）を、「書籍の13例は1対1、追加の行は種別が `additional-not-in-book`」に分けて判定するように直す。
- [x] 5.2 `hil/matrix_ch32v002_wch.json`、`hil/matrix_ch32v006_wch.json`、`hil/matrix_ch32v002.json`、`hil/matrix_ch32v006.json`（ch32fun）に `wwdg` の行を、状態 `build-only` で追加する。`uv run pytest`（実機なし）が通ることを確認する。

## 6. 実機での確認

- [x] 6.1 CH32V002 で、WCH SDK `wwdg` の3つのビルドの HIL を実行する（DUT は 002 が装着されている状態で行う。違う場合はユーザーに差し替えを依頼する）。結果（リセット要因の表示、点の数、リセットの有無、復旧）を `okf/log/` に記録する。
- [x] 6.2 CH32V002 で、ch32fun `wwdg` の3つのビルドの HIL を実行し、結果を記録する。
- [x] 6.3 CH32V006 で、WCH SDK と ch32fun の `wwdg` の HIL を実行し、結果を 002 とは別に記録する（DUT の差し替えはユーザーが行う）。
- [x] 6.4 実機で通ったものだけ、マトリクスの状態を `hil-verified` に更新する。観測できなかったもの（EWI、時間の絶対精度、デバッグ中の動作）は未確認として残す。

## 7. 記録と仕上げ

- [x] 7.1 `okf/open-questions/ch32v00x-unverified.md` の W3（WWDG）の状態と根拠ログを更新し、Arduino の watchdog と省電力は対象外とした理由（Arduino API にない）を P4 と W3 に記載する。
- [x] 7.2 `okf/peripherals/ch32v00{2,6}-port-differences.md` に WWDG の節（資料の確認、実機の結果、RM の記述の不整合）を追加する。
- [x] 7.3 002/006 で、WWDG 以外の既存サンプルの build が変わらないこと（1.1 とのハッシュの一致）と、既存の HIL の状態が悪化していないことを確認し、`uv run pytest` が通ることを確認する。
