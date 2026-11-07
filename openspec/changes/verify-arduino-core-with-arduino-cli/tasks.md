# タスク

## 1. arduino-cli 環境の構築

- [x] 1.1 arduino-cli の最新安定版を選び、バージョン、配布 URL、チェックサムを `scripts/arduino.sh` に固定する。`setup` サブコマンドで `.arduino/bin/` へ取得してチェックサムを照合するよう実装し、`.arduino/` を `.gitignore` に追加する。`./scripts/arduino.sh setup` の後に `.arduino/bin/arduino-cli version` が固定バージョンを返すこと、PATH 上やホームの arduino-cli が使われていないことを確認する。
- [x] 1.2 供給元 `thirdparty`（書籍の robinjanssens URL）と `official`（openwch の配布 index）について、実際に index を取得する。正確な URL、パッケージの vendor:arch 名、提供バージョンの一覧、CH32V00x と CH32VM00X のボード名を `okf/log/` に記録する。その結果に合わせて `.arduino/<supplier>/arduino-cli.yaml` を生成する（data/downloads/user をそれぞれのディレクトリへ）。`./scripts/arduino.sh core-install <supplier>` で core を入れ、`~/.arduino15` に変化がないことを確認する。
- [x] 1.3 `official-git` 供給元を用意する。参照用 clone `externals/arduino_core_ch32` の記録した revision（現時点では d62c6b1）を、clone を変えずに `.arduino/official-git/user/hardware/` へ export し、ツールチェーンは `official` のものを使う。`core list` に表示されること、記録した revision と export の内容が一致することを確認する。
- [x] 1.4 書籍の Blink（PC0、1 秒周期）を3つの供給元それぞれで、書籍の設定（CH32V00x、48MHz Internal）に相当する FQBN で `./scripts/arduino.sh compile` する。`.bin` と `.elf` ができることと、使った core のバージョンが出力に残ることを確認する。書籍 2.1 節の IDE 操作と CLI コマンドの対応表を `okf/log/` に記録する。

## 2. core 供給元の比較と追従判定

- [x] 2.1 book-code の Arduino Core CH32 用スケッチ10本を、3つの供給元で CH32V003 向けに一括 compile する。build は `.arduino/build/` に出し、`externals/` は書き換えない。スケッチと供給元の組ごとに、成否、エラーの要約、Flash/RAM 使用量、core のバージョンまたは revision を表にして `okf/log/` に記録する。`oled.h` などのライブラリが不足して失敗した組は、core の差による失敗と分けて記録する。
- [x] 2.2 `thirdparty` と `official` の core を比べる（`platform.txt`、`boards.txt`、`cores/`、`libraries/`、`variants/` の CH32V00x 関連部分）。書籍が「公式では使えない」とした機能に当たる差を特定する。2.1 の結果と合わせて「追従済み」「一部未追従」「未追従」のどれかを判定し、根拠と「ビルド比較のみ（実機は 4・5 章で確認）」という範囲を `okf/log/` に記録する。判定をユーザーに報告する。
- [x] 2.3 2.2 の判定に基づいて、維持サンプルで使う供給元とバージョン（原則として `official` の配布パッケージ）を決め、design D3 の profile 方針と合わせて `okf/log/` に記録する。`official` が使えない場合は、維持サンプルの供給元をどうするかをユーザーに確認してから次へ進む。

## 3. HIL のフレームワーク選択

- [x] 3.1 `ch32hil/devices.py` で、サンプルのルートとマトリクスのパスを (device, framework) から決めるようにする。既定は `ch32fun` で、既存の値は変えない。不明なフレームワークは `DeviceError` にする。`tests/unit/test_devices.py` に、既定値が従来と同じこと、arduino 選択時のパス、不明な名前のエラーを確認するテストを追加して通す。
- [x] 3.2 `conftest.py` に `--hil-framework {ch32fun,arduino}` を追加する。結果メタデータに `framework` を記録し、フレームワークが一致しないテスト（既存の ch32fun テストと `tests/hil/arduino/`）を理由付きで skip する。マーカー `arduino` を登録する。`uv run pytest -q` が従来どおり通ること、`--hil` なしで arduino テストが skip されることを確認する。
- [x] 3.3 `hil/matrix_arduino.json`（CH32V003）と `hil/matrix_ch32v002_arduino.json` を作り、book-code の Arduino Core CH32 用スケッチ10本を「未実装」の状態で載せる。`tests/unit/test_config_matrix.py` を Arduino 用マトリクスにも広げ、10本がすべて載っていること、`hil-verified` に `hil_tests` と `evidence` が必須であることを確認するテストを通す。
- [x] 3.4 `hil/README.md` に `--hil-framework` の使い方、Arduino サンプルのビルドに使う固定ツール（arduino-cli と core のバージョン）、書き込みは固定 minichlink だけで行うことを書き、記載したコマンドが `--hil` なしで実行できる（skip される）ことを確認する。

