# change fix-ch32v00x-sample-findings の実施記録

- 記録開始: 2026-11-08 21:37 JST（`date` で取得）。以降、タスクごとに追記する。
- 目的: 書籍原稿の執筆中に見つけたサンプルの不整合（[ログ](2026-11-08-2019-ch32v00x-book-articles.md)）の修正と、未確認事項の調査。
- 出所: `openspec/changes/fix-ch32v00x-sample-findings/`。

## 1.1 準備（実測、2026-11-08 21:37 JST）

- 親の `git status --short`: 未追跡のみ（`okf/log/2026-11-08-2019-ch32v00x-book-articles.md`、`openspec/changes/fix-ch32v00x-sample-findings/`、`openspec/changes/write-ch32v00x-book-articles/`）。HEAD `e8f76c4`。
- `externals/ch32fun`: `b28d285`（`scripts/ch32fun.sh` の固定値 `b28d285460ce…` と一致）。
- DUT: 開始時点で CH32V002 が装着済み（ユーザー申告）。
- 修正前 build（実機なし）: 下記のスクリプトで、002/006 の WCH SDK 8 例（7 例＋`adc_dma` の照合用）、ch32fun 全 14 例、Arduino 3 例をbuildし、`.bin` の SHA-256 を記録した。48 件すべて build 成功。
  - WCH SDK: `make -B -C samples_<dev>_wch/<s> build`（固定 toolchain `.arduino/official/.../riscv-wch-gcc/15.2.0`）。
  - ch32fun: `rm -rf build/<dev>; make -C samples_ch32v00x_ch32fun/<s> build PREFIX=riscv64-unknown-elf TARGET_MCU=<DEV>`。
  - Arduino: `make -C samples_<dev>_arduino/<s> build`（official core 1.0.6）。

### 修正前の SHA-256

```
95629ca90c625cd85bf3a7b633cfbbb75c5b5936fd0886efab830a3b4dab7f47 wch/ch32v002/adc
7b59b4085f2017bd31438e7040ac6552b95320372b532cac616b7cb821fc602b wch/ch32v002/adc_dma
dbdac29d453c693aa682920b0bca7fa4c0e85a845937077408c5af95a9c05aa2 wch/ch32v002/timer_blink
b65678576f91a37a42c9bd924017b65363da5b576d84ffc7ba507bcf8234f63d wch/ch32v002/timer_dma
489551e6099e7bd6e80fa511be4b210b0cc9248c1396873e04ae515fe0163e5d wch/ch32v002/sleep_wake
f460056efb53ce6a623bfdb39a16e131c3f49580db966d54ca5ac797f1b2b094 wch/ch32v002/standby_wake
9c080da32a6b256d139998cac44f23333541105f765adb123d4a0bf6674253e5 wch/ch32v002/i2c_master
68841a73e0a73ea4a221f113c013438a7585f0524c60e34bc1c5a0901c712a05 wch/ch32v002/i2c_slave
18b508c4f9beb62381dbd8fe9cf6ac8744d41cc0e532c2d90c811ee8945498ae ch32fun/ch32v002/adc
92edb7948e421c24ee953948a9cc19bed32da4ffb22181fe571c1899ab0c9342 ch32fun/ch32v002/blink_and_read
1a29033fd778b3381345363261957df0359df09be357915b52cc97e52b2c5397 ch32fun/ch32v002/i2c_master
76569575f2623734a30dbb30aaea23c26392f4d66921568064bf6208c527db85 ch32fun/ch32v002/i2c_slave
757542434faf595042abe4efc9d1d9ff9290b63c435259075cb331d1650b3130 ch32fun/ch32v002/i2c_slave_helper
b19bc9639c4491f78ee36efe485470720ede5a4057e648793c37c093259816d7 ch32fun/ch32v002/sleep_wake
b0b767403a9bd67db1d0389bd674ae846d31c46157359929c9b913a6ee9f53aa ch32fun/ch32v002/spi_master
49e9b3dcc4d289caf6bf12b81169c1fce04c701de1e9d73d4ae69b35cc1dfdf6 ch32fun/ch32v002/ssd1306_i2c
266a6696cb014bf8279c4a25679666d86323882e98387fa21950f6af962b6140 ch32fun/ch32v002/timer_pwm
24df7870e1d8b970dbd9a52820c4ccb52fd0538761f91b316feea06944f44104 ch32fun/ch32v002/uart
6c742492ae7f63bda621e902499d91835495e1d458deee352a968356cba3cf8f ch32fun/ch32v002/watchdog
f5b118d0c5ab8a013901d3e505c9563c9b6d6efa00b0538c1c3acc05d40855cf ch32fun/ch32v002/ws2812_spi
47075838da9a0ad2913f935b3095f4b04522b3571eeaf065ab70156f8a67c3de arduino/ch32v002/adc
91a0b4b8ce885e20a8845c2f9c09ca89b78af6756970013155869c56ac1847f2 arduino/ch32v002/neopixel
0fcf3919e8158716bbbe6cdb5030a0de9a22250416b66b6a56b2016f93d42e5e arduino/ch32v002/i2c_slave
57f2eea4224e39705cc2c9a77c6bb3fc672b586918a370c3fb216fefe7725dc4 wch/ch32v006/adc
7fee300170314929e9e798ceecd91324060edac9d3bd0b1aa61f73ea072d4e73 wch/ch32v006/adc_dma
b9a04eadbff2cbc3aa108e91c14bfa9f182b935c11ff6ceb05497cf75c490b2a wch/ch32v006/timer_blink
aee88f28a8f125870f4631fe3acc623e1ab18a32121083c65be9b12ea2420a1e wch/ch32v006/timer_dma
328751a2a7726ec0be0e46f266cc6591da5a73dcc0a49da1934eaeb15cf109fd wch/ch32v006/sleep_wake
1c47223345bfe33fd453b6d072ca5a381bdd5eadd845d20b3477072b505089f0 wch/ch32v006/standby_wake
f889b04bf32bbff10c3054f4c9af891712064683362ff65b10a53025942dcbec wch/ch32v006/i2c_master
c8feafdea8b983f609a1d13ae7af0809fa0cd15012fcdb6e9ff76eec1953b5b7 wch/ch32v006/i2c_slave
285e4fc980f3d3db8b658f1adce110dc379185e0e523206f68c24f834592da6a ch32fun/ch32v006/adc
b0536087db2f8060894a888557bc47fd6c3908c61411ae1be67c082af0657bb0 ch32fun/ch32v006/blink_and_read
47438360157a9023f79b955b3ce7ddf0b4cbab03e7bf81b4d1dfde72e652fc79 ch32fun/ch32v006/i2c_master
ba564b101b79891eccc976637c8d63ed580cf354bd668c80cd73966a55d19fdf ch32fun/ch32v006/i2c_slave
5cf3f7bcd4772a1ec942ee7b5ab491875331fe9fa57c314187f3487c581f227a ch32fun/ch32v006/i2c_slave_helper
9c50a99556d61989135afbf19e4ac56776062348bd7869a3539a7917ced01e54 ch32fun/ch32v006/sleep_wake
689f3081fd3b3a47b2f5a638d119c9d9c8f3da63de6fc8953faef92aa59f2eb7 ch32fun/ch32v006/spi_master
e7497b23c0db41fbb72c4cdbb56338a6aa8cef7c7ffce20e3ea55ed31727c29f ch32fun/ch32v006/ssd1306_i2c
adb69c31c81dbf5b610ac50e7ec1f8338b5ed42472f976534c9a8260deaf834d ch32fun/ch32v006/timer_pwm
52c42b7c0f0395ac1f7f9b22127c371d361782ba2ecae0f81ddaf4acb0f8be69 ch32fun/ch32v006/uart
6770f189722fc1ddd95742d567ce1e7b0ec9fefb89f5923085db2c5891c2bed5 ch32fun/ch32v006/watchdog
9d175d18f25d017ac89db685cdab87c48314f15b6ebbf43cf1dc6dc037130681 ch32fun/ch32v006/ws2812_spi
65fc525e34d9aea14f67ca74e1307c071c7dbed7fac620020e20fdc27b78c086 arduino/ch32v006/adc
1537de929e78e19f4802a9b1d52dc506fe5121caa57f8bbb0264b7f5ed40f550 arduino/ch32v006/neopixel
625e9b086ca0f0c878ec3750c1cf271bcf582f53c61eb7f83d2ea5a0014c28b1 arduino/ch32v006/i2c_slave
```

