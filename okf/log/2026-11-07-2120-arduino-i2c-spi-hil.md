# Arduino i2c_master / i2c_slave / spi_master の CH32V003 HIL と対象外 4 本（verify-arduino-core-with-arduino-cli 5.3〜5.6）

- 作業日時: 2026-11-07 21:18〜21:25 JST（HIL 開始時刻は `date` の実測: 1 回目 21:20:51、2 回目 21:22:09、Arduino 全体 21:22:56〜21:24:13。記録 21:25 頃）
- 対象・配線・ツールは [2026-11-07-2111](2026-11-07-2111-arduino-blink-and-read-hil.md) と同じ（CH32V003F4P6、固定配線、Pico E661AC8863223539、公式 `WCH:ch32v` 1.0.6、arduino-cli 1.5.1、固定 minichlink）。I2C は Pico GP10 SDA / GP11 SCL（外付け pull-up、100 kHz）、SPI は PC5→GP6、PC6→GP7、PC7←GP4、PC0→GP5。
- 範囲: 機能確認。Pico のコマンドは 1 つずつしか実行できず、各転送の直後に出る DUT の Serial 出力は受信できないので、**判定はバス上の内容とタイミング**で行った（Serial の値は未観測）。

## サンプル

| サンプル | 出典（book-code） | 変更点 | Flash / RAM |
| --- | --- | --- | --- |
| `samples_ch32v003_arduino/i2c_master` | `i2c_master-arduino_core_ch32` | なし | 10836 / 1040 |
| `samples_ch32v003_arduino/i2c_slave` | `i2c_slave-arduino_core_ch32` | なし | 10404 / 1080 |
| `samples_ch32v003_arduino/spi_master` | `spi_master-arduino_core_ch32` | **CS を追加**: 元のスケッチは CS を一切操作しない（core の `beginTransaction(SPISettings)` は `CS_PIN_CONTROLLED_BY_USER` で、ハードウェア NSS も使わない）。固定配線の PC0（→ GP5）を CS として、`beginTransaction`〜`endTransaction` の間だけ Low にした（`pinMode`/`digitalWrite` の追加のみ） | 12796 / 1036 |

## 5.3 i2c_master

スケッチ（DUT が master、相手は SHT31 0x44）: setup で `30 A2`（ソフトリセット）→ 300 ms → `30 41`（ステータス消去）→ 300 ms。loop で `24 00` → 300 ms → 6 バイト読み出し → 5000 ms。

Pico を `I2C_SLAVE 0x44` として SHT31 に見立て、読み出しには `66 66 <CRC> 80 00 <CRC>`（Sensirion CRC-8）を返した。

判定（`tests/hil/arduino/test_i2c.py::test_arduino_i2c_master`）:
1. リセットと並行して待ち受け → `rx=30a2`
2. 続けて → `rx=3041`
3. ループの転送 → `rx=2400`、`sent=6`
4. `I2C_SLAVE 0x45` を 3 s 待ち受け → 何も受けない（TIMEOUT、received=0）
5. 次のループの転送 → `rx=2400`、`sent=6`。3 と 5 の間隔が 4.8〜6.0 s（期待 ≈ 5.3 s）

結果:
- 1 回目（21:20:51）: **失敗**。手順 1 で `rx=3041` を受けた（`30a2` ではない）。原因は、直前の readback（minichlink `-b`）で DUT が再起動して setup が既に走り、Pico が待ち受けを始めたときには `30a2` が終わっていたこと（推定。2 番目の書き込み `3041` は 300 ms 後なので受けられた）。対策として、リセット前の待機（`reset_during(..., settle_s=1.0)`）を入れ、readback 由来の起動の書き込みが終わってから待ち受けるようにした。
- 2 回目（21:22:09）: pass。`30a2` → `3041` → `2400`+6 バイト → 0x45 は TIMEOUT・received=0 → `2400`+6 バイト、ループ間隔 **5.319 s**。
- Arduino 全体の実行（21:22:56〜）でも pass。

## 5.4 i2c_slave

スケッチ（DUT が slave 0x10、0x30 バイトのレジスタ）: 書き込みの 1 バイト目を position にし、2 バイト目以降をそこから書く。読み出しは position から 4 バイト返す。初期値は 0x20〜0x23 = `00 10 20 30`。

判定（`::test_arduino_i2c_slave`、Pico が master）: `I2C_PROBE` で 0x10 が ACK、0x11 が NACK。書籍自身のテスト master（`i2c_slave-test_master_arduino_core_ch32`: `endTransmission()` で STOP してから `requestFrom`）と同じく、position の書き込みと読み出しを別トランザクションにする。
- `20` 書き込み → 4 バイト読み出しで `00102030`
- `10 aa bb cc dd` 書き込み → `10` 書き込み → 4 バイト読み出しで `aabbccdd`
- `12` 書き込み → 2 バイト読み出しで `ccdd`

