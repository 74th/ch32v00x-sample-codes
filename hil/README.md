# HIL 設定

`configs/gpio_blink.json` は CH32V003F4P6 と Pico の固定配線を宣言する公開可能な設定例。`dut.device` と `sample`、Pico USB VID/PID と `selection=explicit_or_unique`、ピン・物理ピン・方向・直列抵抗、I2C pull-up と ADC RC、電源と公称電圧、タイムアウト、readback 方針を持つ。`readback` は `required`、`optional`、`disabled`。ポートは実行時 `--hil-port` で指定できる。

電圧の `source=declared_unmeasured` は設定値が配線案の公称値であり、実測・安全確認ではないことを示す。設定の整合性チェックは物理配線、電圧、レベル変換や逆給電を確認できない。使用前の手順は [配線資料](../hardware/wiring.md) と [固定配線案](../hardware/wiring-proposal.md) を参照する。

検証は `uv run pytest -q tests/unit/test_config_matrix.py`。通常の `uv run pytest` は HIL を実行しない。実機を変更する GPIO HIL は次のように明示する。Pico v2 と固定配線、WCH-LinkE、対象 DUT が必要で、DUT firmware を書き換える。

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

`--hil` なしの HIL は `HIL not selected` の理由で skip される。extralibs 依存の book-code サンプルは [matrix.json](matrix.json) で対象外と分類しており、HIL テストはない。 [matrix.json](matrix.json) の `hil-verified` には、根拠となる `hil_tests`（`tests/hil/<file>::<test>`）と `evidence`（`okf/log/` の実測記録）が必須で、単体テストが存在と網羅を確認する。SPI は Pico slave が mode 0 のみのため、データ不一致は検出できるが mode 不一致は検出しない。`gpio_input` サンプルは固定配線で PC4 を Pico から駆動しないため HIL 対象外で、GPIO 入力は `blink_and_read` の PA1 ボタン試験で確認する。

Pico の独立自己検証は、[配線資料](../hardware/wiring.md) の loopback 配線を確認してから `hardware/pico-tester/` の `uart_loopback.py`、`i2c_loopback.py`、`spi_loopback.py`、`pwm_selftest.py`、`sequence_selftest.py` を `uv run python` で実行する。配線はそれぞれ異なり、I2C と SPI は同じピンを使うので同時に構成できない。ADC は PWM 設定と読み値の大まかな変化のみ確認し、電圧・精度の校正はしない。PWM の測定は Pico 内の時計による機能確認で、周波数・デューティの校正ではない。SPI は mode 0 のみ。watchdog/sleep は GPIO の観測のみで、消費電力は測らない。各実験の実施条件と限界は `okf/log/` を参照する。

実行結果は段階別に報告される。build 成功は flash の成功ではなく、flash 成功も readback 一致や実行観測の成功を意味しない。失敗時はログと後始末の結果を確認する。Pico が応答しない場合は信号を安全に切り離し、BOOTSEL を押しながら USB 接続して既知の firmware を書き込む。Pico と DUT の電源ピンは直接接続しない。
