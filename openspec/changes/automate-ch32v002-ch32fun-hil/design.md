# Design

## Context

See `proposal.md` - Why。

現状（観測済み）:

- `ch32hil/dut.py` の `Dut` は `target` 引数で `ch32v002` を受け付け、`Detected CH32V002` を期待型番として扱える。ただし識別領域 `0x1ffff704` の照合は `scripts/ch32fun.sh flash ch32v002` にしかなく、HIL ホスト層にはない。
- `ch32hil/config.py` は `dut.device != "CH32V003F4P6"` を設定エラーにする。`DUT_PHYSICAL` は CH32V003F4P6 の TSSOP20 ピン番号表である。
- `tests/hil/*.py` は `samples_ch32v003_ch32fun/...` と `target='CH32V003'` を直書きしている。`conftest.py` は `--hil`、`--hil-config`、`--hil-port`、`--hil-run-dir` を持ち、デバイス選択オプションはない。
- `hil/matrix.json` は CH32V003 用の 1 ファイルで、デバイス軸を持たない。
- `samples_ch32v002_ch32fun/blink_and_read` は `TARGET_MCU=CH32V002`、`HSI_VALUE=24000000`、生成リンカスクリプトを使い、旧 ch32fun で build・flash・readback・Pico PASS、現 submodule `b28d285` で build・flash・Pico PASS（readback 未実施）を記録済み。
- CH32V002F4P6 の PC0=10、PA1=5、VSS=7、VDD=9、SWIO=18 は CH32V003F4P6 と同じ（記録済み）。開発ボードのピン互換はユーザー申告。他ピンの機能（I2C、SPI、USART、TIM1、ADC チャネル、AFIO リマップの値）は未照合。
- CH32V002 の資料は `okf/sources/ch32v002-datasheet.md`（V1.7）と `okf/sources/ch32v00x-reference-manual.md`（V1.5）で識別している。CH32V003 とはリファレンスマニュアルが別系統であり、レジスタのビット配置が同じとは仮定できない。

## Goals / Non-Goals

**Goals:**

- 一つの HIL テストコードを、CH32V003 と CH32V002 のどちらにも明示選択で使う。
- CH32V002 の各サンプルで、build、識別付き flash、readback、reset、Pico 観測を CH32V003 と同じ段階分けで判定する。
- デバイス差分を、資料根拠と実測を区別してサンプル単位で追跡する。

**Non-Goals:**

- Pico ファームウェアのプロトコル変更や、既存治具能力の再設計。
- CH32V002 以外の CH32V00x（V004/V005/V006/V007）や、F4P6 以外のパッケージ。
- CH32V002 固有の追加機能（OPA、タッチキー等）や、CH32V003 にない周辺機能の新規サンプル。
- ADC 精度、クロック精度、sleep 中の消費電流の評価（CH32V003 と同様に機能確認のみ）。
- 二つの DUT を同時接続して並行実行すること。DUT は一度に一つを差し替えて使う。

## Decisions

### 1. デバイスは pytest オプションと設定ファイルの両方で明示する

`--hil-device {ch32v003,ch32v002}` を追加し、既定は `ch32v003` とする。デバイスごとに `hil/configs/` の設定（例: `gpio_blink.json` と `ch32v002_gpio_blink.json`）を持ち、`--hil-config` 未指定時は選択デバイスの既定設定を選ぶ。テストはデバイスから `samples_<device>_ch32fun/<sample>`、期待型番、結果メタデータの `target` を導出する。

設定の `dut.device` と `--hil-device` が食い違う場合は実機操作前に停止する。設定だけでデバイスを決める案は、既存の CH32V003 コマンドとの後方互換は保てるが、誤った設定ファイルを渡したときに気付きにくいため、両方の一致を要求する。

### 2. デバイス固有値は一か所の対応表にまとめる

`ch32hil` にデバイス定義（device 名、`TARGET_MCU`、期待 minichlink 型番、識別領域の期待型番、物理ピン表、サンプルディレクトリ、マトリクスファイル）を置き、`config.py`、`dut.py`、テストはこの表を参照する。テストごとにデバイス分岐を書く案は、10 サンプル × 2 デバイスで重複が増えるため採用しない。

### 3. CH32V002 の識別領域確認を DUT 操作層へ移す

`Dut` が `ch32v002` のとき、flash 前の検出待ちで `minichlink -r + 0x1ffff704 4 -b` を読み、上位型番が `0x002` でなければ `flash` 段階で失敗させる。既存の `scripts/ch32fun.sh` と同じ判定規則を Python 側で再実装し、模擬出力で単体テストする。shell スクリプト呼び出しへ委譲する案は、段階別エラーと模擬テストを表現しにくいため採用しない。

