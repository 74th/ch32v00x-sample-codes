# Design

## Context

- 固定配線（`hardware/wiring-proposal.md`）：PC1 SDA–GP10、PC2 SCL–GP11（各 220 Ω、DUT VDD へ 4.7 kΩ pull-up）、PC6–GP7（1 kΩ、DUT→Pico）、PC0–GP5（DUT の状態表示に既存試験でも使用）。Pico 単体の loopback は現在 SPI 構成（GP19→GP20 ほか、1 kΩ）。
- Pico firmware は USB CDC の行プロトコル v2（`hardware/pico-tester/protocol.md`）。要求は直列実行で、完了・エラー・切断時に許可ピンを安全状態へ戻す。GP7 は `SPI_SLAVE` の PIO も使う。
- 既存の `I2C_SLAVE` は1回のトランザクションで最大 32 バイトしか扱えず、SSD1306 の更新（初期化 + 1024 バイト）には使えない。
- helper の性質（固定 submodule `b28d285` で確認）
  - `ssd1306_i2c.h`：`SSD1306_I2C_CLKRATE` は `#ifndef` なしの `#define 1000000`。include 前の定義では上書きできない。
  - `ssd1306.h`：`ssd1306_cmd` は 1 コマンド（引数バイトも含む）ごとに制御バイト 0x00 付きの別 I2C 転送で送る。128×64 の `ssd1306_refresh` は COLUMNADDR/PAGEADDR を設定した後、32 バイトずつ 0x40 付きで送る（SH1107 定義時はページアドレッシング）。依存は `stdint.h`、`string.h`、`font_8x8.h` と `ssd1306_pkt_send` だけで、ホストでもビルドできる。
  - `ws2812b_dma_spi_led_driver.h`：SPI1 MOSI（PC6）に 48 MHz/16 = 3 MHz、16 bit DMA で出力する。1 データビットを 4 SPI ビット（`1110`=1、`1000`=0、1 ビット約 1.33 µs）で表す。HSCR の設定は CH32V003 のときだけ。
  - `i2c_slave.h`：I2C1 の event/error 割り込みを使うレジスタ配列型 slave。1 バイト目をレジスタ番号とし、書き込み・読み出しコールバックを呼ぶ。

## Goals / Non-Goals

**Goals:**
- helper を一切変更せずに使い、Pico が観測した送信内容でホスト側が合否を決める。
- 模擬・デコードの解釈ロジックは、Pico に載せる前にホストの単体テストで検証できる形にする。
- 既存の HIL 構造（`ch32hil` の段階判定、マトリクス、`okf/log/` の記録）にそのまま載せる。

**Non-Goals:**
- SSD1306 の全コマンドの模擬（スクロール、コントラストの効果、表示反転の描画への反映など）。
- WS2812 タイミングの規格適合判定や、実デバイスの表示・発光の確認。
- SPI 版 OLED（`ssd1306_spi.h`）、bitbang 版 I2C、`ws2812b_simple.h`。

## Decisions

### D1. 実施順序：i2c_slave helper → SSD1306 → WS2812

i2c_slave helper は Pico の既存 `I2C_MASTER` / `I2C_PROBE` だけで試験でき、治具を追加しなくてよい。SSD1306 は既存の I2C 配線と Pico の I2C slave を流用し、解釈ロジックをホストで先に検証できる。WS2812 は新しい PIO と自己検証が必要なので最後にする。
代替案：WS2812 から始める → 治具開発が最も重く、helper 検証の枠組み（マトリクス・include 方式）を固めるのが遅れるため不採用。

### D2. helper の参照方法

サンプルの Makefile で `EXTRA_CFLAGS += -I../../externals/ch32fun/extralibs`（i2c_slave は `-I../../externals/ch32fun/examples/i2c_slave`）を追加し、ソースでは `#include "ssd1306_i2c.h"` のように名前だけで include する。helper をサンプル内へコピーしない。各サンプルの README または冒頭コメントに、出典パス、submodule revision、book-code の元サンプルからの変更点を記録する。
代替案：book-code のようにサンプル内へコピーする → 固定 submodule の helper を検証したことにならないため不採用。

### D3. i2c_slave helper サンプルの観測可能な契約

アドレスは 0x42（既存の `i2c_slave` 試験と同じ）。サイズ 0x30 のレジスタ配列を持ち、メインループでコールバック情報を観測用レジスタへ反映する。

- 0x00：書き込みコールバックの回数
- 0x01–0x02：最後の書き込みの reg と length
- 0x03：読み出しコールバックの回数
- 0x10–0x1F：master が書き込める領域
- 0x20–0x2F：起動時に既知値で初期化する読み出し専用の領域

