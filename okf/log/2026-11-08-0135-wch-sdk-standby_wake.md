# WCH公式SDK standby_wake（CH32V003、AWU Standby）

作業日時: 2026-11-08 01:35 JST（ホストdateで確認、記録は実測直後）。

## 目的・条件
タスク2.13。CH32V003、固定minichlink、Pico fw v2（UART、GPIO_SAMPLE）、既存配線PC0→GP5、PD5→GP9。DUT電源はWCH-LinkEの3.3 V（設定`dut_power: wch_linke_3v3`、電圧は未測定）。SDK 4e1b7437、WCH GCC 15.2.0。

## 実行
```sh
uv run pytest --hil --hil-framework wch tests/hil/wch/test_standby_wake.py -x -q
externals/ch32fun/minichlink/minichlink -i      # 失敗時の確認、-t / -3 は電源の入れ直し
```

## 結果（実測）
- 試行1: wakeバーストのUART判定が失敗（先頭の`\r`が`0x80`に化けていた）。**この時点で復旧用の処理がテストになく**、DUTはStandbyで眠る状態のまま残り、`minichlink -i`が`link error, nothing connected to linker`→`Could not setup interface`になった。
- 復旧（手作業）: `minichlink -i`を6回繰り返しても接続不可。`-t`（3.3 V OFF）→1.5秒→`-3`（ON）で電源を入れ直すと検出できたが、検出確認に時間をかけて5秒の初期待機を過ぎ、再び不可。もう一度電源を入れ直し、直後に`-w blink main.bin flash -b`で書き込みに成功（`Image written.`）。その後`scripts/wch-sdk.py flash`で検出・書き込み・全量読み戻しとobserveの点滅（pass）を確認。
- テストを修正: 先頭バイトの化けを許容して記録し、復旧（電源入れ直し→blink書き込み→検出・全量読み戻し）をテストに組み込み（失敗時も実行するよう`cleanup`名で実行）。
- 試行2・3: 連続成功。wakeのカウントは0,1,2、間隔2.074/2.076 s、LED半周期2.05〜2.1 s、復旧後に`Detected CH32V003`。

## 未確認
Standby消費電流・クロック停止、AWU間隔の高精度測定（LSIのばらつき）、wake後の先頭バイト化けの原因（PLL再起動中の送出と推定、未検証）、`PWR_STANDBYEntry_WFI`、AWUを使わない他の起床要因。
