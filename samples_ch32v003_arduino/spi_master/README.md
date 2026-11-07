# spi_master（Arduino Core CH32、CH32V003）

- 出典: `externals/ch32v003-book-code/spi_master-arduino_core_ch32`（book-code 4ce0a1b, CC0 1.0、ADT7310 の読み取り）。ファイル名を `spi_master.ino` に変更。
- 変更点: 元のスケッチは CS を操作しない（`SPI.beginTransaction(SPISettings)` は CS をユーザー制御にし、ハードウェア NSS も使わない）。固定配線の PC0（→ Pico GP5）を CS として出力に設定し、各 `beginTransaction`〜`endTransaction` の間だけ Low にした。ほかは同じ。
- 配線: PC5 SCK → GP6、PC6 MOSI → GP7、PC7 MISO ← GP4、PC0 CS → GP5（各 1 kΩ）。1 MHz、mode 0、MSB first。
- HIL: `tests/hil/arduino/test_spi.py`。Pico の SPI slave が返す値で DUT の分岐（0000/FFFF なら reset を送る、それ以外なら 1 s 後に次の読み出し）が変わることを、受信バイトと CS の波形で見る。Serial の値は観測していない。

ビルド: `make -C samples_ch32v003_arduino/spi_master build`（`sketch.yaml` の profile で公式 `WCH:ch32v` 1.0.6 に固定）。書き込みは固定 minichlink だけで行う。
