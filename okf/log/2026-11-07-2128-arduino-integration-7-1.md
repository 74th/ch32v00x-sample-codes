# Arduino 対応後の ch32fun 回帰確認（verify-arduino-core-with-arduino-cli 7.1）

- 作業日時: 2026-11-07 21:28〜21:30 JST（各コマンドの開始・終了時刻は `date` の実測。記録 21:30 頃）
- 対象: CH32V003F4P6、Pico E661AC8863223539、固定配線（GP19→GP20 の loopback 配線は前回からのユーザー申告のまま。未確認）。電圧は実測していない。
- ソース: この change の作業ツリー（Arduino 対応の `ch32hil/devices.py`、`ch32hil/config.py`、`ch32hil/matrix.py`、`conftest.py` の変更と `tests/hil/arduino/` を含む。未コミット）。

## 実行（実測）

```
21:28:35 uv run pytest -q
→ 216 passed, 22 skipped in 1.77s

21:28:37 uv run pytest --hil -q -rxXs --hil-port=/dev/serial/by-id/usb-Raspberry_Pi_Pico_E661AC8863223539-if00
→ 230 passed, 7 skipped, 1 xfailed in 60.67s   （21:29:37 終了）
```

- `--hil-framework` は指定していない（既定の ch32fun）。
- xfailed: `test_extralibs.py::test_ssd1306_helper[helper_1mhz-...]`（従来どおりの参考行）。
- skipped 7: `tests/hil/arduino/` の 7 テスト。理由は `arduino HIL test; --hil-framework ch32fun selected`。

## 比較

- 単体テストの数: 216（この change で 15 件追加。前回の [8.2 の記録](2026-11-07-2043-extralibs-integration-8.md) の時点では 201 件と計算される）。
- ch32fun の HIL: 230 − 216 = **14 passed、1 xfailed**。前回（8.2）の「215 passed、1 xfailed」も 215 − 201 = 14 passed、1 xfailed で、**同じ結果**。失敗はない。
- 結論: Arduino 対応（フレームワーク選択、Arduino 用マトリクス、Arduino テストの追加）の後も、`--hil-framework` を指定しない ch32fun 側の結果は変わらない。

## 未確認

- CH32V002 での ch32fun 全 HIL の再実行（今回は CH32V003 のみ）。
