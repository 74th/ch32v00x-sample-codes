# Arduino Core CH32 サンプル（CH32V006F8P6）

公式 `WCH:ch32v` 1.0.6 の `CH32VM00X_EVT`（`pnum=CH32V006K8`、62 KiB / 8 KiB、48 MHz HSI）をそのまま使う（`arduino.mk`。CH32V002 用の上書きなし）。全 10 スケッチ（`uart` を含む）。進捗の正本は [hil/matrix_ch32v006_arduino.json](../hil/matrix_ch32v006_arduino.json)。

```sh
make -C samples_ch32v006_arduino/<sample> build
uv run pytest --hil --hil-device ch32v006 --hil-framework arduino -m 'hil and arduino' tests/hil/arduino --hil-port=/dev/serial/by-id/<PicoのID> --hil-run-dir=<run用ディレクトリ>
```

- 依存: arduino-cli 1.5.1、core 1.0.6、GCC 15.2.0（`scripts/arduino.sh`）、OLED を使うものは `OLED SSD1306 - SH1106` 1.0.7（`sketch.yaml` で固定）。
- 006 固有の注意: `pwm` は PC4 が無信号のため既定が PATTERN 4（PD2＋PC0）。`i2c_slave` は通常対象の成功に数えない。詳細は各サンプルの README、README のルート、`okf/log/` を参照。
- 未確認: 精度・校正、実 OLED・実 LED・実センサー、PC4 の原因、F8P6 の資料上の位置付け（F8P7 と同一ダイは前 change のユーザー判断に基づく仮定）。
