# Design

## Context

- このリポジトリの DUT 操作は `ch32hil/dut.py` の `Dut` に集まっている。`build()` は `make -C <sample> build` を呼び、成果物 `<sample>/main.bin` ができたことを確認する。`flash()` は固定 minichlink で検出確認、識別領域確認（CH32V002）、書き込みを行い、`readback()` で照合する。サンプル位置は `ch32hil/devices.py` の `Device.sample_root` が `samples_<device>_ch32fun` に固定している。
- arduino-cli はまだ導入していない。参照用 clone の `externals/arduino_core_ch32`（submodule ではなく gitignore 対象、HEAD d62c6b1）を見ると、次のとおりである。
  - `boards.txt` の `CH32V00x_EVT` は CH32V003F4 を扱う。
  - `CH32VM00X_EVT` が持つ variant は `CH32VM00X/CH32V006K8` だけで、CH32V002 の定義はない。
  - WCH-SWD 書き込みは `tools.WCH_linkE`（WCH 版 OpenOCD）を使う。
  - リンク時の Flash/RAM サイズは `upload.maximum_size` / `upload.maximum_data_size` から `--defsym` で渡される。
- book-code の Arduino Core CH32 用スケッチは10本ある。固定配線（`hardware/wiring-proposal.md`）で次のように観測できる。
  - blink_and_read（PC0, PA1, Serial 115200）、adc（PA1/PA2）、pwm（PD2/PC4 は観測可、PD4 は未配線）は観測できる。
  - i2c_master / i2c_slave / spi_master は既定ピンが固定配線と合う見込み。
  - neopixel は PC0 を使うため、WS2812 デコード（GP7）の外にある。
  - i2c_oled と uart は `oled.h` に依存し、OLED 表示を前提にしている。
- AGENTS.md の制約として、書き込みは `externals/ch32fun` の固定 minichlink を使い、`externals/` の参照物はコードの依存先にしない。実験は `okf/log/` に記録する。

## Goals / Non-Goals

**Goals:**
- arduino-cli と core のバージョンを固定し、リポジトリ内に閉じたビルド環境を作る。
- 3つの core 供給元を互いに干渉させずに並べて比較する。
- 既存の `Dut` と HIL の仕組みを変えずに Arduino サンプルを流す（ビルドの入口だけを差し替える）。
- CH32V002 の扱いについて、方針を判断できるだけの事実を集める。

**Non-Goals:**
- arduino-cli の upload と WCH 版 OpenOCD による書き込みは行わない。比較の参考情報としても実行しない。
- IDE の GUI 操作やシリアルモニタ画面そのものは検証しない。
- 公式 core へ修正を送ることや、`externals/arduino_core_ch32` を書き換えることはしない。
- CH32V002 向けの独自ボード定義（out-of-tree の variant）は作らない。調査の結果それが必要になった場合は、別の change として提案する。
- arduino-wch32v003（別 core）のスケッチ3本は扱わない。
- 実物の OLED 表示、NeoPixel の発光、Pico 治具の firmware 変更は対象外とする。

## Decisions

### D1. arduino-cli はリポジトリ内に閉じて導入する

`scripts/arduino.sh setup` が、固定した arduino-cli のリリースバイナリを gitignore 対象の `.arduino/bin/` に取得する。取得後にチェックサムを照合する。設定ファイルは `.arduino/<supplier>/arduino-cli.yaml` に置き、`directories.data` / `downloads` / `user` を同じディレクトリの下に向ける。すべての呼び出しに `--config-file` を付ける。

- 採用理由：ホームの `~/.arduino15` や PATH 上の arduino-cli と混ざらず、AGENTS.md が minichlink について求める「固定物を使う」と同じ方針になる。
- 不採用案：システムへの導入（mise、パッケージマネージャ）。ほかのプロジェクトと共有され、バージョンの固定と再現が利用者の環境任せになる。

### D2. 供給元ごとにデータディレクトリを分ける

供給元は `thirdparty`（書籍の robinjanssens URL）、`official`（openwch の配布 index）、`official-git` の3つとする。`official-git` は `official` と同じツールチェーンを使い、`directories.user/hardware/<vendor>/<arch>` に参照用 clone の特定 revision を置く。clone の作業ツリーは変えず、`git worktree` か export で置く。

- 採用理由：2つの配布パッケージはパッケージ名やアーキテクチャ名が衝突しうる。同じデータディレクトリに入れると、どちらでビルドしたのかが曖昧になる。
- 公式配布 index の正確な URL と、各パッケージの vendor:arch 名は、setup の最初のタスクで実際に取得して確定し、ログに記録する（予想した URL を前提にしない）。

### D3. バージョンの固定は sketch profile で行う

維持サンプルごとに `sketch.yaml` を置き、`profiles` に FQBN（ボードメニュー値を含む）、プラットフォームの名前とバージョン、`platform_index_url` を書く。ビルドは `arduino-cli compile --profile <name>` で行う。

