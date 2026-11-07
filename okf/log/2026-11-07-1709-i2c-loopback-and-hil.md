# Pico I2C loopback と CH32V003 I2C HIL

- 作業日時: 2026-11-07 16:55–17:09 JST。記録は作業後。
- 目的: Pico の I2C master/slave を DUT と独立して自己検証し、次に CH32V003 の両役割を build、flash、readback、通信、異常系、後始末まで確認する。
- 配線: ユーザーが Pico GP16–GP18 を SDA、GP17–GP19 を SCL とし、それぞれ 4.7 kΩ で Pico 3V3 に pull-up したと申告。DUT は既存固定配線の PC1–GP10 SDA、PC2–GP11 SCL、各 DUT VDD への 4.7 kΩ pull-up。抵抗・電圧は独立測定していない。Pico と DUT の I2C バスは別々で、GPIO loopback の導通は自己試験で確認。
- ツール: Pico SDK 2.2.0 `a1438dff1d38bd9c65dbd693f0e5db4b9ae91779`、TinyUSB `86ad6e56c1700e85f1c5678607a762cfe3aa2f47`、arm-none-eabi-gcc 14.2.1、picotool 2.1.1、WCH-LinkE 2.22、固定 ch32fun `b28d285460ce052a179dba8f4a22c6f73ff8e328`、pytest 8.4.2、pyserial 3.5。
- ソース: 未コミット作業ツリー。実験後 SHA-256 `protocol.c` `475fb723eca3cdc8b5e869abec28024f9b8a8f2ea9139cac1bf80674bd0ecb0c`、`i2c_fixture.c` `3ee8ff10c2b4372aa782daddc25e0fd2e8cd9601f94b20b83d90e900668e0734`、`i2c_loopback.py` `a18c865e71e4cea716c1cd09d762fd4d9d491b2cbdc5d9f6c41b7d8408093e06`、`tests/hil/test_i2c.py` `9e5c8ce7b7ae9fd8fadfe064afcc718166045374995639144b81bd6f23834649`。
- コマンド: Pico firmware を固定 SDK で build、`picotool load -f -v -x hardware/pico-tester/build/pico_gpio_tester.uf2` で書込みと verify。再認識は `measure.discover(30)`。`uv run python hardware/pico-tester/i2c_loopback.py`、`./scripts/ch32fun.sh flash ch32v003` でデバイス検出確認後、`uv run pytest --hil -m 'hil and i2c' tests/hil/test_i2c.py -q -s --hil-port /dev/serial/by-id/usb-Raspberry_Pi_Pico_E661AC8863223539-if00`。コード修正に応じて Pico verify、loopback と HIL を再実行。
- 自己検証（実測）: 100 kHz 設定、アイドル時 GP16/GP17 はそれぞれ10点連続 High。master を I2C0/I2C1 と交代し、0x42 への `55aa` 書込み・読み戻しが両方一致。0x43 への負の要求は SDK 戻り値 -1。SDA を接続先から Low 固定すると probe は BUS_CONFLICT、SCL Low 固定では TIMEOUT を識別。終了後 GP16〜19 は output=0、内部 pull 無効。
- DUT HIL（実測）: 両サンプルをそれぞれ build、CH32V003 検出・flash、サイズ指定 readback 一致、reset。DUT slave 時、0x42 の address probe ACK、0x43 NACK、`1234` の書込み・読み返し一致、無通信での slave 待機 timeout を確認。DUT master 時、Pico slave で `55aa` の受信と `1234` の2バイト送信を確認。2 passed、各 cleanup は安全状態確認済み。
- 失敗: 復旧前の Pico 無応答と確認できなかった書込みは `2026-11-07-1649-pico-reflash-unconfirmed.md`。ユーザーの BOOTSEL 再接続後、明示 `picotool load -v -x` の verify OK と v2 応答を確認して復旧。I2C の負アドレス・バス Low・timeout は意図的な異常注入。
- 未確認: 実際のバス電圧、立上り・クロック波形と精度、100 kHz 以外、物理 USB 抜去。SDK の generic error は NACK と一部バスエラーを区別できず、明示 probe の ACK bit と競合・timeout 判定は別途使う。DUT master sample は受信バイトをアプリへ報告しないため、Pico の2バイト送信は確認したが DUT アプリでの受信値までは証明しない。

## 追試: DUT master が受信した値の判定（17:10 JST、記録は実行直後）

- 前述の制限を解消するため、DUT master サンプルが読み出した2バイトを `12 34` と比較し、一致時のみ PC0 を High にするよう変更。Pico 側は I2C slave 要求後に GP5 で PC0 を観測する。
- `uv run pytest --hil -m 'hil and i2c' tests/hil/test_i2c.py -q -s --hil-port /dev/serial/by-id/usb-Raspberry_Pi_Pico_E661AC8863223539-if00` を再実行し、2 passed。Pico が `12 34` を返す場合に GP5 High、意図的に `de ad` を返す場合に GP5 Low を観測。両 DUT サンプルは build・flash・サイズ指定 readback 一致・reset 後に測定した。
- この追試の未コミットソース SHA-256: `tests/hil/test_i2c.py` `b004fbd6963ebc5b6a5cbd5b2870a68c4a4a070b0ef8070f21bbdda39f8b9f72`、`samples_ch32v003_ch32fun/i2c_master/main.c` `7300c7c160bf4b2eba2f34e961597aee6e2d1e543662815010822fc62c19fb32`。上記の Pico ソースは変更なし。電圧・波形は未測定。