## 4. 書籍手順の再現（CH32V003、blink_and_read）

- [x] 4.1 `samples_ch32v003_arduino/blink_and_read/` を作る（book-code からコピーした `.ino`、`sketch.yaml` の profile、`make build` で `main.bin` を出す Makefile、出典と変更点を書いた README）。`make -C samples_ch32v003_arduino/blink_and_read build PREFIX=riscv64-unknown-elf` で `main.bin` ができること、ビルドが `externals/` を参照していないことを確認する。
- [x] 4.2 `tests/hil/arduino/test_blink_and_read.py` を作る。期待値はスケッチのソースから導く：PC0（GP5）の点滅周期、PA1（GP12）入力への応答、PD5（GP9）の Serial 115200 出力の文字列。`--hil` なしで skip されることを確認する。
- [x] 4.3 CH32V003 を接続し、`./scripts/ch32fun.sh flash` 相当の検出確認を通してから `uv run pytest --hil --hil-framework arduino -m 'hil and arduino' tests/hil/arduino/test_blink_and_read.py --hil-port=<Pico>` を実行する。build、flash、readback、観測を別々に判定し、`okf/log/` に記録して、マトリクスの行を実測に合わせて更新する。書籍の「Verified OK」表示は IDE（OpenOCD）固有のため未確認として記録する。

## 5. 周辺機能のサンプル（CH32V003）

- [x] 5.1 adc：`samples_ch32v003_arduino/adc/` と HIL テストを作る（Pico GP12/GP13 の PWM+RC で PA1/PA2 に電圧を与え、Serial 出力の読み値が大まかに変わることを判定する）。`--hil` なしで skip されることを確認したうえで実機で実行し、記録してマトリクスを更新する。
- [x] 5.2 pwm：`samples_ch32v003_arduino/pwm/` と HIL テストを作る（PD2/PC4 を GP14/GP15 で測り、`analogWrite` の値から導いたデューティと周波数を判定する。PC5/PC6 は観測できれば参考情報として残し、PD4 は未配線として記録する）。実機で実行し、記録してマトリクスを更新する。
- [x] 5.3 i2c_master：スケッチの対象アドレスと転送内容を確認し、Pico の I2C slave 能力で観測できる形にする。固定配線に合わせて変えた点は README に記録する。サンプルと HIL テストを作って実機で実行し、記録してマトリクスを更新する。
- [x] 5.4 i2c_slave：スケッチのスレーブアドレスとレジスタの挙動を確認し、Pico の `I2C_MASTER`/`I2C_PROBE` で書き込み、読み戻し、NACK を判定する HIL テストを作る。実機で実行し、記録してマトリクスを更新する。
- [x] 5.5 spi_master：スケッチのピン、mode、クロックを確認し、Pico の SPI slave（mode 0 のみ）で受信データを判定する HIL テストを作る。NSS が固定配線（PC0 → GP5）と合わない場合は、変えた点を記録する。実機で実行し、記録してマトリクスを更新する。
- [x] 5.6 neopixel、i2c_oled、uart（OLED 依存）、i2c_slave-test_master の4本について、HIL の対象外とする理由（固定配線の外のピン、実物の表示、別の DUT を前提にしている）と compile 比較の結果をマトリクスに記録する。マトリクスの単体テストが通ることを確認する。

## 6. CH32V002 への適用可否の調査

- [x] 6.1 3つの供給元の `boards.txt` と variants から、CH32V002 を選べるかと、使えそうな流用元（CH32VM00X/CH32V006K8 など）を調べる。CH32V002F4P6 と流用元の Flash・RAM サイズ、ピン、クロック、起動処理の違いを、公開データシートと core のソースを根拠に `okf/log/` に表にする（`xprivate/` の本文は書き写さない）。
- [x] 6.2 流用元の定義に `--build-property` で Flash 16KB / RAM 4KB を上書きして、`samples_ch32v003_arduino/blink_and_read` 相当のスケッチを CH32V002 向けにビルドする。リンクマップ（メモリ範囲、ベクタ、使われている周辺機能の初期化）と variant のピン表を確認し、F4P6 に存在しないピンや周辺機能に触れていないかを記録する。この段階では書き込まない。
- [x] 6.3 6.1 と 6.2 の結果から「そのまま対応」「流用で動作見込み」「独自定義が必要」「不可」を暫定判定し、ユーザーに報告する。書き込みを試すか、独自定義のために別の change を立てるかの判断を仰ぐ。
- [x] 6.4 （6.3 で書き込みが承認された場合）CH32V003 を外して CH32V002 に差し替え（`hil/README.md` の手順）、識別領域 `0x1ffff704` が `0x002` であることを確認してから書き込む。`samples_ch32v002_arduino/blink_and_read/` を作り、`--hil-device ch32v002 --hil-framework arduino` で HIL を実行する。build、flash、readback、観測を別々に記録し、`hil/matrix_ch32v002_arduino.json` を実測に合わせて更新する。承認されなかった場合は、未確認であることと理由をマトリクスとログに記録する。

