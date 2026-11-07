# i2c_slave（Arduino Core CH32、CH32V003）

- 出典: `externals/ch32v003-book-code/i2c_slave-arduino_core_ch32`（book-code 4ce0a1b, CC0 1.0）。ファイル名だけを `i2c_slave.ino` に変更、ソースの変更なし。
- 配線: PC1 SDA ↔ Pico GP10、PC2 SCL ↔ Pico GP11。
- 挙動: アドレス 0x10 の slave。書き込みの 1 バイト目をレジスタ位置にし、続くバイトをそこから格納する。読み出しでは位置から 4 バイト返す（0x20〜0x23 の初期値は `00 10 20 30`）。
- HIL: `tests/hil/arduino/test_i2c.py::test_arduino_i2c_slave`（Pico が master）。書籍のテスト master と同じく、位置の書き込み（STOP あり）と読み出しを別のトランザクションにしている。repeated START で続けて読むと、前の位置の値が返った（`onReceive` が STOP で呼ばれるため、と推定）。

ビルド: `make -C samples_ch32v003_arduino/i2c_slave build`（`sketch.yaml` の profile で公式 `WCH:ch32v` 1.0.6 に固定）。書き込みは固定 minichlink だけで行う。
