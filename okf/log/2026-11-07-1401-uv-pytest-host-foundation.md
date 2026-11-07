# uv/pytest ホスト基盤の実装（Issue #8 の一部）

- 記録日時: 2026-11-07 14:01 JST（作業と同時に記録）
- 目的: uv/pytest 基盤、DUT 操作層、Pico クライアント、段階記録、設定・マトリクス検証を実機なしで整備する。
- 対象: ホストのみ。Pico/DUT/programmer には一切接続・書き込みしていない（実測なし）。

## 実行コマンドと結果（実測）
- `uv sync` → pyserial 3.5 / pytest 8.4.2 を解決。
- `uv run pytest -q` → 47 passed, 1 skipped（skip は `--hil` 未指定の HIL テスト）。

## 実装内容
- `pyproject.toml`, `uv.lock`, `tests/conftest.py`（`--hil` が無ければ HIL を skip）
- `ch32hil/`: dut.py（minichlink 偽成功・誤型番拒否、サイズ指定 readback）、pico.py、phases.py、config.py、matrix.py
- `hil/matrix.json`, `hil/configs/gpio_blink.json`
- `tests/unit/test_measure.py`: 旧 `hardware/pico-tester/test_measure.py` の 6 ケースを移動（全通過）。

## 未確認・制限
- Pico プロトコル（#7）は未確定。pico.py は design.md の行形式に基づく暫定実装で、実ファームウェアとは未照合。
- `tests/hil/test_blink_and_read.py` は未実行（実機未接続・未選択）。HIL 成功は主張しない。
- CH32V003 追加サンプル（UART 等）は未着手。
- 失敗: 記録された失敗なし（記録時点。後続の実機結果は別ログ）。
