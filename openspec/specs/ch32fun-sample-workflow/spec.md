# ch32fun-sample-workflow Specification

## Purpose

CH32V003とch32funの既知構成を再現可能な基準として確立し、その基準からCH32V002向けサンプルを移植して実機動作まで検証するための要件を定義する。

## Requirements

### Requirement: CH32V003基準環境

ワークフローは、記録された依存関係とコマンドを使ってCH32V003向けch32fun GPIOサンプルをビルドできなければならない（SHALL）。

#### Scenario: CH32V003向けビルドに成功する
- **GIVEN** 必要な外部ソースとツールが準備されている
- **WHEN** 記載されたCH32V003向けビルドコマンドを実行する
- **THEN** CH32V003向けの書き込み可能な成果物が生成される

#### Scenario: 不足している依存関係を報告する
- **GIVEN** 必須ツールまたは外部ソースが不足している
- **WHEN** CH32V003向けビルドを開始する
- **THEN** 不足している依存関係が特定可能な形で失敗する

### Requirement: CH32V003実機検証

ワークフローは、CH32V003実機への書き込み結果とGPIOサンプルの実行結果を、ビルド結果とは別に確認できなければならない（SHALL）。

#### Scenario: CH32V003で既知のGPIO動作を観測する
- **GIVEN** 対象型番と配線が記録されたCH32V003実機が接続されている
- **WHEN** ビルド成果物を書き込み、サンプルを実行する
- **THEN** 仕様で定めたGPIOの既知パターンが実機で観測される
- **AND** 書き込み方法と観測方法が記録される

#### Scenario: 書き込み失敗と実行失敗を区別する
- **GIVEN** CH32V003向けビルド成果物が生成されている
- **WHEN** 書き込みまたは実行時の観測が失敗する
- **THEN** 書き込み未完了と書き込み後の期待動作不一致が異なる結果として報告される

### Requirement: 最小GPIO観測スタブ

ワークフローは、Raspberry Pi PicoでDUTのGPIOパターンを取得し、期待パターンとの一致または不一致を機械的に報告できなければならない（SHALL）。

#### Scenario: PicoでGPIOパターンを取得する
- **GIVEN** DUTとPicoが記録された安全な配線で接続されている
- **WHEN** DUTが基準GPIOパターンを出力する
- **THEN** Picoはサンプル列または測定結果をPCへ返す
- **AND** PC側で期待パターンとの一致を判定できる

#### Scenario: タイムアウト時に未確認とする
- **GIVEN** Picoから有効な測定結果が返らない
- **WHEN** 規定時間が経過する
- **THEN** 実機動作は未確認または失敗として報告される
- **AND** 成功として扱われない

### Requirement: CH32V002への段階的移植

CH32V002向け作業はCH32V003基準環境の実機検証後に行い、CH32V003から変更した設定とコードをデバイス差分として追跡できなければならない（SHALL）。

#### Scenario: 基準未確立の状態では移植完了としない
- **GIVEN** CH32V003の実機検証が完了していない
- **WHEN** CH32V002向け成果物の状態を評価する
- **THEN** CH32V002移植は完了として報告されない

#### Scenario: CH32V002向け変更を追跡する
- **GIVEN** CH32V003基準サンプルの検証が完了している
- **WHEN** GPIOサンプルをCH32V002F4P6向けへ移植する
- **THEN** ターゲット指定、メモリ、クロック、ピン、レジスタその他の変更点と根拠が記録される

### Requirement: CH32V002実機検証

ワークフローは、CH32V002F4P6向けサンプルのビルド、書き込み、GPIO動作をそれぞれ確認できなければならない（SHALL）。

#### Scenario: CH32V002で既知のGPIO動作を観測する
- **GIVEN** CH32V003基準から移植したCH32V002向けサンプルと、型番・配線が記録された実機がある
- **WHEN** CH32V002向け成果物をビルドして実機へ書き込む
- **THEN** 仕様で定めたGPIOの既知パターンが実機で観測される

#### Scenario: ビルドのみを動作確認としない
- **GIVEN** CH32V002向けビルドが成功している
- **WHEN** 書き込みまたは実機観測が未実施である
- **THEN** 結果は実機未確認として報告される

#### Scenario: CH32V003の結果をCH32V002の確認済みとしない
- **GIVEN** 同じサンプル名のCH32V003向けHILが成功している
- **WHEN** CH32V002向けサンプルの検証状態を評価する
- **THEN** CH32V002の実機でHILを実行して成功した場合だけ確認済みとし、CH32V003の結果を流用しない

