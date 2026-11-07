# PWM 自己テスト、GPIO_SEQUENCE 自己テスト、watchdog/sleep HIL、全 HIL 一括

- 目的: PWM 生成・測定、GPIO_SEQUENCE の cancel/timeout、watchdog/sleep の実機観測を確認し、全 HIL を単一コマンドで実行して統合受け入れ（タスク 8.1/8.2/9.x/10.2）を確認する。

- 作業日時: 2026-11-07 約18:27–18:40 JST（各コマンドの開始時刻は未記録）。記録は 18:46 以降。
- 配線・ツール: 同日の `2026-11-07-1845-spi-loopback-and-hil.md` と同じ。PWM 自己テストは GP16→GP18（SPI loopback 配線へ変更する前、I2C loopback 配線が残っていた時点）。それ以外の DUT 試験は既存固定配線。
- ソース（未コミット、SHA-256 先頭16桁）: `pwm_selftest.py` `352f834631c323a4`、`sequence_selftest.py` `e7ec90f2d39bb275`、`tests/hil/test_pwm.py` `46bdcd8c3e03c1e6`、`tests/hil/test_watchdog.py` `f92fdaabe6113d1c`、`timer_pwm/main.c` `40a09828a9a16ea7`、`watchdog/main.c` `712f7e37ba0495c0`、`sleep_wake/main.c` `edaa92356f511c16`。
- PWM 自己テスト（実測）: `uv run python hardware/pico-tester/pwm_selftest.py --port <Pico>`。100 Hz と 10 kHz、duty 10/50/90% で period 10000/10000/10000 µs と 100/100/99 µs、duty 100000〜909090 ppm。許容は period ±5%、duty ±3 ポイントで全 PASS。不正（duty 9/91、1 kHz、同一ピン、入力側 GP18 を出力指定）は ERR。終了後 GP16〜19 は安全。同一 Pico 時計での測定なので周波数の独立校正ではない。
- GPIO_SEQUENCE 自己テスト（実測）: `uv run python hardware/pico-tester/sequence_selftest.py --port <Pico>`。入力 GP5 で 300 点・約3 s の完走、0.5 s 後の `!` で `ERR CANCELED host_request`（1 s 以内）、観測中の他入力で `ERR INVALID busy_input`、範囲外引数の拒否、`RESET_SAFE` 後の安全状態を確認。物理 USB 抜去・Pico 再起動中の挙動は未確認（firmware は切断時に安全状態へ戻る設計だが実測していない）。
- timer_pwm HIL（実測）: DUT PD2→GP14 で period 1000 µs、duty 249000 ppm、許容 800〜1200 µs・20〜30% 内で 1 passed。
- watchdog HIL: 初回は `3+6` ではなく 12 パルスで失敗した。readback 時点で DUT が前回シーケンスの途中にあり、その残りを観測したと推定（未検証の推定）。`tests/hil/test_watchdog.py` の観測前に 4.5 s の待機を追加後、3 回連続で 3 パルス・約1.1 s の Low・6 パルスの署名を確認（passed）。sleep_wake HIL（PC0 の約500 ms 周期のトグルを既存の blink 解析で判定）は成功。消費電流や WFI に入っていることは観測していない。
- 異常: SPI 配線変更の直後、全 DUT HIL が `minichlink exit code 224` で失敗した。そのとき WCH-LinkE が `lsusb` に存在しなかった。ユーザーが再接続（詳細不明）後、`lsusb` で `1a86:8010` が Device 061 として再出現した。`./scripts/ch32fun.sh flash ch32v003` は CH32V003 検出・書き込み成功。消えた原因は未特定（ユーザー申告では minichlink -i で認識）。
- 全 HIL（実測）: マーカー gpio（3）、uart、i2c（2）、spi、adc、pwm、watchdog（2）を個別に実行しすべて passed。続けて `uv run pytest --hil -q --hil-port=/dev/serial/by-id/usb-Raspberry_Pi_Pico_E661AC8863223539-if00` で **91 passed**（単体 80 + HIL 11）、約40 s。
- 注意（実測）: `--hil-port <パス>` の空白区切りだと、パス引数が探索パスとして解釈され conftest が読まれず `unrecognized arguments` になる。パス指定なしで一括実行する場合は `--hil-port=<パス>` を使う。
- 未確認: 電圧・波形、watchdog 周期の絶対精度、sleep 中の消費電力、クリーン checkout からのコマンド再現。

## 追記: 書き込み前の検出待ち（記録 2026-11-07 18:5x JST、時刻は未記録）

- ユーザー申告: 配線は繋ぎ直していない。USB が不安定なのではないかとの見立てで、「いつも少し待つように」依頼された。上記の WCH-LinkE 消失の原因は引き続き未特定（USB 不安定は推定）。
- 変更: `ch32hil/dut.py` の flash/readback/reset の前に `minichlink -i` で WCH-Link と期待チップの検出を最大20 s、1 s 間隔で待つ（`Dut.ready_timeout`）。リトライは検出のみで、書き込み自体は再試行しない。別チップは即失敗、時間切れは段階名付きで失敗。
- 実測: 単体テスト（リトライ成功・時間切れ・別チップ拒否を追加）20 passed。待機が実際に発動する USB 切断状況は再現していない。
- 実測（副作用）: 検出待ちを reset の前にも入れた直後、watchdog HIL が 3 回とも「10 パルス」で失敗した。`reset` の前に走る `minichlink -i` で DUT のリセットが遅れる、またはプローブが DUT に影響する、のいずれかと推定（切り分けていない）。watchdog テストでは観測前に `wait_ready` を済ませ `reset(wait=False)` にして解消し、3 回連続 passed。
