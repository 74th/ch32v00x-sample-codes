# Proposal

## Why

公式SDKのCLI基準blinkは実機確認済みだが、書籍の周辺機能例はまだ維持サンプルになっていない。公式SDKの使い方を周辺機能ごとに検証し、CH32V003を基準にCH32V002でも再現できる状態へ進める。

## What Changes

- book-codeの全13個の`*-wch_sdk`例に対応する公式APIベースのサンプルを追加する。
- CLIのサンプル選択、SDK共通ビルド設定、WCHフレームワークのHIL・検証マトリクスを整備する。
- CH32V003を先に検証し、その後CH32V002専用SDKで段階的に移植する。
- DMA、割り込み、低消費電力も対象とし、固定治具の制約・未観測・既知不具合を個別に残す。

## Capabilities

### New Capabilities

なし。

### Modified Capabilities

- `wch-sdk-sample-workflow`: 周辺サンプルの網羅性、段階別HIL、デバイス別の移植・検証状態を追加する。

## Impact

`samples_ch32v003_wch/`、新規`samples_ch32v002_wch/`、`scripts/wch-sdk.py`、`ch32hil/devices.py`等のフレームワーク選択、`conftest.py`、`tests/hil/wch/`、`hil/matrix*_wch.json`、READMEと作業ログ。
既存ch32fun/Arduinoの既定選択・判定は維持する。Pico firmwareは既存能力を優先し、不足がある場合は該当サンプルの観測制限を明示する。本changeでは新規PicoプロトコルやOLED/NeoPixel用の独自SDK実装は要求しない。
