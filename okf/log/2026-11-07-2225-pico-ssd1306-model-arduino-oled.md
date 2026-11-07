# Pico の SSD1306 模擬の修正と Arduino i2c_oled の HIL（verify-arduino-core-with-arduino-cli 9.3、9.5）

- 作業日時: 2026-11-07 22:22〜22:31 JST（コマンドの開始時刻は `date` の実測: Pico ビルド 22:26:11、書き込み 22:26:17、HIL 22:27:29 / 22:27:42 / 22:28:07 / 22:29:08。記録 22:32 頃）
- 経緯: [2026-11-07-2215](2026-11-07-2215-arduino-excluded-sketches.md) で i2c_oled は Pico の模擬と合わないため観測不可と判定した。ユーザーから「大変じゃないなら Pico 側を直してトライして、直ってから CH32V003 に置き換えよう」との依頼（ユーザー申告）。
- 対象: CH32V002F4P6（差し替えなし）、Pico E661AC8863223539（ファームウェアを再書き込み）、固定配線、公式 `WCH:ch32v` 1.0.6、ライブラリ「OLED SSD1306 - SH1106」1.0.7。電圧は実測していない。実物の OLED は使っていない。

## 原因（ソースの読み取り）

- ライブラリは `begin()` で水平アドレッシング（`0x20 0x00`）にし、`display()` で 4 ページそれぞれに `0xB0+page`、`0x21 0 127`、128 バイトのデータを送る。`0x22` は送らない。
- 修正前の模擬（`ssd1306_model.c`）は、`0x21` で列ポインタとページポインタの両方を先頭に戻し、フレームは「`0x21`/`0x22` 以降のデータ数がウィンドウ面積に達したとき」に数えていた。このためページがすべてページ 0 に重なり、フレームも数えられなかった。
- SSD1306 の公開データシートの読み取りでは、`0x21`（Set Column Address）が戻すのは列ポインタだけで、ページポインタは `0x22`（Set Page Address）で戻る。`0xB0`〜`0xB7` はページアドレッシングモード用。

## 修正（Pico ファームウェア）

- `hardware/pico-tester/ssd1306_model.c`: `0x21` は列ポインタだけ、`0x22` はページポインタだけを戻す（`column_reset` / `page_reset`）。水平・垂直モードでは、ウィンドウの最後のセル（`page_end`, `col_end`）に書いたときに 1 フレームと数える。ch32fun の helper のように `0x21 0 127`、`0x22 0 7` を送ってから 1024 バイトを送る場合は、従来と同じ数え方になる。
- `ssd1306_model.h` のコメントと `protocol.md` の説明を更新した。
- 単体テスト `tests/unit/test_ssd1306_model.py` に 2 件追加した: ライブラリと同じ送り方（ページごとに `0xB0+page`、`0x21 0 127`、128 バイト）でページ 0〜3 → 4〜7 と順に埋まり、2 回目の終わりで 1 フレームになること。`0x22` はページポインタだけを戻すこと。既存 10 件を含め 12 passed（実測）。
- ビルド（22:26:11）: `PICO_SDK_PATH=~/.pico-sdk/sdk/2.2.0 cmake --build hardware/pico-tester/build` → 成功。
- 書き込み（22:26:17）: `~/.pico-sdk/picotool/2.1.1/picotool/picotool load -f -v -x hardware/pico-tester/build/pico_gpio_tester.uf2` → Loading / Verifying 100%、OK、再起動後に `/dev/serial/by-id/usb-Raspberry_Pi_Pico_E661AC8863223539-if00` が戻った（実測）。
- `ssd1306_selftest.py`（Pico 単体の loopback 自己検証）は実行していない。loopback の配線が今は違うため（GP19→GP20 のまま、前回のユーザー申告）。代わりに DUT を使った ch32fun の SSD1306 helper の HIL で回帰を確認した（下記）。

## 期待値（ホストでの描画）

