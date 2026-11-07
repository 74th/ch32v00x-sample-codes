# タスク

## 1. helper 依存の枠組み

- [x] 1.1 `ch32hil` のマトリクス検証に helper 検証サンプルの class（例 `helper-verification`）を追加し、`sample`・`helpers`・`requires`（治具能力）・合否条件を必須にする。`hil-verified` には従来どおり `hil_tests` と `evidence` を要求する。`uv run pytest -q tests/unit/test_config_matrix.py` で、必須項目の欠落と helper 名の誤りを検出するテストを追加して通す。
- [x] 1.2 `hil/matrix.json` の `i2c_oled-ch32fun`、`neopixel-ch32fun`、`i2c_slave-ch32fun` の行を helper 検証の行（状態は未実装）へ変更し、`hil/matrix_ch32v002.json` に対応する未移植の行を追加する。CH32V002 の網羅性テストを含むマトリクスのテストが通ることを確認する。

## 2. i2c_slave helper（Pico の既存コマンドを使用）

- [x] 2.1 `samples_ch32v003_ch32fun/i2c_slave_helper/` を作る。Makefile では固定 submodule の `examples/i2c_slave` を include パスに加え、design D3 の観測用レジスタと PC0 表示を実装する。出典（book-code `i2c_slave-ch32fun`、helper パス、submodule revision）と変更点を冒頭コメントに記録する。`make` で build でき、生成物が `externals/ch32v003-book-code` を参照していないことを確認する。
- [x] 2.2 `tests/hil/test_extralibs.py` に i2c_slave helper の HIL を追加する。`I2C_PROBE` で 0x42 が ACK・0x43 が NACK、`I2C_MASTER` での 0x10 への書き込み、0x20 領域の読み出し、観測用レジスタでの書き込み・読み出しコールバックの回数と reg/length の確認、GP5 の High を確認する。`--hil` なしでは skip されることを `uv run pytest -q` で確認する。
- [x] 2.3 CH32V003 で `uv run pytest --hil -m extralibs tests/hil/test_extralibs.py -k i2c_slave --hil-port=<Pico>` を実行する。build、識別付き flash、readback、各観測を別々に判定し、`okf/log/` に記録して、マトリクスの行を実測に合わせて更新する。

## 3. SSD1306 模擬（治具）

- [x] 3.1 `hardware/pico-tester/ssd1306_model.c/.h` を、ハードウェアに依存しない形で実装する（design D4：転送単位の制御バイト分類、転送をまたぐ引数、0x20/0x21/0x22 とページモード、表示 on/チャージポンプの状態、未対応コマンドの記録、CRC-32）。`tests/unit/` に gcc でビルドするハーネスを追加し、既知の画素位置、COLUMNADDR/PAGEADDR の範囲の折り返し、ページモードでの書き込み、未知コマンド、不完全な転送を確認するテストを通す。
- [x] 3.2 Pico firmware に `SSD1306_CAPTURE` と `SSD1306_PAGE` を追加する（I2C1 slave 0x3C、GP10/GP11）。完了・エラー・`RESET_SAFE`・USB 切断で I2C を解除し、`CAPS` に追加する。`tests/unit/test_pico_protocol_c.py` 相当の試験で、引数の範囲、取得前の `SSD1306_PAGE` のエラー、`CAPS` の表示を確認する。`ch32hil/pico.py` が 256 桁の応答行を受け取れることを単体テストで確認する。
- [x] 3.3 自己検証：Pico 単体の I2C loopback 配線へ切り替えが必要かを判断する（既存の I2C1 slave を使う場合は I2C0 master から送るか、ホストモデル試験で代替するか）。採用した方法で、既知のコマンド・データ列からの CRC 一致、未対応コマンドの報告、タイムアウトを確認する。配線を切り替える場合はユーザーに依頼し、`okf/log/` に記録する。`protocol.md` にコマンド、制限、自己検証の範囲を書く。

## 4. SSD1306 helper（DUT）

