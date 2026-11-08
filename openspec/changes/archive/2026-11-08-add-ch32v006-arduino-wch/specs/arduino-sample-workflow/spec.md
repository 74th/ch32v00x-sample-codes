# Spec Delta

## ADDED Requirements

### Requirement: CH32V006用Arduinoビルド設定

ワークフローは固定arduino-cli 1.5.1と公式配布core 1.0.6でCH32V006F8P6用プロファイルを提供しなければならない（SHALL）。別パッケージ用ボード定義の使用時は対象ピン・メモリ・起動設定を照合し、適用根拠を記録しなければならない（SHALL）。

#### Scenario: CH32V006向けにビルドする
- **WHEN** CH32V006用プロファイルでスケッチをビルドする
- **THEN** FQBN、core・ライブラリの固定版、クロック設定を特定でき、Flash 62 KiB / RAM 8 KiBと整合するELF・メモリ配置・スタック・ヒープを確認できる
- **AND** CH32V002用の16 KiB / 4 KiB制限やスタック・ヒープ上書きを使わない

#### Scenario: K8の定義をF8P6で使用する
- **WHEN** 配布coreのCH32V006K8定義を流用する
- **THEN** 使用するTSSOP20のピンと機能、初期化・クロック・メモリの適用根拠、F8P6について残る資料上の仮定を記録する
- **AND** K8/QFN32で実機確認したとは報告しない

### Requirement: CH32V006 Arduinoサンプルの網羅と状態

ワークフローは既存Arduino Core CH32用10スケッチに対応するサンプルを `samples_ch32v006_arduino/` に置き、全スケッチのbuild結果と独立したCH32V006用検証マトリクスを提供しなければならない（SHALL）。他デバイス・フレームワークの実機結果を確認済み状態に転用してはならない（SHALL NOT）。

#### Scenario: 移植対象を確認する
- **WHEN** CH32V006 Arduino対応表を見る
- **THEN** blink_and_read、adc、pwm、i2c_master、i2c_slave、i2c_slave_test_master、spi_master、i2c_oled、neopixel、uartの実装・ビルド・観測状態と根拠を特定できる

#### Scenario: 通常の実機試験を完了する
- **WHEN** 固定配線で観測できる通常対象8スケッチを検証する
- **THEN** GPIOから順に対象識別・flash・全量readback・Pico観測・後始末を実施し、実測ログを参照して確認済みにする
- **AND** 通常対象はblink_and_read、adc、pwmの通常パターン、i2c_master、i2c_slave_test_master、spi_master、i2c_oled、neopixelの機能確認とする

#### Scenario: UART複合スケッチを確認する
- **WHEN** uartのCO2センサー応答とOLED出力を、1コマンドずつしか実行できない治具で確認する
- **THEN** Picoのセンサー応答を先にDUTの受信バッファへ送り、直後にSSD1306模擬の取り込みを開始する順序で、元スケッチのままDUTが読んだ値を描いた画面を、スケッチ自体とライブラリからホストで描画した期待バッファと比較する
- **AND** 模擬の制約（取り込み中は別コマンドが待たされる、最後のI2C転送が次のSTARTまで確定しない等）に起因する比較対象外のページや条件を記録し、別の値を送ると失敗することを確認する。単純なSerial試験への置き換えで元スケッチを確認済みにしない

#### Scenario: 観測できないピンを代替する
- **WHEN** 固定配線の特定ピンが原因未特定のまま信号を出さず、必須の観測組を成立させられない
- **THEN** 切り分けの結果（他フレームワーク・GPIO出力での再現）を記録し、ユーザーの判断を得たうえで、同じ判定基準で代替ピンの組を必須とする
- **AND** 元の組は参考試験として別保存（XFAIL/XPASSとも）し、確認範囲が元の組を含まないことと原因が未特定であることをREADME・マトリクス・ログに明記する

### Requirement: CH32V006 Arduinoの既知制限と機能判定

Arduino検証はWire slave、PWM参考リマップ、NeoPixelのデバイス依存性を明示し、CH32V006で未観測の失敗を既知不具合として自動的に免除してはならない（SHALL NOT）。観測条件と失敗・XPASSを保存し、機能判定と規格適合を区別しなければならない（SHALL）。

#### Scenario: Wire slaveの不安定を調べる
- **WHEN** i2c_slaveで連続した書き込み・読み出しをタイムアウト付きで複数回実行する
- **THEN** 他デバイスのxfail指定をそのまま適用せず、CH32V006での成功・SCL固着・タイムアウト・復旧結果を記録する
- **AND** 不安定を再現した場合は独立した実測根拠で既知制限とし、HIL確認済みにはしない。再現しなかった場合も実行回数と条件を超える安定性を主張しない

#### Scenario: PWMの参考リマップを実行する
- **WHEN** 通常パターンと別にPATTERN 3のリマップを試す
- **THEN** 参考結果として成功・失敗と条件を残し、通常パターンの確認範囲と区別する

#### Scenario: NeoPixelの機能を判定する
- **WHEN** PicoでCH32V006の出力を取得する
- **THEN** 期待バイト列・フレーム長を判定し、パルス幅・バイト境界・取得条件を記録する
- **AND** 測定結果を見て許容差を無根拠に広げず、実LEDの発光やWS2812タイミング規格適合は未確認として残す
