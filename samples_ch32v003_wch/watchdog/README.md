# watchdog（公式WCH SDK、CH32V003）

書籍`watchdogtimer-wch_sdk`の移植。独立ウォッチドッグ（IWDG）を約2秒でセットし、PA1（プルアップ入力）がHighの間はループごと（500 ms）に給餌し、
Low（ボタン押下）の間は給餌を止めて、最後の給餌から約2秒後にIWDGリセットさせる。LED1は給餌中に250/250 msで点滅、LED2は起動のたびに500 ms点灯。
公式`IWDG_WriteAccessCmd`/`IWDG_SetPrescaler`/`IWDG_SetReload`/`IWDG_ReloadCounter`/`IWDG_Enable`を使用（プリスケーラ128、LSI約128 kHz → 約1 kHz、リロード2000 → 約2秒）。Flash 6,672 B／RAM 696 B。

## 書籍との差
- LED1=**PC0**（GP5）、LED2=**PC4**（GP15）。書籍のPC1/PC2は治具のI2C対。
- 書籍の`IWDGSetReload(2000)`は公式SDKに無い（公式名は`IWDG_SetReload`）ため修正。
- ログはSDI printfの代わりにUSART1 TX（PD5）。
- **追加**: リセット要因（`RCC_GetFlagStatus(RCC_FLAG_IWDGRST)`、直後に`RCC_ClearFlag`）を、起動時の`reset cause: IWDG|other`と、毎ループの`loop N cause=IWDG|other`に出す。書籍には無い機能で、UARTの文字だけでウォッチドッグリセットを識別するため。

## 観測（HIL、実測）
`uv run pytest --hil --hil-framework wch tests/hil/wch/test_watchdog.py`（3回連続成功）
- デバッガのリセット後: `loop N cause=other`。通常稼働でPC0（GP5）が250/250 ms（±100 ms）、ループ番号が増え続ける（例: 8 → 12）。
- PA1をLow（GP12→RC）に1000 ms: リセットなし（番号が増え続け`cause=other`のまま）。最後の給餌は保持開始の0.5 s以内なので、給餌なしは1.6 s未満。
- PA1をLowに2000 ms: ウォッチドッグがリセット。`loop 0 cause=IWDG`、`start loop`も観測。給餌なしが2.0 s以上でリセット。
- 以上から、タイムアウトは約1.6〜2.5秒の間（公称2秒）。LSIの個体差・温度依存や、より狭い時間窓は未測定。
- **起動直後のテキスト**（`init`、`reset cause: …`、`start`）は、Picoの捕捉開始（約0.3 s）がDUTの起動に間に合わないため、確実には取得していない。要因はループ行から判定している。
- LED2（PC4）の起動点灯は観測していない。
