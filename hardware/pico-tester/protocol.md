# Pico fixture protocol v2（GPIO 試作）

USB CDC の ASCII 行プロトコル。新ファームウェアは v1 の `s` / `PICO_GPIO_V1` に対応しない。ホストが明示的な Pico を選び、再列挙を待って `CAPS` で確認する。`CAPS` に表示されない機能は未実装であり、治具として自己検証済みを意味しない。

## フレーム

要求は `<id> <command> [args...]\n`。id は十進の 0〜4294967295、応答は `<id> OK [key=value ...]\n` または `<id> ERR <class> <detail>\n`。コマンドと引数は空白区切り、英数字の大文字小文字は区別する。CR は無視する。複数要求を並行送信せず、1応答を待ってから次を送る。フレームは改行以外最大127文字、受信開始から改行まで1秒以内。空行は無視する。

id を復元できない不正フレーム、長すぎるフレーム、途中終了タイムアウトの応答は id 0。`ERR INVALID` は形式・範囲違反、`ERR UNSUPPORTED` は未知コマンド、`ERR TIMEOUT` は未完フレーム。USB 切断時は応答を保証できず、ホスト側でタイムアウトとして扱う。フレームタイムアウト後に遅れて到着する残りのバイトは別フレームとして扱われうるため、ホストは入力を破棄して再同期する。クライアントは自身の受信期限と `RESET_SAFE` を持つ。

## コマンド

- `1 CAPS` → `1 OK proto=2 fw=pico_fixture ...`（`cmds`、能力版、許可ピン、各上限を返す）
- `2 RESET_SAFE` → `2 OK safe=1`
- `3 GPIO_SAMPLE 5 200 10000` → `3 OK pin=5 count=200 interval_us=10000 samples=<200個の0/1>`
- `4 GPIO_DRIVE 16 1 100` → `4 OK pin=16 level=1 duration_ms=100 safe=1`
- `5 GPIO_LOOPBACK 16 17 1 100` → `5 OK pin=16 input=17 level=1 duration_ms=100 low=<回数> high=<回数> safe=1`
- `6 GPIO_PULSE 5 3000` → `6 OK pin=5 period_us=<周期> high_us=<High幅> duty_ppm=<100万分率> safe=1`
- `7 GPIO_STATE 16` → `7 OK pin=16 output=0 pull_up=0 pull_down=0`
- `8 GPIO_SELFTEST_PWM 16 17 50` → `8 OK output=16 input=17 target_hz=100 target_duty=50 period_us=<周期> high_us=<High幅> duty_ppm=<100万分率> safe=1`
- `9 UART_XFER LOOPBACK 9600 8 N 1 00a5ff 3 1000` → `9 OK mode=LOOPBACK baud=9600 actual_baud=9600 bits=8 parity=N stop=1 sent=3 received=3 uart_errors=0x0 rx=00a5ff safe=1`

`GPIO_SAMPLE` の引数は順に GPIO 番号、1〜300点、1000〜100000 µs。先頭点は直ちに取得、残りの点は要求間隔の待ち時間後に取得する。ソフトウェア処理時間が加算されるため精密な周期ではない。最大待ち時間は約30秒と通信・処理時間。途中の USB 切断では中止して応答を返さない。`GPIO_DRIVE <pin> <level> <duration_ms>` は GP12/13/16/17 のみ、level は 0/1、期間は 10〜2000 ms。GP12/13 は DUT と接続されており、対応する DUT ピンが入力であることと電源・方向を確認してから使う。あらかじめ接続先が安全であることを確認する。成功応答の前、エラー、USB 切断で出力を解除する。USB 切断はポーリングで検出するため約1 ms以上の遅れがある。`GPIO_LOOPBACK <output> <input> <level> <duration_ms>` は指定出力を駆動し、別の許可入力を約1 ms間隔で観測した low/high 件数を返す。応答 OK はコマンド完了であり、配線の判定はホストが行う。同一ピンは `ERR CONFLICT`。独立自己検証が完了するまでは使用済み能力と扱わない。

`GPIO_PULSE <pin> <timeout_ms>` は次の立上り・立下り・立上りの3エッジを最長 10〜5000 ms ポーリングして周期・High幅と duty を返す。期限内に揃わなければ `ERR TIMEOUT pulse_edges`。周波数は 1,000,000 / period_us Hz として計算できる。CPU と USB 処理による取りこぼし・遅延があり、測定範囲や精度は未校正。`GPIO_STATE <pin>` は GPIO の出力設定と内蔵 pull 状態を読む診断用であり、実際の電圧や配線の安全性を証明しない。

