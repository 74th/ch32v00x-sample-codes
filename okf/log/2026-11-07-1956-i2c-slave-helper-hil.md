# i2c_slave helper サンプルの HIL（verify-ch32fun-extralibs-with-pico タスク 2.1〜2.3）

- 実行日時（実測）: 2026-11-07 19:53〜19:54 JST（シェルの `date` の値）。記録は同日 19:56 頃。
- 目的: 固定 submodule `externals/ch32fun/examples/i2c_slave/i2c_slave.h`（`SetupI2CSlave`）を使う DUT サンプルを、Pico の既存 `I2C_MASTER` / `I2C_PROBE` / `GPIO_SAMPLE` だけで検証する。既存のレジスタ直接版 `samples_ch32v003_ch32fun/i2c_slave` は変更しない。
- 条件: CH32V003F4P6（DUT は 2026-11-07 19:36 に差し戻し済みのまま。型番は flash 前の検出で確認）、固定配線 PC1/PC2–GP10/GP11、PC0–GP5、ベース `fb156e5`（作業ツリーは未コミット）、submodule `b28d285`。電圧は未実測。
- サンプル: `samples_ch32v003_ch32fun/i2c_slave_helper/`。helper は固定 submodule を `-I` で参照し、コピーも変更もしない。ビルド生成物の map に book-code への参照がないことを確認（実測）。helper の設定は既定のまま（バスクロック 1 MHz の fast mode 設定。Pico master は 100 kHz）。

## 実行コマンドと結果

1. `make`（サンプルディレクトリ）→ build 成功。FLASH 1460 B、RAM 92 B（実測）。
2. `uv run pytest --hil -m 'hil and extralibs' tests/hil/test_extralibs.py -s -q --hil-port=/dev/serial/by-id/usb-Raspberry_Pi_Pico_E661AC8863223539-if00`
   - 1 回目（19:53）: build/flash/readback/reset は pass。ACK(0x42)/NACK(0x43)、PC0 の Low→High、書き込みの読み戻し、0x20 領域も pass。コールバック観測だけ失敗（観測値 `02 10 04 0d 03`）。原因は、期待値を helper のソースから推測して決めた誤り（実測ではない推測が外れた）。
   - 切り分け: DUT を書き換えず Pico から読み出しのみ実行（scratchpad の使い捨てスクリプト）。結果（write_count, write_reg, write_len, read_count, read_reg）
     - obs0 `02 10 04 13 03` → obs1 `02 10 04 19 03`（観測用の 5 バイト読み出し 1 回で read_count が +6）
     - 4 バイト読み出し後の obs2 `02 10 04 24 03`
     - 0x20 へのポインタのみ書き込み後 `03 20 00 2a 03`
     - 0x11 へ 1 バイト書き込み後 `04 11 01 30 03`
   - 解釈（実測から導いた推定）: write コールバックは書き込み方向の転送の STOP ごとに 1 回（アドレスのみのプローブでも発火し reg=0,len=0）。読み出し転送の後は発火しない。read コールバックは読んだバイト数 +1（先読みの 1 バイト分）。
   - 2 回目（19:54）: 期待値を (2, 0x10, 4, 13, 3) に直して 1 passed（1.81 s）。この期待値は上の解釈（プローブ 1 + 書き込み 1、5+5+3）と一致する。

## 判定範囲

- Pico が観測した I2C 応答、PC0、読み戻しレジスタの範囲で確認。helper の 1 MHz 設定そのものでの動作確認ではない（master は 100 kHz）。
- 内部カウントの期待値は 1 回の実機実行で導いた。複数回の再現性・複数リセットでの確認は未実施。

## 未確認

- CH32V002 版（未移植）。電圧、波形、タイミング。1 MHz master との通信。
