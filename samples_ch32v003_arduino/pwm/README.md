# pwm（Arduino Core CH32、CH32V003）

- 出典: `externals/ch32v003-book-code/pwm-arduino_core_ch32`（book-code 4ce0a1b, CC0 1.0）。ファイル名を `pwm.ino` に変更。
- 変更点: 既定の `#define PATTERN 1`（LED2 = PD4）は、PD4 が固定配線で Pico に繋がっていないため、`#ifndef PATTERN` の既定値を 2（PD2/TIM1_CH1 と PC4/TIM1_CH4）にした。`ARDUINO_FLAGS="--build-property compiler.cpp.extra_flags=-DPATTERN=3"` で書籍の PATTERN 3（PC6/PC5 のリマップ）をビルドできる。
- 配線: PD2 → 1 kΩ → Pico GP14、PC4 → 1 kΩ → Pico GP15（PATTERN 3 は PC6 → GP7、PC5 → GP6）。
- 挙動: 1 kHz・12 bit の PWM。LED1 と LED2 のデューティを 31 ms ごとに k/32 ずつ逆向きに変える。
- HIL: `tests/hil/arduino/test_pwm.py`（PATTERN 3 は参考の xfail。書籍の記述どおり出力されなかった）。
- 参考: `USART_Printf_Init` + `printf` の出力は Pico GP9 で受信できなかった。

ビルド: `make -C samples_ch32v003_arduino/pwm build`（`sketch.yaml` の profile で公式 `WCH:ch32v` 1.0.6 に固定）。書き込みは固定 minichlink だけで行う。
