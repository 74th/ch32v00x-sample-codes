# CH32V006F8P6 の build → flash → measure

**状態（2026-11-08）: 識別値読取・flash・全必須 HIL を実機で確認済み（機能確認のみ）。** 結果は [実測ログ](../okf/log/2026-11-08-1335-ch32v006-hil.md)。開発ボードは CH32V003 検証と同一の物をブレッドボード上で差し替えて使った（ユーザー申告）。ボード上の物理位置・向きは記録対象外とし、MCU のピン番号（VDD=9、VSS=7、SWIO=18 ほか下表）で記録する（ユーザー判断。HIL は固定配線の各信号で合格）。資料照合の詳細は [差分表](../okf/peripherals/ch32v006-port-differences.md)。

## 差し替えの前に確認すること（資料と実物）

1. **型番の確認が最優先。** 手元のデバイスは「CH32V006F8P6」（ユーザー申告）。V006 データシート V2.0 の製品表にある TSSOP20 品は **CH32V006F8P7** で、F8P6 は載っていない。刻印と購入元の表記を確認して記録する（刻印の転記:＿＿＿）。F8P7 と同一ピン配置と仮定して書き込む前に、次の識別値読取で `0x006` を確認する。V005F6P6（TSSOP20、Flash 32K/RAM 6K）など別品なら中止する。
2. ピン配置（資料確認、F8P7 として）: PD4=1、PD5=2、PD6=3、PD7=4、PA1=5、PA2=6、VSS=7、PD0=8、VDD=9、PC0=10、PC1=11、PC2=12、PC3=13、PC4=14、PC5=15、PC6=16、PC7=17、PD1(SWIO)=18、PD2=19、PD3=20。CH32V002F4P6 と同じで、`hil/configs/ch32v006_gpio_blink.json` の物理ピンも同じ。F8P6 実物の互換は**未確認**。
3. 固定配線の全信号（BLINK=PC0、I2C=PC1/PC2、SPI=PC5/PC6/PC7、UART=PD5/PD6、PWM=PD2/PC4、ADC=PA2/PA1、SWIO=PD1）は、資料上 V006 の既定機能で成立する。PC5/PD7 は RST 機能と兼用の注記があり、実機で SPI_SCK(PC5) として使えることを SPI 試験で確認する（未確認）。

## DUT の差し替え手順（人が行う。自動化しない）

