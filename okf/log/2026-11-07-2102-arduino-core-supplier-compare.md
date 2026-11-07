# Arduino Core CH32 供給元の compile 比較と追従判定（verify-arduino-core-with-arduino-cli 2.1〜2.3）

- 作業日時: 2026-11-07 21:02〜21:06 JST（compile 実行はこの範囲内。各コマンドの個別時刻は記録していない）
- 範囲: **ビルド比較とソース差分のみ**。書き込み・実機観測はしていない（実機は 4・5 章で確認する）。
- 環境: [2026-11-07-2055-arduino-cli-setup.md](2026-11-07-2055-arduino-cli-setup.md) で構築したもの（arduino-cli 1.5.1）。

## 対象

- book-code: `externals/ch32v003-book-code`（4ce0a1b, 2026-04-19）の `*-arduino_core_ch32` / `*_arduino_core_ch32` ディレクトリ **10本**。
  - 計画文書は「11本」としていたが、実際は10本。`*-arduino_ch32v003` / `*-arduino_wch32v003` の3本（blink_and_read, i2c_master, pwm）は `hal/wch-hal-i2c.h` や `USART_Printf_Init` を使う arduino-wch32v003 用で、design の Non-Goal（別 core の3本）に当たる。proposal / design / tasks の「11本」を「10本」に訂正した。
- 供給元: thirdparty = `WCH:ch32v@1.0.5-beta`（riscv-none-embed-gcc 8.2.0）、official = `WCH:ch32v@1.0.6`（riscv-wch-gcc 15.2.0）、official-git = `WCHgit:ch32v` @ d62c6b1（= 公式タグ 1.0.5、ツールは official と共有）。
- FQBN: `<vendor>:ch32v:CH32V00x_EVT:pnum=CH32V003F4,clock=48MHz_HSI`（他メニューは既定値）。

## 2.1 一括 compile

```
BC=externals/ch32v003-book-code
for d in <10本>; do for s in thirdparty official official-git; do
  ./scripts/arduino.sh compile $s $BC/$d --fqbn "$(./scripts/arduino.sh fqbn $s CH32V00x_EVT pnum=CH32V003F4,clock=48MHz_HSI)" \
    --build-path .arduino/build/$s/$d
done; done
```

- `externals/ch32v003-book-code` の `git status --porcelain` を前後で比較 → 変化なし（実測）。build 出力は `.arduino/build/<supplier>/<sketch>/` のみ。
- `~/.arduino15` は変化なし（実測、前回と同じ方法）。

結果（Flash / RAM はバイト。上限は Flash 16384、RAM 2048）:

| スケッチ | thirdparty 1.0.5-beta | official 1.0.6 | official-git d62c6b1 |
| --- | --- | --- | --- |
| adc | 成功 8888 / 560 | 成功 8388 / 864 | 成功 9708 / 760 |
| blink_and_read | 成功 7784 / 552 | 成功 7508 / 864 | 成功 8840 / 760 |
| i2c_master | 成功 13476 / 736 | 成功 10836 / 1040 | 成功 12520 / 936 |
| i2c_oled | 失敗（ライブラリ不足） | 失敗（ライブラリ不足） | 失敗（ライブラリ不足） |
| i2c_slave | 成功 13240 / 776 | 成功 10404 / 1080 | 成功 12064 / 984 |
| i2c_slave-test_master | 成功 13500 / 736 | 成功 10856 / 1040 | 成功 12540 / 936 |
| neopixel | 成功 7868 / 552 | 成功 7600 / 864 | 成功 8940 / 760 |
| pwm | 成功 11016 / 576 | 成功 10768 / 936 | 成功 12232 / 832 |
| spi_master | 成功 14544 / 684 | 成功 12744 / 1036 | 成功 14084 / 932 |
| uart | 失敗（ライブラリ不足） | 失敗（ライブラリ不足） | 失敗（ライブラリ不足） |

