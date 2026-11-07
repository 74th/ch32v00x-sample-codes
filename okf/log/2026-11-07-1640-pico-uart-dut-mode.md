# Pico UART DUT モード追加と loopback 再試験

- 作業日時: 2026-11-07 16:38–16:40 JST。記録は作業後。
- 目的: 自己検証後の UART 送受信処理に DUT 用の GP8 TX・GP9 RX を追加し、loopback 側の回帰を確認する。
- 配線・機器: Pico GP16–1 kΩ–GP17 はユーザー申告で接続。DUT の既存配線は維持したが、GP8/GP9 の UART 動作は実行していない。Pico SDK 2.2.0 `a1438dff1d38bd9c65dbd693f0e5db4b9ae91779`、TinyUSB `86ad6e56c1700e85f1c5678607a762cfe3aa2f47`、arm-none-eabi-gcc 14.2.1、picotool 2.1.1。
- コマンド: `cmake --build hardware/pico-tester/build`、`picotool load -f -v -x hardware/pico-tester/build/pico_gpio_tester.uf2`、`for iteration in 1 2 3 4 5; do uv run python hardware/pico-tester/uart_loopback.py || exit; done`。再書き込み後の機器検出は script 内の `measure.discover(30)` を使用。`uv run pytest -q tests/unit/test_pico_client.py`、`git diff --check`。
- 結果: 最終版の Pico build と picotool verify が成功。loopback スクリプトを5回実行し、各回 1200/115200 baud × 7/8 bit × N/E/O × 1/2 stop の24組、32バイト、受信タイムアウト、不正入力、安全状態を確認した。ホスト模擬テスト9件成功。実際の DUT 通信・GP8/GP9 の駆動は行っていない。
- 失敗と対応: DUT モード追加直後に loopback 115200 7N1 で余分なバイトと UART error 0x5 を観測。初期の待ち時間を2 msとした版では 1200 7N1 に framing error と受信不一致が発生。UART 初期化時、TX のアイドルを確立してから RX を有効化し、さらに25 ms 待って受信 FIFO とエラーをクリアする対策を入れた後の5反復は成功。原因は初期化時の過渡状態と推定し、波形では未確認。初期化中に受信したバイトは意図的に破棄する。
- 最終ソースの実験後 SHA-256: `main.c` `8080d37632d38e1c1eecc4de8beafce5d39b0a85ebc4874ed5b8adff9fcea7a1`、`uart_fixture.c` `af4be466c5b5094fe30374c2b349ffce77405e664fe0b60617db13d6cffd4fad`、`uart_loopback.py` `b4189ad7f1ef7b649e671d31ea3af322e158afcf88c24ff87e6336e61c07dea2`、`CMakeLists.txt` `04b371e3e0a5f765e32ca41bfd1082a7b2d92c6ff58313ab470d7d1ac24204c4`。
- 未確認: DUT モードの送受信、外部 baud・波形、初期化中の電気的過渡の原因、parity/framing/break/overrun 注入、物理 USB 抜去。5回の成功は全環境での再発防止の証明ではない。Pico は UART 対応 v2 を実行中。DUT は変更していない。
