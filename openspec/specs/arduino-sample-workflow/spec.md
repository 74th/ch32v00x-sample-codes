# arduino-sample-workflow Specification

## Purpose

Arduino Core CH32 を使う CH32V00x 向けサンプルを、arduino-cli で再現可能にビルドし、固定 minichlink と Pico 治具で実機確認するための要件を定める。あわせて、公式 core の追従状況と CH32V002 への適用可否を証跡付きで判定する。

## Requirements

### Requirement: 固定されたArduinoビルド環境

ワークフローは、バージョンを固定した arduino-cli と、供給元・バージョンを固定した core を使い、利用者のホーム設定に依存しない構成で Arduino サンプルをビルドできなければならない（SHALL）。

#### Scenario: 記録された構成でビルドする
- **GIVEN** 記録された arduino-cli のバージョン、core の供給元 URL・バージョン、ボード設定（FQBN とメニュー値）が準備されている
- **WHEN** 記載された Arduino ビルドコマンドを実行する
- **THEN** 書き込み可能な成果物が生成され、使ったツールと core のバージョンが出力から特定できる

#### Scenario: ホームのArduino設定を使わない
- **GIVEN** 利用者のホームに別の Arduino 設定や core が存在する
- **WHEN** Arduino ビルドを実行する
- **THEN** リポジトリで指定した設定・データディレクトリだけが使われ、ホームの設定は読み書きされない

#### Scenario: 必要なツールやcoreが不足している
- **GIVEN** arduino-cli、指定された core、または同梱ツールチェーンが未導入である
- **WHEN** Arduino ビルドを開始する
- **THEN** 不足している依存関係が特定できる形で失敗し、別バージョンへ暗黙に置き換えない

### Requirement: 書籍手順の再現

ワークフローは、書籍第2章の Arduino IDE 手順（追加ボードマネージャ URL、core 導入、ボード選択、クロックと書き込み方法の設定、Blink、Serial 出力）を、GUI 操作なしのコマンドで再現できなければならない（SHALL）。

#### Scenario: 書籍のBlinkを再現する
- **GIVEN** 書籍が指定するサードパーティ core とボード設定（CH32V00x、48MHz Internal）がある
- **WHEN** 書籍の Blink（PC0）をコマンドでビルドし、書き込み、観測する
- **THEN** 書籍と同じ構成で生成した成果物の PC0 点滅が実機で観測され、IDE 操作とコマンドの対応が記録される

#### Scenario: IDE固有の挙動と区別する
- **GIVEN** 書籍に IDE の画面上の挙動（エラー表示の後の「Verified OK」など）が書かれている
- **WHEN** コマンドでの再現結果を記録する
- **THEN** コマンドで確かめた事項と、IDE 固有のため確かめていない事項が分けて記録される

### Requirement: core供給元の比較と追従判定

ワークフローは、同じスケッチと同じボード設定を複数の core 供給元でビルドした結果を比較し、公式配布パッケージが書籍時点のサードパーティ版に追従しているかを判定して記録しなければならない（SHALL）。

#### Scenario: 供給元ごとのビルド結果を比較する
- **GIVEN** サードパーティ配布、公式配布、公式リポジトリの特定 revision の core が識別できる
- **WHEN** book-code の Arduino Core CH32 用スケッチをそれぞれの core で CH32V003 向けにビルドする
- **THEN** スケッチと供給元の組ごとに、ビルドの成否、失敗理由、成果物サイズ、使った core のバージョンまたは revision が表として記録される

#### Scenario: 追従状況を判定する
- **GIVEN** 供給元ごとのビルド結果と core 間の差分調査がある
- **WHEN** 公式配布の追従状況を判定する
- **THEN** 「追従済み」「一部未追従」「未追従」のいずれかと根拠が記録され、ビルドだけの比較か実機観測まで含むかが明記される

