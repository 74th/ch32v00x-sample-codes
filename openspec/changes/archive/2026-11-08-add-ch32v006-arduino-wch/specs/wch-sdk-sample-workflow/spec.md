# Spec Delta

## ADDED Requirements

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
