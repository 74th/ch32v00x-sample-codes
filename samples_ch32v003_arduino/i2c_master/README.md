# i2c_master（Arduino Core CH32、CH32V003）

- 出典: `externals/ch32v003-book-code/i2c_master-arduino_core_ch32`（book-code 4ce0a1b, CC0 1.0）。ファイル名だけを `i2c_master.ino` に変更、ソースの変更なし。
- 配線: PC1 SDA ↔ Pico GP10、PC2 SCL ↔ Pico GP11（外付け pull-up、Wire の既定ピン）。固定配線に合わせて変えた点はない。
- 挙動: SHT31（0x44）に、setup で `30 A2` と `30 41` を書き込む。loop では `24 00` を書いて 300 ms 待ち、6 バイト読んで温度と湿度を Serial に出し、5 s 待つ。
- HIL: `tests/hil/arduino/test_i2c.py::test_arduino_i2c_master`。Pico が 0x44 の SHT31 の役になり、バス上の書き込み内容、6 バイトの読み出し、ループの周期を見る。Serial の値は観測していない。

ビルド: `make -C samples_ch32v003_arduino/i2c_master build`（`sketch.yaml` の profile で公式 `WCH:ch32v` 1.0.6 に固定）。書き込みは固定 minichlink だけで行う。
