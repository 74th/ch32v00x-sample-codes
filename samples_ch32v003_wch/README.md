# WCH公式SDKのCLIビルド（CH32V003）

MounRiver StudioのGUIなしで、WCH公式SDKをWCH GCC 15.2.0からビルドする最小サンプル。
2026-11-08にCH32V003でビルド、固定minichlinkによる書き込み・全量読み戻し、PicoでのGPIO点滅観測を実施した。
CH32V002はこの構成では未対応・未検証。

```sh
# リポジトリルートから。各段階は独立して実行する。
uv run python scripts/wch-sdk.py build
uv run python scripts/wch-sdk.py flash
uv run python scripts/wch-sdk.py observe
```

`flash`は接続中のCH32V003のプログラムを書き換える。ビルドは別途先に行う。
書き込み器は`externals/ch32fun`に固定し、`scripts/ch32fun.sh programmer`でrevisionと環境を確認する。
既存HILの`Dut.flash`を共用し、期待チップの検出と`Image written.`の確認を通し、全量読み戻し照合後にリセットする。
SDKのビルドは今回の公式SDK対応の依頼に基づく別構成であり、ch32funの起動コードやヘッダには依存しない。

観測は既存固定配線のPC0（DUT）→1 kΩ→GP5（Pico）、共通GNDを前提とする。
Pico firmware v2の`discover`、`CAPS`、`RESET_SAFE`、`GPIO_SAMPLE`を使う。
300点を10 ms間隔で取得し、窓の両端を除いた完全なHigh/Low区間が4個以上、各400～600 msであることを確認する。
電圧や波形の精度測定ではない。サンプルはPC0の500 msごとの点滅だけで、ボタンやUARTは含めない。

## サンプル選択と共通ビルド設定

引数なしの`build`/`flash`/`observe`は従来どおりCH32V003の`blink`を対象にする（互換性を維持）。
`--device`と`--sample`で別サンプルを選べる。不正な名前、存在しないサンプル、`samples_<device>_wch`が無いデバイス（CH32V002は後段）は、ビルドや書き込み器アクセスの前にエラーになる。
`observe`は`blink`専用で、他のサンプルは`--hil-framework wch`のHILテストで観測する。
接続チップが期待型番と異なる場合や成果物が無い場合は`Dut.flash`が書き込み前に中止する（単体テストで確認）。

```sh
uv run python scripts/wch-sdk.py build --sample uart
uv run python scripts/wch-sdk.py flash --device ch32v003 --sample uart
```

各サンプルの`Makefile`は`../wch.mk`を取り込む。追加で必要な公式ドライバだけを`PERIPH := adc dma`のように宣言し、`gpio rcc usart`（公式`debug.c`の依存）は常に含まれる。
SDKの全ヘッダ、サンプルの`*.h`、`wch.mk`、リンカスクリプトのいずれかが更新されると再ビルドされる（`ch32v00x_rcc.h`のtouchで再ビルドを確認）。
`wch.mk`抽出後もblinkの結果はFlash 1,092 B／RAM 268 Bで変わらない。
HILは`uv run pytest --hil --hil-framework wch`で選択する（WCH GCCは各Makefileが決め、ch32fun/Arduino用の`PREFIX`は渡さない）。

## ツールチェーン

既存の公式Arduino環境が導入したWCH GCCを共用する。Arduino coreのコードはリンクしない。
既定パスは`.arduino/official/data/packages/WCH/tools/riscv-wch-gcc/15.2.0`。
未導入環境では既存のセットアップ手順を利用できる（ネットワーク接続が必要）。

```sh
./scripts/arduino.sh setup
./scripts/arduino.sh core-install official
```

別のWCH GCCを使う場合は直接Makeに指定する。検証済みは上記15.2.0だけ。

```sh
make -C samples_ch32v003_wch/blink build TOOLCHAIN=/path/to/toolchain
```

`-march=rv32ec_zicsr -mabi=ilp32e`。公式Startupが`SystemInit()`を呼ぶ。
クロックは外部水晶不要のHSI＋PLL 48 MHz、Flash 16 KB／RAM 2 KB、スタック256 B。
ビルド結果は`blink/main.elf`、`main.bin`、`main.hex`、`main.map`。
公式Delay関数版の結果はFlash 1,092 B、RAM 268 B（初期化データ8 B＋BSS 4 B＋スタック256 B）。

## SDKの転用範囲

