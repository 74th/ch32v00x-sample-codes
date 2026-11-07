# Design

## Context

See `proposal.md` - Why. 現在は `scripts/ch32fun.sh` が固定ch32funによるbuild/flashを、`hardware/pico-tester/measure.py` が単一GPIOの観測を担う。readback、Pico build/flash、DUT reset、測定は手順書上の別コマンドであり、Python側のテストは `unittest` による測定ロジック6件だけである。

PicoファームウェアはUSB CDCで文字 `s` を受け、GP0を300点取得するだけで、出力駆動、ピン所有権、能力照会、後始末を持たない。Picoには真のDACがないためADC刺激には外付け回路と校正が必要である。初回Pico書き込み、物理配線、電圧確認、スイッチ操作を完全にはソフトウェア化できない。

book-codeの現行ch32fun例は、`blink_and_read` 以外の多くが `ch32v003_GPIO_branchless.h`、`ch32v003_SPI.h`、`ssd1306*`、`ws2812*`、`i2c_slave.h` 等へ依存する。今回はそれらをそのまま移植せず、必要ならch32fun標準ヘッダからレジスタを操作する小さな試験用サンプルを新設する。

## Goals / Non-Goals

**Goals:**

- 接続済みの既知構成について、一つのpytestコマンドでPico準備からDUT実測まで再現する。
- Pico能力をDUTとは独立に検証し、治具故障とDUT不一致を区別する。
- 周辺機能を増やしても、プロトコル、ピン設定、PC側実行器を共通利用する。
- HILを明示選択しない限り、接続実機を変更しない。
- build、flash、readback、runtime observationを異なる結果として保持する。

**Non-Goals:**

- `externals/ch32v003-book-code` またはその内側のch32funを実行依存にすること。
- ch32fun `extralibs` 自体の移植・互換性検証、OLEDやNeoPixelの画像・発光内容検証。
- Picoを精密測定器または校正済み電源として扱うこと。
- BOOTSEL、配線変更、電圧確認、保護部品をソフトウェアだけで代替すること。
- 最初の実装で全周辺機能を同時に完成させること。

## Decisions

### 1. pytestをオーケストレータ兼結果モデルにする

`pyproject.toml` と `uv.lock` で `pytest`、`pyserial` 等を固定し、既定実行から `hil` マーカーを除外する。`tests/unit/` はコマンド出力・プロトコル・判定ロジックを模擬し、`tests/hil/` のfixtureが実機操作の段階を組み立てる。

単一の大きなshell scriptも検討したが、fixtureの後始末、skip条件、段階別失敗、模擬テストを表現しにくい。低レベル操作はshellからも再利用できる小さなPython APIまたは既存scriptとして残し、pytest固有コードへminichlink解析を埋め込まない。

### 2. HILは設定ファイルで対象を明示する

対象デバイス、サンプル、Pico USB識別、DUT/Picoピン対応、電圧、直列抵抗・pull-up・RC回路、タイムアウト、readback方針を公開可能な設定へ置く。ホスト固有のポート名はCLIまたは環境変数で上書きし、秘密情報を設定へ入れない。

自動検出だけに頼る案は複数Picoや複数LinkEで誤操作するため採用しない。候補が一意でない場合は停止する。

### 3. Picoプロトコルは行単位のバージョン付き要求/応答にする

USB CDC上で、request id、protocol version、command、引数を持つ行単位フレームを用いる。応答は同じid、`OK`または分類済み`ERR`、測定値・実設定を含む。バイナリ大量転送が必要になるまでは、人がログを読めて既存pyserialで扱える形式を優先する。

既存 `PICO_GPIO_V1` は移行期間にPCクライアントで読めるようにするが、新ファームウェアの主契約にはしない。ファームウェアは `CAPS`、`RESET_SAFE`、`GPIO_*` から始め、能力追加時にprotocol全体ではなくcapability版を増やす。

### 4. 安全状態は全GPIO入力・pull無効を基本にする

起動、通常完了、エラー、watchdog、USB切断検出時に、試験で所有したピンを入力・pull無効へ戻す。I2Cのpull-upやADC用RC等の外付け条件は設定と配線資料で扱う。出力コマンドは許可されたピンとレベルだけを使い、予約ピン、USB用途、電源ピン、競合中ピンを拒否する。

特定の安全レベルを駆動し続ける方式は、片側電源断時の逆流を増やすため既定にしない。例外が必要な試験は配線レビューと明示設定を要求する。

### 5. Pico能力を小さな段階で追加し、各段階を先にループバック検証する

実装順は以下とする。

1. protocol/capability/safe resetと既存GPIO入力測定
2. GPIO出力刺激とエッジ/周期測定
3. UART送受信
4. I2C master/slave
5. SPI master/slave
6. PWM/パルス測定
7. ADC刺激用PWM出力と外付けRC・校正
8. watchdog/sleep/reset-signature観測のための長時間・再起動シーケンス