## 2. コメントと記録の修正（実測: build とハッシュ比較、2026-11-08 21:40〜21:55 JST 頃）

変更内容（002/006 とも同じ文面。コードは変えていない）:

- 2.1 WCH SDK `adc`: 冒頭コメントを「12ビット、239.5サイクル（`ADC_SampleTime_CyclesMode7`）、校正なし、0..4095」に直し、書籍（003）との差（10→12ビット、241→239.5、校正削除、`RCC_ADCCLKConfig(RCC_PCLK2_Div8)` 追加）を明記。`adc_dma/main.c` には分解能・サンプル時間・校正の記述はなく、修正不要（grep で確認）。
- 2.2 WCH SDK `timer_blink`: SDK の `core_riscv.h:81,91` で `IENR[8]`、`IPRIOR[256]`、`ch32v00X.h:74` で `TIM1_UP_IRQn = 35` を確認。コメントを「IENR[35] は範囲外、IPRIOR[35] は範囲内。両方の出力を省いている」に直し、冒頭の「two out-of-bounds NVIC dumps」も直した。
  - 追加（仕様「説明と設定値の一致」に基づく、tasks に明記のない分）: 同じファイルの「50 をセットすれば 1Hz(1s)」（実際は Repetition 5−1 → 500 ms）と、TIM2 の「1000-1 … 1Hz」（main は 500−1 を渡す → 500 ms）にも注記を加えた。
- 2.3 WCH SDK `timer_dma`: 書籍コード（`externals/ch32v003-book-code/timer_dma-wch_sdk/src/main.c:122-136`）と同じ値であることを確認。1回目の `TIM_TimeBaseInit`（PSC 4800−1、Period 4）は直後の2回目で PSC/ATRLR とも上書きされること、書籍に理由の記載がないこと、PSC=480 は分周 481 で 1 カウント約 10.02 µs、Period 10−1 で更新・DMA 要求が約 100 µs（≒100.2 µs）ごと、書籍の「10us ごとにトリガ」は1カウントの長さであることをコメントにした。2回呼ぶ理由は書籍から特定できない（推定もしない）。
- 2.4 `sleep_wake`: 「50 … 1Hz(1s)」→「20−1（20回）、100 ms × 20 = 2 s」。`standby_wake`: 「window value 31 / 80ms * 31」→ 25。
- 2.5 ch32fun 全 12 個の `funconfig.h` の「CH32V002 internal oscillator」→「CH32V002/CH32V006」（固定 ch32fun の `ch32fun.h:183-185` で両者とも HSI 24 MHz の分岐）。Arduino `neopixel`（002/006）の分岐コメントを「CH32V002/CH32V006（CH32VM00X 系列、006 でも同じ機械語・同じ時間を実測）」に（根拠: [ログ](2026-11-08-1636-ch32v006-arduino-batch2.md)）。Arduino `adc.ino`（002/006）の「0~1024」→「12 ビットなので 0~4095（書籍の 003 は 0~1023）」。
- 2.6 `hil/matrix_ch32v002_wch.json` の `adc` の criteria を `tests/hil/wch/test_adc.py:27` の 002 の尺度（4095、≥2800、≤1200、段差 ≥80）に合わせた。006 の criteria は既に12ビットの表記で修正不要。
  - 追加: 同じ 002 マトリクスの `adc_dma` の criteria も「3段が>=20増」のままだったので、`test_adc_dma.py:33` の 002 の値（≥80）に直した。
  - 未修正（記録のみ）: `tests/hil/wch/test_adc.py:7,9` と `test_adc_dma.py:5,12` の docstring は 003 の値（10ビット、700/300、20）で書かれている（判定は SCALE で機種別に正しく行われる）。
- 2.7 結果: 修正後に同じスクリプトで 46 件（1.1 の表と同じ集合）を再 build し、**SHA-256 はすべて一致**（`diff` 差なし）。timer_blink の追加修正後も 002/006 とも 1.1 の値と一致。

CH32V003 版に同じ記述が残っているもの（この change では直さない）:

- `samples_ch32v003_wch/adc/main.c:2-3`（003 では正しい記述。参考）
- `samples_ch32v003_wch/timer_blink/main.c:38`（「50 … 1Hz(1s)」、値は要確認）、`:70`（「IPRIOR[8], IENR[8]」。003 SDK も `IPRIOR[256]`）、`:95`
- `samples_ch32v003_wch/sleep_wake/main.c:42`（「50 … 1Hz(1s)」）
- `samples_ch32v003_wch/timer_dma/main.c:134`（「10us ごとにトリガ」）
- `samples_ch32v003_wch/standby_wake/main.c:60`（「window value 31」）

## 3.1 WCH SDK `i2c_master` のリマップ分岐（資料確認＋build のみ、2026-11-08 21:45 JST 頃）

- 資料: CH32V00X Reference Manual（英語版 V1.5、`xprivate/` の変換物、本文は転載しない）の AFIO_PCFR1 `I2C1_RM[2:0]`（bits 5:3）。000 = SCL/PC2・SDA/PC1（既定）、001 = PD1/PD0、**010（CH32V002/004/005/006 のみ）= SCL/PC5・SDA/PC6**、011 = PB5/PB6、1xx = PB3/PD1（表の一部は PDF の改ページで欠けて変換されたので、PC5/PC6 の行のみを根拠とする）。
- SDK: `GPIO_PartialRemap2_I2C1 = 0x08130010`（002/006 の `ch32v00X_gpio.h:80` 同一）。`GPIO_PinRemapConfig()`（`ch32v00X_gpio.c`、002/006 同一）を読むと、3ビット欄・位置 3 の消去（`7 << 3`）後に `0x10` を書くので、bits[5:3] = 010 になる。書籍（003）の `GPIO_FullRemap_I2C1` は 002/006 の SDK にない。
- 修正前の確認（実測）: `USE_REMAP` を `#ifndef` で囲み `-DUSE_REMAP=1` で選べるようにして build → 002/006 とも `error: 'GPIO_FullRemap_I2C1' undeclared` で失敗。
- 修正: 定数を `GPIO_PartialRemap2_I2C1` に変更（ピンは書籍と同じ PC6=SDA、PC5=SCL のまま）。冒頭コメントと README（002/006）に「build のみ」を記載。
- 修正後（実測）: `make clean; make build EXTRA_CFLAGS=-DUSE_REMAP=1` が 002/006 とも成功。既定 build の SHA-256 は 002 `9c080da3…`、006 `f889b04b…` で 1.1 と一致。
- 未確認: リマップ側の実機動作（固定治具が PC1/PC2 のため観測できない）。

## 3.2 WCH SDK `i2c_slave` の `I2C_ClockSpeed`（CH32V002 実測、2026-11-08 21:43〜21:46 JST）

