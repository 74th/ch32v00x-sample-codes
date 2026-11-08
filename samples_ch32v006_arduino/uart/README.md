# uart（Arduino Core CH32、CH32V006F8P6）

書籍 `uart-arduino_core_ch32`（CO2 センサー＋OLED）をそのまま移植（OLED ライブラリ 1.0.7 固定、128×32）。
- 観測: 006 実機で、Pico がセンサー役（1234 ppm）と SSD1306 模擬を兼ね、DUT が読んだ値を描いた画面がホスト描画と一致（[ログ](../../okf/log/2026-11-08-1632-ch32v006-arduino-uart-oled-hil.md)）。値を変えると失敗することも確認。判定の仕組みと弱み（最終ページはモデルの確定遅れで比較対象外）は `tests/hil/arduino/test_uart.py` 冒頭。
- 実センサー・実 OLED は未使用。
