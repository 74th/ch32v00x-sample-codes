# change `extend-pico-fixture-measurement` の実装記録

作業開始: 2026-11-09 08:05 JST（`date` の実測）。この記録は作業しながら追記する。追記の時刻は各節に書く。

## 1. 準備（タスク 1.1、1.2）

### 1.1 変更前の Pico の状態（実測、08:05 JST）

- `git status`: clean（作業開始時点）。
- 変更前の UF2: `hardware/pico-tester/build/pico_gpio_tester.uf2` の SHA-256 = `84bbf647cea0d12e6cf48abbe17797a3100ba039568afa7fec7c466c430728bf`。これは build ディレクトリに残っていた成果物で、Pico に実際に書き込まれている UF2 と同一かは未確認（`picotool info` は USB シリアル接続中のため BOOTSEL でなく読めなかった）。元に戻す場合はこの UF2 を書き戻す。UF2 の別コピーは取らない（ソースは git の履歴から再 build できる）。
- 変更前の `CAPS` 応答（実測、08:05 JST、`/dev/serial/by-id/usb-Raspberry_Pi_Pico_E661AC8863223539-if00`）:

```
1 OK proto=2 fw=pico_fixture cap_gpio=2 cmds=CAPS,RESET_SAFE,GPIO_SAMPLE,GPIO_SEQUENCE,GPIO_DRIVE,GPIO_BUTTON_TEST,GPIO_LOOPBACK,GPIO_PULSE,GPIO_STATE,GPIO_SELFTEST_PWM,UART_XFER,ADC_OBSERVE,I2C_SELFTEST,I2C_MASTER,I2C_SLAVE,I2C_PROBE,I2C_FAULTTEST,SPI_SELFTEST,SPI_SLAVE,SSD1306_CAPTURE,SSD1306_PAGE,SSD1306_SELFTEST,WS2812_CAPTURE,WS2812_SELFTEST cap_spi=1 cap_i2c=1 cap_adc=1 cap_uart=1 uart_modes=LOOPBACK,DUT uart_baud_min=1200 uart_baud_max=115200 uart_bytes_max=32 pins=0,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,26 sample_max=300 interval_us_min=1000 interval_us_max=100000 drive_pins=12,13,16,17 drive_ms_min=10 drive_ms_max=2000 pulse_timeout_ms_min=10 pulse_timeout_ms_max=5000
```

- DUT: ユーザー申告で CH32V006 が接続されている（作業開始時。型番の実機確認は未実施）。

### 1.2 変更前の基準（既存ログからの転記。今回は再実行していない）

出典: `2026-11-08-2137-fix-ch32v00x-sample-findings.md`（002）、`2026-11-08-2237-ch32v006-sample-findings.md`（006）。いずれも「修正後の全体回帰」の結果。

| デバイス | フレームワーク | 結果 |
|---|---|---|
| CH32V002 | ch32fun | 5 回とも 14 passed、1 xfailed（既知: ssd1306 `helper_1mhz`） |
| CH32V002 | WCH SDK | 14 passed |
| CH32V002 | Arduino | 8 passed、2 xfailed（`i2c_slave` の既知の固着、PATTERN 3 の参考試験） |
| CH32V006 | ch32fun | 5 回とも 14 passed、1 xfailed（既知: ssd1306 `helper_1mhz`） |
| CH32V006 | WCH SDK | 14 passed、1 xfailed（006 専用の PC4 参考試験） |
| CH32V006 | Arduino | 10 passed、2 xfailed（PATTERN 3 と PC4 の参考試験） |

ホスト単体テストの基準: 354 passed、43 skipped（`2026-11-08-2237-…` の記録）。

## 2. エッジ時刻の測定とバックグラウンド取り込みの実装（タスク 2.1 以降、08:5x JST 頃に実施。時刻は厳密には未記録）

