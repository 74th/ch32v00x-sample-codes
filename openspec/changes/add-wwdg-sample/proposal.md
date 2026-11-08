# Proposal

## Why

書籍のウォッチドッグの章（IWDG）と、このリポジトリの `watchdog` サンプルには、WWDG（ウィンドウウォッチドッグ）がありません。
WWDG は、IWDG にはない「早すぎるフィードでもリセットする」性質を持つ周辺機能です。CH32V002/CH32V006 のリファレンスマニュアル（V1.5）に第5章として載っており、書籍の `articles-ch32v00x` の「確認していないこと」にも「WWDG」として残っています（`okf/open-questions/ch32v00x-unverified.md` の W3）。

資料と手元のソースで、CH32V00x で使えることは確認済みです（`xprivate/` の RM 変換物、本文は転載しない）。

- RM 第5章（V00X 全品種共通）: 7 ビットのカウンタ、クロックは HCLK/4096 を WDGTB で 1/2/4/8 に分周、ウィンドウ値 W[6:0]、リセット条件は「カウンタが 0x40 を下回る」か「ウィンドウの外でフィードする」の2つ。早期割り込み（EWI）あり。
- ヘッダ: `WWDG_BASE = 0x40002C00`、`RCC_WWDGEN`、`RCC_WWDGRSTF`、`WWDG_IRQn = 16` は、WCH SDK の `ch32v00X.h` にも固定 ch32fun のヘッダにもある。
- 公式 EVT に `EXAM/WWDG` の例と `ch32v00X_wwdg.{c,h}` がある。ただし、このリポジトリが維持している 002/006 の SDK のコピー（`samples_ch32v00{2,6}_wch/sdk/`）には `ch32v00X_wwdg` は入っていない。

書籍にない内容なので、書籍の移植ではなく、リポジトリ独自のサンプルとして追加します。

## What Changes

**サンプルの追加（CH32V002/CH32V006）**

- WCH SDK: `wwdg`（公式 EVT の `EXAM/WWDG` を元にする）。`samples_ch32v002_wch/wwdg/` と `samples_ch32v006_wch/wwdg/`。
  - 002/006 の `sdk/` に `ch32v00X_wwdg.{c,h}` を EVT からコピーし、`PROVENANCE.md` にコピー元とハッシュを追記する。`ch32v00X_conf.h` の集約も更新する。
- ch32fun: `wwdg`（レジスタ直接操作）。`samples_ch32v00x_ch32fun/wwdg/`（002/006 共通のソース）。
- Arduino: 追加しない。WWDG は Arduino API にない（使うならレジスタか WCH SDK を呼ぶことになる）ため、ユーザー判断で対象外。Arduino の watchdog と省電力も同じ理由で対象外。

**サンプルの動作（案）**

- 起動時に、リセット要因（`RCC_RSTSCKR` の `WWDGRSTF`、`IWDGRSTF`）を読んで UART（PD5）に出し、フラグを消す。
- 動作は、ビルド時のオプション（`-DWWDG_MODE=...`）で3つに切り替える。
  - 窓内でフィード（既定）: 窓の中でフィードし続け、ループの回数を出し続ける。
  - 窓より早くフィード: カウンタが窓の値より大きいうちにフィードする（リセットされるはず）。
  - フィードしない: 時間切れ（0x40 を下回る）でリセットされる。
- 窓の値と分周は、HIL の許容幅（Pico の時計は未校正、1 µs 単位）で区別できる大きさにする（案: HCLK 48 MHz、分周 /8 で 1 カウントが約 683 µs、0x7F から 0x40 まで約 43 ms、窓の上限 0x5F で約 22 ms）。

**HIL（実機観測）**

- 3つのビルドを、Pico 治具で観測する。リセット要因は UART のテキスト（`cause=WWDG` など）で、連続動作かリセットの繰り返しかは起動メッセージの繰り返しで判定する。
- 追加する試験は、既存の `tests/hil/wch/test_watchdog.py` や `tests/hil/test_watchdog.py` と同じ流儀で、`make_args` によるビルドの切り替えを使う。
- 002 と 006 の両方で実行し、結果は各デバイスで別に記録する（結果を引き継がない）。

**確認の範囲（未確認として残すもの）**

- EWI（早期割り込み）、デバッグ中の動作、リセットまでの時間の絶対精度（HCLK を基準にするので内蔵 HSI の精度に依存する。校正はしない）、温度・電源電圧の影響。

## Capabilities

### New Capabilities

なし。

### Modified Capabilities

- `wch-sdk-sample-workflow`: 書籍にない周辺機能のサンプルを追加するときの扱い（書籍との1対1の対応表に含めない種別、SDK へのドライバの追加と出所の記録、ビルドで動作を切り替える HIL）を加える。
- `ch32fun-sample-workflow`: 書籍にない周辺機能（WWDG）の標準 ch32fun サンプルを、002/006 共通のソースとして追加する要件を加える。

## Impact

- 追加するコード
  - `samples_ch32v002_wch/wwdg/`、`samples_ch32v006_wch/wwdg/`、`samples_ch32v00x_ch32fun/wwdg/`
  - `samples_ch32v00{2,6}_wch/sdk/Peripheral/{inc,src}/ch32v00X_wwdg.*`、`sdk/System/ch32v00X_conf.h`、`PROVENANCE.md`
  - `tests/hil/wch/test_wwdg.py`、`tests/hil/test_wwdg.py`（または同等のもの）
- 更新するもの
  - `hil/matrix_ch32v002_wch.json`、`hil/matrix_ch32v006_wch.json`（WCH のマトリクスは書籍の13例と1対1に固定されているため、行の種別とホストの単体テストの前提を直す必要がある）、`hil/matrix_ch32v002.json`、`hil/matrix_ch32v006.json`（ch32fun）
  - `okf/open-questions/ch32v00x-unverified.md`（W3 の更新）、`okf/peripherals/ch32v00{2,6}-port-differences.md`
- 対象外
  - Arduino の watchdog と省電力。
  - 書籍原稿（`externals/ch32v003-book`）の更新（別作業）。
  - `externals/ch32fun` の変更。
  - CH32V003 版（WWDG は CH32V003 にもあるが、この change は 002/006 のみ）。
