# Design

## Context

動機と範囲は [proposal.md](proposal.md) を参照。現状の観察（実機未操作）:

- `samples_ch32v002_ch32fun/` は12サンプル。全Makefileが `TARGET_MCU := CH32V002`、生成リンカスクリプトが `generated_ch32v002.ld`。`main.c` と `funconfig.h` は共通化候補だが、GPIOサンプルの起動表示にはCH32V002の文字列がある。
- 固定ch32fun `b28d285460ce052a179dba8f4a22c6f73ff8e328` の `ch32fun.mk` はCH32V002とCH32V006をともに扱い、CH32V003とは別の `CH32V00x` 定義を使う。`ch32fun.ld` の対応設定はCH32V002がFlash 16 KiB / RAM 4 KiB、CH32V006がFlash 62 KiB / RAM 8 KiB。これはツール実装の確認で、実機容量の実測ではない。
- 同minichlinkのCH32V006検出分岐は型番マスク `0x00600000` と識別領域 `0x1ffff704` を使う。CH32V002では上位12ビットを `0x002` と照合する実装と実機履歴がある。CH32V006の実機識別値は未取得。
- `ch32hil/devices.py` は実機識別と `samples_<device>_<framework>` のパスを結合している。`Dut.build()` は現在ターゲットをMakeへ渡さず、成果物をサンプル直下の `main.bin` として扱う。`scripts/ch32fun.sh` も独自に同じパスを組み立てる。
- HILの期待値生成にも配置依存がある。例えば `ch32hil/expected.py` のSSD1306期待値はCH32V003サンプルを参照する。共通配置への移行で期待値とDUT側のsceneが乖離しないよう確認する。
- CH32V002マトリクスには12サンプルと未移植の `gpio_input` がある。通常の11テストにhelperの必須3テストを足した14件が基準で、SSD1306 helper既定1 MHzの参考試験は別扱い。
- 現行仕様はCH32V002の旧配置を明示的に要求するため、その要件と差分記録のパスをdelta specで更新する。現行HIL仕様のフレームワーク列挙は実装のwch追加に追いついていないが、本changeではCH32V006/ch32funだけを追加する。

