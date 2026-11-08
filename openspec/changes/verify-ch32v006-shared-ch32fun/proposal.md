# Proposal

## Why

CH32V006F8P6を入手したため（ユーザー申告）、CH32V002F4P6と同じ周辺機能HILを実施し、既存ch32funサンプルを共通ソースとして維持できるか確かめたい。同じコアという仮説だけで互換とせず、メモリ・ピン・周辺機能の差分と両実機の結果を根拠に共通化を判断する。

## What Changes

- CH32V006F8P6の資料・基板配線を照合し、既存12サンプルについて、アプリケーションソースと設定の再利用可否を記録する。
- `--hil-device ch32v006` と `scripts/ch32fun.sh ... ch32v006` を追加し、固定submoduleでのbuild、書き込み前の型番照合、readback、Picoによる観測を段階別に検証する。
- GPIOから開始し、UART、I2C、SPI、PWM、ADC、watchdog、sleep、helperへ展開する。CH32V006専用の設定・マトリクス・実験証跡を持ち、既存デバイスの確認済み状態を転記しない。
- **BREAKING（共通化条件成立時）**: `samples_ch32v002_ch32fun/` を `samples_ch32v00x_ch32fun/` に置き換える。CH32V002/CH32V006は同一のアプリケーションソースを使い、ターゲットとリンク設定・成果物は分離する。CH32V003の配置は維持する。ソースのデバイス別処理が必要と判明した場合は移行を保留し、差分と方針をレビュー可能な形で残す。
- READMEに共通化の意味、実際の対応型番、移行先と実行コマンド、デバイス別検証状態、未確認範囲を明記する。`00x`という名前を未検証デバイスの対応表明にしない。

## Capabilities

### New Capabilities

なし。

### Modified Capabilities

- `ch32fun-sample-workflow`: CH32V006の段階的検証、共通化の判定条件、CH32V002サンプル配置要件の条件付き変更、READMEと再現情報。
- `hil-test-runner`: CH32V006の明示選択と型番照合、共通ソースと実機識別の分離、ターゲットを切り替えたときの成果物混同防止。

## Impact

対象はch32funのみ。`samples_ch32v002_ch32fun/`、新しい共通配置、`ch32hil/devices.py`・`dut.py`、`scripts/ch32fun.sh`、`conftest.py`、HIL設定・マトリクス、関連単体テスト、README・hardware文書・OKFに影響する。固定 `externals/ch32fun` のrevisionとhelper本体は変更しない。他のexternalsは調査専用とする。

Arduino/WCH SDKのCH32V006対応、CH32V003ソースの統合、CH32V005/007・QFN32、新規周辺機能、電圧・周波数・消費電流の精度保証は対象外。提案段階ではサンプルの移動、READMEの実績更新、実機操作を行わない。
