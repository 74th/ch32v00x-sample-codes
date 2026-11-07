# Arduino blink_and_read の CH32V003 HIL（verify-arduino-core-with-arduino-cli 4.1〜4.3）

- 作業日時: 2026-11-07 21:08〜21:12 JST（コマンド実行の時刻は `date` の実測。記録 21:13 頃）
- 対象: CH32V003F4P6（`Detected CH32V003`）、Pico `/dev/serial/by-id/usb-Raspberry_Pi_Pico_E661AC8863223539-if00`、WCH-LinkE `usb-wch.cn_WCH-Link_4DFC8F06D2DD`
- 配線: 固定配線（`hardware/wiring-proposal.md`）。Pico の GP19→GP20 loopback 配線は前回の作業から接続されたまま（[2026-11-07-2043](2026-11-07-2043-extralibs-integration-8.md) のユーザー申告。今回は未確認）。今回の試験では GP19/GP20 を使わない。電圧は実測していない。
- DUT が CH32V003 であることは、作業前に `minichlink -i` の `Detected CH32V003` で確認した（実測）。

## ソースとツール

- サンプル: `samples_ch32v003_arduino/blink_and_read/`（book-code `blink_and_read-arduino_core_ch32` のコピー。ソースの変更なし。ファイル名だけを `blink_and_read.ino` に変更）。
- ビルド: `make build` → `scripts/arduino.sh compile official <dir> --profile ch32v003`。arduino-cli 1.5.1、公式 `WCH:ch32v` 1.0.6（profile では `.arduino/official/data/internal/WCH_ch32v_1.0.6_*` に導入される）、riscv-wch-gcc 15.2.0。
- 共通の Makefile 規則: `samples_ch32v003_arduino/arduino.mk`（`PREFIX` は受け取って無視）。
- 書き込み: `ch32hil` の固定 minichlink（`externals/ch32fun`）。`arduino-cli upload` と WCH 版 OpenOCD は使っていない。

## 4.1 ビルド（実測）

```
make -C samples_ch32v003_arduino/blink_and_read build PREFIX=riscv64-unknown-elf
→ Sketch uses 7508 bytes (45%) / Global variables use 864 bytes (42%)、BUILD OK
```

- `main.bin` の SHA-256: `e4e02128ae3481e460838d55ee609cb060d58c5e10ea00e622cf48e6058490cf`。2.1 で official 1.0.6 + `--fqbn` で book-code から直接 compile したものとバイト一致（`cmp`）。
- `ARDUINO_FLAGS=-v` の標準出力に `externals` を含む行は 0 件。リポジトリ外の絶対パスも出ない。使った platform は `.arduino/official/data/internal/WCH_ch32v_1.0.6_bd88b8ad7f094181`。

## 4.2 HIL テスト

`tests/hil/arduino/test_blink_and_read.py::test_arduino_blink_and_read`（マーカー `hil`, `arduino`, `gpio`, `uart`）。期待値はスケッチのソースから導いた:

- 起動直後の Serial（PD5 → GP9、115200 8N1）: `init\r\nstart\r\nloop 0\r\nloop 1\r\n` を含み、`loop` の番号が 0 から連続する。UART 受信を開始してから 0.3 s 後に minichlink でリセットし、起動時の出力を受信窓に入れる（32 バイト、期限 5000 ms）。
- PC0（GP5）: 10 ms 間隔 300 点。端の run を除き High/Low とも 50±10 点（`delay(500)`）。
- PA1（GP12 で RC 経由 Low、3000 ms）: 1.5 s 以降の GP5 がすべて Low（`GPIO_BUTTON_TEST`、点数 ≥30、high=0）。解放後に再び 50±10 点の矩形波。
- `--hil` なしでは `HIL not selected` で skip、`--hil` かつ `--hil-framework ch32fun`（既定）では `arduino HIL test; --hil-framework ch32fun selected` で skip されることを確認（前者は実測、後者は単体テストの模擬テストで確認）。
- `tests/hil/arduino/` は `tests/hil/test_blink_and_read.py` と同名のモジュールを置くため `__init__.py` を置いてパッケージにした。共通処理は `tests/hil/arduino/common.py`。

## 4.3 実機実行（実測）

1. 検出確認（21:11:29）: `./scripts/ch32fun.sh flash ch32v003` → `Image written.`、`FLASH OK (runtime unverified)`（スクリプトが `Detected CH32V003` を確認して成功を返す。出力は末尾 5 行のみ確認）。
2. 1 回目（21:11:29〜21:11:46）:

```
uv run pytest --hil --hil-framework arduino -m 'hil and arduino' tests/hil/arduino/test_blink_and_read.py \
  --hil-port=/dev/serial/by-id/usb-Raspberry_Pi_Pico_E661AC8863223539-if00 --hil-run-dir <scratch>/run43 -s -q -rs
→ 1 passed in 16.80s
```

| 段階 | 結果 |
| --- | --- |
| pico_prepare / fixture_setup | pass |
| dut_build | pass |
| dut_flash（固定 minichlink、`Detected CH32V003`） | pass |
| dut_readback（required、バイト一致） | pass |
| dut_reset（UART 受信と並行） | pass |
| measure_uart | pass: rx=`init\r\nstart\r\nloop 0\r\nloop 1\r\nloo`、received=32、uart_errors=0x0 |
| measure_blink / check_blink | pass: runs `1:50, 0:50, 1:50, 0:50, 1:51, 0:49` |
| measure_button | pass: samples=150、high=0 |
| measure_resume / check_resume | pass: runs `0:100, 1:51, 0:50, 1:50, 0:49`（先頭の 100 は押下中の Low の続き） |
| cleanup | pass |

結果メタデータ: `device=ch32v003`、`framework=arduino`、`core=WCH:ch32v 1.0.6 (official)`、`arduino_cli=1.5.1`。

3. 2 回目（21:12:03 開始）: `1 passed in 15.57s`。UART は 1 回目と同じ。blink `1:50, 0:50, 1:50, 0:51, 1:50, 0:49`、button high=0/150、resume `0:101, 1:50, 0:50, 1:50, 0:49`。

## 判定

- build・flash・readback・観測の各段階が pass。公式配布 core 1.0.6 でビルドし固定 minichlink で書き込んだ書籍の blink_and_read が、CH32V003 で書籍のスケッチどおりに動作した（2 回とも）。
- `hil/matrix_arduino.json` の blink_and_read を `hil-verified` にした（hil_tests / evidence 付き）。
- 書籍 2.2 節の Blink（`scripts/arduino-sketches/book_blink`、PC0 1 s High/1 s Low）は今回書き込んでいない。PC0 の点滅は blink_and_read で確認した（周期は異なる）。

## 未確認

- 書籍の「エラーが表示されても出力タブに Verified OK と表示されれば成功」は、Arduino IDE と WCH 版 OpenOCD に固有の表示なので確認していない（design の Non-Goal）。
- thirdparty（1.0.5-beta）と official-git の成果物は書き込んでいない（ビルド比較のみ）。
- Serial の受信は起動直後の 32 バイトだけ。長時間の連続出力は見ていない。
- PD5 以外のピンへの影響、消費電力、電圧は測っていない。
