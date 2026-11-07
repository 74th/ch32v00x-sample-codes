# Spec Delta

## ADDED Requirements

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
- **WHEN** サンプルがch32funの `extralibs` に依存する
- **THEN** 今回の検証対象外として理由と状態を明示し、代替実装を暗黙に完了条件へ加えない

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
