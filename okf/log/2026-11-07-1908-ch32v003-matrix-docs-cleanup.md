# CH32V003 検証マトリクスと手順書の後始末

- 作業日時: 2026-11-07 19:06–19:08 JST（`date` で取得）。記録は 19:08 以降。
- 目的: アーカイブ済み change `automate-ch32v003-ch32fun-hil` の実測結果と、`hil/matrix.json` および手順書の記載の食い違いを解消する。CH32V002 の作業（`automate-ch32v002-ch32fun-hil`）の前提を揃える。
- 条件: 実機の操作・書き込み・観測はしていない。既存ログの記載だけを根拠にした文書・設定・単体テストの変更。

## 見つけた食い違い

- `hil/matrix.json`: 2026-11-07 18:4x の全 HIL 成功（`2026-11-07-1846-...` に記録）の後も、`blink_and_read` が `manually-verified`／`automation pending`、他は `build-only`、`watchdog` は `not-yet-automatable` のままだった。
- `gpio_input` サンプル（PC4 入力を PC0 に反映）には HIL テストがない。固定配線では PC4 は `PWM_CH4`（DUT→Pico）であり、Pico から PC4 を駆動する配線になっていない。GPIO 入力は `blink_and_read` の `test_button_input`（GP12→RC→PA1）で確認している。
- `hardware/wiring.md` の本文、`hardware/ch32v003-reproduction.md`、`hardware/ch32v002-reproduction.md`、`AGENTS.md` が v1 の `measure.py`／PC0–GP0 構成を現行手順として案内していた。現行の Pico は protocol v2 で、`protocol.md` には v1 と互換がないと記載されている。
- `hardware/wiring-proposal.md` は「未実測の提案」「v1 のみ」「実機で確認するまでは未検証」のままだった。
- SPI: task 7.4 は mode 不一致の検出を求めていたが、`2026-11-07-1845-...` によれば Pico slave は mode 0 のみで、データ不一致だけを検出している。

## 変更

- `hil/matrix.json`: 実測ログに対応する 9 サンプル（`blink_and_read`、`uart`、`i2c_master`、`i2c_slave`、`spi_master`、`timer_pwm`、`adc`、`watchdog`、`sleep_wake`）を `hil-verified` にした。各行に `hil_tests` と `evidence` を追加し、制限を `note` に記録した。`gpio_input` は `build-only` のままとし、理由を記録した。`watchdog` の分類を `equivalent-standard-ch32fun` に直した。
- `ch32hil/matrix.py`: `hil-verified` には `hil_tests` と `evidence` を必須とし、`root` が指定されたときはテスト関数とログファイルの存在も確認するようにした。
- `tests/unit/test_config_matrix.py`: 同梱マトリクスの検証、`tests/hil` の全テスト関数がマトリクスから参照されていることの確認、異常系の 3 テストを追加した。
- 手順書: `wiring.md` の冒頭を現行の固定配線と v2 の説明にし、v1 の記述は安全手順の例として残した。`wiring-proposal.md` の状態表現を実測ログに合わせた。両 reproduction 手順書の Pico 観測は HIL コマンドへの案内、または v1 専用であることの注記に変えた。`AGENTS.md` の検出待ちの参照先を `ch32hil/pico.py` の `discover` に直した。`hil/README.md` にマトリクスの必須項目、SPI の制限、`gpio_input` の扱いを追記した。
- CH32V002 の change と Issue #11 から `gpio_input` の移植を外し、対象外として記録するタスクにした。

## 結果

- `uv run pytest -q`: 86 passed、11 skipped（HIL 未選択）。実測。
- `openspec validate automate-ch32v002-ch32fun-hil --strict`: valid。実測。

## 未対応・未確認

- SPI の mode 不一致検出は実装していない。ユーザーの判断（この記録の作成後、時刻は未記録）により、Pico slave が mode 0 のみでデータ不一致だけを検出する制限として受け入れ、Pico 側の mode 1–3 対応は行わない。制限はマトリクスと `hil/README.md` に記載済み。アーカイブ済みの tasks.md（7.4 は完了扱い）は変更していない。
- 手順書の変更後のコマンドは、実機で再実行していない。
- 削除した GitHub Issue #6〜#8 は、ユーザーの意図ではクローズだった（ユーザー申告）。削除は元に戻せない。
