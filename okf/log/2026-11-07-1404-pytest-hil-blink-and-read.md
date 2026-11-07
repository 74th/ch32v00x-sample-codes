# pytest HIL: blink_and_read 実機実行（Issue #8 の一部）

- 作業・記録日時: 2026-11-07 14:04〜14:06 JST 頃（コマンド実行時刻は date で取得、記録は直後）。
- 目的: `tests/hil/test_blink_and_read.py` による build→flash→readback→reset→measure の一括実行を確認する。
- 条件: ユーザーが「blink_and_read の範囲で実機使用可」「CH32V003 が接続されている」と申告（ユーザー申告）。配線は `hardware/wiring.md` の GPIO 案（PC0–1kΩ–GP0）と同じとユーザーが用意したものとし、スイッチ状態・VDD 実測値は私は未確認。WCH-LinkE と Pico は `lsusb` / `/dev/serial/by-id` で検出（実測）。
- ソース: git HEAD 854472d + 未コミットの ch32hil/ 等。minichlink は `externals/ch32fun`（b28d285）を `scripts/ch32fun.sh programmer` でビルドしたもの。Pico は既存の PICO_GPIO_V1 ファームウェア（本作業では書き換えていない）。

## 実行と結果（実測）
1. 初回: `pytest --hil --hil-port <path>` はオプション未認識で失敗（tests/conftest.py 未読込）。conftest をリポジトリ直下へ移動して修正。実機操作は行われていない。
2. `uv run pytest tests/hil --hil -m "hil and gpio" --hil-port=<Pico by-id> --hil-run-dir=...` → 1 passed (4.14 s)。run.json で environment/pico_prepare/dut_build/dut_flash/dut_readback/dut_reset/fixture_setup/measure/cleanup が全て pass。
3. 直接 `measure.py` → PASS。runs: 1×32, 0×51, 1×50, 0×50, 1×50, 0×50, 1×17（10 ms 刻み、約 500 ms 周期のパルス）。
4. 失敗注入: `--hil-port=/dev/nonexistent` で再実行 → measure 段階のみ fail（build/flash/readback は pass）、cleanup pass。flash 失敗と観測失敗が区別されることを確認。

## 未確認
- flash 失敗系（未接続・誤型番）は unit test の模擬のみ。実機での故障注入（DUT 切断等）は未実施。
- 失敗後の GP0 電気的状態は未測定（v1 では GP0 は入力のみ）。
- Pico protocol v2 / `RESET_SAFE` は未実装。PicoClient は実機未使用。

## 追記: 3.3 V 遮断による切断状態の flash（2026-11-07 14:12 JST 頃、ユーザー提案の方法）
- 実行: `minichlink -t -w main.bin flash -b`（`-t` で WCH-LinkE の 3.3 V 出力を停止）。信号スイッチの状態は未確認（ユーザー側）。
- 結果（実測）: minichlink が終了コード -11（SIGSEGV）で異常終了、`Detected CH32V003` なし。`check_flash_output` は終了コードと検出出力なしの両方で flash 失敗と判定（拒否）した。
- 復旧: `minichlink -3 -b` で 3.3 V 再有効化後、HIL を再実行して pass（結果は上記と同じ構成）。
- 注意: クラッシュは 3.3 V 停止時の minichlink の挙動で、「未接続」の完全な再現とは限らない（推定）。
