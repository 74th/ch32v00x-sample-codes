# WCH公式SDK i2c_master（CH32V003、Pico SHT31模擬）

作業日時: 2026-11-08 01:02 JST（ホストdateで確認、記録は実測直後）。

## 目的・条件
タスク2.5。CH32V003、固定minichlink、Pico fw v2（I2C_SLAVE）、既存配線PC1↔GP10(SDA)・PC2↔GP11(SCL)（各220 Ω、DUT 3.3 Vへ4.7 kプルアップ）、PD5→GP9。SDK 4e1b7437、WCH GCC 15.2.0。

## 実行
```sh
uv run pytest tests/unit/test_wch_sht31.py
uv run pytest --hil --hil-framework wch tests/hil/wch/test_i2c_master.py -x -q
```

## 結果（実測）
- ホスト単体4件成功。最初の期待値25は誤り（69.99切り捨てで24）で、手計算に直した。
- HIL 1回目（書籍どおりのread）: loop0で`I2C`エラー、`sent=7`。最終バイトをNACKせずスレーブが7バイト目を要求された。
- 最終バイトでACK無効化を追加して2回目成功: 30a2、3041、2400+6 B（sent=6）、`Temperature: 24, Humidity: 50`、0x45無反応、周期5.315 s。

## 未確認
実SHT31、400 kHz時の波形、書籍どおり（常にACK）のreadが実SHT31で問題になるか、温度の負値。