- 追加: `hardware/pico-tester/capture.pio`（`edge_len`: High/Low の幅を 2 サイクル 1 カウントで交互に push、`uart_rx`: 8N1、8 サイクル/ビット）、`capture_fixture.{c,h}`（`EDGE_MEASURE`、`EDGE_SELFTEST`、`CAPTURE_START/READ/STOP`、`I2C_HOLD`）。`protocol.c` に配線、`CMakeLists.txt` に追加。`main.c` は USB 切断時に取り込みを停止する。
- 設計との差異: バッファは「リングバッファ」でなく線形バッファ（満杯で DMA が止まり、先頭のデータを残す。満杯は `full=1`、取りこぼしは `overflow=1`（PIO の RXSTALL）で区別する）。仕様（あふれを応答に示す）には合致する。
- `fixture_safe()` は全コマンドの先頭で呼ばれるが PIO1/DMA に触れないので、バックグラウンド取り込みは他コマンドで止まらない。止めるのは `RESET_SAFE`、`CAPTURE_STOP`、USB 切断。`WS2812_*` は PIO1 を共有するので取り込み中は `CONFLICT` を返す。
- build: `PICO_SDK_PATH=/home/nnyn/.pico-sdk/sdk/2.2.0`（build ディレクトリの CMakeCache の値）、arm-none-eabi-gcc。成功（警告の確認は未実施）。**build ディレクトリの UF2 を上書きしたため、1.1 で記録した変更前の UF2 は残っていない**（ハッシュのみ記録。元に戻すには git の変更前のソースから再 build する）。新 UF2 の SHA-256 = `91e5e660cc0e3158d3f3a8e71924e51a108bd8a599b3dc32d7cb9fc0bb5253f8`。
- 書き込み（実測）: `picotool load -f -v -x`、Verify OK。再認識後に `CAPS` が新しい `cmds`（`EDGE_MEASURE` など）と `cap_edge=1` を返した。DUT は接続したまま（ユーザー申告 CH32V006）。
- 自己検証の試行（実測）: `EDGE_SELFTEST 16 18 <hz> 50` を 1 MHz/750 kHz/187.5 kHz/100 kHz で実行 → 4 回とも `ERR TIMEOUT selftest_edges`。`GPIO_LOOPBACK 16 18 1 50` は low=50 high=0、`GPIO_LOOPBACK 16 17 1 50` も low=50 high=0 で、GP16 とこれらのピンの間に導通がない（ループバックの配線がない）とみられる。**配線は未確認**（ユーザーへ確認する）。測定の正しさは未確認。

### 2.3 エッジ時刻の測定の自己検証（実測、ユーザーが GP16 を GP17/GP18 に配線したと申告した後）

- 配線の実測: ユーザーは「GP16 を 1 kΩ で GP17 と GP18 に配線した」と申告したが、`GPIO_LOOPBACK` で全ピンを調べると **GP17→GP18 だけ導通があり、GP16 はどのピンにも導通がなかった**（GP10/11/12/15 などは DUT の出力・プルアップ・RC で出力に依らず High を読むため無視）。GP16 の接続は未解決（ユーザーに確認が必要）。そのため PWM の自己検証は出力を GP17、入力を GP18 にして実施した（`EDGE_SELFTEST` は出力に 16 か 17 を許す）。UART のループバック（GP16→GP17）は未実施。
- スクリプト: `hardware/pico-tester/edge_selftest.py`（`uv run python hardware/pico-tester/edge_selftest.py`、再認識の待ちは `ch32hil.pico.discover`）。ファームウェア UF2 `91e5e660…`。
- 結果: **PASS**（29 応答）。PWM 1 MHz／750 kHz（duty 50・25）／187.5 kHz／100 kHz（duty 10・50・90）／10 kHz／2 kHz で、周期は設定値（Pico のサイクル数から計算）と平均が一致、最大−最小は 0 か 16 ns（1 分解能）。High の幅は設定値と 0〜8 ns 差（750 kHz で −8 ns など、サンプリング位相による 1 サイクルの量子化）。`K_PERIOD=9`、`K_HIGH=4` を実測で確認。1 MHz は周期 1,000,000 ps、750 kHz は 1,336,000 ps（設定の 167 サイクル。分周した公称 1333.3 ns に対し PWM の整数分周の丸め）。
- 不正要求（範囲外のピン・回数・時間、引数不足、同一ピン、出力が 16/17 以外、周波数・duty の範囲外）はすべて `ERR INVALID`/`ERR CONFLICT`。エッジなしは `ERR TIMEOUT edge_words=0 of=22`。取り込み中の `EDGE_MEASURE`／`EDGE_SELFTEST`／2 つ目の `CAPTURE_START`／`WS2812_SELFTEST` は `ERR CONFLICT capture_active`。`CAPTURE_STOP` の後は測定が再び成功し（資源の解放を確認）、GP17/18/22 は `output=0 pull_up=0 pull_down=0`。
- 注意: 測定と PWM は同じ Pico のクロックを基準にしているため、この検証は絶対精度の校正ではない（設計どおり。値は「Pico の時計基準、未校正」）。