- 対象: CH32V002（flash ガードで識別 0x002、`Part Type: 00-20-06-20`）、固定配線（PC1/PC2–GP10/GP11、PD5–GP9）。電圧未測定。
- SDK の計算（`ch32v00X_i2c.c` の `I2C_Init()`、002/006 同一）: `CTLR2.FREQ = PCLK1/1MHz`。`ClockSpeed <= 100000` のとき `CCR = PCLK1 / (ClockSpeed << 1)`（4 未満は 4）。0 のままだと `PCLK1 / 0`。
- 試行1（PB1 経由の読み出し）: `minichlink -r + 0x40005400 0x20` は全 0、`-A -r …` は `Fault reading device`。デバッガ経由の周辺レジスタ読み出しはこの条件では得られなかった（原因未調査）。
- 試行2（診断ビルド、サンプルとしては維持しない）: `main.c` の初期化直後に `printf("C2=%x CK=%x\r\n", I2C1->CTLR2, I2C1->CKCFGR);` を1行加えた複製を scratchpad に置き、`make build SAMPLE_SOURCES=<複製>` で build。guarded flash＋全量読み戻しの後、Pico の `UART_XFER DUT 115200`（1回最大 32 バイト）を開始してから `minichlink -b` でリセットし、起動直後の出力を取得（scratchpad の `diag_uart.py`。`tests/hil/arduino/common.py` の `reset_during`/`uart_receive` を利用）。
  - 修正前（ClockSpeed 未設定）: `init\r\nC2=730 CK=cfff\r\nstart\r\n…` → **CKCFGR = 0xCFFF**（FS=1、DUTY=1、CCR=0xFFF。0 除算の結果 0xFFFF を書き、予約ビット 13:12 は 0 で読める、と解釈）。CTLR2 = 0x730（FREQ = 0x30 = 48、割り込み許可ビット）。
  - 修正後（`I2C_ClockSpeed = 100000`）: `init\r\nC2=730 CK=f0\r\n…` → **CKCFGR = 0x00F0 = 240**（48 MHz / 200 kHz と一致、標準モード）。
  - 取得した 32 バイトの末尾に `ini`/`init` が続いた。`minichlink -b` によるリセットが2回起きている可能性がある（未確認。判定には影響しない）。
- 修正: 002/006 の `main.c` に `I2C_InitTSturcture.I2C_ClockSpeed = 100000;` と理由のコメントを追加、冒頭の「書籍から変えていない」記述も更新。Pico の master は `i2c_fixture.c:37` で 100 kHz。
- HIL（002）: `uv run pytest --hil --hil-device ch32v002 --hil-framework wch -m hil tests/hil/wch/test_i2c_slave.py --hil-run-dir=xprivate/runs/2026-11-08-2146-ch32v002-wch-i2c_slave-clock` → **1 passed**（6.06 s、21:45:45〜21:45:51）。成果物 SHA-256: 002 `25717527336c5f15…`、006 `fb88ec24f3c825aa…`（修正後の build）。
- 006: 未実施（DUT 差し替え後に行う）。

## 3.3 Arduino `i2c_slave` の範囲判定（CH32V002 実測、2026-11-08 21:46〜21:48 JST）

- ソースを読んだ結果: `on_receive` は判定と書き込みが同じ添字 `position + (i - 1)` で、範囲外アクセスはない。問題は `on_request` だけ（`position + (i - 1)` で判定、`position + i` を読む → `position = 0x2D..0x2F` の付近で `i2c_registers[0x30]` を読みうる）。proposal の「`on_receive` も」は、読んだ結果、修正不要と判断した。
- 修正（002/006 同一）: `index = position + i` で判定し、範囲外は `Wire.write(0xFF)`（書籍は 0x00）。README（002/006）に書籍との差を追記。build: 002/006 とも成功。SHA-256: 002 `2f7c9b8edd127549…`、006 `fbdf065880c37f5f…`。
- HIL（002、`tests/hil/arduino/test_i2c.py::test_arduino_i2c_slave`、run dir `xprivate/runs/2026-11-08-2150-ch32v002-arduino-i2c_slave-bounds-{1,2,3}`）: 3 回中 **1 回 XPASS、2 回 XFAIL**。XFAIL の内容は 1 回目 `write_0x10` で `TIMEOUT write_rc=-2`、3 回目 `read_0x12` で `TIMEOUT read_rc=-2`。既知の断続的固着（非 strict xfail、従来 002 で 6 回中 5 回失敗）と同じ症状。
- 範囲外の読み出しの直接確認（診断、scratchpad の `diag_i2c_tail.py`）: リセット後、Pico から `0x10` へポインタ `2e` を書き、別の転送で 4 バイト読む → 3 回とも `rx=0000ffff`（0x2E/0x2F = 00、範囲外 2 バイト = FF）。その直後の `2c`＋4 バイト読み出しは 3 回とも `TIMEOUT`（読み出しの後に続く転送での固着、既知の症状）。
- マトリクス: 002 は `build-only`（既存の基準: 断続的固着のため通常の成功に数えない）のまま。状態は変えない。
- 006: 未実施。

## 3.4 ch32fun `i2c_slave_helper` の write コールバック（CH32V002 実測、2026-11-08 21:48 JST）

- 診断（サンプルは変更せず、既存のレジスタ配列で観測。scratchpad の `diag_helper_cb.py`）: guarded flash＋読み戻しの後、リセットごとに次を 3 回。`obs` = 1 転送で「ポインタ 00 を書き、repeated START で 5 バイト読む」（write_count, write_reg, write_len, read_count, read_reg）。
  - 3 回とも同一: obs0 `00 00 00 03 03` → 読み出しのみ 4 バイト・2 バイト → obs1 `00 00 00 11 03` → 0x11 へ 1 バイト書き込み → obs2 `01 11 01 17 03` → ポインタのみ 0x20 → obs3 `02 20 00 1d 03`。
  - 結論（実測）: 読み出しのみの転送の後、および「ポインタ書き込み＋repeated START 読み出し」の後は write コールバックは呼ばれない。書き込みで終わる転送（1 バイト書き込み、ポインタのみ）の後に 1 回呼ばれる。CH32V003 の解釈（[ログ](2026-11-07-1956-i2c-slave-helper-hil.md)）と一致。
  - 理由（推定、未確認）: master が最後の読み出しバイトに NACK した後、スレーブ送信側では STOPF が立たないため。
- 修正: `main.c` の `on_write` のコメントを観測に合わせた（「読み出し後も STOP を報告」は誤り）。コメントのみで、成果物は 002 `757542434faf…`、006 `5cf3f7bcd477…` のまま（1.1 と一致）。
- 006: 未実施。コメントには 006 も含めて書いたので、006 で異なれば直す。

## 4. ソースと資料の照合（実機なし、2026-11-08 21:50〜22:00 JST 頃）

資料の版: CH32V002 データシート V1.7、CH32V006 データシート V2.0、CH32V00X リファレンスマニュアル（英語）V1.5（いずれも `xprivate/` の変換物。本文は転載しない）。Arduino core: 公式 `WCH:ch32v` 1.0.6（`.arduino/official/.../hardware/ch32v/1.0.6`）。

### 4.1 乗算命令の生成と `-march`

- 逆アセンブル（`riscv64-unknown-elf-objdump -d`、2.7 の後の成果物）で `mul/mulh/mulhu/mulhsu` を数えた（実測）。
  - WCH SDK（`-march=rv32ec_zmmul_zicsr`）: 002/006 の全 15 例で `mul` 系あり（2〜9 個）、`__mulsi3` なし。
  - ch32fun（固定 `ch32fun.mk:79` で CH32V00x は `-march=rv32ec_zmmul`、GCC 13 未満なら `rv32ec`）: `ssd1306_i2c` だけ 1 個（002/006）。他の 13 例はソースに乗算がほぼなく 0 個、`__mulsi3` もなし。
  - Arduino（boards.txt `CH32VM00X_EVT.menu.pnum.CH32V006K8.build.march=rv32ecxw`）: 002/006 の全例で `mul` は 0 個、libgcc の `__mulsi3`（ソフトウェア乗算）がリンクされる。`xw` は WCH GCC の独自拡張で、Zmmul は含まない（指定から読み取れる範囲。`xw` の中身は未確認）。
- 資料: 002/006 のデータシートの機能一覧は「RV32EmC」、注記で「m は M 拡張の乗算サブセット」。→ Zmmul 相当の乗算命令を持つ、が資料の記述。
- コアの表記の揺れ（資料のまま記録）: 002/006 データシートとも、節見出しは「QingKe RISC-V2A Processor」、本文とブロック図は「RISC-V2C」。どちらが正しいかは資料からは決められない。
- 実機での実行確認は 7.2 で行う。