書き込みコールバックが期待した reg・length で発火したら、PC0 を High にする（GP5 で観測）。Pico は `I2C_MASTER 66 <reg+data> <n>` で書き込みと読み出しを行い、観測用レジスタを読み返して照合する。誤ったアドレス（0x43）が NACK になることも確認する。

### D4. SSD1306 模擬：共通 C モデル + Pico I2C slave

- 解釈ロジックは、ハードウェアに依存しない C モジュール（`ssd1306_model.c/.h`）にする。I2C の START から STOP までを1転送とし、先頭の制御バイトで分類する。0x00 はコマンド（引数バイトが別転送で届いても状態を引き継ぐ）、0x40 はデータ。Co ビットを含む他の値は未対応として数える。
- 対応するコマンド：0x20（アドレッシングモード）、0x21/0x22（列・ページ範囲）、0xB0–0xB7 と 0x00–0x0F/0x10–0x1F（ページモード）。引数があるコマンドは表で引数数を管理して読み飛ばす。0xAE/0xAF（表示 off/on）と 0x8D（チャージポンプ）は状態として記録する。それ以外の未知コマンドは件数と最初の数個の値を記録する。
- フレームバッファは 1024 バイトで、ハッシュは CRC-32（IEEE）にする。
- Pico 側のコマンド
  - `SSD1306_CAPTURE <frames> <timeout_ms> [INIT]`：I2C1 を GP10/GP11 の slave 0x3C として開始する。COLUMNADDR/PAGEADDR のウィンドウ面積分（全画面で 1024 バイト）のデータを受けるたびに 1 フレームと数え、指定フレーム数に達した時点で完了してフレームバッファを凍結する（`ssd1306_init` が空フレームを 1 つ送るため、起動直後から取得すると 2 フレーム待つ）。`INIT` 指定では表示オフ（0xAE）を受けるたびに模擬の状態をクリアし、最後の初期化シーケンスからを数える（DUT の二重起動やリセット前の通信が混ざらないようにするため。実機で確認した）。`frames`、`cmds`、`data`、`unknown`、`display_on`、`crc32` を返す。期限切れは `ERR TIMEOUT` と途中の件数を返す。
  - `SSD1306_PAGE <0-7>`：直前に取得したフレームバッファの1ページ（128 バイト、256 桁の hex）を返す。応答行の長さが受信側の制限内であることを先に確認する。
  - 完了・エラー・`RESET_SAFE` のどの場合も I2C を解除してピンを安全状態に戻す。フレームバッファは次の `SSD1306_CAPTURE` まで保持する（ピンを持たないので安全状態と矛盾しない）。
- 同じ `ssd1306_model.c` をホストの単体テストでも gcc でビルドする（既存の `pico_protocol_harness.c` と同じ方式）。

### D5. SSD1306 の期待値：同じ描画コードをホストで実行

DUT サンプルの描画処理を `scene.h`（`ssd1306_setbuf`、`drawstr`、`drawRect`、`drawImage`、`drawPixel` を使う決まった画面）に分ける。DUT の `main.c` とホストのハーネスの両方から include する。ホストのハーネスは `ssd1306_pkt_send` を D4 のモデルに渡すスタブとして定義し、固定 submodule の `ssd1306.h` を include して `ssd1306_init(); scene(); ssd1306_refresh();` を実行し、期待 CRC とフレームバッファを出力する。HIL テストは、Pico の結果がこの期待値と一致することを判定する。
これは helper を helper 自身と比べる自己参照になる。そのため、ホストのテストではモデルの単体テスト（既知のビット位置の画素や文字の一部）を別に置き、描画 API の意味が明らかにおかしくないことも確認する。
代替案：期待フレームバッファを手で作るか Python で再実装する → 描画 API の再実装の誤りを検証することになるため不採用。

### D6. SSD1306 の I2C クロック

`SSD1306_I2C_CLKRATE` はマクロで上書きできない。そこで 2 段階で確認する。

1. 100 kHz：DUT サンプルが `ssd1306_i2c_init()` の後に I2C1 を PE=0 にし、`CKCFGR` を 100 kHz の標準モードの値に設定し直してから PE=1 にする。helper の I2C 送受信処理はそのまま使う。上書きしたことはサンプルに記録する。
2. 1 MHz（helper の既定値）：上書きをビルド時の切り替えで外して実行する。結果が失敗でも 100 kHz の判定には影響させず、別の行として記録する。

代替案：helper を修正、またはコピーして `#ifndef` を足す → 固定 submodule を検証するという前提が崩れるため不採用。

### D7. WS2812 デコード：PIO でパルス幅を測り CPU で分類

