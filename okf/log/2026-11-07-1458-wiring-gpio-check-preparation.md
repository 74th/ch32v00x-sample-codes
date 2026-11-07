# 配線 GPIO 確認の準備

- 作業日時: 2026-11-07 14:58–14:59 JST。記録は作業後。
- 目的: 新しい配線を GPIO レベルで確認するための機器検出と、入力専用 Pico 観測プログラムのビルド。
- 対象・配線: CH32V003F4P6 と Pico の新しい配線はユーザーが「配線した」と申告。実際のピン接続、給電、電圧、保護部品の状態は未確認。実機には観測や書き込みを行っていない。
- ツールとソース: Pico SDK 2.2.0 `a1438dff1d38bd9c65dbd693f0e5db4b9ae91779`、TinyUSB `86ad6e56c1700e85f1c5678607a762cfe3aa2f47`、arm-none-eabi-gcc 14.2.1、picotool 2.1.1。入力専用の一時ソース `/tmp/pico-input-observer/main.c` は GP4–GP15 を入力・pull 無効にし、USB の `s` で100回値を読む。デバイスに書き込んでいない。
- コマンド: `lsusb`、`ls -l /dev/serial/by-id/`、`picotool info`、`PICO_SDK_PATH=/home/nnyn/.pico-sdk/sdk/2.2.0 cmake -S /tmp/pico-input-observer -B /tmp/pico-input-observer/build -G Ninja -DPICO_BOARD=pico`、`cmake --build /tmp/pico-input-observer/build`。
- 結果: USB に Pico `2e8a:000a` 1台と `/dev/ttyACM0` が見えた。WCH-LinkE は `lsusb` 上に見えなかった。観測プログラムのビルドは成功。USB 上の見え方は電圧・電源・配線の実測を意味しない。
- 失敗: `picotool info` は BOOTSEL デバイスがないため終了コード249。USB シリアルの Pico を報告。強制再起動はしていない。
- 未確認: ファームウェアの書き込みと動作、各信号の連続性や短絡、DUT/Pico 電源と各電圧、safe state、ユーザーの実配線と RC/pull-up、DUT と WCH-LinkE の接続。入力の静的な観測だけでは配線の導通を証明できない。
