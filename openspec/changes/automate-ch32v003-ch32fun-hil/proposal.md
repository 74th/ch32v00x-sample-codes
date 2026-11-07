# Proposal

## Why

CH32V003/ch32fun の実機確認は、Pico、WCH-LinkE、測定コマンドを人または Codex が順番に操作しており、同じ条件を一括で再実行できない。book-code で確認してきた周辺機能を継続的に検証するため、Pico を再利用可能な周辺機能治具へ拡張し、ビルドから観測までを明示的な HIL テストとして自動化する。

## What Changes

- `uv` で固定した Python 環境と `pytest` を導入し、実機不要の単体テストと、明示的に選択して実行する HIL テストを分離する。
- ADC は Pico の PWM 設定に対する機能的な変化を確認し、独立した電圧計による校正や精度評価は完了条件に含めない。
- Pico ファームウェアを、バージョン付きコマンドプロトコル、能力照会、GPIO 入出力・エッジ/周期測定、UART、I2C master/slave、SPI master/slave、PWM/パルス測定、ADC 試験用の電圧生成を段階的に追加できる治具へ拡張する。
- 各 Pico 機能をループバックまたは既知信号で先に自己検証してから、DUT のサンプル検証へ使用する。
- CH32V003/ch32fun サンプルについて、Pico 準備、DUT の build、flash、任意の readback、reset、治具設定、測定、判定、安全状態復帰を一つの pytest 実行で行い、段階別の失敗を報告する。
- 最初に既存 `blink_and_read` を end-to-end 化し、その後 GPIO 入力、UART、I2C、SPI、ADC、timer/PWM、watchdog/sleep の順に、Pico で機械判定可能なサンプルを追加する。
- `externals/ch32v003-book-code` は参照元に限定し、維持するコードは `samples_ch32v003_ch32fun/` に置き、ビルド・書き込みは固定 submodule `externals/ch32fun` のみを使う。
- ch32fun の `extralibs` に依存するサンプル（現行 book-code の ADC helper、I2C OLED/slave helper、SPI helper、NeoPixel 等）は今回の ch32fun 検証対象から除外する。Pico側の汎用能力は将来それらを検証できる形にしてよいが、完了条件には含めない。
- 実験・測定結果を日本時間の `okf/log/` に残し、ビルド、書き込み、実機観測を別の結果として記録する。
- 基本配線はSPI NSSのみAFIOでPC0へ移し、I2C、UART、SPI、PWMと2入力ADCを試験ごとの信号ジャンパ変更なしで使う。PA1のADC RCを低速ボタン刺激にも利用し、全GPIOの網羅は求めない。元のリマップ位置の検証は別途手動配線とする。
- 人間がPicoとCH32V003を安全に接続できる周辺機能別手順と概略回路図をMarkdownで提供する。KiCad回路図やSVG/PDF出力は今回の完了条件に含めない。

## Capabilities

### New Capabilities

- `pico-peripheral-fixture`: Pico 治具の安全なコマンドプロトコル、周辺機能スタブ・測定能力、自己検証、USB 再認識と安全状態を定義する。
- `hil-test-runner`: `uv`/`pytest` から実機試験の各段階を再現可能に実行し、選択、失敗分類、証跡、後始末を扱う。

### Modified Capabilities

- `ch32fun-sample-workflow`: CH32V003/ch32fun の基準検証を GPIO 一例から、`extralibs` 非依存の周辺機能サンプル群と自動 HIL ワークフローへ拡張する。

## Impact

- `hardware/pico-tester/`: Pico ファームウェア、PC 側プロトコルクライアント、ビルド・書き込み手順。
- `tests/unit/`, `tests/hil/`, `pyproject.toml`, `uv.lock`: テスト環境、実機マーカー、fixture、模擬テスト。
- `scripts/`: Pico と DUT の build/flash/readback/reset を段階別に呼び出す操作層。
- `samples_ch32v003_ch32fun/`: book-code を参照して維持する、標準 ch32fun のみを使う試験用サンプル。
- `hardware/wiring.md`, 配線案Markdown、`config/`, `okf/`: ピン対応、安全条件、試験構成、実測記録。
- 実機依存: Raspberry Pi Pico、WCH-LinkE、CH32V003F4P6。Pico の初回 BOOTSEL、物理配線、電圧確認は自動化外の前提として残る。
