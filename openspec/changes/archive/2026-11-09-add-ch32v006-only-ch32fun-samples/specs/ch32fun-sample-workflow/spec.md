## ADDED Requirements

### Requirement: 片方のデバイスだけの周辺機能のch32funサンプル

CH32V006 だけにある周辺機能の ch32fun サンプルを共通配置に置く場合は、固定 `externals/ch32fun` のヘッダとレジスタ操作だけで書き、固定 ch32fun を変更してはならない（SHALL NOT）。その周辺機能を持たないデバイス（CH32V002）を指定した build は、理由を示して失敗しなければならない（SHALL）。固定 ch32fun に不足する定義を補う場合は、その内容と根拠（リファレンスマニュアルの章）をサンプルに記録しなければならない（SHALL）。

#### Scenario: CH32V006向けにbuildする
- **WHEN** `usart2`、`tim3`、`opa`、`tkey` を `TARGET_MCU=CH32V006` で build する
- **THEN** build は成功し、使う周辺機能のレジスタへの書き込みが成果物に含まれる

#### Scenario: CH32V002向けにbuildする
- **WHEN** 同じサンプルを `TARGET_MCU=CH32V002` で build する
- **THEN** CH32V002 にその周辺機能がないことを示すエラーで build が止まり、成果物は作られない

### Requirement: WCH SDK版と同じ判定での実機確認

CH32V006 だけの周辺機能の ch32fun サンプルは、WCH SDK 版と同じ観測方法と判定（USART2 は受信した文字列、TIM3 は PC0 の周期と duty、OPA は出力÷入力の比、TKEY は値の記録）で、CH32V006 の実機で確認しなければならない（SHALL）。ほかのデバイスでは、理由を付けて試験を skip しなければならない（SHALL）。TKEY は値に合否を付けない参考の観測として扱い、確認済みとして記録してはならない（SHALL NOT）。

#### Scenario: CH32V006で確認する
- **WHEN** DUT が CH32V006 で、ch32fun の `usart2`、`tim3`、`opa` の HIL 試験を実行する
- **THEN** WCH SDK 版と同じ許容範囲で判定され、測った値がログに記録される

#### Scenario: CH32V002を選ぶ
- **WHEN** `--hil-device ch32v002` で同じ試験を選ぶ
- **THEN** 試験は書き込みの前に理由付きで skip される