## 3. バックグラウンド取り込み・UART の拡張・I2C の保持（タスク 3.x、4.x）

### GP16 の配線の修正（ユーザー申告）

- 上の確認の後、ユーザーが「GP16 を見落としていた」と答え、GP16→GP17、GP16→GP18 が導通した（`GPIO_LOOPBACK 16 17`／`16 18`／`17 16` で high=30 の実測）。以後 GP16 の TX→GP17 の RX で UART、GP16/17→GP18 で PWM の自己検証ができる。

### UART_XFER のボーレート上限の引き上げと PIO の UART 受信

- `uart_fixture.c` の上限を 115200 → 921600 に変更（それ以外の `UART_XFER` の動作は変更なし）。新 UF2 SHA-256 = `3fbbcdcccf5526b1bb3b10cef25549ca1712196aed7d9d64988bb1ab101f83c4`（書き込み済み、`picotool load -f -x`）。
- `hardware/pico-tester/capture_selftest.py`（GP16→GP17 のループバック）の結果: **PASS**（実測）。
  - 1200／9600／115200／230400／460800／921600 baud で、`CAPTURE_START UART 17 <baud>` の後に `UART_XFER LOOPBACK`（別コマンド）を 8 回（1200 は 2 回、32 バイト／回、計 256 バイト。1200 は 8 バイト）実行しても、バックグラウンドの受信が全バイト一致（欠けなし、`frame_errors=0`、`overflow=0`）。`UART_XFER` 自体も同じボーレートで一致。
  - 921600 で 4096+64 バイト送ると `full=1 overflow=1 received=4096`、残った先頭 4096 バイトは正しい。
  - 同じ UART 通信（0x55 ×8、115200 baud）をバックグラウンドの EDGE 取り込みで受け、80 ワード、最短のレベル幅 8624 ns（1 ビット 8681 ns）。取り込み中に別コマンドが実行できることの確認でもある。
  - 不正要求 13 件（範囲外のピン、受信ピンに使えない GP4/8/12、ボーレートの範囲外・省略、EDGE に余分な引数、未知の種別、`CAPTURE_READ` の範囲外・非数値、`CAPTURE_STOP` の余分な引数）は全て `ERR`。`RESET_SAFE` が取り込みを止める（直後の `CAPTURE_START` が成功）。GP16/17 は安全状態。
- 制限・未確認: 921600 は Pico 単体のループバック（1 kΩ、約 数 cm の配線）での結果。DUT との間の最大ボーレートは DUT の実測で別に決める（7.x）。受信ピンは `CAPS` の `capture_uart_pins` で宣言した範囲だけ許す。実際の DUT 出力のピン（GP9、GP14 など）での受信は、ループバックでは GP17 でしか確認しておらず、DUT 試験（6.x）で確認する。パリティ・7 ビットは PIO の受信では未対応（8N1 のみ）。

### 3.1 の確認

- `CAPTURE_START` → `UART_XFER`／`EDGE_SELFTEST`（拒否される）→ `CAPTURE_READ`／`CAPTURE_STOP` の流れで、開始後に他コマンドが実行できることを上の自己検証で確認した（`I2C_SLAVE` などの取引は 6.x の DUT 試験で確認する）。

