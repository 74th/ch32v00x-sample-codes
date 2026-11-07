# i2c_slave（公式WCH SDK、CH32V003）

書籍`i2c_slave-wch_sdk`の移植。PC1(SDA)/PC2(SCL)でI2Cスレーブ（アドレス0x10、レジスタ0x30個）。
公式のI2C1イベント／エラー割り込み（`I2C1_EV_IRQHandler`/`I2C1_ER_IRQHandler`、`I2C_GetLastEvent`、`NVIC_Init`）で処理する。
最初の受信バイトがレジスタポインタ、続くバイトはポインタ位置に保存して進める。読み出しはポインタから返して進める。0x20〜0x23は`00 10 20 30`で起動。
Flash 7,516 B／RAM 752 B。

書籍との差: ロジックは書籍のまま。省いたのはNMI/HardFaultの宣言・定義だけ（公式Startupの既定ハンドラ）と、`printf`用`stdio.h`の追加。
ポインタは割り込み内でバイトごとに動くため、ポインタ書き込み→読み出しはSTOP区切りでも repeated START でも成り立つ。

## 観測（HIL、実測）
`uv run pytest --hil --hil-framework wch tests/hil/wch/test_i2c_slave.py`（3回連続成功。最初の1回は私のテスト期待値の誤りで失敗、DUTではない）
- PicoのI2C_PROBE: 0x10はACK、0x11はNACK。
- 0x20のポインタ設定＋読み出し＝`00102030`。0x10へ`aabbccdd`を書いて読み戻し。0x12から2バイト＝`ccdd`。
- **repeated START**（1トランザクション）: 0x20→`00102030`、0x10→`aabbccdd`、0x22→`2030`。
- UARTログ（`request:`/`receive:`行）は判定していない。Picoが1コマンドずつ実行するため、取得開始前に出力が終わる。
Arduino Coreのslaveで出ていたSCL張り付き（`okf/log/2026-11-07-2310`）は、この実装では今回の4回の実行で観測されなかった（網羅的な確認ではない）。
