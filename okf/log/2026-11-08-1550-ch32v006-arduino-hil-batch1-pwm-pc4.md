# CH32V006 Arduino: adc/i2c_master/spi_master/i2c_slave_test_master の HIL と PWM の PC4 問題（タスク 4.1、未完了）

- 作業日時: 2026-11-08 15:50:58〜15:51:55 JST（Arduino 一括 HIL、56.6 s）、15:53:12〜15:53:17 JST（WCH pwm HIL）、診断はその後 15:54 JST までに実施。`date` で確認。記録は 15:56 JST 頃。
- 対象: CH32V006F8P6（ユーザー申告）。配線は従来の固定治具、今回の測定・目視はしていない。F8P6=F8P7 は前 change の仮定のまま。
- ツール: arduino-cli 1.5.1 / core 1.0.6 / GCC 15.2.0、WCH SDK revision a835ede…。ソース HEAD 532bf54＋未コミット変更。

## 実行コマンド（実測）
```sh
uv run pytest --hil --hil-device ch32v006 --hil-framework arduino -m 'hil and arduino' \
  tests/hil/arduino/test_adc.py tests/hil/arduino/test_pwm.py \
  tests/hil/arduino/test_i2c.py::test_arduino_i2c_master tests/hil/arduino/test_i2c.py::test_arduino_i2c_slave_test_master \
  tests/hil/arduino/test_spi.py --hil-port=<Pico> --hil-run-dir=xprivate/runs/2026-11-08-1600-ch32v006-arduino -rA
```
- 事前変更: `tests/hil/arduino/test_adc.py` の SCALE に `ch32v006: (4095, 2800, 1200)` を追加。根拠はコアの `variant_CH32V006K8.h` の `ADC_RESOLUTION 12`。閾値は002と同じ比率で、結果に合わせた緩和ではない。

## 結果（実測）
- PASSED: `test_arduino_adc`、`test_arduino_i2c_master`、`test_arduino_i2c_slave_test_master`、`test_arduino_spi_master`（全て flash 前に 0x006 確認、全量 readback 一致、cleanup pass）。
- XFAIL（参考）: `test_arduino_pwm_remap_reference`（PATTERN 3、既存の参考試験の想定どおり）。結果は別ファイルに保存。
- **FAILED: `test_arduino_pwm`（必須）**。PD2（TIM1_CH1、Pico GP14）は 1007 µs 周期・duty が k/32 で ramp しているが、PC4（TIM1_CH4、GP15）は全 12 測定で `TIMEOUT pulse_edges`（エッジなし）。

## 切り分け（実測）
1. **WCH 公式 SDK の pwm（同じ PC4=TIM1_CH4）も同じ症状**（`tests/hil/wch/test_pwm.py`、1 failed）。PD2 は period 10–12 µs で ramp、PC4 側は全測定が timeout。→ Arduino core 固有ではない。
2. **PC4 を単純な GPIO 出力で 1 Hz 点滅する診断（一時 WCH プログラム、既に削除）**: Pico GP15 は 300 点すべて `1`（固定 high）で変化なし。同時に GP5 は `0` 固定（PC0 は使っていないので想定どおり）。→ TIM1 の問題ではなく、**PC4→GP15 の経路が DUT の PC4 出力に追従していない**。
3. 診断後に `blink_and_read`（WCH）を書き戻し、readback 一致を確認した。

## 判断・未確認
- 原因は未特定。候補（推定）: (a) 今回差し替えた006 DUT で PC4（TSSOP20 の 14 番ピン）が配線されていない・接触不良、(b) F8P6 のピン配置が資料の F8P7 と一致しない（F8P6=F8P7 は未検証の仮定）、(c) GP15 側の問題。実機の目視確認が必要で、ここでは確認していない。
- 002 では同じ配線で PC4 が出ていたため、治具配線全体ではなく 006 側の個別事象の可能性が高い（推定）。
- PWM の必須 HIL が成功していないため、タスク 4.1 は未完了。判定基準の緩和や skip 化はしていない。
- マトリクス: adc / i2c_master / spi_master / i2c_slave_test_master は `hil-verified`、pwm は `build-only`（理由を note に記載）。