GPIO/RCC、Coreヘッダ、Startup、System、リンカスクリプトと、公式Delay関数のためのDebug・USARTの計14ファイルを公式SDKからコピーした。
起動時のクロック設定後に`Delay_Init()`を一度呼び、`Delay_Ms(500)`で待機する。
`debug.c`は無改変で、UART関連の宣言・ドライバも一緒にコンパイルするが、未使用関数はリンク時に除去される。
`nm`で`Delay_Init`/`Delay_Ms`の存在と、USART関数・`_write`・`_sbrk`が残らないことを確認した。
公式`debug.c`の`_write`に未使用引数`fd`の警告が1件出るが、コピー元を保持している。
`System`だけHSI設定に変更し、その他のコピー元は無改変。第三者のMakefileや変換スクリプトのコードはコピーしていない。
出所revision、コピー前SHA-256、利用条件、参考URLは[PROVENANCE.md](PROVENANCE.md)に記録した。
ビルド時に`externals/ch32v003`を参照しない。

現行のコピー対象にはWCH製マイコンへの使用条件が記載されている。Apache-2.0として扱わない。

## 書籍の公式SDK例との対応

正本は`hil/matrix_wch.json`（書籍`*-wch_sdk`の全13例を一対一で追跡。READMEとの整合は単体テストで照合）。`blink`は上記CLI基準で、この表の13行とは別。状態は`hil-verified`（実機のHILで観測）、`build-only`（ビルドのみ）、`not-ported`（未実装）。`hil-verified`でも、各行の「制限・残課題」にある未観測事項は未確認のまま。

