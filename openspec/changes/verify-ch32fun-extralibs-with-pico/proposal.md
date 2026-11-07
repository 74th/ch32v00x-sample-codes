# Proposal

## Why

book-code の `i2c_oled-ch32fun`、`neopixel-ch32fun`、`i2c_slave-ch32fun` は ch32fun の helper（`extralibs/ssd1306_i2c.h`・`ssd1306.h`、`extralibs/ws2812b_dma_spi_led_driver.h`、`examples/i2c_slave/i2c_slave.h`）に依存するため、現行の検証マトリクスでは「extralibs-excluded」として対象外にしている。固定配線（PC1/PC2–GP10/GP11、PC6–GP7）はすでにこれらの信号を Pico に引き出しており、Pico が OLED・NeoPixel・I2C master のふりをすれば、表示器や LED を目視せずに helper の実機動作を機械判定できる。

## What Changes

- `examples/i2c_slave/i2c_slave.h` の `SetupI2CSlave` を使う DUT サンプルを追加し、Pico の既存 `I2C_MASTER` でレジスタ書き込み・読み出しとコールバック発火を確認する。
- Pico 治具に SSD1306（I2C アドレス 0x3C）の模擬を追加する。DUT が送ったコマンド列とデータから 128×64 のフレームバッファを再構成し、ハッシュとダンプを返す。
- `ssd1306_i2c.h` + `ssd1306.h` を使う DUT サンプルを追加し、Pico が再構成したフレームバッファを、同じ描画コードをホストでビルドして得た期待値と照合する。
- Pico 治具に WS2812 信号のデコード（GP7、PIO）を追加し、先に Pico 単体で自己検証してから DUT に使う。
- `ws2812b_dma_spi_led_driver.h` を使う DUT サンプルを追加し、デコードした GRB バイト列を期待色列と照合する。
- 検証マトリクスで上記3サンプルの状態を `extralibs-excluded` から追跡対象へ変更する。**BREAKING**（仕様上）：「extralibs 依存サンプルは検証対象外」という既存要件を、固定 submodule の指定 helper に限って依存を許す形に改める。
- 固定配線は変更しない。対象は CH32V003 を先に、CH32V002 は CH32V003 で確認済みになった後に同じ手順で移植する。

## Capabilities

### New Capabilities

なし。

### Modified Capabilities

- `ch32fun-sample-workflow`: extralibs 依存サンプルの扱いを「対象外」から「固定 submodule の指定 helper に限り依存可、出典・設定上書き・検証範囲を記録」へ変更する。CH32V002 サンプルの依存制約も同様に改める。
- `pico-peripheral-fixture`: 周辺デバイス（SSD1306 OLED、WS2812 LED 列）を模擬・デコードする治具能力と、その自己検証条件を追加する。

## Impact

- Pico firmware：`hardware/pico-tester/` に SSD1306 模擬（I2C1 slave、GP10/GP11）と WS2812 デコード PIO（GP7）を追加。`CAPS` と `protocol.md` を更新。GP7 は既存 SPI slave PIO と排他使用。
- DUT サンプル：`samples_ch32v003_ch32fun/` に `i2c_slave_helper`、`ssd1306_i2c`、`ws2812_spi` を追加（後に `samples_ch32v002_ch32fun/` へ移植）。
- ホスト：`tests/hil/` に新規 HIL テスト、`tests/unit/` に SSD1306 模擬モデルと期待フレームバッファ生成のテスト、`ch32hil` の設定・マトリクス検証を更新。
- 資料：`hil/matrix.json`、`hil/matrix_ch32v002.json`、`hardware/wiring-proposal.md`、`okf/log/`。
- 依存：固定 `externals/ch32fun` の `extralibs/` と `examples/i2c_slave/` を include パスに追加する。book-code 内の ch32fun は使わない。
