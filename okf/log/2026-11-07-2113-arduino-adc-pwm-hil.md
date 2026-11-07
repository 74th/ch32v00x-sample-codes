# Arduino adc / pwm の CH32V003 HIL（verify-arduino-core-with-arduino-cli 5.1〜5.2）

- 作業日時: 2026-11-07 21:13〜21:17 JST（HIL 開始時刻は `date` の実測: adc 21:13:55、pwm 21:15:54。記録 21:17 頃）
- 対象・配線・ツールは [2026-11-07-2111](2026-11-07-2111-arduino-blink-and-read-hil.md) と同じ（CH32V003F4P6、固定配線、Pico E661AC8863223539、公式 `WCH:ch32v` 1.0.6、arduino-cli 1.5.1、固定 minichlink）。電圧・RC の実測はしていない。
- 範囲: 機能確認。ADC は未校正、PWM は Pico のソフトウェア計測で未校正。

## 5.1 adc

- サンプル: `samples_ch32v003_arduino/adc/`（book-code `adc-arduino_core_ch32` をそのままコピー。ソースの変更なし）。build: Flash 8388 B / RAM 864 B。
- 期待値（ソースと core から導出）: 約 100 ms ごとに `loop <n>` と `X: <analogRead(PA1)>, Y: <analogRead(PA2)>`。core 1.0.6 の CH32V003 は `ADC_RESOLUTION 10` で既定の読み取り分解能も 10 bit なので値域は 0〜1023（書籍コメント「0~1024」と一致）。
- **刺激方法の変更（タスク記載からの差）**: タスクは「GP12/GP13 の PWM+RC」としていたが、Pico の `ADC_OBSERVE` は PWM を出しながら ch32fun サンプル形式（3桁16進）の UART しか受けられない。Pico firmware は変えない方針のため、`GPIO_DRIVE <GP> <0|1> 500` で RC（10 kΩ・1 µF、τ 10 ms）を 500 ms 充放電し、駆動解除後（Pico ピンは入力・pull なし）にコンデンサが保持する電圧を、続く `UART_XFER` で受信した X/Y 行で判定した。
- 判定: 駆動 High のチャンネルが 700 以上、駆動 Low のチャンネルが 300 以下（0〜1023、大まかな変化のみ）。状態は (X 高, Y 低)、(X 低, Y 高)、(両方低) の 3 つ。
- テスト: `tests/hil/arduino/test_adc.py::test_arduino_adc`

```
uv run pytest --hil --hil-framework arduino -m 'hil and arduino' tests/hil/arduino/test_adc.py \
  --hil-port=/dev/serial/by-id/usb-Raspberry_Pi_Pico_E661AC8863223539-if00 --hil-run-dir <scratch>/run51 -q
→ 1 passed in 8.23s
```

| 状態 | 受信行（実測） | 判定 |
| --- | --- | --- |
| X 高 / Y 低 | `loop 11` `X: 1007, Y: 0` | pass |
| X 低 / Y 高 | `loop 23` `X: 0, Y: 1006` | pass |
| 両方低 | `loop 35` `X: 0, Y: 0` | pass |

- build / flash / readback / reset / 観測の各段階が pass。チャンネルの対応（PA1 = X = GP12、PA2 = Y = GP13）も確認できた。
- 1006〜1007 は満点 1023 より少し低い。保持中の放電、Pico 出力の High 電圧、ADC 誤差のどれによるかは切り分けていない（未校正）。

## 5.2 pwm

- サンプル: `samples_ch32v003_arduino/pwm/`。**変更点**: book-code の既定 `#define PATTERN 1`（PD2 + PD4）は、PD4 が固定配線で Pico に繋がっていないため、`#ifndef PATTERN` / `#define PATTERN 2`（PD2/TIM1_CH1 + PC4/TIM1_CH4）に変えた。`-DPATTERN=<n>` で上書きできる。その他のソースは同じ。build: Flash 10768 B（PATTERN 3 の参考ビルドは 10756 B）。
- 期待値（ソースと core 1.0.6 から導出）: `PWM_FREQUENCY` 1000 Hz、`PWM_RESOLUTION` 12 bit。`analogWrite(LED1, 128*i-1)` と `analogWrite(LED2, 128*(33-i)-1)` を i = 1..32 で 31 ms ごとに変える（逆方向も）ので、各デューティは ≈ k/32、同じステップの LED1+LED2 ≈ 33/32。
- 判定: GP14（PD2）と GP15（PC4）を `GPIO_PULSE` で 12 組（約 90 ms 間隔）測る。周期 800〜1200 µs、デューティが最寄りの k/32 から 15000 ppm 以内、LED1+LED2 が 33/32 ± 2/32、デューティの幅が 8/32 以上。k = 32（100%）はエッジがないのでタイムアウトになり、その点は数えない。
- テスト: `tests/hil/arduino/test_pwm.py::test_arduino_pwm`、参考 `::test_arduino_pwm_remap_reference`（PATTERN 3 を `ARDUINO_FLAGS=--build-property compiler.cpp.extra_flags=-DPATTERN=3` でビルドし、PC6 → GP7、PC5 → GP6 を測る。非 strict の xfail）。

```
uv run pytest --hil --hil-framework arduino -m 'hil and arduino' tests/hil/arduino/test_pwm.py \
  --hil-port=/dev/serial/by-id/usb-Raspberry_Pi_Pico_E661AC8863223539-if00 --hil-run-dir <scratch>/run52 -q -rxXs
→ 1 passed, 1 xfailed in 22.55s
```

PATTERN 2（実測、LED1 duty / LED2 duty ppm、LED1 周期 µs）:

```
30938/969092 1002, 156530/874376 1003, 249252/780876 1003, 343968/687250 1003, 436254/593220 1004,
530408/499501 1003, 625124/405782 1003, 718843/281156 1003, 843469/187437 1003, 937250/93718 1004,
969092/61814 1003, 875249/155533 1002
```

- 24 点すべてが周期 1002〜1004 µs、デューティは k/32 からの差が数千 ppm 以内。LED1+LED2 は 12 組中 10 組が 1029474〜1031218 ppm（≈ 33/32 = 1031250）、2 組が 999999〜1000030 ppm（2 回の測定の間にステップが変わったと推定。許容範囲内）。デューティは 30938〜969092 ppm で上下している。→ pass。
- PATTERN 3（参考）: GP7・GP6 とも 12 回すべて `TIMEOUT pulse_edges`（50 ms 以内にエッジなし）→ xfail。書籍の「TIM1、TIM2 のリマップを利用（動作せず）」と同じ結果で、公式 1.0.6 でも PC6/PC5 のリマップ PWM は出なかった。原因（core の pinmap/AFIO 設定か）は調べていない。
- 参考: スケッチの `USART_Printf_Init(115200)` + `printf("up"/"down")` は、GP9 で 2.5 s 受信しても 0 バイトだった（PATTERN 2/3 とも）。書籍の blink_and_read の「not working」というコメントと合う。判定には使っていない。
- 参考テストの後に既定の PATTERN 2 で clean build し直した。
- PATTERN 1（PD4）は未配線なので実機確認していない。

## マトリクス

`hil/matrix_arduino.json` の adc と pwm を `hil-verified` にした（hil_tests と、このログを evidence として付けた）。

## 未確認

- ADC の電圧・精度（校正なし）、RC 保持中の電圧変化。
- PWM の周波数・デューティの校正値、PD4（PATTERN 1）、PATTERN 3 で出力が出ない原因。
- thirdparty / official-git での実機動作（analogRead の分解能の扱いが core で異なるが、実機では比べていない）。
