# Proposal

## Why

CH32V002/CH32V006向けの書籍原稿（change `write-ch32v00x-book-articles`）を書く中で、コードと記録を照合しました。その結果、サンプルのコメントと実際の設定値の食い違い、選択できるのにビルドできない分岐、未初期化の設定値、範囲外を読みうる処理、HIL記録の古い判定文字列が見つかりました。
あわせて、原因が未特定のまま「未確認」として本文に書いた事項も残っています。
読者がサンプルを読み違えたり、そのまま流用して不具合を持ち込んだりしないよう、修正すべきものを直し、調べるべきものを調べて記録します。

一覧の出所は `okf/log/2026-11-08-2019-ch32v00x-book-articles.md` の「執筆中に見つけたサンプル側の不整合」と、原稿の「確認状況と制約」です。

## What Changes

**修正（CH32V002/CH32V006のサンプル）**

- WCH SDK
  - `adc`: 冒頭コメントがCH32V003の説明（10ビット、241サイクル、起動時の校正）のまま → 12ビット、239.5サイクル、校正なしに直す。
  - `timer_blink`: 「IPRIOR[8]」というコメント → 実際は256要素で、範囲外になるのはIENRだけなので直す。
  - `timer_dma`: 「10usごとにトリガ」というコメント → 実際はPSC=480、Period=10で約100 µsなので直す。また、`TIM_TimeBaseInit` を二重に呼んでいる理由と、PSC=480（480−1ではない）が書籍由来であることを明記する。
  - `sleep_wake`: 「50…1Hz(1s)」というコメント → 実際はRepetition 20で約2 sなので直す。
  - `standby_wake`: 「window value 31」というコメント → 実際は25なので直す。
  - `i2c_master`: `USE_REMAP 1` の分岐がCH32V003の定数 `GPIO_FullRemap_I2C1` とピンのままで、002/006用SDKではビルドできない見込み → 資料で正しいリマップを確定して直す。確定できない場合は `#error` で明示的に止める。
  - `i2c_slave`: `I2C_ClockSpeed` が0のまま `I2C_Init()` を呼んでいる → SDKのCKCFGRの計算を確認し、有効な値を設定する。
- ch32fun
  - `i2c_slave_helper`: 「読み出しの後もSTOPを報告する」というコメントが実測の解釈と食い違っている → 002/006で確かめてから直す。
  - 各 `funconfig.h`: CH32V002だけを書いたコメント → 002/006共通であることを反映する。
- Arduino
  - `adc.ino`: 「0~1024」というコメント → 002/006では0〜4095なので直す。
  - `neopixel`: 「CH32V002」というコメント → 006にも適用されることを反映する。
  - `i2c_slave`: `on_request`（および `on_receive`）の範囲判定が `position + (i - 1)` で判定し、`position + i` を読む → 範囲外を読まない判定に直す。
- HIL記録
  - `hil/matrix_ch32v002_wch.json` の `adc` の判定文字列が0..1023の尺度のまま → 試験コードと同じ12ビットの尺度に直す。

**調査（結果は `okf/` に記録する）**

- 固定ch32funの `funAnalogInit()` がCH32V00xで `EXTTRIG` を立てず、予約ビット（RSTCAL/CAL）の解除を待っている。002/006で止まるか、変換できるかを確認する。
- CH32V002 `standby_wake` の起床直後の文字化け。待ちを入れる恒久修正を採るかを、再現回数を増やして判断する。
- CH32V006 PC4（TIM1_CH4）が無信号になる件の切り分け（オプションバイト、ピン機能、別個体）。
- CH32V006 IWDGで、設計値2 sに対して約2.3〜3.1 sでリセットされる件（LSIの周波数、プリスケーラの反映）。
- コアの表記の揺れ（V2AとV2C）と、`zmmul` による乗算命令が生成・実行されているか。
- Arduino
  - PATTERN 3（PC6/PC5のリマップ）で出力が出ない件と、variantの `PinMap_TIM` の対応。
  - `SPISettings(1000000)` の実際のクロック。
  - `printf`（`USART_Printf_Init`）の出力が受信できない件。
- WS2812
  - SPIの「1」のHighの設計値1000 nsが判定範囲の上限を超えている件。
  - フレームの後も信号線がHighのまま待機する件。
- SSD1306 helperの既定の1 MHzで、Picoが何も受信できない件。
- CH32V006の `ADC_CLK_MODE` の既定値。CH32V002の `timer_dma` のCC要求のDMA割当を資料と照合する。
- CH32V006でのSWIO printf（`minichlink -T`）の受信確認。

**未確認事項の棚卸し**

書籍原稿の各章の「確認状況と制約」に「確認していない」と書いた事項を一覧にします（出所: `articles-ch32v00x/*/README.md`、`ef013a6`）。
今の治具で確かめられるものは確かめ、それ以外は理由と必要なもの（機材、部品、GUI操作、別の個体）を付けて一覧に残します。

