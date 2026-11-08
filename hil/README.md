# HIL 設定

`configs/gpio_blink.json` は CH32V003F4P6、`configs/ch32v002_gpio_blink.json` は CH32V002F4P6 と Pico の固定配線を宣言する公開可能な設定。`dut.device` と `sample`、Pico USB VID/PID と `selection=explicit_or_unique`、ピン・物理ピン・方向・直列抵抗、I2C pull-up と ADC RC、電源と公称電圧、タイムアウト、readback 方針を持つ。`readback` は `required`、`optional`、`disabled`。ポートは実行時 `--hil-port` で指定できる。

電圧の `source=declared_unmeasured` は設定値が配線案の公称値であり、実測・安全確認ではないことを示す。設定の整合性チェックは物理配線、電圧、レベル変換や逆給電を確認できない。使用前の手順は [配線資料](../hardware/wiring.md) と [固定配線案](../hardware/wiring-proposal.md) を参照する。

## 対象デバイスの選択

HIL の対象は `--hil-device {ch32v003,ch32v002,ch32v006}` で選ぶ。既定は `ch32v003` で、指定しない既存コマンドは従来どおり `configs/gpio_blink.json`、`samples_ch32v003_ch32fun/`、`Detected CH32V003` を使う。`--hil-config` を省略すると選択デバイスの既定設定（CH32V002 は `configs/ch32v002_gpio_blink.json`）を使う。設定の `dut.device` と `--hil-device` が食い違う場合や未対応のデバイス名は、実機に触れる前にエラーで止まる。デバイス固有値（型番、`TARGET_MCU`、物理ピン、サンプル・設定・マトリクスの場所）は `ch32hil/devices.py` にまとめている。

CH32V002 では、固定 minichlink の `Detected CH32V002` に加えて識別領域 `0x1ffff704` の上位型番 `0x002` を書き込み前に確認し、一致しない・読めない場合は書き込まずに `flash` 段階で失敗する。選択デバイスにサンプルがない、またはそのデバイスのマトリクス（CH32V002 は [matrix_ch32v002.json](matrix_ch32v002.json)）で `not-ported`／`excluded` のテストは、理由付きで skip される（成功ではない）。結果メタデータの `target` に対象デバイスを記録する。

```sh
uv run pytest --hil --hil-device ch32v002 -m 'hil and gpio' tests/hil --hil-port=/dev/serial/by-id/<PicoのID>
```

### CH32V006

`--hil-device ch32v006` は CH32V006F8P6 用（[設定](configs/ch32v006_gpio_blink.json)、[マトリクス](matrix_ch32v006.json)）。`--hil-framework ch32fun`（既定）に加えて `arduino`／`wch` を選べる。Arduino は `samples_ch32v006_arduino/` と [matrix_ch32v006_arduino.json](matrix_ch32v006_arduino.json)（10 行）、WCH は `samples_ch32v006_wch/` と [matrix_ch32v006_wch.json](matrix_ch32v006_wch.json)（書籍 13 行。基準 blink は README と実測ログで追跡）を使う。両マトリクスは他デバイスの結果を転記せず、未移植（`not-ported`、HIL は理由付き skip）と build のみ（`build-only`）を区別する。ch32fun のアプリケーションソースは CH32V002 と共通の `samples_ch32v00x_ch32fun/`（旧 `samples_ch32v002_ch32fun/`）を使う。共通化の判定は [ログ](../okf/log/2026-11-08-1340-ch32v00x-shared-source-decision.md)。`00x` は配置名で、CH32V005/007 などの未検証デバイスへの対応表明ではない。

CH32V006 の Arduino/WCH の結果は `--hil-run-dir=<dir>` の下に `<dir>/ch32v006/<framework>/<sample>/<variant>/<name>.json` として保存する（variant 未指定は `default`）。同名サンプルでもフレームワーク・variant は別ファイルになり、run は `<dir>` で区別する（例: `--hil-run-dir=xprivate/runs/2026-11-08-1600-ch32v006-arduino`。実行ごとに別ディレクトリを使う）。結果の `meta` には `source_revision`（git HEAD、未コミット変更は `+dirty`）、`compiler`、Arduino は `fqbn`・`core`・`arduino_cli`（OLED はライブラリ版も）、WCH は `sdk`（リポジトリ・revision）・`memory`（`main.map` の FLASH/RAM）、さらに `dut` に成果物 SHA-256 と識別値を記録する。CH32V003/002 の保存先は従来どおりフラットな `<dir>/<name>.json`。実装は `ch32hil/evidence.py`。