### 4.2 Arduino PATTERN 3（PC6/PC5）で PWM が出ない理由

- variant `variants/CH32VM00X/CH32V006K8/PeripheralPins.c:64-78` の `PinMap_TIM` は既定配置だけ（TIM2: PD4/PD3/PC0/PD7、TIM1: PD2/PA1/PC3/PC4、相補 PD0/PA2/PD1）で、全エントリが `AFIO_Remap_TIM*_DISABLE`。**PC6・PC5 はない**。
- `cores/arduino/wiring_analog.c` の `analogWrite()` は、ピンが `PinMap_TIM` にないとデジタル出力に落ち、値を 8 ビットに換算して 128 未満なら LOW、以上なら HIGH にする（PWM を出さない）。
- したがって PATTERN 3 では PC6/PC5 は段階ごとに一定レベルになり、過去の観測（003、`GPIO_PULSE` が 50 ms 以内にエッジなしで `TIMEOUT`、[ログ](2026-11-07-2113-arduino-adc-pwm-hil.md)）と矛盾しない。資料上、002/006 の TIM1_CH1 は PC6 に（RM のピン配置表の列による）リマップできるが、core 1.0.6 の variant はリマップ配置を持たない。説明はソースからの推定で、002/006 の PATTERN 3 の実機観測は既存の参考試験（xfail）のまま。

### 4.3 Arduino `SPISettings(1000000)` の見込み

- `libraries/SPI/src/utility/spi_com.c:176-197`: `spi_freq = PCLK2`、`speed >= spi_freq/2, /4, … /128` を順に調べ、最初に満たした分周を選ぶ。`ch32v00X_rcc.c`（core 内）で `PCLK2 = HCLK`。
- HCLK 48 MHz（`clock=48MHz_HSI`）なら、48/2…/32 = 1.5 MHz までは 1 MHz 未満を満たさず、48/64 = 0.75 MHz で成立 → **分周 64、SCK 約 750 kHz**（1 MHz を超えない最大値）。実測は 5.4。

### 4.4 `ADC_CLK_MODE` と `timer_dma` の DMA 割当

- RM `RCC_CFGR0`: bit 31 `ADC_CLK_MODE`（1 = HB クロックを分周しない、0 = 分周する）、**リセット値 0**。bit 28 `ADC_CLK_ADJ`（デューティ）。ADCPRE[15:11]: `110xx` = HBCLK/8、`000xx` = /2。
- WCH SDK（002/006）の `RCC_ADCCLKConfig()` はマスク `0x7FFF07FF` で bit 31 も 0 にしてから ADCPRE を書く。サンプルの `RCC_PCLK2_Div8`（0xC000）→ ADCPRE = 11000 → 48/8 = **6 MHz**。Arduino core も `RCC_ADCCLKConfig(RCC_PCLK2_Div8)`（`analog.cpp:143,643`）。ch32fun の `adc` サンプルは `RCC->CFGR0 &= ~RCC_ADCPRE`（/2 → **24 MHz**）で、bit 31 には触れない（リセット値 0 のまま）。
- データシート（002/006 同じ表）の fADC は典型 16 MHz、最大 48 MHz。どちらの設定も最大値以内。CH32V006 に固有の既定値の違いは資料に見当たらない（RM は V00X 全体の記述）。結果への影響は 7.8 で扱う。
- `timer_dma`（002）: RM の DMA1 要求表で TIM1 は Ch2 = TIM1_CH1、Ch3 = TIM1_CH2、Ch4 = TIM1_CH4/TRIG/COM、Ch5 = TIM1_UP、Ch6 = TIM1_CH3。サンプル（CH1→DMA1_Channel2、CH2→Channel3、CH3→Channel6）と一致。この表は V00X 共通（006 も同じ）。

## 5. 現在の DUT（CH32V002）での実機確認（実測、2026-11-08 21:52〜22:10 JST）

共通条件: CH32V002（各 flash 前に識別 0x002、`Part Type 00-20-06-20`）、固定配線、WCH-LinkE の 3.3 V 給電、電圧未測定。診断用のファームとスクリプトは scratchpad（使い捨て、サンプルとしては維持しない）。要点を本文に、ソースの全文を [診断ソース](2026-11-08-2137-fix-ch32v00x-sample-findings-diag-sources.md) に残す。

### 5.1 固定 ch32fun の `funAnalogInit()` / `funAnalogRead()`（002）

- 診断ファーム（`diag_analog`、ch32fun、`TARGET_MCU=CH32V002`）: UART PD5 に `A`（init 前）、`B:<CTLR2>`（init から戻った後）、以降 200 ms ごとに `r<PA1 の値>`。SysTick の比較割り込みで、init またはread の開始から 300 ms 以内に戻らなければ `T<段階>:<CTLR2>` を出して停止（タイムアウト）。PA1 は治具の GP12 から RC 経由で駆動。
- 結果（boot 3 回、各回同じ）: `AB:e0001` → **`funAnalogInit()` は戻る**。CTLR2 = 0x000E0001（ADON=1、EXTSEL=111、EXTTRIG=0）。
- その後 `T3:4e0001` → **`funAnalogRead()` は変換が終わらずタイムアウト**（SWSTART=1 のまま、EOC が立たない）。PA1 を High/Low に駆動しても `r` は1度も出ない。
- 資料との照合: RM の ADC_CTLR2 では bit 3:2 は予約（読み 0）なので、RSTCAL/CAL の解除待ちはすぐ抜ける。SWSTART は EXTSEL=111 の「外部トリガ源」で、EXTTRIG=1 で有効になる（RM 「外部トリガ」の節）。固定 ch32fun は CH32V20x 以外で EXTTRIG を立てないので、ソフトウェア開始が効かない。観測と一致。
- 判断: サンプル `adc`（ch32fun）は helper を使わず、直接レジスタを操作する現在の実装を維持する（仕様どおり）。上流への報告は別途判断（未実施）。
- 後片付け: `blink_and_read`（ch32fun）を build・flash・全量読み戻しで復旧（成功）。
- 006: 未実施。

### 5.2 CH32V002 `standby_wake` の起床直後の文字化け

- 方法: `main.c` の起床後 `SystemInit();` の直後に一時的に `Delay_Ms(N);` を入れ（N=0/10/100）、各 N で `uv run pytest --hil --hil-device ch32v002 --hil-framework wch -m hil tests/hil/wch/test_standby_wake.py` を 3 回（run dir `xprivate/runs/2026-11-08-2155-ch32v002-standby-delay-N<N>-<k>`）。各回 3 回の起床を記録。化けたバイト数 = 起床バースト先頭から、期待値 `"\r\nAuto wake "` と一致し始めるまでのバイト数。21:53:59〜21:58:50。
- 結果（全 9 回 passed）:
  - N=0（SHA-256 `f460056e…` = 1.1 と同じ）: 9 起床とも **14 バイト**（毎回同じ `58 d6 4c 58 b4 37 b7 1b b2 b7 6c 6d d9 90`）。
  - N=10（`e57c02a8…`）: 9 起床で 1 または 2 バイト（`e1` または `58 fe`）。
  - N=100（`8a750417…`）: 9 起床で 1 または 2 バイト（同じパターン）。
- 判断（ユーザー）: 10 ms の待ちを恒久的に入れる。002/006 の `main.c` に `Delay_Ms(10);` と理由を追加し、README・マトリクスに書籍との差として記載。
- 修正後の確認（002）: 3 回とも passed（run dir `…-2210-ch32v002-standby-delay10-final-{1,2,3}`、22:08〜22:10）。化けは各回 `[1, 1, 2]` バイト。成果物 `e57c02a8…`（N=10 の実験と同一）。
- 残る 1〜2 バイトの原因は未特定。006: 未実施（006 は待ちの追加前から化けなし、[ログ](2026-11-08-1656-ch32v006-wch-batch3-timer-dma-sleep-watchdog.md)）。

### 5.3 Arduino の `printf`（002）

