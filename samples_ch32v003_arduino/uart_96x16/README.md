# uart_96x16（Arduino Core CH32、CH32V003、書籍からの逸脱）

書籍の `uart`（CO2 センサー＋OLED 表示）を CH32V003 で動かすための変種。RAM 2 KiB ではヒープ 504 B に 128×32 のバッファ（512 B）が確保できないため OLED を 96×16（192 B）で宣言し、16 行に収めるため状態・CO2 値の行の y 座標を 20 → 0 にした。それ以外は書籍と同じ。
- 結果: 003 実機で、Pico がセンサー役（1234 ppm のフレーム）と SSD1306 模擬を兼ね、DUT が読んだ値を描いた画面を確認（`tests/hil/arduino/test_uart.py`、判定の仕組みは同ファイル冒頭）。別の値（1235 ppm）を送ると失敗することも確認した。実 OLED は未使用。[ログ](../../okf/log/2026-11-08-1629-ch32v003-arduino-uart-oled.md)
- ビルド: `make -C samples_ch32v003_arduino/uart_96x16 build`（Flash 14.0 KB / 16 KB）。
