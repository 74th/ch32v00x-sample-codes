# WCH公式SDK blink_and_read（CH32V003）

作業日時: 2026-11-08 00:55 JST（ホストdateで確認、記録は実測直後）。

## 目的・条件
openspec change add-wch-sdk-peripheral-samples タスク2.1。CH32V003（WCH-LinkE 2.22、固定minichlink b28d285）、Pico firmware v2、既存固定配線（PC0→GP5、PD5→GP9、PA1←GP12のRC）。SDK 4e1b7437、WCH GCC 15.2.0。配線の物理再測定はしていない。

## 実行
```sh
uv run pytest --hil --hil-framework wch tests/hil/wch/test_blink_and_read.py -x -q
```

## 結果（実測）
- 1回目: 再開確認のみ失敗。解放直後は最大1 sの`Delay_Ms(1000)`が残りlowが長く、完全な周期が2個しか取れなかった（テスト側の待ち不足、DUTの不具合ではない）。
- 2回目: GPIO_SAMPLEの上限300点を超える窓は`INVALID sample_arguments`で失敗（Pico側の制約）。
- 3回目: 解放後に1.2 s待ってから300点を取る形に修正して全phase成功（build/flash/全量readback/reset/UART/点滅/ボタン停止/再開）。UART 32 B受信、エラー0。再開時のruns: 0:29,1:50,0:50,1:51,0:50,1:50,0:20（10 ms/点）。

## 未確認
電圧・波形精度、他の電源条件。フィルタ込みのボタン応答時間は未測定。

## 追記（セクション4の回帰で判明、実測）
後日の回帰で、このテストの起動テキスト判定（`init start loop 0 loop 1`）が約3〜4割で失敗した。`minichlink -b`がDUTを0.5秒以内に2回起動し、32 B捕捉が`init start loop 0 init start`になるため（DUTの不具合ではない）。判定を先頭3行（`init start loop 0`）に緩め、捕捉前のsettleを1.5 sにして10回連続成功した。`loop 1`はループ・点滅の判定で別に確認している。詳細は`okf/log/*-wch-sdk-regression-and-consistency.md`。