### 4. I2C のバスを Low に保つ

- `I2C_HOLD <SDA|SCL|BOTH> <10..2000 ms>`。コードは出力ラッチを 0 にしたまま方向だけを切り替える（`capture_fixture.c`、`gpio_put(…, 0)` のみで High は出力しない）。保持の後は `fixture_safe()` で入力に戻して 200 µs 待ち、解放後のレベルを読む。
- `hardware/pico-tester/i2c_hold_selftest.py`（DUT 固定配線のまま実行。DUT の VDD への 4.7 kΩ のプルアップあり）: **PASS**（実測）。SDA 保持 → `during_sda=0 during_scl=1 after=1,1`、SCL 保持 → `during_sda=1 during_scl=0 after=1,1`、BOTH → `0,0`、解放後 `1,1`。保持後の GP10/11 は `output=0 pull_up=0 pull_down=0`。不正要求（未知の線、10 ms 未満、2000 ms 超、引数不足・過剰、小文字）は全て `ERR INVALID`。
- DUT への影響: 実行時の DUT のファームウェアは作業開始時の状態（直前に書いたサンプルで、I2C を使うものかは未確認）。Low の保持は 220 Ω 経由で最長 100 ms。DUT の I2C を使うサンプルが走っていた場合、バスエラーの原因になりうるが、DUT の動作の確認はしていない。

## 4. ドキュメントとホスト側（タスク 5.1、5.2）

- `hardware/pico-tester/protocol.md` に「エッジ時刻の測定とバックグラウンド取り込み」「I2C のバスを Low に保つ」を追記、`UART_XFER` の baud 上限を更新。`protocol.c` の `CAPS` に新コマンドと `cap_edge=1 edge_periods_max=255 edge_res_ps=16000 capture_edge_words=4096 capture_uart_bytes=4096 capture_uart_pins=… capture_uart_baud_min/max capture_read_max i2c_hold_pins i2c_hold_ms_min/max`、`uart_baud_max=921600` を追加（`proto=2` のまま。既存コマンドは変更なし、追加のみ。`negotiate()` は変更不要）。`README.md`、`hardware/wiring.md`（ループバック配線の表）も更新。
- `ch32hil/pico.py`: `edge_measure`、`capture_start`、`capture_read`、`capture_stop`、`capture_collect`、`i2c_hold`、`edge_widths`、`Capture`、`PicoEdgeTimeout` を追加。`request` に個別の `timeout=` を追加（既存の呼び出しは変更なし）。
- ホスト単体テスト: `tests/unit/test_pico_client.py`（正常・あふれ・タイムアウト・不正・不整合な応答・チャンク読み・`edge_widths`）と、`tests/unit/pico_protocol_harness.c`／`test_pico_protocol_c.py`（`CAPS` の新項目、ディスパッチ、取り込み中の `WS2812_*` の `CONFLICT`、`RESET_SAFE` で解放）を追加。`uv run pytest`（実機なし）: **390 passed、49 skipped**（基準 354 passed、43 skipped から増加）。

## 5. 既存の自己検証の再実行（タスク 5.3 の一部）

- 現在の Pico の配線（GP16→GP17、GP16/17→GP18 のループバック）で実行できるもの（実測、UF2 `3fbbcdcc…`）: `uart_loopback.py`（24 境界ケースと 32 バイト・タイムアウト・不正引数）PASS、`pwm_selftest.py` PASS、`sequence_selftest.py` PASS、`gpio_loopback.py --output 16 --input 17` PASS。`CAPS` は新しい項目を返し、既存の項目は変更前と同じ（`cmds` の先頭 24 件が一致、`uart_baud_max` のみ 115200→921600）。
- **未実施**: I2C（`i2c_loopback.py`、`ssd1306_selftest.py`）、SPI（`spi_loopback.py`）、WS2812（`ws2812_selftest.py`）の Pico 単体の自己検証。それぞれ別のループバック配線（I2C は GP16–18/17–19 とプルアップ、SPI は GP19→20 ほか）が必要で、今の配線（GP16→GP17）と共存しないため。これらは DUT の全 HIL（I2C、SPI、SSD1306、WS2812 の試験）で実機の経路が使われる。