minichlink 表示が `CH32V006` 等と誤る旧挙動は、現 submodule と LinkE 2.22 では解消を確認済みのため、検出文字列は `Detected CH32V002` を要求し、識別領域照合を追加の安全条件とする。

### 4. マトリクスはデバイス別ファイルにする

`hil/matrix.json` は CH32V003 用として残し、`hil/matrix_ch32v002.json` を追加する。行は CH32V003 マトリクスの `sample` と対応させ、整合性テストで「CH32V003 で HIL 対象のサンプルが CH32V002 側に欠けていない」ことを確認する。単一ファイルにデバイス列を足す案は既存テストとログ参照を壊すため採用しない。

### 5. 移植は資料照合 → build → 単体判定 → HIL の順にサンプル単位で行う

各サンプルで次を行う。

1. CH32V002 データシート V1.7 のピン定義と CH32V00X RM V1.5 の該当周辺レジスタで、CH32V003 版が使うピン・AFIO リマップ・レジスタビット・クロック前提を照合し、差分を `okf/` に記録する。
2. `samples_ch32v002_ch32fun/<sample>/` を作成し、build のみ確認する。
3. 期待値（UART ボーレート、PWM 周期、ADC の分解能による値域、watchdog 周期等）がクロックや分解能の差で変わる場合は、CH32V002 用の合否条件をデバイス定義または設定で与える。
4. CH32V002 実機で HIL を実行する。

順序は CH32V003 と同じく `blink_and_read`（GPIO 出力・入力）→ UART → I2C → SPI → timer/PWM → ADC → watchdog/sleep とし、配線全体の成立確認を最初の GPIO 段階で済ませる。

### 6. 固定配線と Pico 治具は変更しない前提で始め、差分が出たら記録して止める

CH32V002F4P6 で CH32V003 の固定配線（SPI NSS を PC0 へリマップ、I2C PC1/PC2、SPI PC5/PC6/PC7、UART PD5/PD6、TIM1 PD2/PC4、ADC PA1/PA2）がそのまま成立する見込みで開始する。資料照合で成立しないネットが出た場合は、そのサンプルを「配線変更が必要」として matrix に記録し、配線変更案を `hardware/wiring-proposal.md` に追記してユーザーレビューを待つ。暗黙に配線や部品値を変えない。

Pico 治具能力は CH32V003 で自己検証済みのものを使い、新しい能力が要る場合だけ追加・自己検証する。

### 7. 実機作業は DUT 差し替えを伴う独立した段階として記録する

CH32V003 と CH32V002 の差し替えは、電源断（WCH-LinkE の 3.3 V 出力停止を含む）、DUT 交換、電圧確認、`./scripts/ch32fun.sh flash ch32v002` 相当の検出確認の順で人が行う。差し替え後の最初の実行は GPIO の HIL とし、配線の成立を確認してから他の周辺機能へ進む。各実験は `okf/log/` に記録する。

## Risks / Trade-offs

- [CH32V002 の AFIO リマップのビット配置が CH32V003 と異なり、SPI NSS→PC0 等の固定配線が成立しない] → 資料照合を build 前に行い、成立しない場合は配線変更案を出してレビューを待つ。
- [HSI 24 MHz と PLL 既定値の差で UART ボーレート、PWM 周期、watchdog 周期の期待値がずれる] → 期待値をデバイス別に持ち、根拠を記録する。許容範囲は CH32V003 の値を流用しない。
- [ADC 分解能や変換時間の差で値域判定が変わる] → CH32V002 用の値域を資料から決め、粗い変化の機能確認に留める。
- [識別領域の読み出し形式が minichlink の版に依存する] → 判定は固定 submodule の出力形式に限定し、単体テストで正常・異常・読めない場合を固定する。
- [CH32V003 用ログ・結果を CH32V002 の確認済みと誤読する] → 結果メタデータとマトリクスにデバイスを必須で持たせる。
- [DUT 差し替え時の逆給電・誤接続] → 差し替え手順を配線資料に明記し、電源断と電圧確認を自動化外の前提として残す。

## Migration Plan

1. デバイス定義と `--hil-device` を追加し、既定 CH32V003 で既存の単体テスト・HIL コマンドの挙動が変わらないことを単体テストで確認する。
2. CH32V002 の識別領域確認と設定・マトリクスを追加する。
3. サンプルを順に移植し build-only を確認する。
4. DUT を CH32V002 に差し替え、GPIO から HIL を実行する。
5. 全サンプル完了後、CH32V003 に戻して全 HIL を再実行し、回帰がないことを確認する。

ロールバック: `--hil-device` を指定しなければ従来の CH32V003 経路だけが動く。CH32V002 用ファイルは追加のみで、既存ファイルの意味は変えない。

## Open Questions

- CH32V002 の ADC 値域・watchdog 周期・UART 実ボーレートの具体値は、各サンプルの資料照合時に決める（判定方法自体は変えない）。
