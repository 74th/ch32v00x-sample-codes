# Design

## Context

動機と範囲は [proposal.md](proposal.md) を参照。提案時の読取調査結果:

- 前changeは `openspec/changes/archive/2026-11-08-verify-ch32v006-shared-ch32fun/` にあり、現行仕様へ同期済み。CH32V006の型番照合・Pico設定・共通ch32fun配置は存在するが、`FRAMEWORK_MATRICES` にCH32V006のArduino/WCHがない。
- CH32V006の既存識別ログは `0x1ffff704` の `20 06 63 00` を記録し、上位型番は `0x006`。F8P6を資料のF8P7と同一ダイとして扱うこと、実基板は従来と同一開発ボードでMCUピン番号による記録を使うことは前作業のユーザー判断として保持する。F8P6の資料表記やピン設定すべてが独立に検証済みとはしない。
- `samples_ch32v002_arduino/arduino.mk` はCH32V006K8のFQBNに16 KiB / 4 KiBのサイズ、`_eusrstack=0x20001000`、`_heap_end=0x20000e00` を上書きする。公式core 1.0.6の `boards.txt` には `CH32VM00X_EVT:pnum=CH32V006K8` があり、63488 B / 8192 B、48 MHz HSIが選択できる。F8P6専用定義ではない。
- Arduinoの共通makeは `.arduino/build/<device-directory>/<sketch>` を使うので新規デバイス配置とキャッシュを分けられる。OLEDのライブラリは既存profileで1.0.7に固定されている。
- `samples_ch32v002_wch/` は13例と基準blinkを持ち、CH32V00X SDKのコピー元は `openwch/ch32v002_004_005_006_007` revision `a835ede9ff3e2dca2c6aa652809b85c9775475d2`。`wch.mk` は `-DCH32V002`、LDは16/4 KiB。元の公式LDはCH32V006用62/8 KiB。PROVENANCEに元パス・ハッシュ・変更・利用条件がある。
- `scripts/wch-sdk.py` の `LAYOUT` は003/002のみ。HILのArduino ADC、WCH ADC/ADC DMAのSCALE、Arduino NeoPixelのパルス境界上限も003/002のみなので、選択を有効にするだけでは足りない。
- Arduino `i2c_slave` は003/002でWire EV割り込み内の待機によるSCL固着が記録され、デバイス別にnon-strict xfailを付けている。PWM PATTERN 3は参考xfail。Arduino `uart` はCO2センサーとOLEDの複合例で既存治具の同時観測対象外。WCH Standbyには002でwake後の先頭文字化けの記録があるが、006へ既知事象として転用できない。
- 現行 `hil-test-runner` はCH32V006でarduino/wchを拒否するシナリオを持つ。本changeのdeltaで許可へ変更し、実装に存在するwchもフレームワーク列挙へ反映する。

## Goals / Non-Goals

**Goals:** 既存の刺激・期待値・固定配線を基準に、CH32V006のArduino/WCHを追加する。profile、SDK、メモリ・起動設定と観測結果を結び付け、再現可能な個別コマンドを提供する。

**Non-Goals:** フレームワーク間の実装統一や追加のシリーズ共通配置、core/SDKの更新・core内部の修正、治具機能追加。前changeで残した精度評価・実表示・RST設定の調査完了を本changeの完了条件にしない。

## Decisions

### 1. デバイス別配置と段階的な有効化

Arduinoは `samples_ch32v006_arduino/`、WCHは `samples_ch32v006_wch/` とする。CH32V002版を起点に移植し、必要なピン・型番文字列・ビルド設定の差分を明記する。共通化の改名は別の判断が必要なので今回は行わない。小さなmake規則の再利用は許すが、WCHのSDKはCH32V006の維持ディレクトリに置く。

各frameworkの基準GPIOを作り、該当マトリクスを未確認で初期化してから `FRAMEWORK_MATRICES` に登録する。残りサンプルは未移植/未確認を区別して段階追加する。既存の `dut.device=CH32V006F8P6` と配線設定を使い、フレームワークごとに電気配線を複製しない。別frameworkのテストは従来どおりskipし、既定はCH32V003/ch32funを維持する。

### 2. Arduinoは配布coreのCH32V006定義を使う

profile `ch32v006` の候補FQBNを `WCH:ch32v:CH32VM00X_EVT:pnum=CH32V006K8,clock=48MHz_HSI` とする。インストール済み固定coreのvariant/pin map、startup・LD、初期化が使うTSSOP20ピンを照合したうえで採用する。coreを改造して独自F8P6定義を作る案は今回採用しない。

CH32V002のmake wrapperは継承せず、汎用Arduino規則を直接利用する。全10スケッチに固定profileを持たせ、OLED依存があるものは既存のライブラリ1.0.7を固定する。buildログ・ELF/mapで62 KiB / 8 KiB、スタック/ヒープがRAM内であることを確認し、アップロード上限値だけで判定しない。build cache・成果物は006専用にする。

NeoPixelは002の送信処理を初期候補とし、バイト順・送信列とPico取得結果を確認する。同じnop数が適切とは先に決めない。変更する場合はコンパイラ・クロック・生成コードと観測に基づく理由を残す。既存テストの時間範囲は受信が解釈可能な条件を調べるためのものとして使い、規格適合を保証しない。広い上限を追加して失敗を消すことはしない。

### 3. WCHは公式CH32V00X SDKの006設定を明示する

SDKファイルは既存PROVENANCEと同じ固定元revisionから必要分をコピーし、元ファイルのハッシュ・元パス・利用条件を保持する。コピー時点のSDK本文・ライセンス表示を確認し、ローカルconf/compatなど独自追加物は区別する。参照用externalsはビルド経路に含めない。