## 6. HIL 試験の追加（タスク 6.x。実装と、DUT=CH32V006 での個別の試し実行）

実装（すべて既存の判定は残し、追加のみ）: `ch32hil/judge.py`（周期・PWM・ログの判定、`uv run pytest tests/unit/test_judge.py` で 8 件）、`tests/hil/capture_helpers.py`（取り込みを USB セッション内で行う `captured`、`i2c_slave_captured`、`pwm_edge_survey`、`observe_i2c_bus_error`）。取り込みは USB シリアルを閉じると止まる仕様のため、開始・取引・読み出しを 1 回のセッションにまとめている。

許容幅（設計 6 の値をそのまま使用、変更なし）: SPI SCK と PWM は周波数の期待値 ±3 %、I2C SCL は −25 %〜+3 %。期待値の根拠は、SPI は ch32fun/Arduino が 48 MHz/64＝750 kHz、WCH SDK が /256＝187.5 kHz、I2C は ch32fun 100 kHz（CKCFGR）、WCH SDK `i2c_master` 400 kHz（`I2C_ClockSpeed`）、Arduino Wire の既定 100 kHz、PWM は ch32fun `timer_pwm` が 1 kHz・duty 25 %、Arduino `pwm` が 1 kHz・duty k/32、WCH `pwm` が 48 MHz/2/256＝93.75 kHz・duty k/32。HSI の許容差は −2.0〜+2.0 %（006 DS）。Pico の時計は未校正。

### 6.1〜6.3 周期の判定の追加（DUT=CH32V006、実測。run dir は `xprivate/runs/2026-11-09-0900-*`、`0920-*`、`0935-*`、`1000-*`、一部は `--hil-run-dir` なしで標準出力のみ）

| 項目 | 期待 | 測定（中央値） | 差 | 判定 |
|---|---|---|---|---|
| SPI SCK、ch32fun | 750 kHz | 744.05 kHz（周期 1344 ns、14 周期） | −0.79 % | passed |
| SPI SCK、Arduino | 750 kHz | 744.05 kHz（1344 ns、14 周期） | −0.79 % | passed（`SPISettings(1 MHz)` の実際の分周が /64 であることを確認） |
| SPI SCK、WCH SDK | 187.5 kHz | 186.29 kHz（5368 ns、14 周期） | −0.65 % | passed |
| I2C SCL、ch32fun | 100 kHz | 98.19 kHz（10184 ns、54 周期） | −1.81 % | passed |
| I2C SCL、Arduino | 100 kHz | 98.19 kHz（10184 ns、90 周期） | −1.81 % | passed |
| I2C SCL、WCH SDK | 400 kHz | 379.94 kHz（2632 ns、90 周期） | −5.02 % | passed（窓 −25〜+3 % の内） |
| PWM、ch32fun `timer_pwm` | 1 kHz、25 % | 平均周期 1007.2 µs（992.8 Hz）、duty 249975〜250038 ppm（10/10 が ±1 ポイント内） | −0.72 % | passed |
| PWM、Arduino `pwm`（PD2） | 1 kHz、k/32 | 平均周期 1008.1 µs（991.9 Hz）、duty は k/32 付近（15/16 が ±15000 ppm 内） | −0.81 % | passed（既存の `GPIO_PULSE` 判定も残して passed） |
| PWM、WCH `pwm`（PD2） | 93.75 kHz、k/32 | 平均周期 10.750 µs（93.02 kHz）、duty は k/32 付近（16/16 が ±20000 ppm 内） | −0.78 % | passed（既存判定も passed） |