#### Scenario: 公式リポジトリのrevisionを維持サンプルの依存にしない
- **GIVEN** 公式リポジトリの参照用 clone を比較に使った
- **WHEN** 維持する Arduino サンプルのビルド構成を定める
- **THEN** 維持サンプルは配布パッケージの固定バージョンだけに依存し、参照用 clone は比較の証跡としてのみ扱われる

### Requirement: Arduino成果物の書き込みと実機観測

Arduino サンプルの書き込みは固定 submodule の minichlink で行わなければならない（SHALL）。ビルド、書き込み、実行観測は段階ごとに分けて判定する。

#### Scenario: 固定minichlinkで書き込む
- **GIVEN** Arduino ビルドで書き込み可能な成果物が生成されている
- **WHEN** DUT へ書き込む
- **THEN** 固定 minichlink が対象型番の検出と書き込み完了を確認し、core 同梱の書き込みツールは使われない

#### Scenario: ビルドのみを動作確認としない
- **GIVEN** Arduino サンプルのビルドが成功している
- **WHEN** 書き込みまたは Pico による実機観測をまだしていない
- **THEN** そのサンプルは実機未確認として報告され、HIL 確認済みとして扱われない

#### Scenario: 固定配線で観測できる機能を判定する
- **GIVEN** 固定配線で観測できる Arduino サンプル（GPIO、Serial、ADC、PWM、I2C master、SPI master）がある
- **WHEN** 書き込み後に Pico 治具で観測する
- **THEN** 期待パターンとの一致・不一致が機械的に判定され、書き込み失敗と実行観測不一致が区別される

### Requirement: Arduinoサンプルの配置と検証マトリクス

維持する Arduino サンプルは `samples_<device>_arduino/<sample>/` に置かなければならない（SHALL）。book-code の各 Arduino スケッチの状態は、デバイスごとの検証マトリクスで追跡する。

#### Scenario: book-codeスケッチの状態を追跡する
- **GIVEN** book-code に Arduino Core CH32 用スケッチがある
- **WHEN** 検証マトリクスを確認する
- **THEN** 各スケッチについて、対応する維持サンプル、状態（compile のみ、HIL 確認済み、対象外など）、判定基準、根拠ログが分かる

#### Scenario: HIL確認済みには根拠を必須とする
- **WHEN** マトリクスで Arduino サンプルを HIL 確認済みとする
- **THEN** 根拠となる HIL テストと `okf/log/` の実測記録が参照され、欠けていれば単体テストで検出される

#### Scenario: 固定配線で観測できないスケッチ
- **GIVEN** 固定配線の外のピンや、実物の周辺機器（OLED の表示など）を必要とするスケッチがある
- **WHEN** マトリクスに載せる
- **THEN** 対象外または未自動化として理由とともに記録され、成功として扱われない

### Requirement: CH32V002への適用可否の判定

ワークフローは、Arduino Core CH32 で CH32V002F4P6 を扱えるかを、ボード定義、メモリ、ピン、クロック、書き込み、実機動作の観点で調査し、方針と根拠を記録しなければならない（SHALL）。CH32V003 での実機確認が終わるまで、CH32V002 の結果を確定としてはならない。

#### Scenario: CH32V002のボード定義を確認する
- **GIVEN** 比較対象の各 core 供給元がある
- **WHEN** CH32V002 を選べるボード定義やバリアントを調べる
- **THEN** 供給元ごとに CH32V002 の対応有無と、代わりに使える定義（CH32V006 など）の候補が記録される

#### Scenario: 別型番の定義を流用する
- **GIVEN** CH32V002 専用の定義がなく、別型番の定義を流用する
- **WHEN** CH32V002 向けにビルドして書き込む
- **THEN** 流用元との差（Flash・RAM サイズ、パッケージとピン、クロック、起動処理）とその根拠が記録され、書き込み前に識別領域で CH32V002 であることが確認される

#### Scenario: 実機観測なしに対応済みとしない
- **GIVEN** CH32V002 向けのビルドが成功している
- **WHEN** CH32V002 での書き込みや実機観測が未実施または失敗である
- **THEN** CH32V002 対応は未確認または不可として記録され、対応済みとは報告されない
