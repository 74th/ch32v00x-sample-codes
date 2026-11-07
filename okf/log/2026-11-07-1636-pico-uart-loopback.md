# Pico UART loopback 実装と自己検証

- 作業日時: 2026-11-07 16:36–16:38 JST。記録は作業後。
- 目的: DUT 使用前に Pico UART 送受信とフレーム設定、境界値、失敗時の分類および安全状態を loopback で検証する。
- 対象・配線: RP2040 Pico の GP16（物理21、UART0 TX）–1 kΩ–GP17（物理22、UART0 RX）はユーザー申告の接続。DUT 配線は維持し、GP8/GP9 など DUT 信号は駆動していない。抵抗値・電圧は今回独立測定していない。
- ソース・ツール: Pico SDK 2.2.0 `a1438dff1d38bd9c65dbd693f0e5db4b9ae91779`、TinyUSB `86ad6e56c1700e85f1c5678607a762cfe3aa2f47`、arm-none-eabi-gcc 14.2.1、picotool 2.1.1、pyserial via `uv`。ソースは未コミット作業ツリーで、実験後の SHA-256 は `main.c` `8d293a8940d0a0cd5d1803f45180ca01bfc7d6520238009b872ae31eaad1642a`、`uart_fixture.c` `e7d4de49b2c832a3d87a42832bd54ba9c193b143487260120beefb352ff5cc29`、`uart_fixture.h` `a8301d559117567e6e75cb5224a41493bc933bdf1a4cccea1a1a865afb0bd963`、`fixture.c` `99e68bc4a200534aa9a6925b03235aa9cd83b9e1cd98994409d25aaf93bb3321`、`CMakeLists.txt` `04b371e3e0a5f765e32ca41bfd1082a7b2d92c6ff58313ab470d7d1ac24204c4`、再実行スクリプト `uart_loopback.py` `b4189ad7f1ef7b649e671d31ea3af322e158afcf88c24ff87e6336e61c07dea2`。
- コマンド: `PICO_SDK_PATH=/home/nnyn/.pico-sdk/sdk/2.2.0 cmake -S hardware/pico-tester -B hardware/pico-tester/build -G Ninja -DPICO_BOARD=pico`、`cmake --build hardware/pico-tester/build`、`picotool load -f -v -x hardware/pico-tester/build/pico_gpio_tester.uf2`。書込み・verify OK。書換後 `hardware/pico-tester/measure.py` の `discover(30)` で Pico を待って pyserial で `UART_XFER LOOPBACK` を実行。`uv run python hardware/pico-tester/uart_loopback.py` で再実行。
- 実測: 1200/115200 baud × 7/8 bit × N/E/O parity × 1/2 stop の24組について各3バイトの送受信一致、UART エラー0。115200 baud の32バイトも一致。設定値はそれぞれ実効 1199/115207 baud と報告（独立周波数測定ではない）。受信なし100 ms は `ERR TIMEOUT`、1199 baud・7 bit で 0xff・引数不足は `ERR INVALID`。その後 GP16/GP17 は output=0、pull_up=0、pull_down=0。
- 中断: 受信待ち5秒の要求から約200 ms後に pyserial の CDC 接続を閉じ、約450 ms後に再接続して両 GPIO が output=0・pull 無効であることを確認。物理 USB 抜去や外部計測は未実施。
- 失敗: 初回ビルドは SDK に `uart_is_busy` がなく失敗。UART の BUSY フラグを使用して修正後にビルド成功。timeout・不正要求は意図的な負のケース。
- 未確認: parity/framing/break/overrun の意図的注入、実際の信号波形や電圧・独立 baud 精度、外部相手機器、DUT 側 GP8/GP9 の UART、物理 USB 抜去。今回の firmware は loopback 専用で DUT 対向 UART は未実装。既存の GPIO 測定・安全機能全体の再検証はしていない。