- CH32V002/CH32V006 の成果物はサンプル内の `build/<device>/main.{elf,bin,hex}`（生成リンカスクリプトも同じ場所）に分かれ、HIL は `TARGET_MCU` を明示して build する。他ターゲットの成果物へはフォールバックしない。CH32V003 は従来どおり `samples_ch32v003_ch32fun/<sample>/main.bin`。
- 書き込み前に `Detected CH32V006` と識別領域 `0x1ffff704` の上位型番 `0x006` を要求し、誤接続（CH32V002 等）・未接続・読取不能は書き込まずに `flash` 段階で失敗する。HIL テストは各段階で全量 readback を行う。識別値の実機読取は未取得。
- 結果（`run.json` の `meta.dut`）に、`device`・`part`・`framework`・`build_target`・`source_dir`・`artifact`・`artifact_sha256`・`variant`（make 変数）・`chip_id` を記録する。002/006 を区別して追跡できる。
- マトリクスは CH32V002 の全 13 行に対応する。実測前は `build-only`（`excluded` の `gpio_input` を除く）で、CH32V002 の結果は転記しない。`hil-verified` にするには CH32V006 の実機ログ（`evidence`）が必要。`gpio_input` の除外理由は CH32V002 と同じ（固定配線で PC4 を Pico から駆動しない）。
- SSD1306 の 100 kHz（主判定）、i2c_slave_helper、WS2812 が helper の必須 3 試験。SSD1306 `helper_1mhz` は参考結果で、CH32V002 の `xfail` を CH32V006 の既知不具合として転用せず、実行結果（XPASS を含む）を別に記録する。
- 選択例（実機接続と配線確認の後に実行する。この change の実機段階は未実施）:

```sh
uv run pytest --hil --hil-device ch32v006 --hil-framework ch32fun -m 'hil and gpio' tests/hil --hil-port=/dev/serial/by-id/<PicoのID>
```

DUT は一度に一つだけ接続する。CH32V003 と CH32V002 の差し替えは自動化外の手作業で、電源断（WCH-LinkE の 3.3 V 出力停止を含む）、交換、電圧確認、`./scripts/ch32fun.sh flash <device>` による検出確認の順に行う。手順は [配線資料](../hardware/wiring.md) を参照する。

## サンプルのフレームワークの選択

HIL で使うサンプルのフレームワークは `--hil-framework {ch32fun,arduino}` で選ぶ。既定は `ch32fun` で、指定しない既存コマンドの挙動と結果は変わらない。`arduino` を選ぶと `samples_<device>_arduino/` のサンプルと Arduino 用マトリクス（CH32V003 は [matrix_arduino.json](matrix_arduino.json)、CH32V002 は [matrix_ch32v002_arduino.json](matrix_ch32v002_arduino.json)）を使う。Arduino 用 HIL テストは `tests/hil/arduino/` にあり、マーカー `arduino` が付く。選択したフレームワークと一致しない HIL テストは理由付きで skip され、未対応のフレームワーク名は実機に触れる前にエラーで止まる。pytest の結果（`user_properties`）と Arduino テストの結果メタデータに `device` と `framework` を記録する。

Arduino サンプルのビルドは固定した arduino-cli と core だけを使う（`scripts/arduino.sh`。ホームの `~/.arduino15` や PATH 上の arduino-cli は使わない）。

- arduino-cli 1.5.1（`./scripts/arduino.sh setup` が `.arduino/bin/` に取得し、チェックサムを照合する）
- core: 公式 Board Manager 配布の `WCH:ch32v` 1.0.6（index `https://github.com/openwch/board_manager_files/raw/main/package_ch32v_index.json`、ツールチェーン riscv-wch-gcc 15.2.0）。各サンプルの `sketch.yaml` の profile で固定する。導入は `./scripts/arduino.sh core-install official`。

各サンプルの `make build` が `scripts/arduino.sh` で compile し、成果物を `main.bin` にコピーする。書き込みはフレームワークによらず `externals/ch32fun` の固定 minichlink だけで行い、ch32fun サンプルと同じ検出・識別領域・readback の確認を通す。core に同梱の書き込みツール（WCH 版 OpenOCD、`arduino-cli upload`）は使わない。

```sh
./scripts/arduino.sh setup && ./scripts/arduino.sh core-install official
uv run pytest --hil --hil-framework arduino -m 'hil and arduino' tests/hil/arduino --hil-port=/dev/serial/by-id/<PicoのID>
```