[CH32V002 の手順](ch32v002-reproduction.md#dut-の差し替え) と同じ。V006 固有の点だけ書く。

1. Pico と WCH-LinkE の USB を抜く。WCH-LinkE の通常操作は DUT に 3.3 V を出力する場合がある。電源断のまま DUT を外す。
2. DUT を CH32V006F8P6 に交換し、ピン 1 の向きと VDD=9、VSS=7、SWIO=18 を目視確認する。
3. WCH-LinkE だけを接続し、VDD–VSS が 3.3 V（公称）、SWIO–VSS が 0 V であることをテスターで確認して**値を記録する**。Pico の信号線は DUT 給電に使わない（Pico 側から電源を逆流させない）。
4. 識別値の読取（実機操作。WCH-LinkE は DUT を給電・リセットし得る）:

```sh
./scripts/ch32fun.sh build ch32v006
./scripts/ch32fun.sh flash ch32v006
```

`flash` は書き込み前に、固定 minichlink が出す `0x1ffff704` の 4 バイト（リトルエンディアン、上位 12 bit が型番）の上位型番が `0x006` であることを要求する。次のいずれかなら書き込まずに止まる: 未接続（`No detected chip.`）、識別値が `0x006` 以外（CH32V002/003 を取り違えた場合を含む）、読取不能、プログラマ異常。書き込み後は成果物サイズ全体を読み戻して一致を確認する。2026-11-08 の読取（[ログ](../okf/log/2026-11-08-1326-ch32v006-identifier-read.md)）で `1ffff704: 20 06 63 00`、上位型番 `0x006` を確認した（書き込みなしの読取）。F8P6 は F8P7 と同一ダイと扱う（ユーザー申告に基づく仮定）。取得できたら下位ビット（revision）とともに実測ログに記録し、上の資料照合と一致するか確認する。一致しない場合は共通化の判断を保留する。

5. Pico を接続し、安全状態（出力なし・プルなし）を確認してから HIL を実行する。最初は GPIO（`-m 'hil and gpio'`）。

```sh
uv run pytest --hil --hil-device ch32v006 --hil-framework ch32fun -m 'hil and gpio' tests/hil --hil-port=/dev/serial/by-id/<PicoのID>
```

## ホスト build（実測済み・実機なし）

```sh
make -C samples_ch32v00x_ch32fun/<sample> build PREFIX=riscv64-unknown-elf TARGET_MCU=CH32V006
```

成果物は `samples_ch32v00x_ch32fun/<sample>/build/ch32v006/`。全 12 サンプルが CH32V002/CH32V006 の両方で build でき、リンクメモリは CH32V002 が Flash 16 KB／RAM 4 KB、CH32V006 が Flash 62 KB／RAM 8 KB と表示された（[作業ログ](../okf/log/)の 2026-11-08 の記録を参照）。ツール側の設定値であり、実機の容量を測ったものではない。

## Arduino Core CH32（2026-11-08）

配線・給電は上記と同じ固定治具。型番確認（識別領域 `0x006`）は flash ガードが書き込み前に行う。build・flash・観測は別段階。

```sh
make -C samples_ch32v006_arduino/<sample> build          # 公式 core 1.0.6、FQBN WCH:ch32v:CH32VM00X_EVT:pnum=CH32V006K8,clock=48MHz_HSI
uv run pytest --hil --hil-device ch32v006 --hil-framework arduino -m 'hil and arduino' \
  tests/hil/arduino --hil-port=/dev/serial/by-id/<PicoのID> --hil-run-dir=<run用ディレクトリ>
```

- 全 10 スケッチが build でき、`blink_and_read`・`adc`・`pwm`・`i2c_master`・`spi_master`・`i2c_slave_test_master`・`i2c_oled`・`neopixel`・`uart` が実機で確認済み（機能のみ）。`i2c_slave` は 006 で固着を再現せず（8 回の HIL と 595 取引、試した条件に限る）、通常対象の成功には数えない。進捗の正本は [hil/matrix_ch32v006_arduino.json](../hil/matrix_ch32v006_arduino.json)。
- 注意点: `pwm` は PC4 が無信号のため PD2＋PC0 の組（ユーザー判断）。`uart` は Pico がセンサーと OLED 模擬を兼ねる（判定の仕組みはテスト冒頭）。`neopixel` は 002 と同一の機械語・同一の測定値（バイト境界 L0 1280 ns、上限 1300 ns）。実 OLED・実 LED・実センサーは未使用。
- 結果の保存先は `<run>/ch32v006/arduino/<sample>/<variant>/`（[hil/README.md](../hil/README.md)）。

## WCH 公式 SDK（2026-11-08）

```sh
uv run python scripts/wch-sdk.py build --all                                     # 006 の 14 例を含むメモリ・SDK 参照元の検査
uv run python scripts/wch-sdk.py build   --device ch32v006 --sample blink        # 以下 3 つは別段階
uv run python scripts/wch-sdk.py flash   --device ch32v006 --sample blink        # 型番 0x006 を確認、全量 readback を照合
uv run python scripts/wch-sdk.py observe --device ch32v006 --sample blink --output <run>/blink-observe.json
uv run pytest --hil --hil-device ch32v006 --hil-framework wch -m 'hil and wch' \
  tests/hil/wch --hil-port=/dev/serial/by-id/<PicoのID> --hil-run-dir=<run用ディレクトリ>
```

- 基準 blink と書籍 13 例が実機で確認済み（機能のみ。[hil/matrix_ch32v006_wch.json](../hil/matrix_ch32v006_wch.json)、[samples_ch32v006_wch/README.md](../samples_ch32v006_wch/README.md)）。
- 006 だけの例外（ユーザー判断）: `pwm` は第 2 チャネルを TIM2_CH3 on PC0 に変更、`timer_dma` は PC4 SA を記録のみ、`watchdog` は PA1 保持を 3.5 s に延長（`GPIO_DRIVE` は 1 回 2000 ms が上限なので連鎖）。いずれも PC4 の無信号と IWDG のタイムアウトが長いという 006 の DUT での観測による（原因未特定）。
- 保存先は `<run>/ch32v006/wch/<sample>/<variant>/`。結果の `meta` に `sdk`・`compiler`・`memory`・`source_revision`・成果物 SHA-256 を含む。

## 未確認・範囲外（Arduino / WCH 共通）
- ADC の精度・校正、時間の精度、Sleep/Standby の消費電流、実 OLED・実 LED・実センサー、WS2812 規格適合。
- **PC4 の無信号の原因**（接触・DUT 個体・F8P6 のピン配置・Pico GP15 側のいずれかは未切り分け）。
- F8P6 の資料上の位置付け（F8P7 と同一ダイは前 change のユーザー判断に基づく仮定）、PC5/PD7 の RST 設定・オプションバイト。