### Requirement: 再現情報

各検証結果には、第三者または後続エージェントが同じ条件を再現するために必要な識別情報と手順を含めなければならない（SHALL）。

#### Scenario: 検証条件を記録する
- **WHEN** CH32V003またはCH32V002の検証結果を保存する
- **THEN** 対象型番、外部ソースのコミットID、ツールバージョン、ビルド・書き込みコマンド、配線、観測方法、結果が記録される

#### Scenario: 推定と実測を区別する
- **WHEN** データシート由来の情報と実機観測を記録する
- **THEN** 資料確認済み、実機確認済み、未確認の状態が区別される

### Requirement: CH32V003周辺機能検証マトリクス

ワークフローは、book-codeで手動確認対象となったCH32V003周辺機能について、サンプル、DUTの役割、Pico治具能力、配線、刺激、期待値、許容差、検証状態を追跡できなければならない（SHALL）。

#### Scenario: 周辺機能を自動HIL対象へ追加する
- **WHEN** GPIO入力、UART、I2C、SPI、ADC、timer/PWM、watchdogまたはsleepのサンプルを追加する
- **THEN** 対応する治具能力の先行検証、対象ピン、試験方向、合否条件がマトリクスに記録される

#### Scenario: 自動化できない手動確認が残る
- **WHEN** Pico治具で同等の観測または刺激をまだ再現できない
- **THEN** その項目は未自動化または未確認として残り、完了として扱われない

### Requirement: 維持するch32funサンプルの配置と依存

維持するCH32V003/ch32funサンプルは `samples_ch32v003_ch32fun/<sample>/` に置き、固定 `externals/ch32fun` の標準機能だけをbuild依存先にしなければならない（SHALL）。

#### Scenario: book-code由来サンプルを自動化する
- **WHEN** `externals/ch32v003-book-code` の実装を基に試験用サンプルを作る
- **THEN** 出典と変更点を記録したプロジェクト内サンプルを作成し、book-code内ch32funまたはPATH上のminichlinkへ依存しない

#### Scenario: extralibs依存サンプルを評価する
- **WHEN** サンプルがch32funの `extralibs` または `examples` 内のhelperに依存する
- **THEN** 「固定submoduleのhelper検証」で許可されたhelperでない限り、今回の検証対象外として理由と状態を明示し、代替実装を暗黙に完了条件へ加えない

### Requirement: 治具先行の段階的追加

各周辺機能のDUTサンプルは、必要なPico治具能力が独立した既知条件で確認された後にHIL合否判定へ使用されなければならない（SHALL）。

#### Scenario: 新しい周辺機能の作業を開始する
- **WHEN** 周辺機能を自動HILへ追加する
- **THEN** Pico側の実装、自己検証、配線レビューを先に完了し、その後にCH32V003サンプルのbuild、flash、観測を追加する

### Requirement: 周辺機能ごとの実機判定

対象となる各サンプルは、build成功、対象CH32V003へのflash成功、必要なreadback、Picoによる刺激・観測結果を別々に判定できなければならない（SHALL）。

#### Scenario: 周辺機能サンプルを確認済みにする
- **WHEN** 対象サンプルのHILテストを実行する
- **THEN** buildとflashに加え、仕様化した入出力または時間特性が実機で観測された場合だけ確認済みとする

#### Scenario: buildだけが成功する
- **WHEN** 成果物を生成できたがflashまたはPico観測を実施していない
- **THEN** build成功かつ実機未確認として報告する

### Requirement: CH32V002周辺機能検証マトリクス

ワークフローは、CH32V003で自動HIL対象とした周辺機能サンプルそれぞれについて、CH32V002F4P6向けのサンプル、使用ピン、必要な治具能力、合否条件、検証状態をCH32V003とは別に追跡しなければならない（SHALL）。

#### Scenario: CH32V003の対象サンプルを網羅する
- **WHEN** CH32V002のマトリクスを検証する
- **THEN** CH32V003マトリクスで自動HIL対象または未自動化とされた各サンプルに対応する行があり、移植済み、未移植、対象外のいずれかと理由が記録されている

#### Scenario: CH32V002で成立しない周辺機能がある
- **WHEN** 資料照合または実機で、CH32V002ではCH32V003と同じ機能・ピン・リマップを使えないと判明する
- **THEN** その項目は根拠付きで対象外または配線変更が必要として記録され、完了として扱われない

### Requirement: CH32V002サンプルのデバイス差分記録

