# WCH公式SDK timer_blink（CH32V003、TIM1/TIM2）

作業日時: 2026-11-08 01:18 JST（ホストdateで確認、記録は実測直後）。

## 目的・条件
タスク2.9。CH32V003、固定minichlink、Pico fw v2、既存配線PC0→GP5、PD5→GP9。SDK 4e1b7437、WCH GCC 15.2.0。

## 実行
```sh
uv run pytest --hil --hil-framework wch tests/hil/wch/test_timer_blink.py -x -q   # tim1とtim2
```

## 結果（実測）
- ビルド時に書籍のNVIC配列添字が範囲外（`NVIC->IPRIOR[35]`）の警告 → 該当2行を省略。
- 1回目: ベクタ位置のテスト内計算が`16+IRQn`で誤り（このSDKのIRQnはベクタスロット番号そのもの）。修正。
- 2回目: UARTイベント文言が見つからず失敗（起動時のレジスタダンプが32 Bを超え、イベントは0.5 s後）。取得を点滅測定の後の途中キャプチャへ変更。
- 3回目: 成功。tim1: slot35、`mret`、点滅50/50、`1sec event`×2以上。tim2: slot38、`mret`、点滅50/50、`500ms event`×2以上。

## 未確認
TIMレジスタ値の実測（捕捉が32 Bまで）、割り込みの優先度・NVIC有効化、周期の高精度測定。