- 診断スケッチ（scratchpad、002 の profile）: (a) `USART_Printf_Init(115200); printf("P1\r\n");` と、ループで `printf`。(b) `Serial.begin(115200);` の後に `printf` と `Serial.print` を交互。どちらも build・guarded flash・読み戻しの後、リセット直後から UART を取得（`diag_uart.py`）。
- 結果: (a) 受信 0 バイト（2 回）。(b) `S\r\n` と `s\r\n`（Serial.print）だけが届き、`printf` の `Q1`/`q<n>` は 1 バイトも届かない（2 回）。
- 原因（ELF とソースで確認）: リンクされる `printf` は WCH GCC 15.2.0 の `libprintf.a(wchprintf.o)` の弱いシンボル（map で確認）。逆アセンブルでは `printf` → `print(NULL, …)` → `printchar(NULL, c)` が `_write(0, &c, 1)`、つまり **fd 0** で書く。core の `Print.cpp` の `_write`（弱いシンボル、リンクされているもの）は fd 1/2 だけ `uart_debug_write` に送り、fd 0（STDIN）は捨てる。core の `system/CH32VM00X/SRC/Debug/debug.c` の `_write` は `#if 0` で無効。したがって `USART_Printf_Init` の有無に関係なく `printf` は何も出さない。
- 回避策（試していない）: スケッチで fd を無視する `_write` を強いシンボルで定義する、など。サンプルは書籍どおり `Serial` を使っているので変更しない。
- 006: 同じ core・同じツールチェーンなので同じ機構と推定。実機確認は 006 差し替え時に行う。
- SWIO の printf（`minichlink -T`）は 006 で行う。

### 5.4 Arduino `spi_master` の SCK（002）

- 方法: Pico の `GPIO_PULSE`（GP6 = PC5 SCK、ソフトウェアのポーリングで 1 µs 単位、未校正）を 8 回。比較のため、分周が既知の ch32fun `spi_master`（BR=/64 → 750 kHz、周期 1.33 µs）と WCH SDK `spi_master`（/256 → 187.5 kHz、周期 5.33 µs）も同じ方法で測った（`diag_pulse.py`、22:01〜22:03）。
- 結果: Arduino `period_us` = 4〜9（多くは 4）。ch32fun（750 kHz）= 4〜5。WCH（187.5 kHz）= 5〜6。
- 解釈: 750 kHz の基準も 4〜5 µs と出るので、この方法は 1 µs 前後の周期を測れない（エッジの取りこぼし。1.33 µs × 3 ≒ 4 µs）。Arduino の値は 750 kHz の基準と同じ傾向で、4.3 の見込み（750 kHz）と矛盾はしないが、測定値としては使えない。
- 必要なもの: PIO などでエッジ時刻を取る治具の機能（7.10 の一覧に記載）。

### 5.5 ch32fun `ws2812_spi`（002）

- 診断ファーム（`diag_ws`）: `WS2812BDMAInit()` の後 1.5 s 送信なし → 1 フレーム（6 LED）→ 1.5 s 後に `SPI1->CTLR1` の SPE=0 → 1 s 後に PC6 を通常の GPIO 出力 Low。Pico が GP7 を 20 ms 間隔で 250 回標本化（`diag_ws_run.py`）。
- 結果（3 回とも同じ）: Low 98 標本（リセット前の待ち＋送信前 1.5 s）→ **High 79〜86 標本（約 1.6 s、フレームの後から SPE=0 まで）** → Low（SPE=0 以降）。
- 解釈（実測から）: 待機 High は helper のバッファ（末尾は 0 を書く）ではなく、送信を終えた後の SPI1（1-line Tx、16 ビット）が MOSI を High に保っていることによる。SPE を 0 にすると Low に戻る。SPI がなぜ High を出すのか（周辺の仕様）は資料で確認できていない。
- 「1」の High: 既存 HIL（`tests/hil/test_extralibs.py -k ws2812`、run dir `xprivate/runs/2026-11-08-2204-ch32v002-ws2812`）で `t0h_ns=304 t1h_ns=976 idle_high=1`（Pico の偏り約 −32 ns）、passed。設計値は 3 MHz の 4 ビットで T0H 333 ns・T1H 1000 ns。WS2812B の T1H 0.8 µs ±150 ns の上限 950 ns を超える。
- 分周の変更について: helper は `SPI1->CTLR1` を `3<<3`（/16 = 3 MHz）に固定し、1 データビット = 4 SPI ビット（`1110`/`1000`）で作る。分周だけを変えると T0H も同じ比で変わり（例: /8 → T1H 500 ns、T0H 167 ns）、規格に入らない。サンプル側だけで直す方法はなく、helper（submodule）の変更が必要。実 LED がないので、規格への適合（実際に点灯・ラッチするか）は未確認のまま。
- 006: 未実施。

### 5.6 SSD1306 helper の既定 1 MHz（002）

- 資料: RM の I2C の節は「2 つの速度モード: 100 kHz と 400 kHz」。helper の `SSD1306_I2C_CLKRATE 1000000` は資料の範囲外。helper の計算（FS=1、DUTY=0）では CCR = 48 MHz/(3×1 MHz) = 16 → SCL High = 16 × 20.8 ns ≒ 333 ns、Low ≒ 667 ns。
- 観測（`diag_pulse.py`、`HELPER_CLOCK=1` と `=0` を build・flash、Pico は slave を動かさず `GPIO_PULSE`）: どちらの build でも GP11（SCL）と GP10（SDA）にエッジがある（SCL `period_us` 25〜27、SDA 4。両 build で同じ値なので、周期ではなく再送の間隔などを拾っていると考える。数値は使わない）。→ **DUT は 1 MHz 版でもバスに出力している**。
- Pico 側: `ssd1306_hw.c:46,79` が `i2c_init(…, 100000)`。pico-sdk 2.1.1 の `i2c_set_baudrate()` は `fs_spklen = lcnt < 16 ? 1 : lcnt/16` を設定する。100 kHz・125 MHz なら lcnt = 750、spklen = 46 サイクル ≒ 368 ns。DUT の SCL High 約 333 ns はこれより短いので、**Pico の I2C slave がスパイクとして捨てる**、とソースから説明できる（Pico の clk_sys が 125 MHz であることは設定から推定。Pico のファームを変えて確かめることはしていない＝治具の変更になる）。
- 結論: 何も受信できないのは Pico 側の設定による可能性が高い。ただし 1 MHz 自体が資料の範囲外なので、サンプルは 100 kHz に書き換える現在の実装を維持する。

## 7. 未確認事項の確認（CH32V002 実測分、2026-11-08 22:11〜22:23 JST）

共通条件は 5 と同じ。診断ファームはすべて scratchpad の使い捨て（全文は [診断ソース](2026-11-08-2137-fix-ch32v00x-sample-findings-diag-sources.md)）。各診断の前に guarded flash（識別 0x002）と全量読み戻しを行った。

### 7.2 乗算命令の実行（002）

- 診断: 12 個の 32 ビット入力（0、1、−1、2、0x7fffffff、0x80000000、0x12345678、0xdeadbeef、3、−3、0xffff、0x10000）の全 144 組について、`a*b`（mul）、`(int64)a*b >> 32`（mulh）、`(uint64)a*b >> 32`（mulhu）、`(int64)a*(uint64)b >> 32`（mulhsu）を計算し、結果の FNV-1a 32 を `H<hex>` で 300 ms ごとに出す。入力は `volatile`、各演算は `noinline`（コンパイル時に畳み込まれないように）。
- build と逆アセンブル: ch32fun 版（riscv64-unknown-elf、`-march=rv32ec_zmmul`）に `mul`×2、`mulh`、`mulhu`、`mulhsu` 各 1。WCH SDK 版（WCH GCC 15.2.0、`-march=rv32ec_zmmul_zicsr`、002/006 とも）に `mul`×7、`mulh`、`mulhu`、`mulhsu` 各 1。
- 期待値: ホストの Python で同じ計算を独立に行い `H318d595b`。
- 実機（002、22:11）: ch32fun 版・WCH SDK 版とも `H318d595b` を繰り返し受信（各 3 回以上）。→ **002 で mul/mulh/mulhu/mulhsu が正しく実行される**（この入力の範囲）。006: 未実施。

