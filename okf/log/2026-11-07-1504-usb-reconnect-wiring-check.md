# 再起動後の USB 機器確認

- 作業・記録日時: 2026-11-07 15:04 JST以降（終了時刻未記録）。
- 目的: GPIO 配線確認に向け、再起動後の Pico と WCH-LinkE の USB 検出を確認する。
- 条件: ユーザー申告では PC 再起動後に WCH-LinkE–CH32V003 の外れた配線を修復。DUT–Pico の各接続、電源電圧、保護部品は未確認。USB 検出後の修復のため、その後の DUT 検出は未実施。
- コマンド: `lsusb`、`ls -l /dev/serial/by-id/`、一時入力観測ファームウェアについて `PICO_SDK_PATH=/home/nnyn/.pico-sdk/sdk/2.2.0 cmake -S /tmp/pico-input-observer -B /tmp/pico-input-observer/build -G Ninja -DPICO_BOARD=pico`、`cmake --build /tmp/pico-input-observer/build`。
- 実測結果: USB に WCH-Link `1a86:8010` と Pico `2e8a:000a` を検出。Pico は `/dev/ttyACM1`、Link は `/dev/ttyACM0`。前回の `/tmp` は再起動で消え、入力専用観測ファームウェアを再ビルドできた。ファームウェアは書き込んでいない。
- 失敗: この作業での失敗なし。未確認: DUT の識別・電源・各信号、配線導通、観測プログラムの実動作。USB 上の検出は DUT が通電・接続されていることを証明しない。