RP2040のhardware peripheralで十分な役割はそれを使い、slave対応や正確なエッジ取得で不足する場合のみPIOを使う。全機能を先にPIO化する案は柔軟だが、実装・検証面積が大きいため採用しない。

各能力には、可能ならPicoの異なるピン間のループバック、PC側の不正要求テスト、応答タイムアウトを用意する。I2Cは外付けpull-up、ADCはRCと電圧実測が必要なので、配線なしの自己テストと実回路の校正済み試験を区別する。

### 6. DUT検証はPico能力が通った順に載せる

最初のvertical sliceは既存 `blink_and_read` とし、Pico build/flash、USB再認識、CH32V003 build/flash/readback、GPIO測定、safe resetを一括化する。その後、GPIO入力、UART、I2C、SPI、ADC、timer/PWM、watchdog/sleepの順を基本にする。

DUTサンプルは `samples_ch32v003_ch32fun/<sample>/` に置き、固定 `externals/ch32fun/ch32fun/ch32fun.mk` と標準ヘッダだけを使う。book-codeの意図とピン設定は参照するが、extralibs helperを必要とする元サンプルはscope matrixで除外とする。標準ヘッダから直接レジスタを使う試験用サンプルは「元サンプルそのものの検証」ではなく「同じ周辺機能のch32fun環境での検証」と記録する。

### 7. readbackは成果物サイズで行い、ポリシーを明示する

最初のCH32V003 HILではflash後readbackを既定で要求し、生成したbinaryのサイズを使用してbyte一致を確認する。速度が問題になった場合のみ、試験設定で `required`、`optional`、`disabled` を選べるようにし、結果へ方針を残す。

minichlinkの終了コードだけは信頼せず、期待型番、`Image written.`、否定的出力を解析する。CH32V002等を後で追加するときは識別領域確認も既存規則に従う。

### 8. 実験ログは自動生成物だけで完結させない

pytestはJSON等の機械可読run artifactを出す。実機の配線・電源条件、ユーザー申告、実測と推定の区別を加えた `okf/log/YYYY-MM-DD-HHMM-*.md` は各実験作業時に作成する。時刻は実行時に取得できた値だけを使い、推測しない。

### 9. 配線はMarkdown、KiCad、可視化出力を同じネット名で管理する

`hardware/wiring.md` を人間の作業手順と安全チェックの正本とし、`hardware/` 配下にKiCad回路図 `.kicad_sch` を置く。回路図にはDUT/Picoの物理ピン、信号方向、1 kΩ等の保護抵抗、I2C pull-up、ADC用RC、共通GND、接続してはいけない電源ネットを表す。SVGまたはPDFを生成して、KiCadがない環境でもレビュー可能にする。

テスト設定、Markdown、回路図で同じ論理ネット名を使用する。単一の自動生成元へ直ちに統合する案はKiCadファイルの生成・保守が先に複雑になるため採用せず、初期段階ではレビュー用チェックリストと可能な範囲の機械照合で同期する。

## Risks / Trade-offs

- [PicoとDUTが同じ信号を同時駆動する] → ピン所有権、既定input、直列抵抗、設定レビュー、競合拒否を重ねる。
- [WCH-LinkE操作がDUT 3.3 Vを有効化する] → flashと治具駆動を別段階にし、実測済み電源条件を構成に必須化する。
- [USB再列挙で別Picoを選ぶ] → serial/by-id等の明示識別を優先し、複数候補では停止する。
- [Pico測定精度を過大評価する] → 実設定・サンプル窓・許容差を結果へ含め、精密なanalog/clock検証は別測定器が必要と明記する。
- [PWM+RCのADC刺激が電源・負荷で変動する] → 外付け回路、settling time、実測校正、広すぎないが現実的な許容差を試験構成ごとに記録する。
- [一つのPicoに全役割を載せファームウェアが複雑化する] → capability単位のモジュール化と段階導入を行い、resource上限を`CAPS`で公開する。
- [HIL全件が遅く不安定になる] → 単体テストを既定とし、HILを周辺機能マーカーで個別選択可能にする。
- [book-code手動確認と新しい標準ch32funサンプルの意味がずれる] → source matrixで「移植」「同等機能の再実装」「対象外」を区別する。

## Migration Plan

1. `uv`/pytestの基盤を入れ、既存 `test_measure.py` を動作を変えず単体テストへ移す。
2. Pico protocol v2とPCクライアントを追加し、既存v1測定との並行期間を設ける。
3. 既存blink HILを一括化し、現行手順との結果一致を実機で確認する。
4. GPIO出力から順にPico能力を自己検証し、確認済み能力だけDUT HILへ追加する。
5. 各周辺機能を追加するたびにscope matrix、配線、OKFログを更新する。
6. v2で既存GPIO HILが安定した後、v1専用クライアントを削除または互換shimへ縮小する。

ロールバック時は既存 `measure.py` と個別 `scripts/ch32fun.sh` 手順を維持し、新しいHILマーカーを無効化する。Picoファームウェアは既知のUF2へ `picotool load -f -v -x` で戻せるが、USB応答不能時は手動BOOTSELが必要である。