`GPIO_SELFTEST_PWM <output> <input> <duty_percent> [frequency]` は出力 GP16/17 と異なる入力 GP16〜19 を指定し、100 Hz または 10000 Hz、duty 10〜90% の Pico ハードウェア PWM を出力し、入力で3エッジを観測する。GP16–GP17 を抵抗を介して接続した Pico 単体の自己検証にのみ使用する。結果の許容範囲の判定はホストが行う。生成と計測は同一 Pico の時計を共有するため、独立した周波数校正にはならない。USB 切断・失敗・成功時は PWM を停止して安全状態へ戻す。SPI は未実装。

## UART loopback 試作

`UART_XFER <mode> <baud> <bits> <parity> <stop> <tx_hex> <rx_count> <timeout_ms>` は、`LOOPBACK` の場合 Pico UART0 の GP16 TX、GP17 RX を、`DUT` の場合 Pico UART1 の GP8 TX、GP9 RX を使用する。`LOOPBACK` は事前に GP16–1 kΩ–GP17 を接続する。`DUT` は PD6 RX / PD5 TX の接続と双方の電圧・方向を確認してから使用する。指定 baud 1200〜115200、データ 7/8 bit、parity `N`/`E`/`O`、stop 1/2、送受信各最大32バイト、期限 10〜5000 ms。`tx_hex` は偶数桁の16進、送信なしは `-`。7 bit の場合は 0x80 以上の送信値を拒否する。`rx_count` は期待受信数で 0〜32。送受信数がともに0の場合は拒否する。呼出は排他的・同期的で、完了、タイムアウト、エラー、CDC 切断で UART を停止し GPIO を入力・pull 無効に戻す。

成功応答は実際の baud、送信・受信数、受信データを含む。`uart_errors` の bit 0/1/2/3 はそれぞれ framing/parity/break/overrun、bit 4 は受信バッファ超過。エラーがあれば `ERR UART`、期限切れなら `ERR TIMEOUT` とし、どちらも部分受信データとエラービットを返す。実際の baud はハードウェア設定値で、独立した実測値ではない。エラー検出経路への意図的な framing/parity 不一致注入は未検証。DUT 用 GP8/GP9 の UART は実装済みだが実機未検証。初期化時に約27 ms をかけてアイドルを確立し、その間の受信データは破棄する。初期化完了前に届く起動メッセージの受信には使えない。期限はこの初期化後から数える。

自己検証（実機を駆動する明示操作）:

```sh
uv run python hardware/pico-tester/uart_loopback.py
```

## ADC の機能確認（未校正）

`ADC_OBSERVE <duty_percent> <settle_ms> <timeout_ms>` は GP13 に 10 kHz PWM を出し、PA2 の外付け RC に印加する。同時に GP9 UART RX から、DUT が出力する3桁16進 ADC 値＋改行を受け取る。duty は10〜90%、settle は100〜2000 ms、受信期限は300〜3000 ms。成功例は `10 OK duty=50 pwm_hz=10000 settle_ms=500 adc=489 actual_baud=115207 calibrated=0 safe=1`。PWM と UART は成功・エラー・切断時に解除する。DUT は別途 ADC サンプルを実行している必要がある。

これは PWM 設定と ADC の大まかな変化を確認する機能であり、電圧・ADC 精度は校正も保証もしない。GP13 の出力は PA2 が ADC 入力であることを確認してから使用する。10 kHz PWM のデジタル出力自体は GP16→GP18 の loopback で確認したが、RC 後の電圧は測定していない。

`GPIO_SELFTEST_PWM` は任意の第4引数に `100` または `10000` Hz を指定できる。省略時は100 Hz。I2C 自己検証の配線中は GP16→GP18 / GP17→GP19 でも使用できる。

## I2C loopback 試作

`I2C_SELFTEST MASTER0` / `MASTER1` は、GP16–GP18 を SDA、GP17–GP19 を SCL として2つの I2C コントローラーを接続し、master/slave を入れ替えてアドレス 0x42 に `55aa` を送り同じデータを読み返す。各信号線に Pico 3V3 への 4.7 kΩ 外付け pull-up が必要。存在しない 0x43 への負の要求も行い、SDK の戻り値を `wrong_address_rc` として返す。SDK の `-1` は NACK と他の一部バスエラーを区別できない。`I2C_FAULTTEST SDA` / `SCL` は一方の接続先を Low に固定し、もう一方の probe がバス競合または SCL タイムアウトを報告するかを確認する。試験失敗は `ERR I2C` または通信 timeout とし、終了時は4ピンを入力・pull 無効へ戻す。`uv run python hardware/pico-tester/i2c_loopback.py` でこれらをまとめて実行できる。

### DUT 向け I2C

GP10 SDA・GP11 SCL、外付け pull-up、100 kHz を使用する。`I2C_MASTER <7bit_addr_decimal> <tx_hex|-> <rx_count> <timeout_ms>` は指定バイトを書き、読み数があれば repeated START で読む。送受信は各最大32バイト、各トランザクションの上限は10〜1000 ms。成功は `OK addr=66 write_rc=2 read_rc=2 rx=1234 safe=1` の形式。期限切れは `ERR TIMEOUT`、SDK が区別できない NACK やバスエラーは `ERR I2C` と数値 `write_rc` / `read_rc` で報告する。

