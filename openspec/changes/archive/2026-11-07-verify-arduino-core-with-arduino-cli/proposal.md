# Proposal

## Why

書籍 ch32v003-book 第2章は Arduino IDE 2.x を前提にしており、2025年3月時点では公式 openwch/arduino_core_ch32 のボードマネージャ配布が公式リポジトリに取り込まれた PR に追いついていなかった。そのため、サードパーティ（robinjanssens/WCH32V_board_manager_files）のパッケージを使うよう案内している。公式リポジトリはその後も更新されている（参照用 clone `externals/arduino_core_ch32` の HEAD は d62c6b1、2026-11-03）。公式の配布パッケージがサードパーティ版に追いついたか、そして CH32V002（公式 core では `CH32VM00X` 系）を公式 core で扱えるかは、まだ確かめていない。arduino-cli を使えば IDE の GUI 操作をコマンドに置き換えられるので、ビルド・書き込み・実機観測をこのリポジトリの既存 HIL（固定 minichlink、Pico 治具）に載せて機械判定できる。

## What Changes

- 書籍 2.1 節の IDE 操作（追加ボードマネージャ URL、core のインストール、ボード「CH32V00x」、Clock 48MHz Internal、Upload WCH-SWD）を、arduino-cli のコマンドで再現する手順として用意する。arduino-cli 本体と core のバージョンを固定し、リポジトリ内の設定で閉じた環境にする。
- 次の3つの core 供給元で、同じスケッチを CH32V003 向けにコンパイルして比較する。
  - 書籍が使うサードパーティのパッケージ
  - 公式のボードマネージャ配布パッケージ
  - 公式リポジトリの HEAD（調査専用）

  あわせて、書籍が「サードパーティ版でないと使えない」とした機能が公式版で使えるかを、book-code の Arduino Core CH32 用スケッチ10本の compile 結果と差分から判定し、比較表に記録する。
- 書き込みは arduino-cli の upload（WCH 版 OpenOCD）を使わない。生成した `.bin` を固定 submodule の minichlink で書き込み、Pico 治具で実行を観測する。対象は固定配線で観測できる blink_and_read、Serial（UART）、ADC、PWM、I2C master、SPI master から始める。
- 維持する Arduino サンプルを `samples_<device>_arduino/<sample>/` に置き、HIL 検証マトリクスで状態（compile のみ、HIL 確認済み、対象外など）を追跡する。
- CH32V002 の扱いを調査する。公式 core の `CH32VM00X` には CH32V006K8 の variant しかない。V002（CH32V002F4P6）を選べるのか、V006 の定義を流用したときのメモリ・ピン・クロックの差、書き込みと実機動作の可否を確認し、取れる方針を判定して記録する。CH32V003 の実機確認が終わるまで、CH32V002 の結果は確定扱いにしない。
- HIL ランナーの「build は ch32fun に固定」という要件を、サンプルのフレームワークごとに固定ツールを記録する形に改める。書き込みは引き続き固定 minichlink に限る。

## Capabilities

### New Capabilities

- `arduino-sample-workflow`: arduino-cli による Arduino Core CH32 サンプルの再現可能なビルドを定める。ほかに、core 供給元の比較と追従状況の判定、固定 minichlink での書き込みと実機観測、Arduino サンプルの配置と検証マトリクス、CH32V002 への適用可否の調査と記録を扱う。

### Modified Capabilities

- `hil-test-runner`: 「固定ツールと対象識別」の build に関する固定対象を、ch32fun に限らずサンプルのフレームワークごとに記録した固定ツールへ広げる（flash は固定 minichlink のまま）。HIL でサンプルのフレームワーク（ch32fun または arduino）を選ぶ要件を追加する。

## Impact

- 新規ツール依存として arduino-cli（バージョン固定）を追加し、`riscv-wch-gcc` などの core 同梱ツールチェーンも加わる。導入物はリポジトリ内の gitignore 対象ディレクトリに置き、ホームの `~/.arduino15` は使わない。
- スクリプト：`scripts/arduino.sh` を新設する（setup、compile、core の切り替え）。
- サンプル：`samples_ch32v003_arduino/` を新設する。調査で方針が決まれば `samples_ch32v002_arduino/` も作る。
- HIL：`ch32hil/devices.py`（サンプル位置のフレームワーク対応）、`conftest.py`、`tests/hil/` の Arduino 用テスト、`hil/` の Arduino 用マトリクス、`tests/unit/` を変更・追加する。
- 資料：`README.md`、`hil/README.md`、`okf/log/` の比較・実測記録。
- `externals/arduino_core_ch32` と `externals/ch32v003-book-code` は参照・比較用に使うだけで、維持するサンプルの依存先にしない。Pico 治具の firmware と固定配線は変えない。
