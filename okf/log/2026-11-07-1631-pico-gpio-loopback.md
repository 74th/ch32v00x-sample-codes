# Pico GPIO loopback 自己検証

- 作業・記録日時: 2026-11-07 16:31 JST。作業開始時刻は記録していない。
- 目的: GPIO の出力・入力・周期測定と中断後のピン設定を DUT と独立に確認する。
- 配線: ユーザー申告で Pico GP16（物理21）と GP17（物理22）の間に 1 kΩ を接続。既存 DUT 配線は維持したが、駆動対象には使用しない。Pico は USB 給電。電源・信号電圧と抵抗値は今回独立測定していない。
- ソース・ツール: `hardware/pico-tester/main.c`, `fixture.c`, `fixture.h`, CMake 設定の作業時点。Pico SDK 2.2.0 `a1438dff1d38bd9c65dbd693f0e5db4b9ae91779`、TinyUSB `86ad6e56c1700e85f1c5678607a762cfe3aa2f47`、arm-none-eabi-gcc 14.2.1、picotool 2.1.1、pyserial（`uv run`）。
- ソース識別（SHA-256）: `main.c` `00c9405ce25abbcdc3578ba44151ca9613364f8878eeacc88159c1e264510301`、`fixture.c` `99e68bc4a200534aa9a6925b03235aa9cd83b9e1cd98994409d25aaf93bb3321`、`fixture.h` `39b65118d1eac8a558a289260d06e5bd34737fcdfe22652ed5b0803db46bb18c`、`CMakeLists.txt` `e73014fa25570c7eed9f6e0e97456f8b205b18e7f69fa16daa2dd3b4d033ef2c`。ハッシュの記録は実験後。
- コマンド: `cmake --build hardware/pico-tester/build`、`picotool load -f -v -x hardware/pico-tester/build/pico_gpio_tester.uf2`、PWM 機能追加後 `PICO_SDK_PATH=/home/nnyn/.pico-sdk/sdk/2.2.0 cmake -S hardware/pico-tester -B hardware/pico-tester/build -G Ninja -DPICO_BOARD=pico` と再ビルド・再書き込み。双方で picotool verify OK。書込み後は `hardware/pico-tester/measure.py` の `discover(30)` で再認識を待ち、pyserial で下記コマンドを実行。
- 実測（最終ファームウェア）: `GPIO_LOOPBACK` GP16→GP17 および逆方向で High/Low を100 ms、各期待した論理値が100点で反対値0点。GP16→GP17 Low 10 ms は10点、High 2000 ms は1999点すべて期待どおり。同一ピンは `ERR CONFLICT`、2001 ms は `ERR INVALID`、無変化の GP16 に対する `GPIO_PULSE 16 100` は `ERR TIMEOUT`。`RESET_SAFE` 後 `GPIO_STATE` は両ピンとも output=0、pull_up=0、pull_down=0。
- 中断: `GPIO_DRIVE 16 1 2000` を送り約200 ms後に pyserial の CDC 接続を閉じ、約450 ms後に開いて状態を読むと GP16 は output=0、pull_up=0、pull_down=0。これはホストの CDC 接続終了の試験で、USB ケーブル物理抜去ではない。外部計測器による駆動停止時刻の観測は未実施。
- PWM loopback: `GPIO_SELFTEST_PWM 16 17` の 100 Hz 指定で duty 10/25/50/75/90% は period 10000 µs、high 幅 1000/2500/5000/7501/9000 µs。逆方向 50% は period 10000 µs、high 4999 µs。同一ピンと duty 9% はエラー。発生と測定は同じ Pico のクロックを共有するので独立した校正ではない。
- 失敗: 予期しない失敗なし。意図的な不正・timeout は上記のとおり。
- 未確認: 他の周波数・高速度・精度限界、電気的な安全状態と physical USB 抜去、watchdog/reset 中、DUT 側出力刺激、UART/I2C/SPI。Pico は v2 GPIO 試作を実行中、旧 v1 とは互換なし。