- I2C の窓の根拠の見直し: 実測の差は −1.8 %（100 kHz）と −5.0 %（400 kHz）で、設計の窓（−25〜+3 %）の内側。窓の下側は 400 kHz の −5 % より十分広く、プルアップの立ち上がり時間の影響の上限（−25 %）として残す。**窓は変更しない**。ただし 1 台の DUT（CH32V006）・1 回の測定の結果であり、CH32V002 での測定（7.1）で改めて確認する。
- 測定が全て設定より 0.65〜1.8 % 低いのは、DUT の HSI の誤差（−2.0〜+2.0 %）と整合する（ch32fun と Arduino の SPI、I2C が同じ −0.79 %／−1.81 % なのは同じ DUT のクロックを使うため）。Pico 側の誤差は未測定のため、HSI の誤差と分離はできない（未確認）。

### 6.4 ログの値の判定（DUT=CH32V006、実測。passed）

- Arduino `i2c_master`: 取引（loop1、Pico が SHT31 0x44 として応答）と同時に取り込んだ Serial が `loop 1\r\ntemperature: 24 humidity: 50\r\n`（38 バイト、`overflow=0`、`frame_errors=0`）。模擬の値（T=0x6666、H=0x8000）から本の式で計算した期待の `temperature: 24 humidity: 50` と一致。
- Arduino `spi_master`: 有効な応答 `0c80` の読み出しの直後の出力が `loop\r\nraw: 0C80\r\nraw_int:400\r\ntemp: 25.0000\r\n`（45 バイト）。ADT7310 の模擬値 0x0C80 から計算した期待と一致。
- Arduino `i2c_slave_test_master`: `20` の書き込みと 4 バイト読み出し（応答 `a1b2c3d4`）の直後の出力が `receive available: 4\r\nread :A1 B2 C3 D4\r\n`（41 バイト）で期待と一致。
- WCH SDK `i2c_slave`: Pico の master の一連の取引（14 回）の間に取り込んだ `printf()` が 428 バイト。`reg[0x20]: 0 10 20 30` と `reg[0x10]: aa bb cc dd` を含み、`request:`/`receive:` の行も取れた（修正前は 4 回とも 0 バイトだった）。判定に使うのはレジスタの 2 行のみ。`count=`、`length=` の数値は DUT のタイミングに依存するため判定に使わない。
- 取り込めない、あふれた、フレームエラーがある場合は失敗にする（`judge_log`、単体テストで確認）。

### 6.5 I2C のバスエラーの観測（DUT=CH32V006、観測。記録のみで DUT の動作では失敗にしない。合否の対象外）

DUT の書き込みを待って（`I2C_SLAVE`）すぐに `I2C_HOLD`（SDA、続いて SCL を 1 秒）を実行し、その後に DUT の次の書き込みを待つ（最大 2 回、各 5 秒）。治具が線を解放できない場合のみ失敗。3 本とも passed（治具の解放は GP10/11 が `output=0 pull_up=0 pull_down=0`、解放後のレベルは SDA/SCL とも 1）。

| サンプル | SDA を保持した後 | SCL を保持した後 | DUT のログ |
|---|---|---|---|
| ch32fun `i2c_master` | 次の取引が戻った | 10 秒（2 回）待っても取引なし（TIMEOUT） | なし（ログ出力なし） |
| Arduino `i2c_master` | 戻った | 取引なし（TIMEOUT） | `loop 3`、`loop 4` は進み、`temperature: 129 humidity: 99`（0xFF ばかり読んだ値）が複数回。ループは止まらないが読み出しは失敗している |
| WCH SDK `i2c_master` | 戻った | 取引なし（TIMEOUT） | `i2c error: i2c bus busy` が複数回出た後、`Temperature: 24, Humidity: 50` に戻る行もある |

- 解釈の制限（未確認）: 「SCL を保持した後に Pico の `I2C_SLAVE` が取引を見ない」のが DUT 側の固着か、Pico の I2C スレーブ側の状態かは切り分けていない（WCH のログには保持後も `Temperature: 24, Humidity: 50` が出ており、DUT が応答を受け取ったことを示すが、その取引は `I2C_SLAVE` の待ちの外だった可能性がある）。書籍のサンプルに回復処理はない。マトリクスでは `hil_tests_variants`（観測の参照）にだけ載せ、確認済みには数えない。

### 6.6 ホスト単体テスト

