# CH32V003 標準 ch32fun サンプル 8 種の build-only 確認（Issue #8 の一部）

- 作業・記録日時: 上記ファイル名の時刻（JST）、作業直後に記録。
- 目的: UART/I2C/SPI/timer-PWM/ADC/watchdog/GPIO 入力の標準 ch32fun サンプルを追加し、ビルドできることを確認する。
- 条件: 固定 `externals/ch32fun`（b28d285）、`riscv64-unknown-elf` GCC。extralibs 不使用（`ch32v003_SPI.h`/`ch32v003_GPIO_branchless.h` 不使用）。
- 追加: `samples_ch32v003_ch32fun/{gpio_input,uart,i2c_master,i2c_slave,spi_master,timer_pwm,adc,watchdog}`。各 main.c 先頭に出典（book-code の意図）と信号契約を記載。book-code のコードそのものではなく同等機能の再実装。
- コマンド: `make -C <sample> build PREFIX=riscv64-unknown-elf`
- 結果（実測）: 8 件すべてビルド成功（main.bin 608〜880 bytes）。`uv run pytest` 成功。
- **実機未確認**: flash・Pico 観測は一切していない。ピン割当（UART=PD5/PD6、I2C=PC1/PC2、SPI=PC5/6/7+PC0 CS、PWM=PD2、ADC=PA2）は未レビューで、wiring 側（担当 A）の配線表と未照合。
- 未実施: sleep モード、実機での動作、Pico 側 capability（#7 未確認）。matrix 上の state は build-only。
- 失敗: 記録された失敗なし（build のみ。後続の実機結果は別ログ）。
