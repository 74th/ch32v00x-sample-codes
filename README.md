# CH32V00x sample codes

CH32V003向けに作成したサンプルコードを、CH32V002 / CH32V005 / CH32V006 / CH32V007へ移植し、実機で再現可能な形に整備するプロジェクトです。

WCH公式SDKのGUI不要なCLIビルド例は [samples_ch32v003_wch](samples_ch32v003_wch/README.md) にあります。CH32V003でビルド・書き込み・読み戻し照合・PicoによるGPIO点滅観測を確認済みです（CH32V002は未対応）。

このリポジトリでは、単にビルドできるコードを増やすことを目的にしません。デバイスごとの差分を調査し、実機試験で動作を確かめ、その過程で必要になった知識を再利用可能な形で残すことを重視します。

> [!IMPORTANT]
> 現在は準備・設計段階です。記載されている対象デバイスや試験構成のすべてで動作確認が完了しているわけではありません。検証状況は、コードや文書ごとに明示していきます。

## このプロジェクトで実現すること

成果物は、大きく次の3つです。

1. **CH32V00x向けサンプルコード**  
   CH32V003向けの既存サンプルを起点に、各デバイスのCPUコア、メモリ、周辺機能、ピン配置、リマップなどの差異を反映したコードを整備します。

2. **実機自動テスト環境**  
   ビルド、書き込み、信号の生成・測定、PASS/FAIL判定までを自動化し、サンプルコードの動作を継続的に確認できるHardware-in-the-Loop（HIL）環境を構築します。

3. **移植に必要だった知識**  
   データシートの読み解き方、デバイス間の差分、ツールチェーンの設定、ハードウェア上の注意点、検証方法などを、`okf/` にOpenKnowledgeFormat（OKF）で蓄積します。

最終的には、コードだけでなく「なぜその実装になるのか」「どの実機で何を確認したのか」「別のサンプルへどう応用できるのか」まで公開できる状態を目指します。

## 基本方針

### 実測を根拠にする

- ビルド成功だけを動作確認とはみなしません。
- LEDの目視やシリアルログの印象ではなく、可能な限り信号や測定値に対する機械的な判定を行います。
- 未確認の内容、データシートからの推定、実機で確認済みの内容を区別して記録します。
- あるデバイスでの成功を、別のデバイスやパッケージの動作保証として扱いません。

### 小さく検証してから広げる

最初から全デバイス・全周辺機能へ展開せず、次の順序で進めます。

1. デバイス、資料、書き込み方法、治具の安全性を確認する
2. 1本のGPIOを使って、ビルドから実測判定までの最小ループを完成させる
3. UART、I2C、SPI、ADC、DMA、Timer/PWMなどへ対象を広げる
4. 他のデバイス、パッケージ、固有機能へ横展開する

### 元のサンプルを尊重する

