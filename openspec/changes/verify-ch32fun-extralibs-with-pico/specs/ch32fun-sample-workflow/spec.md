## MODIFIED Requirements

### Requirement: 維持するch32funサンプルの配置と依存

維持するCH32V003/ch32funサンプルは `samples_ch32v003_ch32fun/<sample>/` に置き、固定 `externals/ch32fun` の標準機能だけをbuild依存先にしなければならない（SHALL）。

#### Scenario: book-code由来サンプルを自動化する
- **WHEN** `externals/ch32v003-book-code` の実装を基に試験用サンプルを作る
- **THEN** 出典と変更点を記録したプロジェクト内サンプルを作成し、book-code内ch32funまたはPATH上のminichlinkへ依存しない

#### Scenario: extralibs依存サンプルを評価する
- **WHEN** サンプルがch32funの `extralibs` または `examples` 内のhelperに依存する
- **THEN** 「固定submoduleのhelper検証」で許可されたhelperでない限り、今回の検証対象外として理由と状態を明示し、代替実装を暗黙に完了条件へ加えない

### Requirement: CH32V002サンプルの配置と依存

維持するCH32V002/ch32funサンプルは `samples_ch32v002_ch32fun/<sample>/` に置き、固定 `externals/ch32fun` の標準機能だけをbuild依存先にしなければならない（SHALL）。

#### Scenario: CH32V002サンプルをビルドする
- **WHEN** CH32V002向けサンプルをビルドする
- **THEN** 固定submoduleの `ch32fun.mk` と標準ヘッダだけを使い、「固定submoduleのhelper検証」で許可されたhelper以外の `extralibs`、book-code内のch32fun、PATH上のツールに依存しない

## ADDED Requirements

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