## 実行

検証は `uv run pytest -q tests/unit/test_config_matrix.py tests/unit/test_devices.py`。通常の `uv run pytest` は HIL を実行しない。実機を変更する GPIO HIL は次のように明示する。Pico v2 と固定配線、WCH-LinkE、対象 DUT が必要で、DUT firmware を書き換える。

```sh
uv run pytest --hil -m 'hil and gpio' tests/hil/test_blink_and_read.py --hil-port /dev/serial/by-id/<PicoのID>
```

UART、I2C、SPI、ADC、PWM、watchdog/sleep の実機テストもそれぞれ明示的に選択する。実行するたび DUT の該当サンプルを build・flash・readback する。マーカーは `gpio`、`uart`、`i2c`、`spi`、`adc`、`pwm`、`watchdog`。

```sh
uv run pytest --hil -m 'hil and uart' tests/hil --hil-port /dev/serial/by-id/<PicoのID>
uv run pytest --hil -m 'hil and i2c' tests/hil --hil-port /dev/serial/by-id/<PicoのID>
uv run pytest --hil -m 'hil and spi' tests/hil --hil-port /dev/serial/by-id/<PicoのID>
uv run pytest --hil -m 'hil and adc' tests/hil --hil-port /dev/serial/by-id/<PicoのID>
uv run pytest --hil -m 'hil and pwm' tests/hil --hil-port /dev/serial/by-id/<PicoのID>
uv run pytest --hil -m 'hil and watchdog' tests/hil --hil-port /dev/serial/by-id/<PicoのID>
```

単体テストと全 HIL（CH32V003 の対応済み11テスト）を単一コマンドで実行する。パス引数なしでは `--hil-port` を `=` で指定する（空白区切りだとパスが探索対象と誤解され、オプションが認識されない）。

```sh
uv run pytest --hil -q --hil-port=/dev/serial/by-id/<PicoのID>
```

`--hil` なしの HIL は `HIL not selected` の理由で skip される。extralibs 依存の book-code サンプルのうち、固定 submodule の `i2c_slave.h`、`ssd1306_i2c.h`/`ssd1306.h`、`ws2812b_dma_spi_led_driver.h` を使う 3 つは、`helper-verification` として [matrix.json](matrix.json) に載せ、`tests/hil/test_extralibs.py`（マーカー `extralibs`）で確認する（`uv run pytest --hil -m 'hil and extralibs' tests/hil/test_extralibs.py --hil-port=...`。CH32V002 は `--hil-device ch32v002`）。ほかの extralibs 依存サンプルは対象外で、HIL テストはない。SSD1306 の `helper_1mhz` は参考情報として `xfail` になる。確認範囲と未確認事項は [README](../README.md) を参照。 [matrix.json](matrix.json) の `hil-verified` には、根拠となる `hil_tests`（`tests/hil/<file>::<test>`）と `evidence`（`okf/log/` の実測記録）が必須で、単体テストが存在と網羅を確認する。SPI は Pico slave が mode 0 のみのため、データ不一致は検出できるが mode 不一致は検出しない。`gpio_input` サンプルは固定配線で PC4 を Pico から駆動しないため HIL 対象外で、GPIO 入力は `blink_and_read` の PA1 ボタン試験で確認する。

Pico の独立自己検証は、[配線資料](../hardware/wiring.md) の loopback 配線を確認してから `hardware/pico-tester/` の `uart_loopback.py`、`i2c_loopback.py`、`spi_loopback.py`、`pwm_selftest.py`、`sequence_selftest.py` を `uv run python` で実行する。配線はそれぞれ異なり、I2C と SPI は同じピンを使うので同時に構成できない。ADC は PWM 設定と読み値の大まかな変化のみ確認し、電圧・精度の校正はしない。PWM の測定は Pico 内の時計による機能確認で、周波数・デューティの校正ではない。SPI は mode 0 のみ。watchdog/sleep は GPIO の観測のみで、消費電力は測らない。各実験の実施条件と限界は `okf/log/` を参照する。

実行結果は段階別に報告される。build 成功は flash の成功ではなく、flash 成功も readback 一致や実行観測の成功を意味しない。失敗時はログと後始末の結果を確認する。Pico が応答しない場合は信号を安全に切り離し、BOOTSEL を押しながら USB 接続して既知の firmware を書き込む。Pico と DUT の電源ピンは直接接続しない。