### 7.3 GPIO（002、22:16、同じ手順を 2 回、結果は 2 回とも同じ）

- 診断: UART のコマンド（Pico GP8 → PD6）で設定を切り替え、応答を PD5 → GP9 で受ける。治具の配線: PC0 → GP5（1 kΩ）、PA1 ← GP12（10 kΩ＋1 µF）、PC1 は 4.7 kΩ で DUT の VDD へプルアップ（→ GP10）。
- プル入力（PA1 の 1 µF を Pico で充電・放電した後、1 ms ごとに 1 s 読む）: 浮動入力は High のまま／Low のまま 1 s 変化なし。**プルダウン（CNF=10、ODR=0）で 57 ms 後に Low**、**プルアップ（ODR=1）で 25 ms 後に High**。→ プルアップ・プルダウンとも働く（抵抗値は未測定）。
- 出力の MODE ビット（PC0、CNF=00、High を出して GP5 を 50 回標本化、続けて Low）: **MODE=1 と MODE=3 は High/Low とも出力される。MODE=2（ch32fun の `GPIO_Speed_2MHz` の値）は High を書いても GP5 は Low のまま**（出力にならない）。WCH SDK（002/006）の `GPIO_Speed_*` は `GPIO_Speed_30MHz`（=1）だけで、`50MHz` は 003 の値 3 にあたる。→ 原稿の「資料からの推定」（MODE は 1 ビット、2 は出力にならない）を実測で支持。MODE=3 は bit0=1 なので出力になる。
- オープンドレイン: PC0（プルアップなし）で ODR=1 → GP5 は Low のまま（Pico 側もプルなしなので、DUT が High を出していないことと矛盾しない）、PP の High は High。PC1（4.7 kΩ プルアップ）で ODR=1 → High、ODR=0 → Low。
- EXTI（PA1、立ち上がり・立ち下がり両方、割り込み）: GP12 で High/Low を 3 往復 → 立ち下がり 3 回ちょうど、立ち上がりは 12 回・10 回（2 回の試行）。RC（時定数 10 ms）の遅い立ち上がりで、割り込みが複数回起きている（ハンドラは入った時点の PA1 のレベルで分類しているので、立ち上がり途中の揺れは「立ち上がり」に数えられる）。EXTI は両エッジで動作するが、この配線では回数の正確な確認はできない。
- 006: 未実施。

### 7.4 通信（002）

- UART（診断 `diag_comm`、22:18）: DUT の BRR を 57600／38400／19200／9600／2400 に切り替え、Pico から `HELLO123` を送って全てエコーされ、DUT 側の PE/FE/NE/ORE は 0、Pico 側の `uart_errors=0x0`。230400 は Pico の UART_XFER の上限が 115200 のため試せない。
- パリティ: DUT 8E1（9 ビット語＋PCE）に対し、Pico 8E1 → エコー・エラー 0。Pico 8O1 → DUT の PE が 5 バイトで 5。Pico 8N1 → PE 2・FE 4。
- フレーミング: DUT 115200 8N1 に Pico 57600 で `UUUU` → FE 6、`00`×4 → FE 4。→ PE と FE の検出は動作する。
- SPI 16 ビット: DUT が DFF=1、モード 0、/64 で 0xA55A を 1 フレーム送ると、Pico `SPI_SLAVE` が `rx=a55a`（MSB 先頭）、DUT は Pico の応答 `3cc3` を 16 ビットで受信（`Y3cc3`）。
- SCK/SCL の周期: Pico の `GPIO_PULSE` は 1 µs 単位のポーリングで、5.4 のとおり 1 µs 前後の周期は測れない。I2C は ch32fun `i2c_master`（100 kHz）で 1 回だけ `period_us=10`（残りは送信の間隔を拾った）。WCH SDK `i2c_master`（400 kHz）は Pico が slave 応答をしないと送信が止まり、エッジが得られなかった（`TIMEOUT pulse_edges`）。→ 周期の測定は保留（必要なもの: PIO 等でのエッジ時刻の取得、slave 応答と同時に測れること）。
- I2C のバスエラーからの復旧: Pico の `GPIO_DRIVE` は GP12/13/16/17 のみ、`I2C_FAULTTEST` は Pico 内部のループバック（GP16〜19）用で、DUT のバス（GP10/11）を Low に保持する機能がない → 保留（必要なもの: GP10/GP11 をオープンドレインで Low に保持するコマンド）。

### 7.5 ログ出力（002）

- 方法（`diag_log_run.py`）: Pico で取引（SHT31 模擬の `I2C_SLAVE`、ADT7310 模擬の `SPI_SLAVE`、WCH `i2c_slave` への `I2C_MASTER`）を行った直後に、32 バイトの UART 取得を始める。
- 結果: WCH SDK `i2c_slave` は 4 回とも 0 バイト（`printf` の行は取引の直後に出て、取得の開始に間に合わない）。Arduino `i2c_master` は起動直後の `start / loop 0 / temperature: 129` の断片だけ（模擬の手順が書籍の起動シーケンスに合っておらず、値も無効）。Arduino `spi_master` は `loop / software reset` の繰り返し（模擬の応答と DUT の周期が合っていない）。
- 判断: 今の治具では、取引と同時に UART を取り込めない（Pico は 1 コマンドずつ実行）ため、ログの値の確認はできない。HIL の判定には加えない。保留（必要なもの: I2C/SPI の模擬中に UART をバックグラウンドで受信し、後で返す Pico の機能）。なお、WCH SDK の `printf`（USART1）自体は 3.2 の診断で `init` などを受信できている。

### 7.6 省電力（002、22:22）

- ch32fun のスタンバイと PA1 の EXTI による起床（診断 `diag_stby`、ch32fun の `examples/standby_btn` を元に PA1・両エッジのイベント）: 5 s の待ちの後、PDDS=1、SLEEPDEEP=1 で `__WFE()`。起床ごとに `SystemInit()` → 800 ms 後に `K<n>,<PA1>`。
- 結果: Standby 中は `minichlink -i` が `Could not setup interface.`（デバッガ接続不可）。エッジなしの 2 s は出力なし。GP12 で High/Low を 3 往復させると `K0,1`、`K1,0`、`K2,1`、`K3,0`、`K4,1`、`K5,0`（エッジごとに 1 回起床、n は RAM で連続＝リセットではなく実行再開）。
- 後片付け: WCH-LinkE の 3.3 V を切って入れ直し（`minichlink -t` / `-3`）、5 s の待ちの間に ch32fun `blink_and_read` を書き込み、検出と全量読み戻しで復旧を確認。
- 消費電流・クロック停止は測っていない。006: 未実施。

### 7.1 未確認事項の一覧（資料作業、22:25 JST 頃）

- 原稿 `externals/ch32v003-book/articles-ch32v00x/*/README.md`（`ef013a6`）の全 15 章の「確認状況と制約」から「確認していない」事項を抜き出し、[okf/open-questions/ch32v00x-unverified.md](../open-questions/ch32v00x-unverified.md) に分類・状態・根拠付きで一覧にした（type: Open Question）。006 の結果が出た後に状態を更新する。

### 7.8 資料の確認（実機なし）

