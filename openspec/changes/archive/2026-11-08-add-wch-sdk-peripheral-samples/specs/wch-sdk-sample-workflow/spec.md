# Spec Delta

## MODIFIED Requirements

### Requirement: SDKの配置と出所管理

維持コードはsamples_<device>_wch配下に置き、参照専用externalsの公式SDKをビルド依存にしてはならない（SHALL NOT）。必要なコピーにはrevision、元パス、ハッシュ、利用条件、変更箇所を記録しなければならない（SHALL）。

#### Scenario: SDKをコピーして維持する
- **WHEN** サンプルで公式SDKファイルを利用する
- **THEN** 元の著作権・利用条件が保持され、コピー元とローカル変更が追跡できる
- **AND** 対象ファイルにないApache-2.0条件を仮定しない

#### Scenario: デバイス別にSDKを維持する
- **WHEN** CH32V002向けサンプルをビルドする
- **THEN** CH32V002用の公式SDKと起動・メモリ設定を使い、CH32V003用ヘッダを型番だけ変えて流用しない

## ADDED Requirements

### Requirement: 書籍の公式SDKサンプルの網羅性

ワークフローはbook-codeの全13個のwch_sdk例に対応する公式APIサンプルと対応表を提供しなければならない（SHALL）。対象はGPIO入出力、UART、ADC、ADC DMA、I2C master/slave、SPI master、PWM、Timer割り込み、Timer DMA、Watchdog、Sleep、Standbyとする。

#### Scenario: サンプルごとの対応を確認する
- **WHEN** 対応表を見る
- **THEN** 各書籍例の維持パス、公式API、ピン変更、期待動作、build・flash・観測の状態、制限と根拠ログを特定できる

### Requirement: 周辺機能の意味を保持する

サンプルは書籍の周辺機能・DUTの役割・データ処理を保持しなければならない（SHALL）。治具向けのピンや観測方法の変更は説明し、DMA・割り込み・低消費電力をポーリングや単純点滅で代替してはならない（SHALL NOT）。

#### Scenario: 通信例を検証する
- **WHEN** UART、I2C、SPIのサンプルを観測する
- **THEN** 既知データを使ったコマンド・応答とデータ変換を照合し、単なるバイト送受信試験で書籍相当全体の確認済みとはしない

#### Scenario: DMAと低消費電力を検証する
- **WHEN** ADC DMA、Timer DMA、Watchdog、Sleep、Standbyを評価する
- **THEN** 各機能の実際の設定・使用と観測根拠を記録し、GPIOが点滅することだけで内部動作や消費電力を確認したとはしない

### Requirement: WCHフレームワークのHILと状態管理

HILは明示選択したWCHサンプルを固定書き込み器で検証できなければならない（SHALL）。既存フレームワークの既定挙動を維持し、デバイス別マトリクスに失敗・未実施も記録しなければならない（SHALL）。

#### Scenario: 実機確認を記録する
- **WHEN** WCHサンプルのHILを実行する
- **THEN** 型番検出、全量読み戻し、Pico能力・刺激・期待値・許容差、後始末、実測ログが別段階として残る

#### Scenario: 治具が不足する
- **WHEN** 必要なピンや周辺機器を既存治具で観測できない
- **THEN** ビルド可能な実装を残し、未観測理由と必要な追加条件を記録する。HIL成功扱いにはしない

### Requirement: CH32V002への段階的展開

CH32V003の基準を先に確立し、各サンプルをCH32V002専用SDKで移植しなければならない（SHALL）。メモリ・クロック・ピン・ADC等の差分を記録し、対象サンプルのCH32V003観測前にCH32V002の実機検証完了を宣言してはならない（SHALL NOT）。

#### Scenario: CH32V002に書き込む
- **WHEN** CH32V002の成果物をflashする
- **THEN** Flash 16 KB/RAM 4 KBの設定を使い、識別領域0x1ffff704で型番を検証してから書き込み・読み戻しを行う

#### Scenario: デバイスが手元にない
- **WHEN** 移植コードをビルドできても対象実機で観測できない
- **THEN** build-onlyとして記録し、実機確認タスクは未完了のままにする