- 失敗はすべて `fatal error: oled.h: No such file or directory`。**core の差ではなくライブラリ不足**。`i2c_oled-arduino_core_ch32/README.md` が指定する Library Manager の「OLED SSD1306 - SH1106」（durydevelop/arduino-lib-oled）が必要。
- 切り分けのため、`./scripts/arduino.sh cli <supplier> lib install "OLED SSD1306 - SH1106@1.0.7"`（2026-11-07 時点の最新）を各供給元の `.arduino/<supplier>/user/libraries` に入れて再 compile した（build-path は `<sketch>-withlib`）:

| スケッチ（ライブラリ導入後） | thirdparty | official | official-git |
| --- | --- | --- | --- |
| i2c_oled | 成功 13220 / 776 | 成功 10916 / 1096 | 成功 13084 / 992 |
| uart | 成功 15492 / 808 | 成功 14028 / 1120 | 成功 16088 / 1016（Flash 98%） |

- 警告: official / official-git では全スケッチで ld の `has a LOAD segment with RWX permissions` が1件ずつ出る（GCC 15 / binutils の新しい警告。thirdparty の GCC 8 では出ない）。それ以外の警告はない。
- 傾向（推定を含む）: official 1.0.6 は Flash が最も小さく RAM が最も大きい。1.0.6 で Serial に RX バッファが追加された（上流 ddc1f61）ことが RAM 増の一因と推定する。official-git（1.0.5）は 1.0.6 より Flash が 1.3〜1.7 KB 大きい。uart（official-git）は Flash 98% で余裕がない。

## 2.2 core の差分と追従判定

### 書籍時点で何が「公式では使えなかった」か

書籍 2.1 節は「公式リポジトリに取り込まれたすべての PR が 2025年3月時点では Board Manager のパッケージに反映されていない」とする。GitHub の compare API で確認した事実（実測）:

- thirdparty の platform は `robinjanssens/arduino_core_ch32`（`openwch/arduino_core_ch32` の fork）のタグ 1.0.5a / 1.0.5b。
- `openwch 1.0.4...robinjanssens 1.0.5b`: ahead 30 / behind 0。30 コミットのうち 26 件は公式リポジトリにマージ済みの PR（2023-12〜2024-09。debug 機能 #68、HardwareTimer と PWM ピン修正 #71、EEPROM #103、tone #111、**I2C slave と scanning #108**、yield in delay #115、ARDUINO_ARCH_CH32 #116、TinyUSB #121/#127、wchisp upload #129、F_CPU 定義 #133 など）。
- 残り 4 件（9ed101e, 53084ba, f491c3d, f84cc7d）は robinjanssens 独自で、変更ファイルはすべて `variants/CH32V20x/CH32V203G6_LANA_TNY/`、`boards.txt` の同ボード定義、`tools/makeboards.py`。**CH32V00x には関係しない**。
- 当時の公式配布は 1.0.4（tp の差は上記 26 PR）。book-code の i2c_slave は #108 の I2C slave に依存するため、これが書籍の言う「使えない機能」の中心と推定する（書籍に機能名の明記はない）。

### 公式 1.0.6 に入っているか

- `robinjanssens 1.0.5b...openwch 1.0.6`: official 1.0.6 は ahead 81 / **behind 4**。behind の 4 件は上記の LANA TNY 関連のみ。つまり **tp 1.0.5-beta が持つ公式 PR 26 件はすべて公式 1.0.6 に含まれる**（実測）。
- `boards.txt` の `CH32V00x_EVT.*` 行は両者で**完全一致**（diff 出力なし）。
- `platform.txt` の差はツールチェーン切り替え（riscv-none-embed-gcc 8.2.0 → riscv-wch-gcc 15.2.0、openocd → openocd-wch）、`-DARDUINO_{build.board}` の追加、`version` のみ。
- 公式側にだけある CH32V00x 関連の変更（1.0.5〜1.0.6 での後続修正。実機挙動に影響しうるもの）:
  - `variants/CH32V00x/CH32V003F4/PeripheralPins.c`: ADC1_IN6/IN7 のピンを PA6/PA4（誤り）→ **PD6/PD4** に修正。I2C1 の remap（PD0/PD1、PC6/PC5）を追加。
  - `system/CH32V00x`: 既定の割り込みハンドラを startup の asm から `ch32v00x_misc.c` の weak 関数へ移動（issue #204）。
  - `cores/arduino/wiring_time.c`: `delay()` を micros 基準に変更（最初の 1 ms が 0〜1 ms になる問題の修正）。
  - `cores/arduino/wiring_analog.c`: `analogRead` の分解能変換を `ADC_RESOLUTION` から `mapResolution()` で行うよう変更（tp は内部分解能を 12 bit 扱いにしていた）。**adc サンプルの読み値の尺度が供給元で異なる可能性**がある（5.1 で確認）。
  - `HardwareSerial` / `ch32/uart.c`: RX バッファ追加など（差分 213 行 / 35 行）。`HardwareTimer.cpp`（135 行）、`ch32/clock.c`（82 行）、Wire `twi.c`、SPI `spi_com.c` にも差分あり（詳細未読）。
  - 1.0.6 の platform アーカイブは TinyUSB submodule を同梱（official-git の git archive には含まれない）。

