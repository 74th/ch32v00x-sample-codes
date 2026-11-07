# adc（Arduino Core CH32、CH32V003）

- 出典: `externals/ch32v003-book-code/adc-arduino_core_ch32`（book-code 4ce0a1b, CC0 1.0）。ファイル名だけを `adc.ino` に変更、ソースの変更なし。
- 配線: PA1（X）← 10 kΩ ← Pico GP12、PA2（Y）← 10 kΩ ← Pico GP13、各 1 µF → GND。PD5（TX）→ Pico GP9。
- 挙動: 約 100 ms ごとに `loop <n>` と `X: <analogRead(PA1)>, Y: <analogRead(PA2)>` を 115200 baud で出力する（公式 core 1.0.6 では 10 bit、0〜1023）。
- HIL: `tests/hil/arduino/test_adc.py`。Pico の `GPIO_DRIVE` で RC を充放電した後、保持された電圧の読み値が High/Low に大まかに従うことを見る（未校正）。

ビルド: `make -C samples_ch32v003_arduino/adc build`（`sketch.yaml` の profile で公式 `WCH:ch32v` 1.0.6 に固定）。書き込みは固定 minichlink だけで行う。
