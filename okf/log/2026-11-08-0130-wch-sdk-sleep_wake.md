# WCH公式SDK sleep_wake（CH32V003、WFI＋TIM1）

作業日時: 2026-11-08 01:30 JST（ホストdateで確認、記録は実測直後）。

## 目的・条件
タスク2.12。CH32V003、固定minichlink、Pico fw v2（UART、GPIO_SAMPLE）、既存配線PC0→GP5、PD5→GP9。SDK 4e1b7437、WCH GCC 15.2.0。消費電流の測定器は無い。

## 実行
```sh
uv run pytest --hil --hil-framework wch tests/hil/wch/test_sleep_wake.py -x -q   # 計6回
```

## 結果（実測）
- ビルド失敗: `__WFI`が参照する`WFE`が未定義。公式`core_riscv.c`をsdk/Coreへ無改変コピーし（PROVENANCEへSHA-256追記）、共通のwch.mkに加えた。blinkは1,092 B/268 Bのまま変化なし。
- テスト1〜3回目: Picoの`UART_XFER`が38バイト・8000 msを拒否（上限32バイト・5000 ms）。32 B・5 sへ変更。
- 4〜6回目: 3回連続成功。UART `['awake','sleep','tim','awake']` 32 Bに3.11 s、LED半周期 2.05/2.0/2.0/2.0/2.0/2.0 s。

## 未確認
消費電力・クロック停止、復帰遅延の測定、Sleepと他の低消費電力モードの差。