- PIO プログラムは、入力の Low がリセットしきい値（約 50 µs 以上）続くのを待ってから計測を始める。各パルスの High 幅と Low 幅をカウンタ値として DMA で RAM へ送る。CPU は High 幅で 0（約 333 ns）と 1（約 1000 ns）を分類する。しきい値の中間付近（例：約 500–800 ns）や、1 ビット周期が大きく外れたものは範囲外として数える。
- コマンド：`WS2812_CAPTURE <pin> <bytes> <timeout_ms>`。pin は 7（DUT 用）か 20（自己検証用）、bytes は 3–96。成功時は `rx=<hex>`、`bits`、`bad_pulses`、`t0h_ns`/`t1h_ns` の代表値（中央値）、`threshold_ns` を返す。範囲外のパルスがあれば `ERR WS2812`、期限切れは `ERR TIMEOUT` と受信済みのビット数を返す。
- 自己検証 `WS2812_SELFTEST <OK|BADWIDTH|TIMEOUT>`：既存の SPI loopback 配線（GP19→GP20）を使う。Pico の SPI0 を 3 MHz・16 bit で動かし、helper と同じ 4 ビット符号化の既知パターンを送る。BADWIDTH は `1100` 符号（High 約 667 ns）を混ぜ、TIMEOUT は何も送らない。生成と測定で同じ Pico のクロックを共有するため周波数の校正にはならないことを protocol.md に書く。
- DUT サンプルは決まった色の列（6 LED。0x00、0xFF、0xA5、0x5A、0x01、0x80 を含む GRB）を 100 ms ごとに送る。期待するバイト順（WSGRB でのワイヤ上の順序）は、ホストで helper の `bitquartets` の並びから導く。
- 代替案：GPIO をポーリングして CPU でデコードする → 333 ns の分解能を USB 処理と並行して保証できないため不採用。SPI slave で MOSI を 3 MHz で取り込む → クロック線がなく同期できないため不採用。

### D8. ホストとマトリクス

- `tests/hil/test_extralibs.py` に3サンプル分の HIL を、既存の `_prepare` / `_with_client` / `_cleanup` を使って追加する。マーカーは `extralibs` と各周辺機能の名前。
- `tests/unit/` に、SSD1306 モデル、期待値ハーネス、WS2812 分類ロジック（ホストで実行する C またはハーネス）、マトリクスの整合性のテストを追加する。
- `hil/matrix.json` の `extralibs-excluded` の3行を、検証サンプル・治具能力・合否条件を参照する行へ変更する。`ch32hil` のマトリクス検証が新しい `class` を受け付けるようにする。CH32V002 のマトリクスには未移植の行を追加する。

## Risks / Trade-offs

- [1 MHz で波形の立ち上がりが足りない（4.7 kΩ + 220 Ω）] → D6 で 100 kHz を主な判定にする。1 MHz の失敗は別の行として記録する。pull-up の変更は配線変更なので、ユーザーのレビューを経るまで行わない。
- [RP2040 の I2C slave が 1 MHz・連続転送で取りこぼす、またはクロックストレッチで DUT の helper がタイムアウトする] → 受信件数を報告して、取りこぼしと helper の失敗を区別する。1 MHz の行は未確認のままにできる。
- [GP7 の 1 kΩ と入力容量で 3 MHz の波形がなまり、パルス幅の判定が変わる] → 中央値の幅を応答に含めて記録する。しきい値は自己検証と DUT で同じ値を使う。
- [SSD1306 の期待値が helper 自身を含む自己参照になる] → D5 のモデル単体テストで補う。spec でも「送信内容の一致」に範囲を限定している。
- [`i2c_slave.h` の割り込みとサンプルのメインループの競合] → 観測用レジスタの更新はメインループで行い、コールバック内では値を記録するだけにする。
- [WS2812 の DMA と USB CDC の割り込み] → PIO の FIFO と DMA で CPU の介入をなくし、分類は取得後に行う。
- [応答行が長い（`SSD1306_PAGE` は 256 桁）] → ホストの `ch32hil/pico.py` の受信処理が行長に制限を持たないことを単体テストで確認する。問題があれば半ページに分ける。

## Migration Plan

- Pico firmware は追加コマンドだけで、既存コマンドの互換を保つ。`CAPS` の能力一覧にコマンドを追加し、プロトコル版は 2 のままにする。ロールバックは前の revision の firmware を書き戻す。
- CH32V002 は、CH32V003 で3サンプルが確認済みになった後に移植する。WS2812 の HSCR の差分と、I2C 割り込みベクタの名前・番号を RM と照合してから行う。

## Open Questions

- 1 MHz で失敗した場合に、pull-up を強める配線変更を提案するかどうか。これは 100 kHz の結果と 1 MHz での受信件数を見てから決める（本 change の完了条件には含めない）。
