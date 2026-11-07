# uart（公式WCH SDK、CH32V003）

書籍`uart-wch_sdk`の移植。USART1でMH-Z19系CO2センサーを扱う: 自己校正ON（`FF 01 79 A0 … E6`）を送って応答9 Bを捨て、
以降1秒ごとに読み出しコマンド（`FF 01 86 … 79`）を送り、`FF 86`を探して9 Bを受信、checksum（`0xff - sum(b[1..7]) + 1`）を検証し`CO2: %5d ppm`を出す。
公式`USART_Init`/`USART_GetFlagStatus`/`USART_SendData`/`USART_ReceiveData`を使用。Flash 5,240 B／RAM 372 B。
フレーム処理は`co2.c`（純関数）に分離し、ホストでも単体テストする。

## 書籍との差（治具のため）
- 書籍既定のPC0/PC1リマップ＋SDI printfをやめ、**PD5(TX)/PD6(RX)**に固定。Pico（GP9/GP8）がセンサー役になる。
- 診断printfはセンサー線と混ぜない。結果文字列は同じTX線に出すが、コマンド・応答の1往復が終わった後だけで、フレームと重ならない。
- 受信timeoutはループ回数ではなくバイトごと500 ms（`Delay_Us(100)`で監視）。ホスト駆動のセンサー模擬が応答する時間を確保する。
- 読み出し後の待ちはループ先頭に置いた（初回に1秒待つ点だけが書籍と異なる）。

## 観測
- ホスト（`tests/unit/test_wch_co2.py`）: 既知応答`ff8604d200000000a4`→1234 ppm、書籍の固定コマンド2本のchecksum、checksum異常（値は保持して報告）、ヘッダ異常。
- HIL（`uv run pytest --hil --hil-framework wch tests/hil/wch/test_uart.py`、実測）: Picoが9600 8N1でセンサー役。
  自己校正コマンドの内容一致→応答→`start`、読み出しコマンドの内容一致→既知フレーム→`CO2:  1234 ppm`、
  checksum不正フレーム→`invalid checksum`、応答なし→`read timeout`。UARTエラー0。
- 実センサーでの確認はしていない。PicoのUARTは1呼出ごとに半二重のため、応答は1回の呼出内の送信で行う（応答タイミングは厳密に模擬していない）。