照合に使う一次資料の入口はWCH公式 [CH32V006DS0](https://www.wch-ic.com/downloads/CH32V006DS0_PDF.html)、[CH32V002DS0](https://www.wch-ic.com/downloads/CH32V002DS0_PDF.html)、[CH32V00XRM](https://www.wch-ic.com/downloads/CH32V00XRM_PDF.html)、[QingKeV2 manual](https://www.wch-ic.com/downloads/QingKeV2_Processor_Manual_PDF.html)。ローカル公式SDK参照元は `externals/ch32v002_004_005_006_007` revision `a835ede9ff3e2dca2c6aa652809b85c9775475d2`。SDKは調査専用。ウェブの製品ページはJSが必要で本文取得できなかったため、F8P6の物理ピンや資料版・ページの照合済みとはしていない。資料本文と変換物は `xprivate/` に留める。

## Goals / Non-Goals

**Goals:** アプリケーションソースを共有できるかを先に検証し、実機名、ビルドターゲット、ソース配置、成果物、証跡の関係を明示する。ソース共通化とメモリ容量の違いを両立する。

**Non-Goals:** コア一致によるバイナリ互換の証明、全Flash/RAMの容量試験、ソース分岐を増やしてでも共通ディレクトリに収容すること。周辺機能の機能確認の範囲を広げることはproposalの対象外事項に従う。

## Decisions

### 1. 共通化の意味と判定時点

「同じコード」は `main.c`、`funconfig.h`、sceneなどのアプリケーションソースを両デバイスで共有し、デバイス別の処理分岐を追加しないこととする。起動表示を汎用化するなど両ターゲットに共通の修正は許容する。Make側のターゲット、メモリ定義、デバイス名のメタデータは区別する。CH32V002のバイナリをCH32V006へそのまま書く案は、CH32V006のメモリを使った正規リンク設定を検証できないため採用しない。

まず旧配置のソースを使って `TARGET_MCU=CH32V006` を指定できるビルド経路を追加する。ソースのコピーは作らず、CH32V006の暫定 `sample_root` は旧CH32V002配置を指す。これは再利用可能性の検証用であり、共通化済みの表明ではない。全12サンプルの両ターゲットbuildと両実機必須HILが同一ソースrevisionで成功したら、ディレクトリ名を変更する。必要なデバイス別処理が判明したら、その最小差分を残して移行を保留する。保留中は移行タスクを完了にせず、proposal/spec/design/tasksを結果に合わせて更新してから後続方針を決める。

### 2. 実デバイスとソース配置を分離する

`Device` にch32fun用の明示的なソースルートを持たせ、`ch32v002` と `ch32v006` が同じ場所を参照できるようにする。`name`、`part`、`target_mcu`、`chip`、`chip_id_type`、設定・マトリクスは別に保つ。ディレクトリ名を `00x` にしたために実機名やCLIを `ch32v00x` に変えることはしない。

CH32V006の設定は `hil/configs/ch32v006_gpio_blink.json`、マトリクスは `hil/matrix_ch32v006.json` とする。公式資料と実基板を照合してから物理ピン定義を登録する。Arduino/WCHのパス解決は従来どおりとし、CH32V006との未対応の組み合わせは実機アクセス前にエラーとする。

### 3. 生成物はターゲットごとに分離する

各サンプルは共通の小さなmake設定を使い、対応ターゲットをCH32V002/CH32V006に限定する。直接makeするときの既定はCH32V002とし、CLI/HILからは常に `TARGET_MCU` を明示する。成果物はサンプル内の `build/<target>/main.{elf,bin,hex}`、生成リンカスクリプトも同ディレクトリに置く方針とする。固定ch32funの `TARGET` と `GENERATED_LD_FILE` をプロジェクト側で設定し、submoduleを書き換えない。`ch32fun.mk` は `FILES_TO_COMPILE := ... $(TARGET).c ...` とするため、出力パスを変えた後も入力が既存の `main.c` を指すよう、include後にプロジェクト側で入力リストを明示する。出力先ディレクトリはbuild前に準備する。

ターゲット別の `binary` をHILとflash経路で解決する。SSD1306の `HELPER_CLOCK` 切り替えは既存の再build方針を維持し、ターゲット・variant・主要make設定と成果物hashの対応も保存する。異なる設定の古い成果物をflashだけで再利用しないよう確認する。共通直下 `main.bin` を探すfallbackは設けない。ターゲット分離だけでmake設定変更を検知できるとは考えず、設定が変わる場合は当該ターゲットを再生成する。

ターゲット切り替えのたびに全サンプルをcleanする案より、別ターゲットの成果物を保持でき、意図したflash対象を確認しやすい。既存パスへのsymlink互換層は置かず、破壊的変更として文書化する。

### 4. 識別はソース配置に依存させない

CH32V006では `Detected CH32V006` に加え、`0x1ffff704` の読取値上位12ビットが `0x006` であることをflash前に要求する。資料および実機読取を照合してから有効化し、下位ビットは対象型番・revisionの証跡として記録する。検出・識別の不一致、未検出、読取不能、偽成功を模擬テストで確認する。CH32V002選択でCH32V006接続、その逆を、flashを呼ばない模擬ケースとして検証する。

HILだけでなく `scripts/ch32fun.sh flash ch32v006` も同じ条件で停止させる。CH32V006のflash後は必ず成果物全体のreadbackを照合してから観測する。minichlinkの情報取得自体がリセット・給電に影響し得るため、識別値取得も実機操作として配線確認後に行う。

### 5. 既存治具の能力を使って順に検証する

Picoは現在のprotocol v2と既存の自己検証済み能力を使用し、再列挙待ちは `discover` と `timeouts.pico_enumeration` を使う。新しい治具能力は追加しない。差し替えは人が電源断して実施し、WCH-LinkEの3.3 V給電、Pico信号線の逆流給電、基板側負荷を確認する。

| 段階 | 対象 | 判定と進行条件 |
| --- | --- | --- |
| 資料・配線 | F8P6刻印、電源、GND、SWIO、全HIL信号 | ピン・AF・リマップ・電圧条件を照合し、差し替え手順を記録 |
| ホスト | 全12サンプル、両ターゲット | build成功、ELF/リンクメモリ、設定切り替え、識別異常系を確認 |
| 最小実機 | blink_and_read | 型番一致、flash、全量readback、PC0点滅。続いてPA1入力と期待不一致検出 |
| 通信 | uart、i2c_master/slave、spi_master | 既存の通信内容・方向・ACK/NACK・timeout判定 |
| 周辺機能 | timer_pwm、adc、watchdog、sleep_wake | 既存HILの期待値で機能確認 |
| helper | i2c_slave_helper、ssd1306_i2c、ws2812_spi | 既存3必須試験。SSD1306 100 kHzが主判定、1 MHzは参考結果 |
| 回帰 | CH32V002、移行後CH32V006、CH32V003 | 共通ソースの両機能確認と、既存CH32V003経路の維持 |

各段階の失敗は次段階の成功で隠さない。CH32V002のADCは既に12-bit値を `>> 2` してPicoの0..1023報告形式に合わせているため、CH32V006でも同じ意味であることを資料・実機で確認する。新デバイスに合わせて許容差を広げて通すことはしない。1 MHz試験の既存xfailをCH32V006での既知不具合の実測として転用せず、デバイス別の実行結果・XPASSも記録する。

### 6. READMEの記載方針

実装完了後は、検証マトリクスへのリンクを持つ型番別の表を設け、「共通ソースをデバイス別にbuildする」「CH32V003は別配置」「00xのうち実機確認対象はCH32V002F4P6/CH32V006F8P6」と明記する。現在地・ロードマップ・helper節のCH32V006未着手表記を、実際に達成した範囲で更新する。過去ログは改変せず、現行手順に旧→新パス対応を示す。

共通化成立時に提供するコマンド例（現時点では未実装）:

```sh
make -C samples_ch32v00x_ch32fun/adc build TARGET_MCU=CH32V006 PREFIX=riscv64-unknown-elf
./scripts/ch32fun.sh build ch32v006
./scripts/ch32fun.sh flash ch32v006
uv run pytest --hil --hil-device ch32v006 --hil-framework ch32fun -m 'hil and gpio' tests/hil --hil-port=/dev/serial/by-id/<PicoのID>
uv run pytest --hil --hil-device ch32v006 --hil-framework ch32fun tests/hil --hil-port=/dev/serial/by-id/<PicoのID>
```

## Risks / Trade-offs

- [F8P6の資料版による表記・ピン差分、実基板の追加負荷] → 型番・基板・資料版とページを照合し、未確認のピン互換を前提に書き込まない。
- [同じコアでも周辺機能やクロックが違う可能性] → 使用箇所別の差分表と段階的HILで判断し、アプリケーション分岐が必要なら移行保留。
- [共通化の検証中にCH32V002が回帰する] → 同一ソースrevisionでCH32V002の全必須HILを再実行し、過去実績だけで代替しない。
- [名前変更で過去のmakeコマンドが壊れる] → README・現行手順・テスト・設定を一緒に更新し、旧パスの移行先を明記。
- [Pico機能確認を精度保証と誤解する] → ADC精度、時間校正、消費電流、実デバイス表示・発光は未確認と明記する。

## Migration Plan

1. 旧配置のままターゲット別buildとCH32V006選択・識別・設定・マトリクスを追加する。ホスト試験後に、同じソースをCH32V006実機で段階検証する。
2. 同一ソースrevisionでCH32V002の全必須HILを再実行し、全12サンプルの共通化条件を判定する。不成立なら移行保留とする。
3. 成立したら `samples_ch32v002_ch32fun` を `samples_ch32v00x_ch32fun` へ移動し、両デバイスのソースルート、現行コード・設定・マトリクス・文書を更新する。アーカイブ済みOpenSpecと過去ログ内の旧パスは維持する。
4. 新配置から両ターゲットbuildと両実機HILを再確認する。CH32V003でも既存HILを回帰確認し、READMEとOKFを最終状態に合わせる。
5. 戻す場合は配置・参照変更を一体で戻し、変更前後の検証履歴を残す。DUTファームウェアを戻す操作は正しい実機選択と型番照合を通す。実機が未接続の場合はその段階を未完了として記録する。