## 7. 統合確認

- [x] 7.1 `uv run pytest -q` と、既存の ch32fun 全 HIL（`uv run pytest --hil -q --hil-port=<Pico>`、フレームワークは指定しない）を実行し、Arduino 対応を入れた後も ch32fun 側の結果が変わらないことを確認して記録する。
- [x] 7.2 `README.md` に、Arduino サンプルの状態（供給元ごとの compile 結果の要約、HIL 確認済みの一覧、公式 core の追従判定、CH32V002 の判定、未確認の事項）を追記する。記載したコマンドが現状で動くことを確認する。

## 8. CH32V002 への残りのサンプルの移植（6.4 の後にユーザーの依頼で追加）

- [x] 8.1 CH32V002 用の上書き（Flash/RAM サイズ、`_eusrstack`、`_heap_end`）を `samples_ch32v002_arduino/arduino.mk` に集約し、`blink_and_read` が同じ成果物になることを確認する。
- [x] 8.2 adc、pwm、i2c_master、i2c_slave、spi_master を `samples_ch32v002_arduino/` に移植してビルドする（ソースは CH32V003 版と同じ。ADC は variant が 12 bit なので、HIL の期待値をデバイスの分解能から導く）。
- [x] 8.3 `--hil-device ch32v002 --hil-framework arduino` で Arduino HIL 全体を実行し、段階ごとの結果を `okf/log/` に記録して、`hil/matrix_ch32v002_arduino.json` を実測に合わせて更新する（対象外 4 本は理由を記録する）。README の記載を更新する。

## 9. 対象外にしたスケッチの追加検証（ユーザーの依頼で追加。実機は公式配布 core 1.0.6 のみ）

- [x] 9.1 i2c_slave-test_master: サンプルを作り（ソース変更なし）、Pico の `I2C_SLAVE 0x10` で DUT の書き込み（`10 n n+1 n+2 n+3`）、`20` の書き込みと 4 バイト読み出し、ループごとの n の増加を判定する HIL テストを作って実行し、記録してマトリクスを更新する。
- [x] 9.2 neopixel: データピンを固定配線の WS2812 デコード（PC6 → GP7）に合わせて変えたサンプルを作り、`WS2812_CAPTURE` で受けたバイト列とスケッチから導いた期待値を比べる HIL テストを作って実行し、記録してマトリクスを更新する。
- [x] 9.3 i2c_oled: OLED ライブラリの送り方（アドレス、アドレッシング方式、128×32）を調べ、Pico の SSD1306 模擬で観測できるかを判定する。観測できる場合はサンプルと HIL テストを作って実行し、できない場合は理由を記録する。（当初は模擬の不一致で観測不可と判定し、9.5 で模擬を直して観測した）
- [x] 9.5 （ユーザーの依頼で追加）Pico の SSD1306 模擬を、データシートどおり `0x21` は列ポインタだけ・`0x22` はページポインタだけを戻し、フレームはウィンドウの最後のセルへの書き込みで数えるよう直す。単体テストを追加し、Pico を再書き込みして ch32fun の SSD1306 helper と全 HIL に退行がないことを確かめ、i2c_oled を OLED ライブラリから描いた期待画像と比べる HIL テストを作って実行する。
- [x] 9.4 uart と arduino-wch32v003 の 3 本は対象外のまま、理由をマトリクスとログに記録する。実機確認は公式配布 core のみとし、サードパーティ版と official-git はビルド比較の証跡に留めることを記録する（ユーザーの判断）。

## 10. CH32V003 での再確認と修正（ユーザーの依頼で追加）

- [x] 10.1 CH32V003 に戻して、Arduino と ch32fun の全 HIL を実行する。失敗は配線（PD5）と CH32V003 固有の問題に切り分けて記録する。
- [x] 10.2 neopixel を、MSB 先頭で送り、WS2812B の規格の中央に合うよう nop の数を系列ごとに調整したコードに直す。Pico の WS2812 デコーダに High/Low 幅の範囲の報告を追加し、規格の範囲で判定するテストにする（CH32V003 で確認）。
- [x] 10.3 i2c_oled（RAM 不足）と i2c_slave（SCL の固定）を CH32V003 での既知の問題として、テスト・マトリクス・ログに記録する。
- [x] 10.4 CH32V002 で neopixel の nop の数を実測して調整し、i2c_slave の診断を行う（DUT の差し替えが必要）。

## Workflow follow-up

- ユーザーのレビュー後に specs を同期して、change を archive する。
- 6.3 で「独自定義が必要」となった場合は、CH32V002 用のボード定義を作る別の change を提案する。
