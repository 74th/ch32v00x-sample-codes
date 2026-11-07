# standby_wake（公式WCH SDK、CH32V003）

書籍`standby_mode_blink-wch_sdk`の移植。Standby（`PWR_EnterSTANDBYMode(PWR_STANDBYEntry_WFE)`）を自動ウェイクアップ（AWU）で復帰する。
起動後に`wait`を出して5秒待ち、`init`/`start`の後、ループで`go to standby: N`→Standby→AWU（LSI約128 kHz、分周10240、ウィンドウ25 → 80 ms×25＝**約2秒**、EXTI line 9のEvent）で復帰→`SystemInit()`でクロック復元→`Auto wake up: N`、LEDトグル。
設定は公式EVT `PWR/Standby_Mode`と同じ（分周10240、ウィンドウ25、EXTI_Line9 event）。Flash 6,944 B／RAM 712 B。
Sleep（`sleep_wake`）との違い: `PWR_CTLR_PDDS`とSLEEPDEEPを立てた深いモードで、起床後はクロックの再設定（`SystemInit()`）が必要。

## 書籍との差
LEDを**PC0**（治具のBLINK→GP5。書籍のPC1は治具のI2C SDA）。NMI/HardFaultの宣言・定義を省いた。他は書籍のコード。公式`core_riscv.c`（`WFE`の実体）を追加コピー。

## 復帰動作の実測と注意
`uv run pytest --hil --hil-framework wch tests/hil/wch/test_standby_wake.py`（2回連続成功）
- 起動から約7秒後、wakeごとのUART（`\r\nAuto wake up: N \r\ngo to standby: N+1`）の連続3回で**カウントが連番**（0, 1, 2）。**リセットではなく、WFEの直後から実行が再開**し（`wait`/`init`が再出力されない）RAMが保持される。到着間隔は2.074、2.076秒。
- LED（PC0→GP5）の半周期は2.05〜2.1秒（公称2.0秒＋起床時間）。
- **wake直後の最初の1バイトが化ける**: 本来`\r`のところが毎回`0x80`（クロックのPLL再起動中に送出されるため。確認した3回すべて）。以降の文字は正しい。
- **デバッガ接続不可**: Standbyに入る機種ではminichlinkが`link error, nothing connected to linker`→`Could not setup interface`となり、検出も書き込みもできなくなる（この治具で実測）。サンプルの5秒の初期待機が、リセット後に書き込める唯一の窓。
- **復旧手順**（テストに組み込み済み）: DUTの3.3VはWCH-LinkE供給なので、固定minichlinkで`-t`（3.3 V OFF）→1.5秒待つ→`-3`（ON）で電源を入れ直し、5秒の初期待機内に既知の`blink`を書き込む（`-w … flash -b`）。その後、型番検出・全量読み戻し・点滅を確認する。復旧に成功し、終了後に`Detected CH32V003`を確認した。
- **Standbyの消費電流・クロック停止は測定していない**。復帰間隔とレジスタ非リセットの挙動のみを観測。電源の入れ直しは治具の電源（LinkEの出力）をテストが操作するため、DUTがLinkE給電であることを設定で確認してから行う。