結果:
- 1 回目: **失敗**。最初はテストを「書き込み → repeated START → 読み出し」（`I2C_MASTER 16 20 4`）で書いており、`rx=00000000` が返った。
- 原因の確認: 2 回目の参考ステップで、position を 0x12 にした後に repeated START で `20` を書いてから読むと `rx=ccdd0000`（0x12 からの値）が返った。Wire の slave の `onReceive` は STOP で呼ばれるため、repeated START の読み出しは前の position のまま行われる、と判断した（実測からの推定。core のソースは読んでいない）。書籍のテスト master の手順（STOP あり）なら問題にならない。テストは書籍の手順に合わせ、repeated START の結果は参考値として記録するだけにした。
- 2 回目: pass。probe 0x10 ack=1、0x11 ack=0、`00102030`、`aabbccdd`、`ccdd`。参考の repeated START は `ccdd0000`。
- Arduino 全体の実行でも pass。

## 5.5 spi_master

スケッチ（ADT7310 の読み取り、`SPISettings(1 MHz, MSBFIRST, MODE0)`）: setup で 3000 ms 待ってから `reset_adt7310()`。これは 1 つの CS フレームで `FF FF FF FF` を送り、500 ms 待って `54` を送り、さらに 500 ms 待つ。loop では 2 バイトの `00 00` フレームで `raw` を読む。`raw` が 0000/FFFF なら再び `reset_adt7310()`、それ以外なら表示して 1000 ms 待つ。

Pico `SPI_SLAVE`（mode 0 のみ。CS ごとに 2 バイト受信、2 バイト返答）と、GP5（CS）の `GPIO_SAMPLE`（10 ms 間隔）で判定した（`tests/hil/arduino/test_spi.py::test_arduino_spi_master`）:
1. 起動時の reset フレームの先頭 → `rx=ffff`
2. reset フレームの CS Low（≥ 20 点）の後に High になることを確認
3. 読み出しフレームに `0c80`（13 bit で 25.0 ℃）を返す → `rx=0000`
4. 次の読み出しフレーム → `rx=0000`。3 と 4 の間隔が 0.9〜1.3 s（有効値なので `delay(1000)` の経路）。このとき `0000` を返す
5. 4 の直後の CS が ≥ 40 点（≥ 400 ms）連続 Low（無効値なので `reset_adt7310()` の経路）
6. その後の読み出しフレーム → `rx=0000`（ループが再開する）

結果:
- 1 回目: **失敗**。手順 2 がなかったため、手順 3 の `SPI_SLAVE` が同じ reset フレームの続き（500 ms 後の `54`）を拾い、`rx=5400` になった。Pico の PIO slave は CS の立ち下がりを待たず、CS が Low の間のバイトを受けると判断した（実測からの推定）。手順 2（CS が High に戻るのを待つ）を入れた。
- 2 回目: pass。`ffff` → CS `0:50, 1:10` → `0000`（返答 0c80）→ 1.007 s 後に `0000`（返答 0000）→ CS `0:50, 1:30`（最長 Low 50 点 ≈ 500 ms）→ 1.005 s 後に `0000`。
- Arduino 全体の実行でも pass。
- 1 MHz・mode 0・MSB first の設定は、Pico が受けたバイト列と一致したことでだけ確認した（Pico slave は mode 0 しか受けないので、mode の取り違えは検出できない）。クロック周波数は測っていない。

## Arduino HIL 全体（21:22:56〜21:24:13、実測）

```
uv run pytest --hil --hil-framework arduino -m 'hil and arduino' tests/hil/arduino \
  --hil-port=/dev/serial/by-id/usb-Raspberry_Pi_Pico_E661AC8863223539-if00 --hil-run-dir <scratch>/runall -q -rxXs
→ 6 passed, 1 xfailed in 77.00s
```

xfailed は PWM の PATTERN 3（参考、[2026-11-07-2113](2026-11-07-2113-arduino-adc-pwm-hil.md)）。

## 5.6 HIL の対象外 4 本

`hil/matrix_arduino.json` に `excluded` として理由と compile 比較の結果（[2026-11-07-2102](2026-11-07-2102-arduino-core-supplier-compare.md)）を記録した。

| スケッチ | 対象外の理由 | compile（3 供給元） |
| --- | --- | --- |
| neopixel | WS2812 のデータを PC0 に出す。固定配線の WS2812 デコード（PC6 → GP7）とは別のピン。実 LED の発光は対象外 | 3 つとも成功 |
| i2c_oled | 実物の SSD1306 OLED と Library Manager の「OLED SSD1306 - SH1106」が必要。表示内容を治具で観測できない | ライブラリなしでは `oled.h` 不足で 3 つとも失敗、ライブラリ 1.0.7 を入れると 3 つとも成功 |
| uart | 9600 baud の UART で CO2 センサー（コマンド `FF 01 86 ...`）と通信し、結果を SSD1306 OLED（`oled.h`）に表示する。実センサーと表示が前提 | i2c_oled と同じ（official-git は Flash 98%） |
| i2c_slave-test_master | book の i2c_slave に対する 2 台目の DUT（I2C master）。この役割は Pico が `test_arduino_i2c_slave` で受け持つ | 3 つとも成功 |

マトリクスの単体テスト（evidence のファイルの存在も検査する）は、このログを書いた後の `uv run pytest -q` で通った（216 passed、22 skipped。実測）。

## 未確認

- I2C・SPI の各転送の後に DUT が Serial に出す値（温度・湿度、`on_receive`/`on_request` の表示、`raw`/`temp`）。
- SPI のクロック周波数と mode（mode 0 以外は Pico で受けられない）、I2C のクロック。
- 実物の SHT31 / ADT7310 との組み合わせ。
- Wire slave の repeated START の挙動について、core のソースでの確認。
