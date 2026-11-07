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

維持コードはsamples_ch32v003_wch配下に置き、参照専用externalsの公式SDKをビルド依存にしてはならない（SHALL NOT）。必要なコピーにはrevision、元パス、ハッシュ、利用条件、変更箇所を記録しなければならない（SHALL）。

#### Scenario: SDKをコピーして維持する
- **WHEN** サンプルで公式SDKファイルを利用する
- **THEN** 元の著作権・利用条件が保持され、コピー元とローカル変更が追跡できる
- **AND** 対象ファイルにないApache-2.0条件を仮定しない

### Requirement: 段階別の書き込みと実機観測

build・flash・observeは独立して実行・判定できなければならない（SHALL）。書き込みは固定ch32funのminichlinkで期待型番と完了出力を確認し、成果物全量の読み戻しを照合しなければならない（SHALL）。

#### Scenario: 基準blinkを観測する
- **WHEN** CH32V003への書き込み・読み戻し後にPicoでPC0を10 ms間隔で300点観測する
- **THEN** 両端以外の完全なHigh/Low区間が4個以上かつ各400～600 msであることを判定し、治具をRESET_SAFEで終了する

#### Scenario: 実機観測がない
- **WHEN** buildまたはflashだけが完了している
- **THEN** 実機動作確認済みと報告せず、失敗・未確認段階と再現条件をokf/logに記録する