- 移植元は『CH32V003開発ガイドブック』の[サンプルコード](https://github.com/74th/ch32v003-book-code)です。
- 元コードは参照元として保持し、移植や試験のための変更と混在させない方針です。
- まずレジスタ直接操作版とch32fun版を優先し、WCH SDK版やArduino版は後続の対象とします。
- 移植に伴う変更点は、デバイス差分として説明できる形にします。

### 参照実装を調査する

移植元に加え、WCH公式のSDKサンプルとArduino coreを参照します。調査用リポジトリは`externals/`へチェックアウトし、公開リポジトリ本体には含めません。

```bash
./scripts/setup-externals.sh
```

このスクリプトは次のリポジトリを取得します。既に取得済みのリポジトリは更新せず、その時点のブランチとコミットIDを表示します。

| ローカルディレクトリ | 用途 | 取得元 |
| --- | --- | --- |
| `externals/ch32v003-book-code` | CH32V003向けの移植元サンプル | [74th/ch32v003-book-code](https://github.com/74th/ch32v003-book-code) |
| `externals/ch32v003` | CH32V003向けWCH公式SDK・サンプル | [openwch/ch32v003](https://github.com/openwch/ch32v003) |
| `externals/ch32v002_004_005_006_007` | CH32V00x向けWCH公式SDK・サンプル | [openwch/ch32v002_004_005_006_007](https://github.com/openwch/ch32v002_004_005_006_007) |
| `externals/arduino_core_ch32` | WCH公式Arduino core | [openwch/arduino_core_ch32](https://github.com/openwch/arduino_core_ch32) |

特定時点を調査や検証の根拠にした場合は、参照したコミットIDを`okf/`または試験結果に記録します。

### CH32V003 のビルド環境

現時点の確認環境は Ubuntu 26.04 x86-64、GCC 15.2、RISC-V GCC 14.2、GNU Make 4.4.1 です。必要なパッケージは `git make gcc gcc-riscv64-unknown-elf binutils-riscv64-unknown-elf libnewlib-dev pkg-config libusb-1.0-0-dev libudev-dev` です。書き込みには WCH-LinkE と CH32V003 が必要です。USB アクセス権も必要です。

ビルドに必要な ch32fun は `externals/ch32fun` の Git submodule です。固定コミットは `b28d285460ce052a179dba8f4a22c6f73ff8e328` です。book-code はサンプルの出典・参照元であり、ビルドや書き込みには不要です。

```bash
git submodule update --init externals/ch32fun
./scripts/ch32fun.sh check
./scripts/ch32fun.sh build
./scripts/ch32fun.sh programmer
./scripts/ch32fun.sh flash
```

`build` は DUT 不要で `samples_ch32v003_ch32fun/blink_and_read/main.bin` を生成します。`flash` は既存ファームウェアを上書きします。固定 ch32fun の minichlink を使用し、書き込み成功と GPIO 実測は別です。サンプルは book-code の CC0 版を基に PC0 出力と PA1 入力を保持しています。CH32V003F4P6 の LED 点滅と Pico での測定は確認済みですが、配線条件の確認は残っています。詳細は [暫定観測記録](hardware/ch32v003-observation.md) を参照してください。将来の移植先は `samples_<device>_<framework>/<sample>/` に配置します。

以前使用した book-code 内の古い minichlink は DUT 未検出でも終了コード 0 と `Image written` を返したため、`flash` スクリプトは現在の minichlink でも検出結果を確認します。成功表示は読み戻し照合の代わりにはなりません。

### 安全に失敗できる試験環境を作る

- DUT、書き込み器、測定器の電圧・給電元・GNDを明確にします。
- GPIOの出力衝突、電源断中の逆流給電、書き込み端子との競合を防ぎます。
- 各試験にタイムアウトを設け、成功・失敗にかかわらず治具を安全な状態へ戻します。
- ビルド失敗、書き込み失敗、起動失敗、通信タイムアウト、測定値不一致を区別して報告します。
- 復旧方法が確立するまでは、デバッグやリセットを無効化し得る設定を自動試験の対象にしません。

## 対象範囲

対象とするシリーズはCH32V002 / CH32V005 / CH32V006 / CH32V007です。ただし、実機の入手状況に合わせて段階的に進めます。

当面は次のTSSOP20デバイスを優先します。

| デバイス | 位置づけ |
| --- | --- |
| CH32V002F4P6 | 最初の移植・HIL試験対象 |
| CH32V006F8P6 | 同一治具での差し替えとデバイス差分の検証対象 |

CH32V006K8U6（QFN32）は後続フェーズ、CH32V005 / CH32V007は実機を用意した後に検証します。型番やデータシートの版による差異もあるため、対象部品の刻印と対応資料を照合してから仕様を確定します。

## 検証環境の構想

初期構想では、WCH-LinkEをDUTへの書き込みに、Raspberry Pi Pico（RP2040）を信号生成・測定用の治具に使います。PC側から一連の操作を実行し、pytestで結果を判定します。

```text
PC / test runner
  ├── WCH-LinkE ── 書き込み・リセット ──┐
  └── Raspberry Pi Pico ── 信号生成・測定 ├── CH32V00x DUT
                                         ┘
```

目標とする試験単位は次のとおりです。

```text
build → flash → reset → fixture setup → measure → assert → safe state
```

具体的な配線、使用ツール、コマンド、判定条件は、実物と資料を確認したうえで確定します。

CH32V003 と Pico の観測用配線の準備案と接続前の確認項目は [hardware/wiring.md](hardware/wiring.md)、Pico 側の試作、書き換えと PC 側の自動判定の手順は [hardware/pico-tester/README.md](hardware/pico-tester/README.md) にあります。

CH32V003F4P6 の build → flash → measure をまとめた手順は [hardware/ch32v003-reproduction.md](hardware/ch32v003-reproduction.md) にあります。

CH32V002F4P6 の差分と実機検証手順は [hardware/ch32v002-reproduction.md](hardware/ch32v002-reproduction.md) にあります。固定配線の Pico 治具で、CH32V003 と同じ HIL（機能確認のみ。既存 11 件と、下記の helper 検証 3 件＋参考の xfail 1 件）を `--hil-device ch32v002` で実行でき、2026-11-07 の実機で成功しています（状態は [hil/matrix_ch32v002.json](hil/matrix_ch32v002.json)）。

## `okf/` に残す知識

`okf/` は補足メモ置き場ではなく、このプロジェクトの主要な成果物の一つです。サンプルコードの移植中に得た知識をOpenKnowledgeFormatで表現し、人間が参照できるだけでなく、別の移植作業やツールからも再利用できる状態を目指します。

主に次の内容を蓄積します。

- デバイス、パッケージ、データシート版ごとの差分
- ピン配置、Alternate Function、リマップの対応関係
- CPUコア、メモリ、クロック、割り込み、周辺レジスタの差分
- ビルド定義、ツールチェーン、書き込みツールの要件
- サンプルごとの移植手順と判断根拠
- 配線、電源、保護、復旧に関する安全要件
- HIL試験の構成、入力条件、期待値、許容差
- 実機、ファームウェア、ツールバージョンを含む検証結果
- 調査中の事項、既知の制約、データシートと実測の不一致

知識を追加するときは、少なくとも次の状態を区別します。

- **確認済み:** 対象と条件を記録した実機試験で確認したもの
- **資料確認済み:** 一次資料で確認したが、実機では未確認のもの
- **仮説・要確認:** 移植や試験のために置いた仮説で、根拠の追加が必要なもの

OKFの具体的なディレクトリ構成やスキーマは、最初の知識項目を作る段階で定めます。形式を先に固定するのではなく、出典、対象型番、検証条件、確度を失わず表現できることを優先します。

## 一次資料と変換データの扱い

データシートやリファレンスマニュアルは、移植と検証に必要な一次資料です。検索、比較、引用箇所の特定、機械処理をしやすくするため、PDFをMarkdownなどのテキスト形式へ変換して利用します。

ただし、PDFやその全文に近い変換データは、公開成果物には含めません。原著作物の再配布になり得るため、個人用の調査資料としてGit管理対象外の`xprivate/`に置きます。`xprivate/`は`.gitignore`で除外します。

```text
xprivate/
  sources/              # 入手したPDFなどの一次資料
  converted/            # PDFから変換したMarkdown、画像、抽出表
  notes/                # 調査途中のメモや照合記録
```

公開する`okf/`には、一次資料そのものではなく、プロジェクトで必要になった知識を整理して記述します。

- 内容は原文の転載ではなく、目的に必要な事実、差分、制約、判断を中心に要約する
- 出典資料名、版、ページまたは節を記録し、確認箇所を追跡可能にする
- 公開されている一次資料には、可能な限り配布元または公式文書へのリンクを付ける
- 図、文章、表をそのまま大量に複製せず、必要な関係を独自の構造や表現で記述する
- PDFから読み取った内容と、実機試験で確認した内容を区別する
- 公開可否が判断できない素材は`xprivate/`に留める

この分離により、`xprivate/`を調査と機械処理のための作業領域、`okf/`を出典と検証状態が明確な公開知識として扱います。

## ロードマップ

### Phase 0: 対象と試験基盤の確定

- 手持ちデバイスの型番・パッケージ・対応データシートを照合する
- WCH-LinkE、Pico、変換基板、電源、保護部品を確認する
- 書き込み、リセット、復旧の手順を確立する
- 暫定配線をレビューし、信号競合や逆流給電が起きない構成にする
- 最初のOKF項目として、対象デバイスと検証環境の事実を記録する

### Phase 1: 最小のGPIO HIL試験

- CH32V002F4P6向けのGPIO出力サンプルをビルドする
- WCH-LinkEによる書き込みとリセットを自動化する
- DUTの既知パターンをPicoで測定し、pytestで判定する
- 意図的な不一致、タイムアウト、試験後の安全状態を確認する
- CH32V006F8P6でも同じ試験を行い、差分を記録する

Phase 1の完了条件は、ローカルコマンド1つでビルド、書き込み、測定、判定まで実行でき、失敗原因が区別され、失敗後も治具が安全状態へ戻ることです。

**状況（2026-11-07）:** CH32V003F4P6 と CH32V002F4P6 では、この条件を満たす HIL を実機で確認済みです。CH32V006F8P6 は未着手です。

### Phase 2: 周辺機能の移植と試験

UART → I2C Master/Slave → SPI（DUT Master）→ ADC → ADC+DMA → Timer/PWMの順を基本として追加します。その後、GPIO入力・割り込み、Watchdog、Sleep/Standby、NeoPixelなどへ広げます。

**状況（2026-11-07）:** CH32V003 / CH32V002 の両方で、GPIO、UART、I2C master/slave、SPI（DUT master）、ADC、Timer/PWM、Watchdog、Sleep、および ch32fun の helper を使う I2C slave・SSD1306 OLED・WS2812 NeoPixel（下記）の HIL が成功しています（いずれも機能確認で、電圧・波形・タイミング精度の実測ではありません）。未実施: ADC+DMA、GPIO 入力・割り込み（固定配線の都合で PC4 を駆動できず、PA1 のボタン入力のみ）、Standby、SPI helper（`ch32v003_SPI.h`）、CH32V005 / CH32V006 / CH32V007。

### Phase 3: デバイスとパッケージの拡張

QFN32のCH32V006、続いてCH32V005 / CH32V007へ展開します。各デバイス固有の周辺機能、ピンリマップ、制約は、それぞれの実機で検証します。

## リポジトリ構成

```text
okf/                    # 移植・検証で得たOpenKnowledgeFormatの知識（log/ に実験ごとの記録）
openspec/               # 変更提案・仕様（OpenSpec）。specs/ が現行仕様、changes/archive/ が完了した変更
samples_<device>_<framework>/  # デバイス・フレームワーク別のサンプル
hardware/
  pico-tester/          # 信号生成・測定を行うPicoファームウェアと自己検証スクリプト
  wiring.md             # 配線と安全手順（wiring-proposal.md は固定配線案）
hil/                    # 試験設定（configs/）と検証マトリクス（matrix*.json）
ch32hil/                # 書き込み・Pico操作・判定のPythonライブラリ
scripts/                # ビルド・書き込み（固定の externals/ch32fun を使う）
tests/unit/             # 実機なしの単体テスト
tests/hil/              # pytestによる実機試験（--hil を指定したときだけ実行）
externals/              # 参照元（ch32fun は Git submodule で固定）

# Git管理対象外
xprivate/               # PDF、変換データ、非公開の調査メモ
```

## 公開に向けた基準

公開するコードと知識は、次の基準を満たす状態を目指します。

- 対象デバイスとパッケージが明記されている
- 必要なツール、配線、実行方法が再現可能な形で記載されている
- 検証済みの範囲と未検証の範囲が区別されている
- 根拠となる一次資料と、その版が追跡できる
- 実機試験の条件、期待値、結果が追跡できる
- 第三者が安全上の注意を理解して試せる
- 元コードと利用するツール・ライブラリのライセンス条件を満たしている

## 現在地

2026-11-07 時点で、CH32V003F4P6 と CH32V002F4P6 を対象に、ビルド、書き込み（読み戻し照合付き）、Pico による観測、判定までを `uv run pytest --hil` で実行できます（実機を書き換えるため、明示したときだけ動きます）。ホストだけで動く単体テストは `uv run pytest` です。

- 実機で確認済み: 上記 2 デバイスでの周辺機能の HIL（詳細は [hil/matrix.json](hil/matrix.json)、[hil/matrix_ch32v002.json](hil/matrix_ch32v002.json)、実験ごとの記録は `okf/log/`）。
- Arduino Core CH32（公式 1.0.6）のサンプル: CH32V003 で 7 本、CH32V002 で 8 本を HIL 確認済み（`i2c_slave` は両デバイスで、`i2c_oled` は CH32V003 で問題あり）（下の「Arduino Core CH32 のサンプルの検証状況」）。
- 未着手・未確認: CH32V006 / CH32V005 / CH32V007、QFN32、ADC+DMA、Standby。電圧・波形・タイミング精度の実測は、ほとんど行っていません。
- 配線・電源の扱いは [hardware/wiring.md](hardware/wiring.md) の安全手順に従ってください。実機を使う試験は、Pico と DUT の電源・信号線を確認してから行います。

進捗に応じて、このREADME、各サンプルの文書、`okf/` の知識、HIL試験結果を一緒に更新します。

## ch32fun の helper を使うサンプルの検証状況

book-code の `i2c_oled`、`neopixel`、`i2c_slave`（ch32fun 版）が使う、`externals/ch32fun` 内の次の 3 種類のヘッダ（以下 helper）を、変更せずに使うサンプルを `samples_ch32v003_ch32fun/` と `samples_ch32v002_ch32fun/` に置いています。Pico が OLED や LED のふりをして、DUT が送った内容を観測します。

| サンプル | 使う helper | Pico の役割 |
|---|---|---|
| `i2c_slave_helper` | `examples/i2c_slave/i2c_slave.h` | I2C master |
| `ssd1306_i2c` | `extralibs/ssd1306_i2c.h`、`extralibs/ssd1306.h` | SSD1306 の模擬（I2C 0x3C） |
| `ws2812_spi` | `extralibs/ws2812b_dma_spi_led_driver.h` | WS2812 信号のデコード |

CH32V003 と CH32V002 の両方で、Pico が観測した内容が期待どおりであることを実機で確認しています（詳細: `hil/matrix.json`、`okf/log/2026-11-07-1956-*`、`2012-*`、`2027-*`、`2036-*`）。

**確認できていないこと**（「確認済み」は Pico が観測した送信内容が期待と一致した範囲に限ります）:

- 実際の OLED の表示、実際の LED の発光と色。
- `ssd1306_i2c` で helper 既定の I2C 1 MHz（Pico が何も受信できず、原因は未切り分け。`xfail` として記録）。100 kHz に下げた場合のみ確認済みです。
- WS2812 のタイミング規格への適合。Pico の測定は理論値より約 32 ns 小さく出ます（原因は未切り分け）。Pico の生成と測定が同じクロックを共有するため、自己検証は周波数の校正になりません。
- `ws2812_spi` の信号線が、フレームの後も High のまま待機する理由（観測のみ。LED のラッチへの影響も未確認）。
- 本のサンプルの色順コメントと helper のソースの食い違い（ソースを読んだ観察のみ）。
- 電圧・波形の実測、1 kΩ 経由の波形の質、DUT 差し替え時の電圧。
- 複数回のリセットを跨ぐ再現性（各確認は build・flash・reset を行った数回の実行のみ）。
- Pico 単体の自己検証で試していない異常系（SSD1306 模擬の不完全な転送や `overflow` の実機での発生など。ホストの単体試験でのみ確認）。

## Arduino Core CH32 のサンプルの検証状況

書籍第2章の Arduino IDE の手順を arduino-cli で再現し、book-code の Arduino Core CH32 用スケッチ（10 本）を `samples_ch32v003_arduino/` と `samples_ch32v002_arduino/` に置いています。書き込みは core 同梱の OpenOCD ではなく、固定 submodule の minichlink で行います。

```sh
./scripts/arduino.sh setup                    # arduino-cli 1.5.1 を .arduino/ に取得（チェックサム照合）
./scripts/arduino.sh core-install official    # 公式 Board Manager 配布の WCH:ch32v 1.0.6
make -C samples_ch32v003_arduino/blink_and_read build
uv run pytest --hil --hil-framework arduino -m 'hil and arduino' tests/hil/arduino --hil-port=/dev/serial/by-id/<PicoのID>
```

- **公式 core の追従判定: 追従済み**（CH32V00x、ビルドとソース比較の範囲）。書籍がサードパーティ版（robinjanssens 1.0.5-beta）を使う理由だった、公式にマージ済みで配布に未反映の PR 26 件は、すべて公式配布 1.0.6 に入っています。CH32V00x のボード定義も同じです。維持するサンプルは公式 1.0.6 に固定しています（[比較の記録](okf/log/2026-11-07-2102-arduino-core-supplier-compare.md)）。
- **供給元ごとの compile 結果**（サードパーティ 1.0.5-beta / 公式 1.0.6 / 公式リポジトリ d62c6b1）: 3 つとも同じ結果です。8 本が成功し、`i2c_oled` と `uart` はライブラリ「OLED SSD1306 - SH1106」が無いと失敗します（入れると成功）。
- **CH32V003F4P6 で HIL 確認済み**: `blink_and_read`、`adc`、`pwm`、`i2c_master`、`spi_master`、`i2c_slave-test_master`、`neopixel`（[hil/matrix_arduino.json](hil/matrix_arduino.json)）。`pwm` は PD4 が未配線なので PATTERN 2（PD2/PC4）、`spi_master` は書籍のスケッチに CS が無いので PC0 を CS として追加しています。`neopixel` は書籍のコードを直しています（データピンを PC6 に、送り順を MSB 先頭に、タイミングを WS2812B の規格の中央に合わせる。書籍のコードは LSB から送っています。[記録](okf/log/2026-11-07-2310-arduino-neopixel-timing.md)）。
- **CH32V003 + 公式 1.0.6 で見つかった問題**: `i2c_oled` は RAM が足りず描画バッファ（512 B）を確保できないため、正しく表示されません（ヒープ 504 B。GCC 15 の newlib の stdio 用構造体などが RAM を使う）。`i2c_slave` は、Wire の slave がときどき SCL を Low のまま固定し、バスが止まります。core の slave 処理が、割り込みの中で送信完了を待ち続けるためで、**CH32V002 でも起きます**（読み出しの直後に次の転送があると起きやすい）。`i2c_oled` の問題は CH32V002 では起きていません。HIL の対象外は `uart` だけです。
- **CH32V002F4P6: 流用で動作**。公式 1.0.6 には CH32V002 のボード定義がありません。CH32VM00X（CH32V006K8）の定義に、Flash/RAM サイズとスタック・ヒープの位置（`_eusrstack`、`_heap_end`）の上書きを加えて（`samples_ch32v002_arduino/arduino.mk`）、`blink_and_read`、`adc`、`pwm`、`i2c_master`、`spi_master`、`i2c_slave-test_master`、`i2c_oled`、`neopixel`（タイミングを CH32V002 用に調整）が動作しました（`i2c_slave` は上記の問題あり）（ADC は 12 ビット）。サイズの上書きだけでは、スタックが RAM の外になって動きません（[調査](okf/log/2026-11-07-2125-arduino-ch32v002-survey.md)、[実機](okf/log/2026-11-07-2156-arduino-ch32v002-hil.md)、[移植](okf/log/2026-11-07-2200-arduino-ch32v002-port-all.md)、[hil/matrix_ch32v002_arduino.json](hil/matrix_ch32v002_arduino.json)）。

**確認できていないこと**:

- 書籍の IDE の「Verified OK」表示など、Arduino IDE と WCH 版 OpenOCD に固有の挙動。
- I2C・SPI の転送後に DUT が Serial に出す値（判定はバス上の内容とタイミングで行っています）。`printf`（`USART_Printf_Init`）の出力は受信できませんでした。
- ADC の電圧・精度、PWM の周波数・デューティの校正値。`pwm` の PATTERN 3（PC6/PC5 のリマップ）は出力が出ません（書籍の記述と同じ）。
- サードパーティ版と公式リポジトリ版の実機での動作（ビルドの比較のみ。実機で確かめるのは公式配布だけとしました）。
- `neopixel` の実 LED での発光と色。CH32V003 ではバイトの切れ目の T0L が規格の上限を約 100 ns 超えます。CH32V002 では切れ目の T0L が 1280 ns です。
- `i2c_oled` の実物の OLED での表示（Pico の模擬で受けた内容のみ）、`uart`、別 core（arduino-wch32v003）の 3 本。
- CH32V002 用の専用ボード定義（流用と上書きで動かしています）。CH32V002 での Arduino HIL は各 3 回の実行です。

## 関連資料

- 移植元: [74th/ch32v003-book-code](https://github.com/74th/ch32v003-book-code)
- [CH32V002データシート](https://ch32-riscv-ug.github.io/CH32V006/datasheet_en/CH32V002DS0.PDF)
- [CH32V005 / CH32V006データシート](https://ch32-riscv-ug.github.io/CH32V006/datasheet_en/CH32V006DS0.PDF)
- [CH32V00xリファレンスマニュアル](https://ch32-riscv-ug.github.io/CH32V006/datasheet_en/CH32V00XRM.PDF)