- 今の治具で確かめるもの
  - **CPU**: 乗算命令（`zmmul`）が002/006の実機で正しく実行されるか。生成されているかの確認だけでなく、既知の積を計算する試験ファームウェアで結果を確かめる。`-march` の指定の根拠（WCHの資料、ch32funとSDKの指定）も記録する。
  - **GPIO**: プルダウン入力、オープンドレイン出力、`GPIO_Speed_2MHz`/`50MHz` を指定したときに出力になるか（原稿では資料からの推定と書いた）、PA1でのEXTI割り込み。
  - **UART**: 115200と9600以外のボーレート、パリティとフレーミングのエラーの扱い。
  - **I2C**: Picoで測ったSCLの周期（100 kHz、400 kHz）、バスエラーからの復旧、100 kHz以外のmasterとの通信。
  - **SPI**: Picoで測ったSCKの周期、16ビット転送。
  - **ログ**: Arduinoの `i2c_master`・`spi_master` などのスケッチがSerialに出す値（今はバス上の内容だけで判定している）、WCH SDK `i2c_slave` の `printf()`。
  - **省電力**: ch32funでのスタンバイ、EXTIの外部ピンによる起床。
  - **リセットの扱い**: CH32V006のPC5/PD7のリセット機能の設定（オプションバイト）の読み出し、WCH SDK `watchdog` のLED2（PC4）の点灯（006はPC4の件と合わせて調べる）。
  - **再現性**: 主な試験を、リセットを跨いで複数回実行したときの再現性。
- 治具を足す必要があるもの（必要な配線や治具の能力を記録する）
  - `timer_dma` のSB、SC、SEL3、SDPのピンと、桁とセグメントの切り替えの同期。
  - SPIのモード0以外。Pico側のslaveがモード0だけに対応しているため。
  - リマップしたピン（I2C、SPI、UART、PWM）。固定配線と別のピンを使うため。
- 測定器・実物の部品・別の個体が要るもの（一覧に残すだけにする）
  - 消費電流、電圧、波形の品質、立ち上がり時間。
  - ADCの精度・直線性・オフセット・ノイズ（基準電圧の測定が要る）。
  - 時間の精度（校正したクロック）、ボーレートの誤差とHSIの精度、LSIの周波数の絶対値。
  - 実物のモジュール: OLED、NeoPixel、SHT31、ADT7310、CO2センサー、LEDの明るさ、スイッチ。
  - 温度・電源電圧による変化、複数個体の差。
- GUIの操作が要るもの（ユーザーの手作業。手順と結果を記録する）
  - Arduino IDEの画面操作、IDEからの書き込み（OpenOCD）、シリアルモニタ、ライブラリの導入。
  - MounRiver Studio、PlatformIO、SDI-Print。
- サンプルがないもの（追加するかを判断し、追加しない場合は理由を記録する）
  - WWDG、Arduinoでのwatchdogと省電力。
  - ch32funの `ch32v003_SPI.h`、`ws2812b_simple.h`、SSD1306のSPI・ビットバンギング版、128×64のArduinoのスケッチ。
  - 006だけにある機能（USART2、OPA、TKEYなど）。
- 資料の確認で済むもの
  - 最小回路のコンデンサの値。
  - ADCのクロックの違い（ch32funは24 MHz、WCH SDKは6 MHz）が結果に影響するか。
  - サードパーティ版のArduino coreは、実機では動かさない方針のまま記録する。

## Capabilities

### New Capabilities

なし。

### Modified Capabilities

- `wch-sdk-sample-workflow`: 次の要件を追加する。
  - サンプル内の説明と設定値を一致させる。
  - コンパイル時に選べる分岐は、対象デバイスでビルドできるか、明示的に失敗させる。
  - SDKの初期化構造体には有効な値を入れる。
- `arduino-sample-workflow`: 維持するスケッチのバッファ操作は、受信長やインデックスによらず範囲内に収める、という要件を追加する。
- `ch32fun-sample-workflow`: 固定ch32funのhelperがデバイスの仕様と合わない場合は、使うか避けるかを実機の根拠で決めて記録する、という要件を追加する。

## Impact

- 対象コード
  - `samples_ch32v002_wch/`、`samples_ch32v006_wch/` の `adc`、`timer_blink`、`timer_dma`、`sleep_wake`、`standby_wake`、`i2c_master`、`i2c_slave`
  - `samples_ch32v00x_ch32fun/`（`i2c_slave_helper` と各 `funconfig.h`）
  - `samples_ch32v00{2,6}_arduino/` の `adc`、`neopixel`、`i2c_slave`
  - `hil/matrix_ch32v002_wch.json`
- 動作が変わる修正（`i2c_slave` のクロック設定、Arduino `i2c_slave` の範囲判定、`i2c_master` のリマップ分岐）は、002と006の両方でbuildとHILをやり直す。コメントだけの修正は、buildで成果物が変わらないことを確かめる。
- 調査の多くは実機と治具（WCH-LinkE、Pico）が必要で、DUTの差し替えはユーザーが行う。
- 対象外
  - `externals/ch32fun` のsubmodule自体の変更。上流への報告は、結果を記録したうえで別途判断する。
  - CH32V003版サンプルの同じコメントの修正。記録だけ残す。
  - 書籍原稿（`externals/ch32v003-book`）の更新。原稿は `e8f76c4` を参照しているため、この変更の後に別作業で追従する。