- `uv run pytest`（実機なし）: **398 passed、52 skipped**（基準 354 passed、43 skipped）。`test_judge.py`（8 件）、`test_pico_client.py`、`test_pico_protocol_c.py` が増えた。新しい HIL 試験 3 本は `hil/matrix*.json` の `i2c_master` に `hil_tests_variants` として登録（既存のマトリクス整合の試験を通すため）。

## 7. CH32V006 での全 HIL（タスク 7.2。ユーザー指示により 002 より先に実施。DUT=CH32V006、ユーザー申告）

UF2 `3fbbcdcc…`、配線は GP16→GP17/GP18、GP17→GP18 のループバックも残した状態。各 `uv run pytest --hil --hil-device ch32v006 --hil-framework <fw> -m hil tests/hil -q -rA`（run dir `xprivate/runs/2026-11-09-1040-ch32v006-<fw>-full`。コマンド列はスクリプトの時計で 08:31〜08:40 JST 台）。

| フレームワーク | 結果 | 備考 |
|---|---|---|
| ch32fun | 18 passed、1 xfailed（115.6 s） | xfailed は既知の ssd1306 `helper_1mhz`。passed が基準（14）より増えたのは追加した試験（バスエラー観測など）と wwdg 等 |
| WCH SDK | 18 passed、1 xfailed（237.2 s） | xfailed は 006 の PC4 参考試験（既知） |
| Arduino | 初回 10 passed、1 failed、2 xfailed（133.9 s） | 失敗は `test_arduino_spi_master` の `dut_readback`（`minichlink exit code 247`）で、追加した判定の前の書き込み・読み戻し段階の失敗（ツールの一過性とみられるが原因は未調査）。同じ試験を単独で 2 回再実行 → 2 回とも passed（10.8 s。SCK・ログの判定を含む）。xfailed は PATTERN 3 と PC4 の参考試験（既知） |

- 既存の状態の悪化なし（基準: ch32fun 14 passed／1 xfailed、WCH 14 passed／1 xfailed、Arduino 10 passed／2 xfailed）。件数の増加は上記のとおり試験の追加による。
- 全試験の中で新しい判定（SCK・SCL・PWM の周期、ログ、バスエラーの観測）が使われ、passed。測定値は 6 の表と同程度（個別の値は run dir）。

## 8. CH32V002 での全 HIL（タスク 7.1。DUT=CH32V002、ユーザー申告で差し替え済み）

- 書き込み前の確認: `./scripts/ch32fun.sh flash ch32v002` → `Part Type: 00-20-06-20`、識別領域の上位型番 0x002 の照合を通過、`FLASH OK`（実測）。
- 各 `uv run pytest --hil --hil-device ch32v002 --hil-framework <fw> -m hil tests/hil -q -rA`（run dir `xprivate/runs/2026-11-09-1130-ch32v002-<fw>-full`、スクリプトの時計で 08:41〜08:49 JST 台）:

| フレームワーク | 結果 | 備考 |
|---|---|---|
| ch32fun | 18 passed、1 xfailed（115.4 s） | xfailed は既知の ssd1306 `helper_1mhz` |
| WCH SDK | 18 passed（230.3 s） | 失敗・xfail なし |
| Arduino | 9 passed、2 xfailed（119.0 s） | xfailed は `i2c_slave` の既知の固着と PATTERN 3 の参考試験 |

- 測定値（002）: 8 の表の 002 は `okf/peripherals/ch32v002-port-differences.md`。Arduino SCK 748.50 kHz（−0.2 %）、WCH SCK 187.41 kHz（−0.05 %）、Arduino SCL 98.66 kHz（−1.34 %）、WCH SCL 382.26 kHz（−4.43 %）、PWM は Arduino 997.2 Hz、WCH 93.56 kHz（duty は k/32 の 16/16）。ログ判定は Arduino `i2c_master`、`spi_master`、`i2c_slave_test_master`、WCH `i2c_slave`（367 バイト）とも期待どおり。バスエラーの観測は 006 と同じ傾向（SDA 保持後は戻る、SCL 保持後は 10 秒取引なし）。
- 既存の状態の悪化なし（基準 002: ch32fun 14 passed／1 xfailed、WCH 14 passed、Arduino 8 passed／2 xfailed。件数の増加は追加試験による）。ch32fun の測定値は結果ファイルを保存しない試験なので値は未記録（passed のみ）。

