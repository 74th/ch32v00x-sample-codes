# WCH公式SDK watchdog（CH32V003、IWDG）

作業日時: 2026-11-08 01:27 JST（ホストdateで確認、記録は実測直後）。

## 目的・条件
タスク2.11。CH32V003、固定minichlink、Pico fw v2（GPIO_SAMPLE、GPIO_DRIVE、UART）、既存配線PC0→GP5、PD5→GP9、PA1←GP12（10 kΩ＋1 µF RC）。SDK 4e1b7437、WCH GCC 15.2.0。

## 実行
```sh
uv run pytest --hil --hil-framework wch tests/hil/wch/test_watchdog.py -x -q   # 計6回（うち3回は起動テキストの判定方法を直す前の失敗）
```

## 結果（実測）
- 試行1〜6: 起動テキスト（`init`/`reset cause: other`）を捕捉して判定しようとして失敗。調査で、Picoの捕捉開始がDUT起動とほぼ同時（約0.3 s）で先頭の数行を取り逃がすこと（`wait_ready`の再起動で既に走り始めたDUTのloop出力を拾って捕捉が終わる）が原因と判明。判定を`loop N cause=other`行へ変更。
- 試行7〜9: 3回連続成功。前: `loop 8 cause=other`、1 s停止後 `loop 12 cause=other`（リセットなし）、2 s停止後 `loop 0 cause=IWDG`（`start loop`も観測）。
- 書籍の`IWDGSetReload`は公式SDKにないため`IWDG_SetReload`へ変更（ビルド時に未定義参照になる）。

## 未確認
起動直後のテキスト、LED2の起動点灯、1.6〜2.5秒より狭いタイムアウトの時間窓、LSI周波数の実測、温度・電圧依存。