| 書籍ディレクトリ | 維持名 | 状態 | 根拠（作業ログ） | 検証内容・制限・残課題 |
|---|---|---|---|---|
| `blink_and_read-wch_sdk` | `blink_and_read` | hil-verified | [2026-11-08-0055-wc…](../okf/log/2026-11-08-0055-wch-sdk-blink-and-read.md) | 公式GPIO入力・Delay_Msで移植。ログはSDI printfの代わりにUSART printf(PD5)。実機観測済み（CH32V003）。判定: PD5 UART 115200: init/start/loop 0/loop 1と連番; PC0 500/500 ms(±100 ms); PA1 low(GP12)で3 s停止、解放後に再開 |
| `uart-wch_sdk` | `uart` | hil-verified | [2026-11-08-0058-wc…](../okf/log/2026-11-08-0058-wch-sdk-uart.md) | 書籍のCO2コマンド・checksum・値変換を実装。PD5/PD6、Picoがセンサー役。診断printfとは混在させず結果は往復後にTXへ出力。実機観測済み（CH32V003）、実センサーは未確認。判定: Pico(9600 8N1)がセンサー役: 自己校正cmd一致→start; 読み出しcmd一致→既知フレームでCO2:  1234 ppm; checksum不正でinvalid checksum; 無応答でread timeout; uart_errors 0 |
| `adc-wch_sdk` | `adc` | hil-verified | [2026-11-08-0059-wc…](../okf/log/2026-11-08-0059-wch-sdk-adc.md) | 公式ADCで2チャネル・校正・変換を移植。実機観測済み（CH32V003）。電圧の絶対精度は未確認。判定: RC充放電: High駆動>=700/Low駆動<=300（0..1023）、2チャネル独立; 10 msパルス累積3段が>=20ずつ増加; 外部基準なし |
| `adc_dma-wch_sdk` | `adc_dma` | hil-verified | [2026-11-08-0100-wc…](../okf/log/2026-11-08-0100-wch-sdk-adc_dma.md) | 書籍の2チャネルscan+DMA(circular)を移植（adc_bufはvolatile）。実機観測済み（CH32V003）。DMAレジスタの直接読みは未実施。判定: 静的: ADC_DMACmd/DMA_Init/DMA_Cmdあり・ADC_GetConversionValueなし; PA1=x/PA2=yの順序と更新を再起動なしで確認; 10 msパルス累積3段が>=20増; 外部基準なし |
| `i2c_master-wch_sdk` | `i2c_master` | hil-verified | [2026-11-08-0102-wc…](../okf/log/2026-11-08-0102-wch-sdk-i2c_master.md) | 書籍のSHT31コマンド・応答・変換を移植。PC1/PC2、最終バイトNACKを追加。Pico SHT31模擬で実機観測済み（CH32V003）。実SHT31は未確認。判定: Pico=SHT31(0x44): 30a2,3041,2400+6B read(sent=6); 出力'Temperature: 24, Humidity: 50'一致; 0x45無反応; 周期4.8..6.0 s |
| `i2c_slave-wch_sdk` | `i2c_slave` | hil-verified | [2026-11-08-0104-wc…](../okf/log/2026-11-08-0104-wch-sdk-i2c_slave.md) | 書籍のレジスタ型slaveを公式I2C割り込みで移植。実機観測済み（CH32V003、4回中3回連続成功＋repeated START）。UARTログ行は未判定。判定: 0x10 ACK/0x11 NACK; reg0x20=00102030; write0x10 aabbccdd読み戻し; 部分読み; repeated STARTで0x20/0x10/0x22を読む |
| `spi_master-wch_sdk` | `spi_master` | hil-verified | [2026-11-08-0106-wc…](../okf/log/2026-11-08-0106-wch-sdk-spi_master.md) | 書籍のreset/config/read・符号付き温度変換を移植。CSはPC0・フレームごとに戻す（Pico slave制約）。実機観測済み（CH32V003）。実ADT7310は未確認。既知の間欠現象: リセットフレーム先頭ビットが稀に欠落（7fff、17回中2回）、原因未確認。判定: Pico SPI slave mode0: reset frame先頭2Bがffff、CS lowが約400 ms後にhigh、read frame 0000が約1 s間隔; 返答f380/0c80に対しUARTがraw_int -400/400とtempを出力 |
| `pwm-wch_sdk` | `pwm` | hil-verified | [2026-11-08-0116-wc…](../okf/log/2026-11-08-0116-wch-sdk-pwm.md) | 書籍のTIM1 PWM(CH1/CH4)を公式APIで移植。CH1=PD2、CH4=PC4(USE_REMAP 0)。実機観測は粗い（Pico GPIO_PULSE、1 us分解能）。PC4は書籍式がperiod超過で多くが常時High。判定: 周期9..12 us（nominal 10.67 us）、PD2のdutyが>=35 %にわたり3段階以上、PC4にランプ読みと常時High、分解不能読みは除外; 粗い・未校正 |
| `timer_blink-wch_sdk` | `timer_blink` | hil-verified | [2026-11-08-0118-wc…](../okf/log/2026-11-08-0118-wch-sdk-timer_blink.md) | 書籍のTIM1/TIM2更新割り込みを移植（LEDはPC0、NVICの範囲外ダンプ2行を省略）。両構成を実機観測済み（CH32V003）。レジスタ値の実測は未確認。判定: tim1/tim2両構成をmake clean後に書き込み: PC0 500/500 ms(±100 ms); UARTイベント文言(1sec event/500ms event)×2以上; ELFでTIM1_UP=35/TIM2=38がベクタに入りmret |
| `timer_dma-wch_sdk` | `timer_dma` | hil-verified | [2026-11-08-0123-wc…](../okf/log/2026-11-08-0123-wch-sdk-timer_dma.md) | 書籍のTimer要求DMAによる4桁走査を公式APIで移植（printf削除）。ピン別High比率で実機観測（CH32V003）。SB/SC/SEL3/SDPと表示器・桁同期は未観測。判定: 各ピンのHigh比率(300点,1.17 ms間隔): SEL1/SEL2/SEL4/SA/SD=0.75, SE/SG=0.5, SF=0.25 (±0.10)、静的ならず; 未観測: SB,SC,SEL3,SDP,表示器 |
| `watchdogtimer-wch_sdk` | `watchdog` | hil-verified | [2026-11-08-0127-wc…](../okf/log/2026-11-08-0127-wch-sdk-watchdog.md) | 書籍のIWDG給餌/停止を公式APIで移植（IWDG_SetReload、リセット要因表示を追加）。給餌停止1 s: 稼働、2 s: IWDGリセットを実機観測（CH32V003）。時間窓は1.6〜2.5 s。判定: cause=otherでループ番号が増加・PC0 250/250 ms; PA1 low 1 s: リセットなし; 2 s: cause=IWDGでループ番号が0から; 時間窓は約1.6〜2.5 s |
| `sleep_mode_blink-wch_sdk` | `sleep_wake` | hil-verified | [2026-11-08-0130-wc…](../okf/log/2026-11-08-0130-wch-sdk-sleep_wake.md) | 書籍のSleep(WFI)+TIM1復帰を移植（LEDはPC0、core_riscv.cを追加コピー）。UART順序tim→awake→sleepとLED 2 s周期を実機観測（CH32V003）。消費電力は未測定。判定: ELFにwfi; UART行がtim→awake→sleepの循環で32 Bに>=1.8 s; PC0半周期1.6..2.4 s; 消費電力は未測定 |
| `standby_mode_blink-wch_sdk` | `standby_wake` | hil-verified | [2026-11-08-0135-wc…](../okf/log/2026-11-08-0135-wch-sdk-standby_wake.md) | 書籍のAWU+Standbyを公式APIで移植。wake間隔約2 s・カウント連番(リセットではなく再開)・wake直後の先頭1バイト化けを実機観測（CH32V003）。Standby中はminichlink接続不可、電源入れ直し+blink書き込みの復旧手順をテストに組込み。消費電流は未測定。判定: wake3回のカウントが連番、間隔1.7..2.3 s、LED半周期1.6..2.4 s; 復旧: LinkE給電を入れ直しblinkを書き込み・検出・全量読み戻し |
