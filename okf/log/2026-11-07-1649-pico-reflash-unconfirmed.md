# Pico の再書き込み確認保留

- 作業日時: 2026-11-07 16:49–16:50 JST。記録は作業後。
- 目的: ADC 機能確認用に build した Pico firmware を書き込む。
- 条件: Pico と WCH-LinkE は USB 上に検出。ユーザーは I2C loopback の配線変更には Pico を抜く必要があると申告し、その後いったん Pico を抜く旨を申告。DUT と Pico の電圧、配線作業のタイミングは未測定。
- コマンド: `PICO_SDK_PATH=/home/nnyn/.pico-sdk/sdk/2.2.0 cmake -S hardware/pico-tester -B hardware/pico-tester/build -G Ninja -DPICO_BOARD=pico` と `cmake --build hardware/pico-tester/build` は成功。`picotool load -f -v -x hardware/pico-tester/build/pico_gpio_tester.uf2` は終了コード0を返したが `Waiting for device to reboot` までで、通常の Loading、Verifying、OK の出力がなかった。`lsusb` は Pico `2e8a:000a` と WCH-Link `1a86:8010` を表示。`measure.discover(30)` の後、pyserial で `CAPS` を送ったが応答なし。
- 結果: firmware の書き込み・verify・実行はいずれも確認できていない。終了コードだけでは書き込み成功としない。Pico を抜くとのユーザー申告後、再接続確認まで追加の USB 操作を控える。
- 失敗・未確認: BOOTSEL 移行が完了しなかった理由、Pico の現在の firmware と状態、ADC コードの実機動作。電源断時の逆流をこの操作だけでは評価できない。
