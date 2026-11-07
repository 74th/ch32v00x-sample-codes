# Pico SPI loopback と CH32V003 SPI HIL

- 作業日時: 2026-11-07 約18:27–18:40 JST（各コマンドの開始時刻は未記録）。記録は 18:45 以降。別エージェントが 17:26 に build まで進めて中断した作業の引き継ぎ。
- 目的: Pico の SPI slave（PIO）を DUT の SPI master で検証し、Pico の SPI master（SPI0）と PIO slave を Pico 内 loopback で自己検証する。
- 配線: DUT は既存固定配線（PC0–GP5 CS、PC5–GP6 SCK、PC6–GP7 MOSI、PC7–GP4 MISO、各 1 kΩ）。**ユーザー申告**で、I2C loopback 配線（GP16–GP18、GP17–GP19、4.7 kΩ pull-up）を外し、SPI loopback として各 1 kΩ で GP19→GP20、GP18→GP21、GP17→GP22、GP26→GP16 を接続した。抵抗値・導通・電圧は独立測定していない。
- ツール: Pico SDK 2.2.0 `a1438dff1d38bd9c65dbd693f0e5db4b9ae91779`、picotool 2.1.1、WCH-LinkE 2.22、固定 ch32fun `b28d285460ce052a179dba8f4a22c6f73ff8e328`、pytest 8.4.2。
- ソース（未コミット、SHA-256 先頭16桁）: `protocol.c` `56fb6afd52d2be35`、`spi_fixture.c` `f8d688a65995df65`、`spi_loopback.pio` `510d0581a5f74cf3`、`spi_dut_slave.pio` `04c33d02ddf56b92`、`spi_loopback.py` `0ffdc38b40588797`、`tests/hil/test_spi.py` `7ad8b09f129c4af6`、`spi_master/main.c` `7aa67dbc9b16d3c9`。
- コマンド: `picotool load -f -v -x hardware/pico-tester/build/pico_gpio_tester.uf2`（verify OK、再書き込み 2 回: 17:26 build の firmware、その後 SPI_MASTER 削除版）、`uv run pytest --hil -m 'hil and spi' tests/hil/test_spi.py -q -s --hil-port /dev/serial/by-id/usb-Raspberry_Pi_Pico_E661AC8863223539-if00`、`uv run python hardware/pico-tester/spi_loopback.py --port <同>`。
- DUT HIL（実測、SPI_MASTER 削除前の firmware）: spi_master を build・flash・サイズ指定 readback 一致・reset。Pico PIO slave が `a55a` を受信、`3cc3` を返したとき DUT の PD2 High（`samples=1` 相当）、`0000` を返したとき Low を観測。MODE3 要求は `UNSUPPORTED` で拒否。1 passed。後始末で関連ピンが output=0・pull なしを確認。
- Pico loopback（実測、削除後の firmware）: `SPI_SELFTEST MODE0` を2回実行しいずれも `master_tx=a5 master_rx=3c slave_rx=a5`、baud 実効 99681。`MODE3` と余剰引数は `ERR INVALID`。終了後 GP16–22,26 は output=0、pull 無効。
- 判断: `SPI_MASTER`（GP4/6/7）は独立した相手がなく検証できないため、firmware から削除し、能力として公開しない。Pico の master 役は `SPI_SELFTEST`（SPI0 + PIO slave）のみで検証済み。
- 失敗: 初回の loopback スクリプト作成は実行前にユーザーが中断した（その後再実行して成功）。
- 未確認: mode 0 以外（Pico 側は未対応で拒否のみ）、100 kHz と DUT 750 kHz 以外の速度、信号波形・電圧、PIO slave の1回あたり2バイト以外、物理 USB 抜去。DUT 側の mode 不一致そのものは検出していない（Pico が mode 0 のみ対応のため、データ不一致の検出のみ確認）。