- 最小回路のコンデンサ: 002（DS V1.7）・006（DS V2.0）とも、1.4.3「Power Supply Scheme」の本文は VDD 2.0〜5.5 V（ADC 使用時 2.4 V 以上）だけで、デカップリング容量の値の記載はない（変換物の範囲。図はない）。容量が出てくるのは NRST の特性の図の「Filter 0.1uF」だけ。→ 推奨値は資料からは決められない（評価ボードの回路図の確認が要る。未実施）。
- 同じ表から: 内部プルアップ／プルダウンの等価抵抗は 35〜55 kΩ（典型 45 kΩ）、Schmitt のヒステリシス 150 mV 以上。7.3 の時間（プルダウン 57 ms、プルアップ 25 ms、1 µF＋10 kΩ）は時定数 約 55 ms と同じ桁で矛盾しない（しきい値は未測定なので計算での照合はしない）。
- ADC のクロックとサンプル時間: どちらのサンプルも SMP=7（239.5 サイクル）。ch32fun（ADCCLK 24 MHz）は 約 10.0 µs、WCH SDK（6 MHz）は 約 39.9 µs。DS の表 3-24-1（fADC 16 MHz）では 55.5 サイクル（3.47 µs）以上で外部入力インピーダンスの制限がなくなる（RAIN の最大 50 kΩ まで）。両設定ともこれより長いので、サンプル時間による結果の違いは資料上見込まれない。変換時間は 252 サイクル（24 MHz で 約 10.5 µs、6 MHz で 約 42 µs）。fADC は両方とも最大 48 MHz 以内。同じ入力での比較は「必要なら」の条件に当たらないと判断し、行っていない。

### 7.10 保留にする項目と必要なもの（この change では実施しない）

一覧の詳細は [unverified 一覧](../open-questions/ch32v00x-unverified.md)。必要なものをまとめると次のとおり。

- Pico 治具の機能の追加（ファームの変更）
  - PIO によるエッジ時刻の取得（ns 単位）: SPI の SCK、I2C の SCL の周期・Duty、WS2812 以外のパルス幅（S2、I1、5.4）。
  - I2C/SPI の模擬と同時に UART をバックグラウンドで受信し、後で返す機能: Arduino・WCH SDK のログの値の判定（I4、S6、7.5）。
  - GP10/GP11（DUT の I2C）をオープンドレインで Low に保持するコマンド: バスエラーからの復旧（I2）。
  - SPI slave のモード 1〜3、I2C master の 100 kHz 以外の速度（S1、I3）。UART_XFER の 115200 超（U1 の 230400）。
  - I2C slave のスパイクフィルタ（`fs_spklen`）を設定できるようにする: SSD1306 helper の 1 MHz の切り分けの確認（M4）。
- 配線の追加
  - `timer_dma` の SB、SC、SEL3、SDP と、複数ピンの同時サンプリング（T2）。
  - リマップしたピン（I2C の PC5/PC6、SPI・UART・PWM のリマップ先）（U4、T8）。
- 測定器
  - オシロスコープ／ロジックアナライザ: 波形、立ち上がり時間、周期の精度（G5、T1、T6、I1、M2）。
  - 電流計（µA 級）: 消費電流、スタンバイ（P1、C13）。
  - 校正した基準電圧・電圧計: ADC の精度・直線性（A1）。
  - 周波数カウンタまたは校正したクロック: HSI・LSI の絶対値、ボーレート誤差（U3、W1、P2）。
- 実物の部品・別個体
  - OLED（SSD1306）、NeoPixel、SHT31、ADT7310、CO2 センサー、LED、スイッチ、ジョイスティック（M1、U6、A7、G6）。
  - CH32V006 の別個体（PC4 の切り分け、ユーザーの TODO）、複数個体・温度・電源電圧の条件（T4、R2）。
- ユーザーの GUI 操作
  - Arduino IDE（ボード選択、書き込み、シリアルモニタ、ライブラリの導入）、MounRiver Studio、PlatformIO、SDI-Print（C8、C9）。
- 資料・問い合わせ
  - コアの表記（V2A/V2C）、F8P6 の扱い、推奨のデカップリング容量（評価ボードの回路図）（C3、C5、C6）。

### 6.2 の比較用データ（002、実測）

- LSI の推定（AWU の周期を Pico で測る）: `standby_wake` の HIL が記録した起床間隔（AWU = LSI の 10240 × 25 = 256000 サイクル、公称 2.000 s）を 5.2 の 12 回分（24 間隔）で集計。平均 2.2246 s（2.219〜2.232）。待ちの長さ別でも 2.221〜2.232 s でほぼ一定（起床後の処理時間はほとんど効かない）。→ **002 の LSI は 約 115 kHz**（Pico の時計基準、未校正。公称 約 128 kHz）。
- IWDG の時間（診断 `diag_iwdg`、ch32fun、WCH SDK の `watchdog` と同じ PR=/128・RLDR=2000、フィードしない）: 起動直後に読み戻した PSCR=5、RLDR=2000（設定が反映）。リセットまで 約 2.3〜2.4 s（3 回同じ。HSI 基準の 100 ms 刻み）。リセット後の IWDGRSTF=1。LSI 115 kHz からの計算値 2.22 s に近い（差は HSI と刻みの誤差の範囲と見る）。

### 7.7 再現性（002、22:22:46〜22:27:42）

- `uv run pytest --hil --hil-device ch32v002 --hil-framework ch32fun -m hil tests/hil` を 5 回連続（run dir `xprivate/runs/2026-11-08-2223-ch32v002-ch32fun-repeat-{1..5}`）。各回 build・flash・読み戻し・リセットを各試験で行う。対象: adc、blink_and_read（3 件）、i2c（slave/master）、pwm、spi、uart、watchdog（reset と sleep_wake）、extralibs（i2c_slave_helper、ssd1306 100 kHz、ws2812）。
- 結果: **5 回とも 14 passed、1 xfailed**（xfailed は既知の参考試験 ssd1306 `helper_1mhz`）。失敗なし。

### 8.2 の 002 分（22:32〜22:36）

- WCH SDK 全体（`--hil-framework wch`）: **14 passed**（161 s）。変更した `i2c_slave`（ClockSpeed）、`standby_wake`（10 ms の待ち）、コメントのみの各例を含む。
- Arduino 全体（`--hil-framework arduino`）: **8 passed、2 xfailed**（`i2c_slave` の既知の固着、PATTERN 3 の参考試験）。前回の回帰（[ログ](2026-11-08-1731-ch32v00x-regression-6-2.md)）と同じ内訳で、悪化なし。
- ch32fun は 7.7 の 5 回で確認（前回と同じ内訳）。

## CH32V006 での実機確認

006 の結果は [2026-11-08-2237-ch32v006-sample-findings.md](2026-11-08-2237-ch32v006-sample-findings.md) に分けて記録した（006 のマトリクスの根拠ログを 006 用に分けるため）。

## 8.3 書籍原稿で古くなった箇所（原稿の更新は別作業）

原稿 `externals/ch32v003-book/articles-ch32v00x/`（`ef013a6`）は、サンプルを `e8f76c4` のリンクで参照している。この change の後に追従が要る箇所:

- 全章・`sample-map.md`: サンプルへのリンクの固定コミット（`e8f76c4`）。コメントやコードを変えたサンプルは、新しいコミットへのリンクに更新が要る。
- 2 章 Arduino: 「`USART_Printf_Init()` と `printf()` のログは受信できませんでした」→ 原因が分かった（WCH GCC の `libprintf` が fd 0 で `_write` を呼び、core の `_write` が捨てる。006 でも同じ）。
- 3 章 WCH SDK: 「`zmmul` の指定の公式な根拠と、乗算命令の実際の使用は確認していません」→ データシートの「RV32EmC」で根拠、002/006 で生成と実行を確認。
- 4 章 ch32fun: 「SWIO 経由の printf（006）記録なし」→ 006 で受信を確認。「`zmmul`、`GPIO_Speed_2MHz/50MHz` は未確認」→ 確認済み。「1 MHz で Pico が受信できない」→ Pico のスパイクフィルタによる、とソースから説明（1 MHz は RM の範囲外）。
- 5 章 GPIO: 「プルダウン入力、オープンドレイン出力、`GPIO_Speed_2MHz`、GPIO の割り込みは確認していません」→ 002/006 で確認（EXTI は立ち上がりの回数を除く）。資料からの推定とした記述（MODE、プルダウン）は実測で支持された。
- 6 章 DMA・Timer: `timer_dma` のコメント（PSC 480、10 µs／100 µs、`TIM_TimeBaseInit` の 2 回呼び出し）と、`timer_blink` の「IPRIOR[8]」のコメントを直した。本文がサンプルのコメントを引用していれば合わせる。「CH32V006 の PC4 の無信号、原因未特定」→ タイマーではなくピン〜GP15 の経路の問題と判明（個体・接触の切り分けは未了）。
- 7 章 PWM: 「PATTERN 3 で出力が出ない」→ core 1.0.6 の `PinMap_TIM` に PC6/PC5 がなく、`analogWrite` がデジタル出力に落ちるため、と説明できる。
- 8 章 ADC: WCH SDK `adc` の冒頭コメントを 12 ビット・239.5 サイクル・校正なしに直した。「`EXTTRIG` が要ることは資料で確認できていません」→ RM で確認できた。「`ADC_CLK_MODE` の既定値」→ リセット値 0。「ADC のクロックの違い」→ サンプル時間が両方とも十分で、資料上は違いがない。「`funAnalogInit`／`funAnalogRead` は確認していません」→ init は戻るが read がタイムアウト。Arduino `adc.ino` のコメント（0〜4095）を直した。
- 9 章 UART: 「115200 と 9600 以外のボーレート、パリティ・フレーミングのエラー処理、SWIO 経由のログ出力」→ 確認済み（230400 は治具の上限で未確認）。
- 10 章 I2C master: WCH SDK `i2c_master` の `USE_REMAP 1` は build できなかった → `GPIO_PartialRemap2_I2C1` に直した（build のみ）。本文でリマップに触れていれば合わせる。
- 11 章 I2C slave: WCH SDK `i2c_slave` に `I2C_ClockSpeed = 100000` を追加（書籍との差）。Arduino `i2c_slave` の `on_request` の範囲判定を直した（範囲外は 0xFF、書籍との差）。ch32fun `i2c_slave_helper` の「読み出し後も STOP を報告」というコメントを直した。
- 12 章 SPI: 「16 ビット転送」→ 確認済み。「SCK の実際の周波数」→ 見込み 750 kHz（測定は治具の能力不足で未了）。
- 13 章 Watchdog: 「CH32V006 で設計値より長くかかった原因」→ 006 も約 2.3〜2.4 s で 002 と同じ。LSI が約 115 kHz（推定）であることと、以前の測り方の幅による、と考える。
- 14 章 省電力: WCH SDK `standby_wake` に起床後 10 ms の待ちを追加（書籍との差、002 の化けは 14→1〜2 バイト）。「待ちの実験は各 1 回で、恒久的な修正は未適用」→ 各 3 回で確認し、適用した。`sleep_wake` の「50 … 1Hz(1s)」、`standby_wake` の「window value 31」のコメントを直した。「EXTI の外部ピンによる起床、ch32fun でのスタンバイ」→ 002/006 で確認。
- 15 章 外部モジュール: 「ws2812_spi の High 待機の理由」→ 送信後の SPI1 が MOSI を High に保つ（SPE=0 で Low）。「ssd1306 の 1 MHz の原因未切り分け」→ 4 章と同じ。

### 7.9 サンプルのない題材の判断（途中、ユーザー回答）

- Arduino の watchdog と省電力: **追加しない**（ユーザー判断: Arduino API にないため。使うならレジスタか WCH SDK の呼び出しになる）。
- WWDG: 書籍にない内容なので、別の change `add-wwdg-sample` で追加を提案した（`openspec/changes/add-wwdg-sample/`、validate --strict で valid、実装は未着手）。
- 残り（`ch32v003_SPI.h`、`ws2812b_simple.h`、SSD1306 の SPI・ビットバンギング版、128×64 の Arduino スケッチ、006 だけにある機能）は、ユーザーの判断待ち。
- 追加の判断（ユーザー回答）:
  - `ch32v003_SPI.h`: 追加しない（CH32V003 向けで、レジスタ直接の書き方は原稿で解説済み）。原稿 `externals/ch32v003-book/articles-ch32v00x/12-spi/README.md` から、12.4 の言及、12.4.5 の節、12.8 の未確認の一覧の項目を削除した（作業ツリーのみ、未コミット）。
  - SSD1306 の SPI・ビットバンギング版: 追加しない（あったら良い程度の記述で、002 で動かされた記録もない）。
  - 128×64 の Arduino スケッチ: 不可として扱う（既知の `malloc(512)` の失敗）。
  - 006 だけの機能: Pico で測れるものを change `add-ch32v006-only-feature-samples` で提案。
  - 周期の測定・取引と同時の UART の取り込み・I2C のバスエラー・試験の改善: change `extend-pico-fixture-measurement` で提案。
  - 残り: `ws2812b_simple.h`（と WCH SDK の SSD1306 版）は判断待ち。
  - `ws2812b_simple.h`（2026-11-08 23:30 頃、ユーザー回答）: 002/006 で使うにはライブラリを直す必要があるので、本書では扱わない（[確認の記録](2026-11-08-2327-ch32v006-ws2812b-simple-check.md)）。原稿の 15 章で「前者を使ったサンプルはなく、002/006 では確認していません」を「002/006 には対応していなかった（`GPIO_Speed_2MHz` で出力にならず、006 の実機で信号が出なかった）」に書き換え、15.x の「確認していないこと」から外した。15 章の根拠になる 5 章の「`GPIO_Speed_2MHz` で入力のままになるのは推定で、実機では未確認」の 2 文も、002/006 の実測に合わせて直した（いずれも `externals/ch32v003-book` の作業ツリー、未コミット）。
- 7.9 の結論: WWDG と 006 だけの機能は別の change で提案、Arduino の watchdog・省電力、`ch32v003_SPI.h`、SSD1306 の SPI・ビットバンギング版、`ws2812b_simple.h` は追加しない、128×64 の Arduino スケッチは不可。すべての題材について判断が付いた。


## 追加: 002 の WCH SDK `watchdog` の LED2（PC4）（実測、2026-11-08 23:35〜23:38 JST）

- DUT: ユーザーが CH32V002 に差し替え（23:35 頃、ユーザー申告）。`minichlink -r + 0x1ffff704 4 -b` で `Detected CH32V002`、識別 `20 06 20 00`。固定配線（PC4 → GP15、PA1 ← GP12）。
- 方法（scratchpad の `diag_led2_run.py`、使い捨て）: `samples_ch32v002_wch/watchdog` を build・guarded flash・全量読み戻し（成果物はリポジトリの既存のサンプル）。
  - デバッガのリセット: `minichlink -b` の 0.3 s 前から GP15 を 10 ms ごとに 300 回標本化（3 回）。
  - IWDG のリセット: 1.5 s 待ってから PA1 を 2000 ms Low に保ち（`GPIO_DRIVE 12 0 2000`）、その直後から GP15 を 10 ms ごとに 300 回標本化し、続けて UART の `loop N cause=…` を読む（3 回）。
- 結果:
  - デバッガのリセット後: 3 回とも Low 45 → **High 50 標本（約 500 ms）** → Low。
  - IWDG のリセット後: 3 回とも Low 84〜88 → **High 50〜51 標本（約 500 ms）** → Low。UART は `loop 4 cause=IWDG`（標本化の後に読んだので、リセットから約 2.5 s 後の行）。
- 結論: **002 で、LED2（PC4）は起動のたびに約 500 ms 点く**（デバッガのリセット後と IWDG のリセット後の両方。時間は Pico の時計基準、未校正）。
- 補足（推定）: IWDG のリセットは、保持の終わりから約 0.85 s 後に起きた（3 回ともほぼ同じ）。サンプルは PA1 を読んでから 250/250 ms の点滅の後にフィードするので、保持の直前に読んだ回のフィードが保持の始まりから最大 0.5 s 遅れ、解放の後の次のフィードの前に時間切れになった、と考える。1.5 s の待ちがループの周期（500 ms）の倍数なので、毎回同じ位相になったと見る。既存の HIL の判定（`cause=IWDG` と小さいループ番号）には影響しない。
- 006 は PC4 の経路が通らないため観測できない（[006 のログ](2026-11-08-2237-ch32v006-sample-findings.md) 6.1）。