## 9. マトリクス・未確認事項の更新（タスク 7.3、7.4）

- `hil/matrix_ch32v00{2,6}{,_arduino,_wch}.json` の該当行（spi_master、i2c_master、pwm、i2c_slave（WCH）、i2c_slave_test_master（Arduino））の `criteria` に周期とログの判定を追記。許容幅（SPI/PWM ±3 %、I2C −25〜+3 %）と根拠は本ログの 6 と `ch32hil/judge.py`。CH32V003 の基準マトリクスは今回 003 で実測していないので criteria を変更していない。全 `i2c_master` 行に観測の `hil_tests_variants` を追加（確認済みには数えない）。`ch32fun` の 002/006 マトリクスには criteria 欄がなく変更なし。`matrix_ch32v002_wch.json` の `spi_master` 行は criteria 欄がないため追記できていない。
- `okf/open-questions/ch32v00x-unverified.md`: U1、I1、S2 を「一部」、I2 を「観測済み」、I4、S6 を「確認済み」に更新（根拠を追記）。`okf/peripherals/ch32v00{2,6}-port-differences.md` に測定値の表を追記。

## 未確認・残件

- Pico 単体の I2C／SPI／SSD1306／WS2812 の自己検証は今回再実行していない（別のループバック配線が必要。DUT の全 HIL で同経路は passed）。
- DUT との 230400 baud 以上、波形・立ち上がり時間、Pico の時計の校正、SCL 保持後の固着の切り分け。
- 作業日時はスクリプトの時計の表記（08:xx）と、ユーザー側の時刻の記録に差があるかもしれない。厳密な時刻は run dir 名とスクリプトログ（`full006.log`、`full002.log`）を参照。

## 10. 既存の Pico 単体の自己検証の再実行（タスク 5.3 の残り。UF2 `3fbbcdcc…`、配線はユーザーが張り替え）

5 の節で未実施だった I2C／SPI／SSD1306／WS2812 を、ユーザーに配線を張り替えてもらって実行した（時刻は未記録）。

- I2C 配線（GP16–GP18 を SDA、GP17–GP19 を SCL、各 3V3 へ 4.7 kΩ。ユーザー申告）: `i2c_loopback.py` **PASS**（`fault=SCL observed=TIMEOUT` を含む）、`ssd1306_selftest.py` **PASS**（実測）。
- SPI 配線（GP19→GP20、GP18→GP21、GP17→GP22、GP26→GP16。ユーザー申告）:
  - 初回の `spi_loopback.py` は失敗（`ERR SPI master_rx=00 slave_rx=a5`）。slave は `a5` を受信しており MOSI/SCK/CS は通っていたが、`GPIO_LOOPBACK` で GP16 を駆動しても GP26 が Low のままで、MISO（GP26→GP16）が未接続とみられた。ユーザーが「GP26 が抜けていた」と申告し配線を直した。**ファームウェアの不具合ではなく配線の誤り**。
  - 直した後の `spi_loopback.py` **PASS**（実測）。
  - `ws2812_selftest.py`（GP19→GP20）**PASS**（SPI 配線を作る前の初回実行でも PASS。`ERR TIMEOUT ws2812 bits=0` はタイムアウトの負のケースの期待どおりの応答）。
- これで 5.3 の既存の自己検証（GPIO、UART、I2C、SPI、SSD1306、WS2812、PWM、sequence）はすべて新しいファームウェアで PASS。既存の能力の変化なし。
- 配線は、ログの 6 以降の DUT 試験の前後で変わっている（今は SPI／WS2812 用の配線で、GP16→GP17/GP18 の UART／PWM 用ループバックは外れている）。DUT の HIL はループバック配線に依存しない。