- `tests/unit/arduino_oled/`: `Arduino.h`・`Print.h`・`Wire.h` のホスト用代用ヘッダーと `harness.cpp`。harness はサンプルの `.ino` をそのまま include して `setup()` と `loop()` を 1 回実行し、ライブラリの描画バッファ（128×32 = 4 ページ × 128 バイト）を出力する。I2C のビット操作は `digitalRead` が常に High を返すので待たずに終わる。
- `tests/hil/arduino/oled_expected.py` がこれを g++ でビルドする。ライブラリは profile で導入された `.arduino/official/data/internal/OLED_SSD1306_-_SH1106_1.0.7_*` のもの（`user/libraries` に入れた 1.0.7 と `oled.cpp` が同一であることを `diff` で確認）。
- 単体テスト `tests/unit/test_arduino_oled_expected.py`: 描画結果が 4 × 128 バイトで、ページ 0〜3 の 0〜31 列がスケッチの `BUNCHO_74TH` 配列（128 バイト、縦 1 ビット）と一致し、文字と四角形の領域が空でないこと。

## サンプル

- `samples_{ch32v003,ch32v002}_arduino/i2c_oled/`（ソースの変更なし）。`sketch.yaml` の profile に `libraries: - OLED SSD1306 - SH1106 (1.0.7)` を追加した。build: V003 Flash 10916 B / RAM 1096 B（描画バッファ 512 B は malloc なので含まれない）、V002 12332 B / 1116 B。

## HIL（CH32V002、実測）

判定（`tests/hil/arduino/test_oled.py::test_arduino_i2c_oled`）: `SSD1306_CAPTURE 2 5000 INIT` を先に構えてから DUT をリセットする（ch32fun 側の `_capture_across_dut_reset` を再利用）。模擬のページ 0〜3 と 4〜7 がどちらも期待画像のページ 0〜3 と一致すること。あわせて display_on=1、display_on_seen=1、charge_pump=1、bad_control=0、overflow=0。

| 開始 | 実行 | 結果 |
| --- | --- | --- |
| 22:27:29 | ch32fun の SSD1306/WS2812/I2C helper（`-m 'hil and extralibs'`、`--hil-device ch32v002`） | 3 passed, 1 xfailed（従来どおり。xfail は helper 既定 1 MHz の参考行） |
| 22:27:42 | Arduino i2c_oled | 1 passed。`frames=2 transfers=34 cmds=92 data=2048 unknown=0 bad_control=0 overflow=0 display_on=1 display_on_seen=1 charge_pump=1 crc32=c691944f`。ページ 0〜7 すべて期待画像と一致 |
| 22:28:07 | ch32fun の全 HIL（`--hil-device ch32v002`） | 233 passed, 10 skipped, 1 xfailed（単体 219 件を除く HIL は 14 passed で従来と同じ。skipped 10 は Arduino テスト） |
| 22:29:08 | Arduino の全 HIL（`--hil-device ch32v002 --hil-framework arduino`） | 9 passed, 1 xfailed（xfail は pwm PATTERN 3 の参考行）。i2c_oled は crc32=c691944f で 1 回目と同じ |

- data=2048 バイトは、初期化での消去の表示 1 回と、ループの表示 3 回（各 512 バイト）に相当する（INIT は最後の表示オフから数える）。

## 判定

- CH32V002 で、Arduino i2c_oled が OLED ライブラリで描いた絵を、期待どおりのバイト列で SSD1306（0x3C）に送っていることを確認した（実物の表示ではなく、Pico の模擬で受けた内容）。
- Pico の修正後も、ch32fun の HIL の結果は変わらなかった（CH32V002）。
- `hil/matrix_ch32v002_arduino.json` の i2c_oled を `hil-verified`、`hil/matrix_arduino.json`（CH32V003）は `build-only`（未実行）にした。

## 未確認

- 実物の OLED での表示。特に、水平モードで `0xB0` が実機で効くかどうか（効く場合はページ i のデータがページ i に入り、効かない場合はデータシートどおりページが順に進む。模擬は後者で実装した。どちらでも 128×32 の画面に見えるページ 0〜3 の内容は同じ）。
- `ssd1306_selftest.py` による Pico 単体の自己検証（配線の都合で今回は未実施）。
- CH32V003 での i2c_oled、i2c_slave-test_master、neopixel の実行と、Pico の修正後の CH32V003 での ch32fun 全 HIL（差し替え後に行う）。
