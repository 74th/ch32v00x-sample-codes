# Design

## Context

基準コミット38b17ab。samples_ch32v003_wch/blinkは公式Delay版を実機確認済み。scripts/wch-sdk.pyは現在サンプル固定。ch32hil/devices.pyのFRAMEWORKSはch32fun/arduinoだけ。既存tests/hilのPico能力とDutの検出・読み戻しを再利用できる。
SDKは003が4e1b7437ada5d3ae8831a6f4b811a6320e4e23c7。002はexternals/ch32v002_004_005_006_007を調査元にし、採用revisionと対象ファイルの条件を固定してコピーする。002の既定ヘッダは006、Link.ldも62K/8Kなので明示的に変更が必要。

## Goals / Non-Goals

Goals: 書籍の公式SDK例を公式APIの使用例として維持し、対応・差分・観測状態を追跡する。
Non-Goals: 今回の計画作成時の実装、他frameworkのOLED/NeoPixelの独自SDK化、Pico新規プロトコルの全面開発、消費電力の実測。

## Decisions

### 機能ごとの対応と受け入れ観点

次の表をマトリクス初期値とする。全行CH32V003で実装・ビルドし、その後002へ移植する。数値・通信列は書籍src/main.cと設定から導出し、テスト前に固定する。

| 書籍ディレクトリ（末尾-wch_sdk） | 維持名 | 検証内容・制約 |
|---|---|---|
| blink_and_read | blink_and_read | PC0点滅、PA1入力で停止・再開。既存blinkは基準として保持 |
| uart | uart | CO2センサー要求・応答、値の抽出、checksum/timeout。PD5/PD6へ調整し診断printfとの混在を避ける |
| adc | adc | PA1/PA2の2チャネル、校正・既知刺激と10-bit値の関係。RC経由で機能確認 |
| adc_dma | adc_dma | 上記の2チャネルscanをDMAで連続バッファ転送。順序と更新を確認 |
| i2c_master | i2c_master | SHT31 0x44のコマンド、応答と温湿度変換。PC1/PC2で治具の対応能力を確認 |
| i2c_slave | i2c_slave | 0x10のレジスタ型slave、書き込み、ポインタ、連続読み、repeated START |
| spi_master | spi_master | センサーreset/config/read列と符号付き温度変換。PC5/6/7、CSの配線制約も記録 |
| pwm | pwm | TIM1 PWMのduty変化。観測可能PD2を優先し、PC4等のチャンネルは範囲を明記 |
| timer_blink | timer_blink | TIM1/TIM2割り込みの周期とGPIOイベント。PC1からPC0への変更を記録 |
| timer_dma | timer_dma | タイマ要求によるGPIO BSHRへのDMAと4桁7seg走査。多ポート配線が必要、固定治具で一部のみの可能性 |
| watchdogtimer | watchdog | 給餌中は稼働、入力で給餌停止して再起動、reset要因・時間窓を照合 |
| sleep_mode_blink | sleep_wake | sleepからTimer割り込みで復帰、GPIO/UARTの時系列。消費電力は未測定 |
| standby_mode_blink | standby_wake | AWUによる復帰、保持/再開の実際の挙動を公式資料と照合。sleepと同一視しない |

13例以外のOLED/NeoPixelはwch_sdk版がないため本changeの必須対象外。将来の別changeで扱う。

### ビルドとAPI

各deviceのsdkを共有する小さなwch.mkを用意し、必要な公式周辺ドライバだけを追加する。公式Delay、GPIO、RCC、USART、ADC、DMA、I2C、SPI、TIM、PWR、IWDG等を使用。独自待機やch32funで代用しない。既存blink CLIの引数なし動作を保ち、--device/--sampleで選択を追加する。対象チェック・成果物パスで異機種の誤書き込みを防ぐ。共通SDK変更では依存が再ビルドされることも確認する。

### HIL統合

--hil-framework wchを追加し、既存Dutのflash/readbackとRunのフェーズを共用。WCH GCCでのbuildはframework専用にする。既存Arduinoのテストを無条件に流用せず、書籍のプロトコルと期待値に合わせる。治具の既存I2C/SPI/UART能力で書籍プロトコルを表現できない場合、部分確認と未観測を記録する。失敗の隠蔽や広いxfailは使わない。

### CH32V002は後段

003各行の状態が明らかになった後、002の公式SDK、startup、rv32e/ilp32eと拡張、16K/4K、-DCH32V002、HSI設定を用意。ADCは12-bitなど値の違いをデバイス側期待値へ反映。0x1ffff704による検出ガードを共用し、002の実機接続時にだけ書き込む。

## Risks / Trade-offs

- 書籍コードのCC0と各SDK/第三者部分の条件が異なる → ファイルごとの出所・条件を確認し、最小限の転用と変更表示を行う。
- 公式debugのprintfがRAM・通信線を消費 → map/sizeを確認し、センサーUARTとログを競合させない。
- Sleep/Standbyでデバッグが不安定 → 初期待機・復旧手順を文書化し、実験後に既知blinkへ戻して検出確認する。
- 治具と書籍のピン・周期が異なる → 意味を保持して変更理由を残し、精密測定済みとは言わない。
- 低消費電力やDMAの内部使用は点滅だけでは証明できない → 設定・コード・必要な状態観測を合わせ、保証範囲を限定する。

## Migration Plan

CLIとHILの選択を追加して既定動作は維持。003サンプルを少数ずつ追加・実測後に002へ展開。失敗した機能だけを未確認として残し、既知blinkと既存フレームワークで復旧できる構成にする。実機がない場合に実測タスクを完了扱いにしない。
