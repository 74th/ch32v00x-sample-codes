# Spec Delta

## MODIFIED Requirements

### Requirement: 固定ツールと対象識別

DUTのbuildはサンプルのフレームワークごとに記録された固定ツール（ch32funサンプルは `externals/ch32fun` の固定submodule、Arduinoサンプルはバージョン固定のarduino-cliと固定core）を使用しなければならない（SHALL）。flashはフレームワークによらず `externals/ch32fun` の固定minichlinkを使用し、検出出力と必要な識別領域を確認して、対象不明または誤識別の状態で成功としてはならない（SHALL NOT）。

#### Scenario: CH32V003へ書き込む
- **WHEN** CH32V003用成果物を書き込む
- **THEN** 固定minichlinkが対象型番と書き込み完了を確認し、選択したポリシーでreadback一致を確認できる

#### Scenario: CH32V002へ書き込む
- **WHEN** CH32V002用成果物を書き込む
- **THEN** 固定minichlinkの検出出力に加え、識別領域 `0x1ffff704` の型番部分が `0x002` であることを書き込み前に確認し、書き込み完了と選択したポリシーでのreadback一致を確認できる

#### Scenario: DUTを検出できない
- **WHEN** minichlinkが未接続、unknown chip、期待外型番、または曖昧な成功出力を返す
- **THEN** テストランナーはflash段階を失敗とし、観測段階へ進まない

#### Scenario: 識別領域が選択デバイスと一致しない
- **WHEN** 選択したデバイスと識別領域の型番が一致しない、または識別領域を読めない
- **THEN** テストランナーは書き込み前に失敗し、DUTのflashを変更しない

#### Scenario: Arduinoサンプルを書き込む
- **WHEN** Arduinoサンプルの成果物を書き込む
- **THEN** core同梱の書き込みツールではなく固定minichlinkが使われ、ch32funサンプルと同じ検出・識別・readbackの確認が行われる

## ADDED Requirements

### Requirement: HILサンプルのフレームワーク選択

テストランナーは、HILで使うサンプルのフレームワーク（ch32funまたはarduino）を利用者が明示選択でき、選択したフレームワークとデバイスのサンプル・マトリクスだけを使って実行しなければならない（SHALL）。

#### Scenario: フレームワークを指定しない
- **WHEN** 利用者がフレームワークを指定せずにHILを実行する
- **THEN** 従来どおりch32funサンプルが使われ、既存コマンドの結果は変わらない

#### Scenario: Arduinoを選択してHILを実行する
- **WHEN** 利用者がarduinoフレームワークを選択してHILを実行する
- **THEN** `samples_<device>_arduino/` のサンプルとArduino用マトリクスが使われ、結果に対象デバイスとフレームワークが記録される

#### Scenario: 選択したフレームワークにサンプルがない
- **WHEN** 選択したフレームワークとデバイスの組にテスト対象のサンプルがない、またはマトリクスで対象外とされている
- **THEN** そのテストは理由付きでskipされ、成功として報告されない

#### Scenario: 不明なフレームワークを指定する
- **WHEN** 利用者が対応していないフレームワーク名を指定する
- **THEN** テストランナーは実機操作の前に設定エラーとして停止する
