# Pico 治具

現在のファームウェアは GPIO、UART、I2C、SPI、ADC 刺激、PWM 測定、SSD1306 OLED の模擬、WS2812 信号のデコードを持つ protocol v2 です。実機を駆動するので、配線は [wiring.md](../wiring.md) を確認してから使います。自己検証は `uv run python hardware/pico-tester/{uart,i2c,spi}_loopback.py`、`ssd1306_selftest.py`（I2C loopback 配線）、`ws2812_selftest.py`（GP19→GP20）、`pwm_selftest.py`、`sequence_selftest.py`、DUT 試験は [hil/README.md](../../hil/README.md) を参照してください。コマンドと制限は [protocol.md](protocol.md) を参照してください。以下の v1 説明と `measure.py` は過去ファームウェア向けです。v2 に `s` を送っても動作しません。

過去の GPIO v1: Raspberry Pi Pico (RP2040) の GP0 を入力にし、USB シリアルで `s` を受け取ると約 10 ms 間隔で 300 点を採取します。応答は `PICO_GPIO_V1 10000 <300桁の0/1>` と改行です。間隔は要求値であり、ソフトウェア処理時間が加わるため精密な時間測定ではありません。入力はプルなしです。

確認環境: Pico SDK 2.2.0 commit `a1438dff1d38bd9c65dbd693f0e5db4b9ae91779`、TinyUSB `86ad6e56c1700e85f1c5678607a762cfe3aa2f47`、arm-none-eabi-gcc 14.2.1、picotool 2.1.1、Ubuntu 26.04。SDK とその submodule の取得、CMake、Ninja、ARM GCC、picotool が必要です。

新しい作業ディレクトリで固定 SDK を取得する例（既存ディレクトリを上書きしないでください）:

```sh
git clone https://github.com/raspberrypi/pico-sdk.git pico-sdk-2.2.0
git -C pico-sdk-2.2.0 checkout --detach a1438dff1d38bd9c65dbd693f0e5db4b9ae91779
git -C pico-sdk-2.2.0 submodule update --init lib/tinyusb
git -C pico-sdk-2.2.0 rev-parse HEAD
git -C pico-sdk-2.2.0/lib/tinyusb rev-parse HEAD
```

## 現行ファームウェアのビルド・書き込み

```sh
export PICO_SDK_PATH=/path/to/pico-sdk
cmake -S hardware/pico-tester -B hardware/pico-tester/build -G Ninja -DPICO_BOARD=pico
cmake --build hardware/pico-tester/build
picotool load -f -v -x hardware/pico-tester/build/pico_gpio_tester.uf2
```

初回は BOOTSEL 状態で書き込みます。以後は本ファームウェアが動いて USB が応答していれば、上記 `-f` で BOOTSEL に移行して書き換えられます。フリーズ等で USB が応答しない場合は手動 BOOTSEL またはデバッガーによる復旧が必要です。複数台接続時は picotool のデバイス選択を指定してください。

PC 側に Python 3 と pyserial を用意して、次のように測定します。Pico は USB VID/PID で自動検出します。同じ種類の Pico が複数ある場合は `--port /dev/serial/by-id/...` を指定します。

以下は v1 のみで使う手順です。

```sh
python3 hardware/pico-tester/measure.py
python3 -m unittest discover -s hardware/pico-tester -p 'test_*.py' -v
```

両端の途中から始まる区間を除き、少なくとも3区間があり、各区間が40〜60サンプルの場合に PASS とします。これは概ね 400〜600 ms の点滅を判定する許容範囲で、精密な時間保証ではありません。終了コードは PASS=0、MISMATCH=1、検出または応答タイムアウト=2、接続・プロトコルエラー=3 です。既定のタイムアウトは6秒で `--timeout` で変更でき、検出待ちと測定応答待ちにそれぞれ適用されます。

2026-11-07、接続された Pico で初回書き込み後、BOOT ボタンを使わず `-f -v -x` による再書き込みと照合に成功。接続された CH32V003 の PC0 を GP0 で取得し、自動判定 PASS（完全区間 49〜50 サンプル）を確認しました。配線の電圧・電源条件は [配線案](../wiring.md) を参照してください。
