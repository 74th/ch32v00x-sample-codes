# Proposal

## Why

公式SDKの使い方をGUIなしで検証する基準環境が必要である。今回実装・実機確認を終えたCH32V003のCLIビルドと公式Delay版blinkを、後続作業の契約として記録する。

## What Changes

- 公式SDKの必要なファイルを出所・利用条件付きで維持し、WCH GCCでCLIビルドする。
- 公式Delay APIを使うPC0 blinkを固定minichlinkで書き込み、読み戻し照合・Pico観測する。
- build、flash、observeを分離し、結果と制限をログに残す。

## Capabilities

### New Capabilities

- `wch-sdk-sample-workflow`: 公式SDKを利用したCLIビルド、出所管理、段階別の実機検証。

### Modified Capabilities

なし。

## Impact

`samples_ch32v003_wch/`、`scripts/wch-sdk.py`、README、okf/log。既存WCH GCC 15.2.0を共用。固定ch32funは書き込み器としてのみ使用する。CH32V002移植・周辺サンプル展開は含めない。
