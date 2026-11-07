# HIL ホスト層のデバイス選択（Issue #10）

- 作業日時: 2026-11-07 19:1x–19:17 JST。開始時刻は記録していない。終了時刻は `date` で取得した。
- 目的: `automate-ch32v002-ch32fun-hil` のタスク 1.1–1.6、2.2、2.4。HIL のホスト層・設定・テストを `--hil-device {ch32v003,ch32v002}` で選べるようにする。既定は CH32V003 とし、従来の挙動を変えない。
- 条件: 実機は操作していない。書き込み、読み出し、検出もしていない。単体テストと模擬出力だけで確認した。

## 変更

- `ch32hil/devices.py`（新規）: デバイス固有値を一か所にまとめた。対象は型番（`CH32V003F4P6`／`CH32V002F4P6`）、`TARGET_MCU`、minichlink の期待型番、識別領域の期待型番（CH32V002 のみ `0x002`）、TSSOP20 の物理ピン表、サンプルディレクトリ、既定設定、マトリクス。マトリクスで `not-ported`／`excluded` のサンプルと、ディレクトリがないサンプルは skip 理由を返す。
- `ch32hil/config.py`: `CH32V003F4P6` 固定のチェックを、デバイス定義の型番と物理ピン表の参照に置き換えた。`validate(cfg, device)` と `load(path, device)` は、選択したデバイスと `dut.device` の不一致を拒否する。`select(device, config)` は既定の設定を解決する。`DUT_PHYSICAL` は互換のための別名として残した。
- `ch32hil/dut.py`: `Dut(target=...)` は未知のデバイスを生成時に拒否する。CH32V002 は `flash()` で、検出待ちの後、書き込みの前に `minichlink -r + 0x1ffff704 4 -b` を実行する。上位 12 ビットが `0x002` でない、読めない、終了コード 0 で空出力、否定的な出力のいずれでも `flash` 段階で失敗する。判定規則は `scripts/ch32fun.sh` と同じで、リトルエンディアンの 4 バイトを読む。
- `conftest.py`: `--hil-device`（既定 `ch32v003`）を追加した。未知の値は `pytest.UsageError` になる。`--hil-config` の既定を選択デバイスの設定にした。fixture `hil_selection`／`hil_device`／`hil_config`／`hil_dut` を追加した。設定の誤りは実機に触れる前に fail とし、使えないサンプルは理由付きで skip する。
- `tests/hil/*.py`: サンプルのパスと結果メタデータの `target` を、選択したデバイスから導くようにした。全テストで `hil_dut(sample)` を Pico の準備より前に呼ぶので、skip は実機操作の前に起きる。
- `hil/configs/ch32v002_gpio_blink.json`（新規）: `gpio_blink.json` と同じネット・ピン・部品値で、`dut.device=CH32V002F4P6` にした。
- `hil/matrix_ch32v002.json`（新規）: CH32V003 マトリクスで `sample` を持つ 10 行に対応させた。`blink_and_read` は既存ログに基づき `manually-verified`、他は `not-ported` とした。
- `ch32hil/matrix.py`: 状態 `not-ported` を追加した。網羅チェック `coverage_problems` を追加した。
- `ch32hil/wiring.py`: `main` で全デバイスの既定設定を配線資料と照合する。
- `hil/README.md`: `--hil-device` の使い方、既定値、識別確認、skip、DUT 差し替えの前提を記載した。
- `tests/unit/test_devices.py`（新規）: 26 件。

## CH32V002F4P6 の物理ピン（タスク 1.3）

資料で確認した（実機では未確認）。CH32V002 データシート V1.7 のピン配置図（PDF p.13）と表 2-1（PDF p.16–19）によると、TSSOP20 の PD4:1、PD5:2、PD6:3、PD7:4、PA1:5、PA2:6、VSS:7、PD0:8、VDD:9、PC0:10〜PC7:17、PD1:18、PD2:19、PD3:20 は、CH32V003F4P6 の表と同じ。照合は subagent が非公開の変換資料で行い、ページ番号だけを記録した。固定配線の各ネットの機能照合（タスク 2.1）は Issue #11 の範囲として別に記録する。

## 実行コマンドと結果（実測）

- `uv run pytest -q`: 112 passed、11 skipped（HIL 未選択）。変更前は 86 passed。
- `uv run pytest --hil --hil-device ch32v002 -m 'hil and gpio' tests/hil --collect-only -q`: 3 件を収集した（収集のみで、実行していない）。
- `uv run pytest --help`: `--hil-device` が表示された。
- `uv run python -m ch32hil.wiring`: 両デバイスの設定と `hardware/wiring-proposal.md` が一致した。
- `openspec validate automate-ch32v002-ch32fun-hil --strict`: valid。
- 単体テスト `test_hil_skip_reason_is_reported_without_hardware` は、`--hil --hil-device ch32v002` で実際の fixture を使う。存在しないサンプル名で skip 理由が表示されることを確認する。存在しないサンプルなので実機には触れない。

## 未確認

- CH32V002 の識別確認を、実機の minichlink 出力で通していない。模擬出力 `1ffff704: 20 06 20 00` は 2026-11-07 11:56 の実測ログの値。実際の出力行の形式は、Issue #11 の GPIO HIL で確認する。
- CH32V003 実機での回帰（タスク 9.3）は未実施。