`I2C_PROBE <7bit_addr_decimal> <timeout_ms>` はオープンドレインでアドレスを送って ACK ビットを直接読む。`OK addr=66 ack=1` が ACK、`ack=0` が NACK。SCL が解放されない場合は `ERR TIMEOUT`、アイドル SDA が Low または arbitration の不一致は `ERR I2C bus_conflict`。Pico が同じバスを駆動する相手の役割を先に確認する。

`I2C_SLAVE <7bit_addr_decimal> <expected_rx_count> <reply_hex|-> <timeout_ms>` は DUT master からの書き込みと読み出しに応答し、受信・送信数と受信バイトを返す。上限は各32バイト、待機10〜5000 ms。途中経過で期限に達すれば `ERR TIMEOUT`、予定を超えるデータは `ERR I2C`。これらのコマンドと loopback の能力は電気的波形の校正を意味しない。

## GPIO の継続観測

`GPIO_SEQUENCE` は `GPIO_SAMPLE` と同じ引数・出力を持ち、最大300点、最大約30秒の有界観測を行う。観測中に改行なしの `!` を1文字送ると、次のサンプル時に `ERR CANCELED host_request` を返し安全状態へ戻る。観測中の他の入力は `ERR INVALID busy_input` として中断される。キャンセル後に `RESET_SAFE` を送れる。ピンの restart signature の解釈はホスト側で行う。

`GPIO_BUTTON_TEST <hold_ms>` は固定配線の GP12 を 2000〜5000 ms Low にし、1.5秒後以降の GP5 を観測して点数と High 数を返す。DUT の PA1 が入力である場合にのみ使用する。

## SPI

`SPI_SLAVE <4桁hex応答> [MODE0]` は PIO slave（GP4 MISO、GP5 CS、GP6 SCK、GP7 MOSI、固定配線で DUT の PC7/PC0/PC5/PC6 と接続）として、CS 1回あたり2バイトを受信し、指定した2バイトを返す。mode 0・MSB first のみ対応し、他の mode は `ERR UNSUPPORTED spi_mode`、応答が4桁 hex でなければ `ERR INVALID`、3秒以内に2バイトを受信しなければ `ERR TIMEOUT`。成功時は `OK mode=0 bit_order=msb received=2 rx=<hex> tx=<hex> safe=1`。DUT の SPI master（`samples_ch32v003_ch32fun/spi_master`）で実機確認済み。

`SPI_SELFTEST MODE0` は Pico SPI0 master（GP16 MISO、GP17 CS、GP18 SCK、GP19 MOSI、約100 kHz）と PIO slave（GP20 MOSI、GP21 SCK、GP22 CS、GP26 MISO）の間で `a5` を送り `3c` を返す自己検証。各線は 1 kΩ で GP19→GP20、GP18→GP21、GP17→GP22、GP26→GP16 と接続する（I2C loopback 配線とは共存できない）。成功時は `OK mode=0 bit_order=msb baud=<実効> master_tx=a5 master_rx=3c slave_rx=a5 safe=1`。Pico の master 役はこの自己検証のみで確認しており、独立した外部 slave での検証はしていない。mode 0 以外、複数バイト、100 kHz 以外の速度は未対応・未確認。`SPI_MASTER` は独立した相手がないため firmware から削除した。実行は `uv run python hardware/pico-tester/spi_loopback.py`。

## 安全状態と限界

許可ピン GP0・GP4〜GP22・GP26 を起動時、応答成功時、不正要求、フレームタイムアウト、USB 切断時に入力・内部 pull 無効にする。未許可ピンは拒否する。要求は直列実行され、出力は指定期間だけ所有する。長期間の予約は未実装で、loopback の同一ピン競合以外の同時割当は表現できない。USB 切断の検出は実行中も確認するが、最長サンプル間隔ぶん遅れる。Pico の未通電・リセット中のピン状態や外部 pull-up、RC の電荷はこの処理では制御できない。

## v1 からの移行

既存 `measure.py` は GP0 の v1 専用で v2 には使えない。旧 PC0–GP0 配線・v1 ファームウェアと、新 PC0–GP5 配線・v2 ファームウェアを混同しない。v2 に対応するホストで `CAPS` を取得し `GPIO_SAMPLE 5 ...` を使う。ロールバックする場合は接続・電源条件を確認し、過去 revision の v1 `main.c` を別ディレクトリでビルドして Pico に書き戻し、必要な配線を安全に戻す。BOOTSEL が必要になる場合がある。新たな配線とファームウェアを自己検証するまで、過去の v1 の PASS を v2 の PASS としない。
