# Proposal

## Why

CH32V006F8P6のch32fun実機検証と共通配置への移行が完了したため、残っているArduino Core CH32とWCH公式SDKへ展開する。CH32V002で整備したサンプルとPico治具を基準に、CH32V006のビルド・書き込み・実行観測をフレームワーク別の証跡で確認したい。

## What Changes

- `samples_ch32v006_arduino/` に既存10スケッチを移植する。固定arduino-cli 1.5.1／公式core 1.0.6とCH32V006のプロファイルを使い、CH32V002用Flash/RAM・スタック・ヒープ上書きを持ち込まない。
- `samples_ch32v006_wch/` に書籍対応13例と基準blinkを移植する。固定revision由来のCH32V00X SDKをプロジェクト内で維持し、CH32V006用の型番定義・起動・メモリ・クロック設定を明示する。
- `--hil-device ch32v006 --hil-framework arduino|wch` を有効化し、固定minichlinkによる型番照合・全量readbackの後、GPIOから通信、ADC/PWM、DMA・割り込み・低消費電力へ段階的に検証する。
- `hil/matrix_ch32v006_arduino.json` と `hil/matrix_ch32v006_wch.json` を追加する。他デバイスやch32funの成功を転記せず、各項目のbuild、flash、観測、既知制限、未実施と証跡を追跡する。
- ArduinoのWire slave不安定、PWMリマップ参考試験、UART＋OLED複合スケッチの観測制約を個別に扱う。通常の検証対象で新規失敗が残る場合は完了とせず、既知制限の再現は対象と根拠を明示する。
- README、各フレームワークの再現手順、OKFを更新し、機能確認と未検証の精度・実表示等を区別する。

## Capabilities

### New Capabilities

なし。

### Modified Capabilities

- `arduino-sample-workflow`: CH32V006F8P6用プロファイル、10スケッチの移植、独立マトリクスと実機判定。
- `wch-sdk-sample-workflow`: CH32V006用の公式SDK設定、基準blinkと13例のCLI/HIL検証・出所管理。
- `hil-test-runner`: CH32V006のArduino/WCH選択を許可し、フレームワーク別成果物・期待値・証跡を使用する。現行仕様の「CH32V006でarduino/wchを拒否」を置き換える。

## Impact

新規サンプル2系統、`ch32hil/devices.py`、`scripts/wch-sdk.py`、必要なビルド共通規則、Arduino/WCH HILと単体テスト、README・hardware文書・OKFが対象。ch32funの共通配置と既存CLIの既定値を維持する。Arduino/WCHまで `samples_ch32v00x_*` に統合する改名は行わない。

既存の固定ツール・core・SDK revisionを維持し、参照専用externalsは依存先にしない。精度評価（ADC、時間校正、消費電流）、実OLED/LED、WS2812規格適合、PC5/PD7のRST割当・オプションバイト変更、core本体修正・更新、新しい治具能力、CH32V005/007・別パッケージは範囲外。PC5等の実行上の競合は検出・記録し、設定を自動変更して回避しない。