### 判定

**追従済み**（CH32V00x / CH32V003 について、ビルド比較とソース差分の範囲）。

根拠:
1. 書籍が thirdparty を使う理由だった「公式にマージ済みだが配布に未反映の PR」26 件は、すべて公式配布 1.0.6 に含まれる。thirdparty にあって公式にないのは CH32V203G6 LANA TNY 用の 4 コミットだけ。
2. CH32V00x のボード定義（boards.txt）とメニューは同一で、書籍の設定（CH32V00x、48MHz Internal、WCH-SWD）がそのまま選べる。
3. book-code の10本は、3供給元とも同じ成否（8本成功、2本は同じライブラリ不足で失敗、ライブラリ導入後は10本とも成功）。core の差による compile 失敗はない。

範囲の注意:
- **ビルド比較のみ（実機は 4・5 章で確認）**。公式側は後続の修正（ADC ピン表、delay、analogRead の分解能、Serial）で挙動が変わっている可能性があり、実機で同じ動作になるかは未確認。
- 公式 1.0.5 / 1.0.6 は Board Manager index に 2026-11-03 / 2026-11-07 に載ったばかり。ツール（riscv-wch-gcc 15.2.0、openocd-wch 2.10.0）の配布元は `github.com/medtty/board_manager_files` で、openwch 自身のリポジトリではない（index は openwch 管理）。
- design の Open Question（公式配布がいつ Board Manager に反映されたか）: index リポジトリの履歴では 1.0.4 の後、2023-12 から 2026-11-03 まで更新がなく、1.0.5 の追加が 2026-11-03（実測）。

## 2.3 維持サンプルの供給元

- 維持サンプル（`samples_<device>_arduino/`）は **official の配布パッケージ `WCH:ch32v@1.0.6`**（index `https://github.com/openwch/board_manager_files/raw/main/package_ch32v_index.json`）を使う。2.2 で追従済みと判定し、official で使えない要素がないため、ユーザー確認は不要と判断した。作業中（21:06 頃）にユーザーから「なるべく公式を使って」と指示があり、この決定と一致する（ユーザー申告）。
- design D3 に従い、各サンプルの `sketch.yaml` に profile を置く:

```yaml
profiles:
  ch32v003:
    fqbn: WCH:ch32v:CH32V00x_EVT:pnum=CH32V003F4,clock=48MHz_HSI
    platforms:
      - platform: WCH:ch32v (1.0.6)
        platform_index_url: https://github.com/openwch/board_manager_files/raw/main/package_ch32v_index.json
default_profile: ch32v003
```

- profile でのビルドは `./scripts/arduino.sh compile official <sketch> --profile ch32v003 ...` で行う（config は official のもの）。
- thirdparty と official-git は比較の証跡としてだけ使い、維持サンプルの依存にしない。

## 未確認

- 供給元間の実行時の挙動差（4・5 章の HIL で official について確認する。thirdparty / official-git は書き込みの予定なし）。
- HardwareTimer、clock.c、twi.c、spi_com.c の差分の内容。
- OLED ライブラリを使うスケッチの実機表示（HIL 対象外）。
