# i2c_master（公式WCH SDK、CH32V003）

書籍`i2c_master-wch_sdk`の移植。I2C1（400 kHz）でSHT31（0x44）へ、起動時に`30 A2`（soft reset）→300 ms→`30 41`（status clear）→300 ms、
ループで`24 00`（単発測定）→300 ms→6 B読み出し→変換→`Temperature: <t>, Humidity: <h>`をUSART1 TX（PD5）へ出力。
I2Cヘルパーと初期化は書籍のもの（公式`I2C_*`）。変換は`sht31.c`に分離（ホストでも単体テスト）。Flash 7,904 B／RAM 696 B。

## 書籍との差
- **PC1(SDA)/PC2(SCL)**（`USE_REMAP 0`）。書籍既定はPC6/PC5リマップだが、治具のI2C対はPC1/PC2。
- 最終バイトでACKを無効化（NACK）。書籍は常にACKで、スレーブへ余分に1バイト要求する。Pico模擬で`sent=7`＋`ERR I2C`として観測された。実SHT31では見えない差かもしれない。
- 結果の出力を読み出しの300 ms後にし、最後の待ちを4,700 msに短縮（周期は同じ約5.3 s）。Picoは1コマンドずつ実行するため、I2C応答後にUARTテキストを捕捉できるようにする。
- `read_i2c_data`に`return 0`を追加（書籍は戻り値なしで関数を終える）。
- 温度は書籍の`uint32_t`演算のため、0 ℃未満はwrapする（`raw=0`→4294967251）。書籍どおりで未修正。CRCバイトも検査しない（書籍どおり）。

## 観測
- ホスト（`tests/unit/test_wch_sht31.py`）: 手計算した既知値（`0x6666/0x8000`→24 ℃/50 %。69.99が切り捨てられて24）、フルスケール、wrap。
- HIL（`uv run pytest --hil --hil-framework wch tests/hil/wch/test_i2c_master.py`、実測）: PicoがSHT31（0x44）役。`30a2`→`3041`→`2400`＋6 B読み出し（sent=6）、
  DUTが出力した`Temperature: 24, Humidity: 50`が既知応答と一致、0x45へは送信なし、ループ周期5.315 s。
- Pico側バスは100 kHz設定で、DUTの400 kHzのクロック周波数自体は判定していない。実SHT31・温湿度の実測値は未確認。