`wch.mk` は `-DCH32V006`、公式startup/system、既定48 MHz HSI、006用LD（Flash 62 KiB / RAM 8 KiB）を使用する。既存WCH GCC 15.2.0とABIを維持し、既存002向けISA指定の適用根拠も公式設定・生成ELFと照合する。資料間のコア表記の揺れを「同じコア」で解決したことにしない。

`scripts/wch-sdk.py` に006のLAYOUTを追加し、`build --all` が006の14例を含めてメモリ配置とELFの参照元を検査するようにする。GPIO/通信に加え、DMAチャネル・IRQベクタとハンドラが006で妥当か確認し、既存static_checksと実測結果を組み合わせる。

### 4. HILの期待値・証跡をフレームワーク別に管理する

ADC/ADC DMAは006の12-bit全域に対応する期待値を資料・実装に基づき追加する。002の粗い比率閾値を出発点にできるが、新機種が通るよう結果に合わせて緩和しない。UART、通信処理、PWM、復帰シーケンスは既存テストを再利用する。

書き込みは既存の固定minichlink、検出名・識別領域0x006、全量readbackを通す。汎用 `scripts/ch32fun.sh flash` はch32fun成果物を扱うためArduino/WCHのflash入口に転用しない。WCHは `scripts/wch-sdk.py flash --device ch32v006 --sample ...`、両者の実機試験は対応HILを使う。

マトリクスは `hil/matrix_ch32v006_arduino.json`（10行）と `hil/matrix_ch32v006_wch.json`（書籍13行、基準blinkはREADMEと実測ログで追跡）に分ける。結果保存はdevice/framework/sample/variant/runで識別できるようにし、同名サンプルの上書きを防ぐ。core/FQBN/ライブラリまたはSDK/コンパイラ、ソースrevision、BIN hash、設定、コマンド、段階別結果を残す。Pico再列挙は `discover` と設定timeout、終了時はRESET_SAFEを使う。

### 5. 対象と完了条件

| 系統 | build対象 | 実機判定 |
| --- | --- | --- |
| Arduino | 既存10スケッチすべて | 通常8スケッチは必須機能確認。Wire slaveは別途複数回試験。uartは複合観測制約のためbuildのみ |
| WCH | 書籍13例＋基準blink | 基準blink観測、13例の既存機能HILを必須とする |
| 回帰 | 既存003/002の両framework＋006/ch32fun | ホストの選択・ビルド・期待値テスト、影響箇所の実機回帰 |

順序は各frameworkともGPIO → UART/通信 → ADC/PWM → 残り。WCHでは続いてADC DMA、Timer割り込み/DMA、watchdog、sleep、standbyを行う。ArduinoのWire slaveは少なくともリセットを挟む3回の系列を試し、連続取引と時間間隔をログに残す。timeout時もcleanupして試験を有限にする。

Wire slaveの006での再現はcore 1.0.6の既知制限として扱えるが、006の実測根拠を追加するまでxfail対象へ含めない。確認済み状態は付けず、build-onlyと不具合ログを残す。再現しなければ試した条件・回数に限って結果を示す。PWM PATTERN 3は通常パターンと別の参考試験で、XFAIL/XPASSとも保存する。これら2件とuart観測対象外を除く新規の必須HIL失敗は完了を妨げる。

通常対象8スケッチの機能成功、全10build、Wire slaveの検証結果、WCHの14buildと必要な全実機観測、マトリクス・README・ログの整合が完了条件。既存デバイスを実機回帰できなければそのタスクは未完了で残す。新たな実機制約を理由に必須対象をskipへ落として完了にはしない。

### 6. 未検証事項は用途を区別して維持する

READMEはch32fun/Arduino/WCHの型番別状況を分け、今回成功した機能だけ更新する。精度・校正・電流、OLED表示・LED発光、WS2812規格適合は未確認として残す。PC5/PD7のRST設定やオプションバイトは読み書きによる網羅調査をしない。SPI等に支障があれば症状と現状を記録してその段階で止め、勝手にRST/SWIO設定を変更しない。

## Risks / Trade-offs

- [K8用variantとF8P6の差] → 使用ピン・初期化だけを具体的に照合し、前作業のユーザー判断と資料確認を区別する。
- [002用のメモリ上書き残留] → 006用profileとELF/map・スタック/ヒープ検査で検出する。
- [Wire slaveやStandbyの不一致を他デバイスの既知事象として隠す] → 006固有の再現条件と結果を残し、免除範囲を上記に限定する。
- [SDKコピー重複] → 今回はdevice別の独立性を優先し、PROVENANCEと検査で管理する。共通SDK配置への変更は別changeとする。
- [実測を伴うデバイス交換] → 従来の電源断・逆流給電防止手順を使い、接続したDUTの型番を毎回確認する。

## Migration Plan

1. 新規サンプルの基準GPIOとビルド設定、ホスト試験、未確認マトリクスを作る。
2. framework選択を登録して各GPIOの実機確認を完了し、サンプルと対応期待値を段階追加する。
3. 通常対象・既知制限を区別して実測し、各追加段階で文書と証跡を更新する。
4. 新規全対象と既存経路を統合確認する。既定CLI・ch32fun配置を変更しないため利用者の既存コマンド移行は不要。
5. 戻す場合は006の新規framework登録・サンプル・関連設定を一体で戻し、実測ログを保持する。実機のファームウェア復帰も対象識別付きflashを使う。