- [x] 4.1 `samples_ch32v003_ch32fun/ssd1306_i2c/` を作る。`scene.h`（決まった描画）、`main.c`（init → 100 kHz への CKCFGR 上書き → scene → refresh を 500 ms ごとに繰り返す。上書きはビルド時の切り替えで無効化できる）、`extralibs` を include パスに加えた Makefile を用意し、出典と上書き内容を記録する。両方の切り替え設定で `make` が通ることを確認する。
- [x] 4.2 `tests/unit/` に期待値ハーネスを追加する。`ssd1306_pkt_send` をモデルに渡すスタブとして定義し、固定 submodule の `ssd1306.h` と `scene.h` で期待 CRC とフレームバッファを生成する。生成結果が決定的であること（2回実行して同じ値になる）と、scene の代表的な画素がモデルの単体テストと矛盾しないことを確認する。
- [x] 4.3 `tests/hil/test_extralibs.py` に SSD1306 の HIL を追加する。`SSD1306_CAPTURE` の CRC が期待値と一致すること、`display_on=1`、`unknown` の件数を記録する。不一致のときは `SSD1306_PAGE` で差分ページを取得して結果に添付する。
- [x] 4.4 CH32V003 で 100 kHz の HIL を実行して判定し、記録する。続けて上書きを外して helper の既定値 1 MHz で実行し、結果（成功・失敗・受信件数）を別の行として記録する。マトリクスと `okf/log/` を更新し、1 MHz の扱い（design の Open Question）をユーザーに報告する。

## 5. WS2812 デコード（治具）

- [x] 5.1 Pico firmware に WS2812 用の PIO（リセット待ち、High/Low 幅の計測、DMA）と、CPU による分類を実装し、`WS2812_CAPTURE <pin> <bytes> <timeout_ms>` を追加する（pin 7/20 のみ）。分類ロジックはホストのハーネスで単体テストできる形に分け、典型値、しきい値の境界、範囲外、ビット数の不足を確認するテストを通す。
- [x] 5.2 `WS2812_SELFTEST <OK|BADWIDTH|TIMEOUT>` を追加する（SPI0 3 MHz 16 bit、GP19→GP20）。`hardware/pico-tester/ws2812_selftest.py` を作り、今の SPI loopback 配線で3ケースがそれぞれ期待どおりの結果になることを実機で確認する。配線の状態は実行前にユーザーへ確認し、`okf/log/` に記録する。
- [x] 5.3 `protocol.md` と `hardware/pico-tester/README.md` に WS2812 のコマンド、しきい値、GP7 の `SPI_SLAVE` との排他、同じクロック源を使う自己検証の限界を書く。`CAPS` に表示され、未知の pin が `ERR INVALID` になることを確認する。

## 6. WS2812 helper（DUT）

- [x] 6.1 `samples_ch32v003_ch32fun/ws2812_spi/` を作る。固定 submodule の `ws2812b_dma_spi_led_driver.h`、`WSGRB`、6 LED の決まった色列を 100 ms ごとに送る。出典と book-code からの変更点（HSV アニメーションを固定色へ）を記録し、`make` で build できることを確認する。
- [x] 6.2 `tests/hil/test_extralibs.py` に WS2812 の HIL を追加する。期待するワイヤ上のバイト列をホスト側で導き、`WS2812_CAPTURE 7 18 <timeout>` の `rx` と照合し、`bad_pulses=0` を確認する。中央値の High 幅を結果に記録する。
- [x] 6.3 CH32V003 で HIL を実行し、build、flash、readback、デコード一致を別々に判定して `okf/log/` に記録し、マトリクスを更新する。

## 7. CH32V002 への移植

- [ ] 7.1 3サンプルを `samples_ch32v002_ch32fun/` へ移植する。CH32V002 で異なる点（WS2812 helper の HSCR 分岐、I2C1 の割り込みベクタ、I2C の CKCFGR の計算、SPI1 のクロック）を RM V1.5 と照合して記録し、build を確認する。
- [ ] 7.2 DUT を CH32V002 に差し替えて（既存の手順 `hardware/ch32v002-reproduction.md` に従う）、`--hil-device ch32v002` で3サンプルの HIL を実行する。結果を `hil/matrix_ch32v002.json` と `okf/log/` に記録し、DUT を CH32V003 に戻す。

## 8. 統合確認

- [ ] 8.1 `uv run pytest -q`（実機なし）が通ることと、`openspec validate verify-ch32fun-extralibs-with-pico --strict` が通ることを確認する。
- [ ] 8.2 CH32V003 で全 HIL（既存 + extralibs）を1つのコマンドで実行し、既存試験に回帰がないことを確認して記録する。
- [ ] 8.3 マトリクス、`hardware/wiring-proposal.md` の対象外の記述、README、protocol.md が実測ログと一致しているかを見直す。実測・ユーザー申告・推定が区別されていることと、`xprivate/` の内容を含まないことを確認する。

## Workflow follow-up

- 実装とレビューが済んだら、`openspec-archive-change` で specs を同期してアーカイブする。