## 追記: PC4 以外のピンで PWM は動くか（2026-11-08 16:44:42〜16:44:54 JST、実測）
- 目的: PC4（TIM1_CH4）が出ない原因が「PWM 全般」か「PC4 だけ」かの切り分け。ユーザー依頼（PC4 以外のピンで PWM が動くかに置き換える）。
- 変更: `samples_ch32v006_arduino/pwm/pwm.ino` に診断用の `PATTERN 4`（書籍にない追加）を追加。LED1=PD2（TIM1_CH1）→ GP14、LED2=**PC0（TIM2_CH3）→ GP5**（固定配線で Pico に接続済みの DUT→Pico 出力のうち、コアのタイマー出力表にあるもの）。テスト `test_arduino_pwm_pc0_diagnostic`（参考試験、xfail 非 strict、006 のみ）を追加。判定基準は PATTERN 2 と同一（1 kHz、duty が k/32 の ±15000 ppm、LED1+LED2≈33/32、ramp）。
- 結果: **XPASS**（基準を満たした）。周期 1007〜1009 µs、duty は PD2 が 29791→…、PC0 が 968253→…と相補的に変化、和は 0.998〜1.032×10⁶ ppm、24 測定。実行後に既定（PATTERN 2）を build し直した（flash はしていないので DUT は PATTERN 4 のまま）。
- 解釈: TIM1（PD2/CH1）と TIM2（PC0/CH3）の PWM は 006 で動作する。PC4 だけが出ない。さらに先の診断（PC4 を GPIO 出力にしても GP15 が固定 high）と合わせると、**タイマーやフレームワークではなく PC4 のピン（またはその先の Pico 側経路 GP15）の問題**と考えられる。原因（接触不良、DUT 個体、F8P6 のピン配置、GP15）はまだ特定していない。
- 要件との関係: PATTERN 2（PD2＋PC4）の必須試験は引き続き失敗のまま。PATTERN 4 は参考の診断で、必須判定の代わりにしていない。

## 決定と再実行（2026-11-08 16:48:31〜16:49:36 JST、実測）
- ユーザー判断（口頭）: 「PD2、PC0で動作したならば一旦よいことにしよう」。006 の必須 PWM の組を PD2（TIM1_CH1）＋PC0（TIM2_CH3）にする。PC4 の問題は**未解決のまま**で、原因（接触・DUT 個体・F8P6 のピン配置・GP15 側）の切り分けは残る。
- 変更: 006 の `pwm.ino` の既定を PATTERN 4（PD2/PC0）に、`test_arduino_pwm` は 006 で GP14/GP5 を測る。PATTERN 2（PD2＋PC4）は参考試験 `test_arduino_pwm_pc4_reference`（xfail 非 strict、結果は別ファイル `arduino_pwm_pc4.json`）として維持。診断用だった `test_arduino_pwm_pc0_diagnostic` は上記に置き換えた。003/002 は従来どおり PATTERN 2（PD2＋PC4）。
- 結果: 2 回実行（各 32 s）とも `test_arduino_pwm` は PASSED（判定基準は従来と同じ: 1 kHz、duty が k/32 の ±15000 ppm、LED1+LED2≈33/32、ramp）。`test_arduino_pwm_remap_reference`（PATTERN 3）と `test_arduino_pwm_pc4_reference`（PATTERN 2）は XFAIL（結果保存）。XPASS ではない。
- 意味: 006 の PWM は「PD2＋PC0」の組で確認した。**書籍相当の PD2＋PC4 の組は確認できていない**。このため PWM の `hil-verified` は PC4 を除いた範囲に限る。