- 採用理由：arduino-cli の標準の仕組みで core のバージョンとインデックスを固定でき、別途ロックファイルを作らずに済む。
- 比較用の一括ビルド（book-code のスケッチ）は `externals/` を書き換えないよう profile を使わず、`--fqbn` と `--build-path .arduino/build/...` で行う。そのとき使った core のバージョンは `core list` の出力として記録する。

### D4. Arduino サンプルも Makefile を入口にする

`samples_<device>_arduino/<sample>/` は `<sample>.ino`、`sketch.yaml`、`Makefile` で構成する。`make build` は `scripts/arduino.sh compile` を呼び、出力された `.bin` を `main.bin` にコピーする（`.elf` も同様）。`PREFIX` 変数は受け取って無視する。

- 採用理由：`Dut.build()`、`flash()`、`readback()` と `scripts/ch32fun.sh flash` を変更せずにそのまま使える。
- 不採用案：`Dut` にフレームワーク別のビルダーを足す。変更範囲が広がり、既存 ch32fun の HIL の挙動を変えてしまう危険がある。

### D5. HIL のフレームワーク選択

- `conftest.py` に `--hil-framework {ch32fun,arduino}`（既定は `ch32fun`）を追加する。
- `Device.sample_root` とマトリクスのパスは (device, framework) から決める。Arduino 用のマトリクスは `hil/matrix_arduino.json` と `hil/matrix_ch32v002_arduino.json` にする。
- Arduino 用 HIL テストは `tests/hil/arduino/` に置き、マーカー `arduino` を付ける。フレームワークが一致しないテストは理由付きで skip する。
- 判定基準は、書籍スケッチの挙動（Serial の出力文字列、点滅周期、PWM のデューティなど）を Pico 治具の既存能力で測れる形に定める。期待値はスケッチのソースから導き、テストに書く。
- 採用理由：書籍スケッチの挙動は ch32fun サンプルと違うので、既存テストを使い回すと期待値が混ざる。

### D6. 維持サンプルは書籍スケッチをできるだけそのまま使う

book-code のスケッチを `samples_ch32v003_arduino/` にコピーする。固定配線に合わない部分（未配線ピン、実物の周辺機器）だけを変え、変えた点と理由をサンプルの README とマトリクスに記録する。最初の対象は blink_and_read、adc、pwm、i2c_master、i2c_slave、spi_master の6本とする。neopixel、i2c_oled、uart（OLED 依存）、i2c_slave-test_master は compile 比較にだけ含め、HIL の対象外とする理由をマトリクスに記録する。

### D7. CH32V002 は調査してから方針を決める

各供給元の `boards.txt` と variants から、CH32V002 を扱えるかを確かめる。専用の定義がない場合は、同じ系列の CH32V006K8 の定義に `--build-property` で Flash 16KB・RAM 4KB を上書きしてビルドし、次の点を記録する。

- variant のピン表で F4P6 に存在するピンだけを使えているか
- 起動処理とクロック設定が V002 に合うか

書き込みは、既存の CH32V002 識別確認を通した後にだけ行う。判定の結果は「そのまま対応」「流用で動作」「独自定義が必要」「不可」のいずれかとし、「独自定義が必要」の場合は別の change で提案する。

## Risks / Trade-offs

- [サードパーティのパッケージや配布 index が取得できない、または内容が変わっている] → 取得した index と package のバージョンをログに記録する。取得できない場合は「書籍手順は現在再現不可」という結果として記録し、比較は残りの供給元で続ける。
- [配布ツールチェーン（riscv-wch-gcc）が Linux 環境で動かない] → setup で compile を単体確認し、動かなければ供給元ごとに不可として記録する。別のツールチェーンには置き換えない（D1 の固定方針）。
- [Arduino core の起動処理や SysTick の使い方が minichlink 書き込み後のリセットで正しく動かない] → 書き込み、readback、リセットの各段階を分けて記録し、OpenOCD を使った場合の挙動とは比べない（Non-Goal）。動かない場合は flash 段階ではなく実行観測不一致として報告する。
- [Serial のボーレート誤差などで Pico の UART 受信が不安定になる] → 既存 UART 治具の自己検証結果を前提にする。誤差が疑われる場合は、受信した生データを結果に残して判定理由を区別する。
- [CH32V006 の定義を流用したビルドが、V002 に存在しない周辺機能やピンを初期化する] → 書き込み前にリンクマップと variant のピン表を確認し、未確認のまま書き込まない。結果は「流用で動作」と「対応済み」を区別して記録する。
- [`.arduino/` の導入物が大きい] → gitignore 対象にし、`scripts/arduino.sh` で再取得できるようにする。

## Migration Plan

既存の ch32fun 用 HIL コマンドは `--hil-framework` を指定しなければ従来どおりに動く。切り戻すときは、Arduino 用のサンプル、マトリクス、テストと `--hil-framework` オプションを外せばよい。既存の ch32fun 資産には手を入れない。

## Open Questions

- 公式の配布パッケージが Board Manager にいつ反映されたか（リリース履歴）。追従判定の根拠を補う情報で、手順や分担には影響しない。
