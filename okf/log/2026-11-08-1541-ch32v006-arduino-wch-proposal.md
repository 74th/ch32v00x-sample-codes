# CH32V006 Arduino/WCH対応のchange提案

- 記録日時: 2026-11-08 15:41 JST。作業開始時刻は未記録。調査中に15:36 JST、検証後に15:41:13 JSTを取得した。
- 目的: CH32V006/ch32fun完了後のArduino Core CH32とWCH SDK実装・機能検証を計画する。
- ユーザー申告: 前changeは完了してアーカイブ作業中。精度・校正・電流・実表示・WS2812タイミング・PC5/PD7のRST設定・Arduino/WCHが未検証として報告された。今回はArduino/WCHへ進めたい。
- 条件: ソースと既存記録の読取調査のみ。実機接続・配線状態は確認せず、環境構築・ビルド・書き込み・測定は行っていない。固定ツール・SDKの更新も行っていない。

## 調査と実行コマンド

`cat`、`rg`、`sed` とPythonのJSON読取で、現行3仕様、device選択、Arduino/WCH make/CLI、公式配布core 1.0.6のboards.txt、HILの機種別期待値・既知失敗指定、マトリクス、WCH PROVENANCE/LD、CH32V006再現手順を確認した。

```sh
openspec context --json
openspec list --json
openspec list --specs
openspec show arduino-sample-workflow --type spec --json --no-scenarios
openspec show wch-sdk-sample-workflow --type spec --json --no-scenarios
openspec new change add-ch32v006-arduino-wch
openspec status --change add-ch32v006-arduino-wch --json
openspec instructions proposal --change add-ch32v006-arduino-wch --json
openspec instructions specs --change add-ch32v006-arduino-wch --json
openspec instructions design --change add-ch32v006-arduino-wch --json
openspec instructions tasks --change add-ch32v006-arduino-wch --json
openspec validate add-ch32v006-arduino-wch --strict
git diff --check
```

## 結果・判断

- 前changeは実際にはarchiveディレクトリにあり、現行仕様にも同期されていた。今回はそこへ変更していない。
- ソース観察: coreには006K8/62 KiB/8 KiB定義がある。002向けArduinoはメモリ・スタック/ヒープを縮小しているため006へそのまま持ち込まない。WCHも002用define/LDを006向けに明示変更する必要がある。
- ソース観察: HIL選択登録だけでなくADCのSCALE、NeoPixel条件、WCH LAYOUTと証跡保存の対応が必要。Arduino Wire slaveなど他機種の失敗を006へ自動適用しない。
- 提案: Arduino10スケッチ（通常8の実機機能確認＋Wire slave再現試験＋uart build）、WCH13例と基準blinkを対象とし、別々の配置・マトリクスで管理する。
- 生成物: proposal、3 capabilityのdelta spec、design、tasks。精度等の範囲外事項を保持し、必要な実機結果を完了条件とした。実装・READMEの実績表は変更していない。

## 失敗・修正・未確認

- SDK出所ファイルの探索で `sdk/SOURCES*` は存在せず、正しいルートの `PROVENANCE.md` を確認した。
- 初回strict検証は既存シナリオ名の欠落を検出した。未対応フレームワーク拒否のシナリオ名を保持して対象を未対応frameworkへ更新し、006/Arduino・WCHを許可する別シナリオを加えた。再検証はvalid。
- 新規サンプルのbuildと実機動作は未確認。F8P6の資料上の仮定やRST設定は本調査で解消していない。既存実測値は過去ログ由来で、今回の実測ではない。
- 非公開資料本文や変換物は成果物に含めていない。
