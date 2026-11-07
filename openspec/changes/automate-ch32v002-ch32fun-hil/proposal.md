# Proposal

## Why

CH32V003/ch32fun については、Pico 治具と `uv`/`pytest` による HIL で GPIO、GPIO 入力、UART、I2C master/slave、SPI、ADC、timer/PWM、watchdog、sleep の 11 テストを実機で通せるようになった（`automate-ch32v003-ch32fun-hil` でアーカイブ済み）。一方、CH32V002F4P6 は `blink_and_read` の手動 build・flash・readback・Pico 測定しか確認しておらず、HIL のホスト層・設定・テストも `CH32V003F4P6` に固定されている。CH32V003 基準が確立した今、同じ治具と固定配線を使って CH32V002 の周辺機能サンプルを自動検証できる状態にする。

## What Changes

- HIL 設定、DUT 操作層、pytest の HIL テストを、対象デバイス（`ch32v003` / `ch32v002`）を明示選択して同じテストを実行できる形にする。デバイス未指定時の既定は従来どおり CH32V003 とし、既存の CH32V003 実行コマンドを壊さない。
- CH32V002 の書き込み・readback・reset でも、固定 minichlink の検出出力に加えて識別領域 `0x1ffff704` の型番 `0x002` を HIL ホスト層で確認する（現在は `scripts/ch32fun.sh flash` にのみ実装）。
- CH32V003 マトリクスで `hil-verified` の 9 サンプルを、データシート（V1.7）・CH32V00X リファレンスマニュアル（V1.5）と照合したデバイス差分を記録したうえで `samples_ch32v002_ch32fun/<sample>/` へ移植する。対象は `blink_and_read`（既存）、`uart`、`i2c_master`、`i2c_slave`、`spi_master`、`timer_pwm`、`adc`、`watchdog`、`sleep_wake`。固定配線で HIL 対象外の `gpio_input` は移植せず、CH32V002 マトリクスでも同じ理由で対象外とする（GPIO 入力は `blink_and_read` の PA1 ボタン試験で確認）。
- CH32V003 と同じ固定配線（SPI NSS は PC0 リマップ）が CH32V002F4P6 でもピン機能・AFIO リマップ・電気条件として成立するかを確認し、成立しない機能は配線変更案または対象外理由を記録する。
- CH32V002 用の検証マトリクスを追加し、各サンプルの状態を「build-only」「HIL 確認済み」「未自動化」「対象外」で追跡する。
- Pico ファームウェアとプロトコル v2、各治具能力の自己検証結果は再利用する。CH32V002 の仕様差で新しい治具能力や許容範囲変更が必要になった場合だけ追加し、追加した能力は従来どおり先に自己検証する。
- 実験・測定を `okf/log/` に記録し、build、flash、readback、実行観測を別結果として扱う。

## Capabilities

### New Capabilities

（なし）

### Modified Capabilities

- `ch32fun-sample-workflow`: CH32V002 の検証範囲を GPIO 一例から、CH32V003 と同じ周辺機能サンプル群とデバイス別マトリクス・自動 HIL へ拡張する。
- `hil-test-runner`: HIL 実行の対象デバイスを明示選択でき、CH32V002 の識別領域確認を含むデバイス別の対象識別を行う。
- `pico-peripheral-fixture`: 人間向け配線資料と配線整合性確認の対象を CH32V003 から CH32V002F4P6 を含むデバイス別構成へ広げる。

## Impact

- `ch32hil/`（`config.py`、`dut.py`、`matrix.py`、`wiring.py` など）: デバイス選択、CH32V002 識別、設定・マトリクス検証。
- `hil/configs/`、`hil/matrix*.json`、`hil/README.md`: CH32V002 用設定とマトリクス、実行方法。
- `tests/hil/`、`tests/unit/`、`conftest.py`: デバイス指定オプション、パラメータ化、模擬テスト。
- `samples_ch32v002_ch32fun/`: 移植サンプル。
- `hardware/wiring.md`、`hardware/wiring-proposal.md`、`hardware/ch32v002-reproduction.md`: CH32V002 の配線・手順。
- `okf/log/`、必要に応じて `okf/peripherals/`: 実測記録と資料照合。
- 実機依存: Raspberry Pi Pico（既存治具）、WCH-LinkE（firmware 2.22 で CH32V002 識別を確認済み）、CH32V002F4P6 開発ボード（CH32V003 ボードとのピン互換はユーザー申告）。DUT の差し替え、配線確認、電圧確認は自動化外の前提。