CH32V002向けに移植した各サンプルは、CH32V003版からのターゲット指定、クロック、メモリ、ピン機能、AFIOリマップ、レジスタ、期待値の変更点と資料上の根拠を記録しなければならない（SHALL）。

#### Scenario: 周辺機能サンプルを移植する
- **WHEN** `samples_ch32v003_ch32fun/<sample>/` を基に `samples_ch32v002_ch32fun/<sample>/` を作成する
- **THEN** 変更点ごとにデータシートまたはリファレンスマニュアルの版とページ、あるいは実測ログへの参照が記録され、資料確認済み・実機確認済み・未確認が区別される

#### Scenario: 変更不要と判断する
- **WHEN** CH32V003版のコードをCH32V002向けに変更せずに使う
- **THEN** 変更不要と判断した根拠が記録され、無根拠な互換性の仮定として扱われない

### Requirement: CH32V002サンプルの配置と依存

維持するCH32V002/ch32funサンプルは `samples_ch32v002_ch32fun/<sample>/` に置き、固定 `externals/ch32fun` の標準機能だけをbuild依存先にしなければならない（SHALL）。

#### Scenario: CH32V002サンプルをビルドする
- **WHEN** CH32V002向けサンプルをビルドする
- **THEN** 固定submoduleの `ch32fun.mk` と標準ヘッダだけを使い、「固定submoduleのhelper検証」で許可されたhelper以外の `extralibs`、book-code内のch32fun、PATH上のツールに依存しない

### Requirement: 固定submoduleのhelper検証

helper検証用と明示したサンプルは、固定 `externals/ch32fun` 内の指定helper（`extralibs/ssd1306_i2c.h`、`extralibs/ssd1306.h`、`extralibs/ws2812b_dma_spi_led_driver.h`、`examples/i2c_slave/i2c_slave.h`）を変更せずにinclude依存してよい（SHALL）。サンプルはhelperの出典パス、submodule revision、上書きした設定を記録しなければならない。

#### Scenario: helperを使うサンプルをビルドする
- **WHEN** helper検証サンプルをビルドする
- **THEN** 固定submodule内のhelperを直接参照し、helperのコピー、book-code内のch32fun、PATH上のツールを使わない

#### Scenario: helperの設定を変えて検証する
- **WHEN** helperの既定設定（I2Cクロック、LED数、色順など）を変えて試験する
- **THEN** 変更した設定値と理由が記録され、既定設定で未確認の項目は未確認として残る

### Requirement: helper検証の判定対象

helper検証サンプルの確認済み判定は、Pico治具が観測した送信内容がDUTの意図した内容と一致した範囲に限らなければならない（SHALL）。実デバイスでの表示・発光、電気的タイミングの規格適合は確認済みに含めない。

#### Scenario: OLED helperを確認済みにする
- **WHEN** SSD1306 helperサンプルのHILを実行する
- **THEN** Picoが再構成したフレームバッファが、同じ描画内容からホストで生成した期待フレームバッファと一致した場合だけ確認済みとし、実OLEDでの表示は未確認として記録される

#### Scenario: NeoPixel helperを確認済みにする
- **WHEN** WS2812 helperサンプルのHILを実行する
- **THEN** Picoがデコードした色バイト列が期待列と一致した場合だけ確認済みとし、実LEDでの発光とWS2812仕様上のタイミング適合は未確認として記録される

#### Scenario: I2C slave helperを確認済みにする
- **WHEN** `i2c_slave.h` サンプルのHILを実行する
- **THEN** Pico masterからのレジスタ書き込み、読み出し値、書き込み・読み出しコールバックの発火がそれぞれ観測された場合だけ確認済みとする

### Requirement: helper検証のマトリクス追跡

検証マトリクスは、helper依存のbook-codeサンプルについて、対応する検証サンプル、使用helper、必要な治具能力、合否条件、検証状態をデバイスごとに追跡しなければならない（SHALL）。

#### Scenario: helper依存サンプルを追跡対象へ移す
- **WHEN** `extralibs-excluded` だったbook-codeサンプルにhelper検証サンプルを用意する
- **THEN** マトリクスの行が検証サンプルと治具能力を参照し、状態は実機HILの証跡があるときだけ確認済みになる

#### Scenario: CH32V002で未移植のhelper検証がある
- **WHEN** CH32V003でhelper検証が確認済みで、CH32V002版が未作成または未実行である
- **THEN** CH32V002マトリクスに未移植または未確認の行と理由が記録され、CH32V003の結果をCH32V002の確認済みとしない
