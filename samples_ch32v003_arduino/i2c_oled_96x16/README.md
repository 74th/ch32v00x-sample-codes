# i2c_oled_96x16（Arduino Core CH32、CH32V003、書籍からの逸脱）

書籍の `i2c_oled` と同じソースで、OLED の宣言だけ 128×32 → 96×16 にした CH32V003 専用の試行。CH32V003 は RAM 2 KiB でヒープが 504 B しかなく、128×32 のバッファ（512 B）の `malloc` が失敗するため、ライブラリが対応する最小サイズ 96×16（192 B）にした。
- 結果: 003 実機で Pico の SSD1306 模擬に対して合格（[ログ](../../okf/log/2026-11-08-1616-ch32v003-oled-96x16.md)）。表示は 96×16 に縮み、書籍と同じ表示ではない。実 OLED は未使用。
- ビルド: `make -C samples_ch32v003_arduino/i2c_oled_96x16 build`。HIL: `--hil-device ch32v003 --hil-framework arduino` の `test_arduino_i2c_oled_small_buffer`。
