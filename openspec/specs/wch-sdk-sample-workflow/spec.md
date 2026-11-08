# wch-sdk-sample-workflow Specification

## Purpose

WCH公式SDKのAPIと起動処理を使うサンプルをGUIなしでビルドし、固定書き込み器とPicoで実機確認するための要件を定める。SDKの出所と利用条件を保持し、ビルドと実行観測の証跡を分けて再現可能にする。

## Requirements

### Requirement: 公式SDKのCLIビルド

ワークフローは、記録されたWCH GCCと公式SDKの起動処理・リンカ設定を使い、CH32V003用成果物をGUIなしで生成できなければならない（SHALL）。

#### Scenario: 基準構成でビルドする
- **WHEN** 記載されたCLIコマンドで基準blinkをビルドする
- **THEN** ELF・BIN・HEXとメモリ使用量が得られ、ツールチェーン、CPU設定、SDK revisionを特定できる

### Requirement: 公式APIによるサンプル

サンプルは、検証対象の公式SDK APIを利用し、対応する公式機能がある場合に独自実装で置き換えてはならない（SHALL NOT）。

#### Scenario: 公式の遅延関数を利用する
- **WHEN** 基準blinkがクロック初期化後に開始する
- **THEN** 公式Delay初期化とミリ秒待機を利用してPC0の500 msごとの点滅を行う

### Requirement: SDKの配置と出所管理

維持コードはsamples_<device>_wch配下に置き、参照専用externalsの公式SDKをビルド依存にしてはならない（SHALL NOT）。必要なコピーにはrevision、元パス、ハッシュ、利用条件、変更箇所を記録しなければならない（SHALL）。

#### Scenario: SDKをコピーして維持する
- **WHEN** サンプルで公式SDKファイルを利用する
- **THEN** 元の著作権・利用条件が保持され、コピー元とローカル変更が追跡できる
- **AND** 対象ファイルにないApache-2.0条件を仮定しない

#### Scenario: デバイス別にSDKを維持する
- **WHEN** CH32V002向けサンプルをビルドする
- **THEN** CH32V002用の公式SDKと起動・メモリ設定を使い、CH32V003用ヘッダを型番だけ変えて流用しない

### Requirement: 段階別の書き込みと実機観測

build・flash・observeは独立して実行・判定できなければならない（SHALL）。書き込みは固定ch32funのminichlinkで期待型番と完了出力を確認し、成果物全量の読み戻しを照合しなければならない（SHALL）。

#### Scenario: 基準blinkを観測する
- **WHEN** CH32V003への書き込み・読み戻し後にPicoでPC0を10 ms間隔で300点観測する
- **THEN** 両端以外の完全なHigh/Low区間が4個以上かつ各400～600 msであることを判定し、治具をRESET_SAFEで終了する

#### Scenario: 実機観測がない
- **WHEN** buildまたはflashだけが完了している
- **THEN** 実機動作確認済みと報告せず、失敗・未確認段階と再現条件をokf/logに記録する

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

### Requirement: CH32V006公式SDKビルドと出所

ワークフローは `samples_ch32v006_wch/` にCH32V006用の公式SDK設定とCLIビルドを提供しなければならない（SHALL）。SDKは固定revision由来の必要ファイルをプロジェクト内に保持し、元の利用条件・ハッシュ・元パス・変更点を記録し、参照専用externalsをビルド依存にしてはならない（SHALL NOT）。

#### Scenario: CH32V006用設定を確認する
- **WHEN** CH32V006の基準blinkをビルドする
- **THEN** CH32V006定義、公式CH32V00X起動処理、48 MHz HSI構成、Flash 62 KiB / RAM 8 KiBと整合するスタック・ヒープが使われ、ELF・BIN・HEX・map・使用量を確認できる
- **AND** CH32V002の定義や16 KiB / 4 KiB設定、CH32V003 SDKを混入させない

#### Scenario: 全サンプルの依存元を検査する
- **WHEN** CH32V006のSDKサンプルを一括ビルドして検査する
- **THEN** 各成果物のメモリ配置と参照ソースがCH32V006用維持ディレクトリに対応し、別デバイスやexternalsのファイルがリンクされていれば失敗として報告する

### Requirement: CH32V006公式SDKサンプルの段階的検証

CH32V006F8P6向けに基準blinkと既存13例を実装し、基準GPIOのbuild・型番照合・flash・全量readback・Pico観測の成功後に周辺機能へ進まなければならない（SHALL）。各例は公式APIと書籍のDUTの役割・処理を保持し、CH32V006専用マトリクスで結果を管理しなければならない（SHALL）。

#### Scenario: 基準blinkから開始する
- **WHEN** CH32V006の基準blinkの実機試験を実行する
- **THEN** PC0の既知のHigh/Lowパターンを既存Pico判定で観測し、型番・全量readback・刺激/期待値・後始末・実測ログを記録する
- **AND** GPIOの実行観測が成功するまで周辺機能の検証完了を宣言しない

#### Scenario: 13例を追跡する
- **WHEN** CH32V006 WCHマトリクスを見る
- **THEN** blink_and_read、uart、adc、adc_dma、i2c_master、i2c_slave、spi_master、pwm、timer_blink、timer_dma、watchdog、sleep_wake、standby_wakeの移植差分・判定条件・状態・根拠を特定できる
- **AND** 他デバイスやch32funでの成功をCH32V006/WCHの確認済み状態として転用しない

#### Scenario: DMA・割り込み・低消費電力を確認する
- **WHEN** ADC DMA、Timer DMA、Timer割り込み、Watchdog、Sleep、Standbyを検証する
- **THEN** CH32V006のDMA割当・割り込み・起動設定と生成ELFの根拠に、Pico観測の機能結果を組み合わせて判定する
- **AND** 単純点滅への代替や、GPIO観測だけによる消費電流・精度の確認済み表明はしない

#### Scenario: 新しい不一致が発生する
- **WHEN** CH32V006で期待データ・復帰連番・波形パターンが一致しない
- **THEN** build・flash・観測のどこで失敗したかと再現条件を残し、他デバイスの既知事象として免除せず対象の検証タスクを未完了にする

#### Scenario: 観測できない信号・設定差を例外として扱う
- **WHEN** CH32V006のDUTで特定ピンが信号を出さない、または公式SDKの設定値と実測の挙動（例: IWDGのタイムアウト）が異なり、既存の判定をそのまま満たせない
- **THEN** 切り分けの結果と原因が未特定であることを記録し、ユーザーの判断を得たうえで、判定対象の限定（記録のみ）、代替ピン、保持時間の延長のいずれかを機種限定で適用する。判定できる項目（例: リセット要因フラグ）は維持する
- **AND** 元の条件は参考試験として別保存し、例外の内容と範囲をREADME・マトリクス・ログに明記する。他デバイスの判定は変えない
