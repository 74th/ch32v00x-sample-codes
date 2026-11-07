# CH32V003 GPIO 観測記録（暫定）

2026-11-07、WCH-LinkE firmware 2.9 が CH32V003 を検出。ユーザーは対象型番を CH32V003F4P6 と確認。ユーザーの申告では DUT の電源は WCH-LinkE の 3.3 V、PC0 の High 電圧は 3.1 V、PC0 と Pico GP0 の間には 1 kΩ の直列抵抗があります。`-t` による出力停止後の VDD–VSS 間は 0.606 V（ユーザー実測）。残留電圧の経路と電源断前の信号線切り離し方法は未確認です。配線レビュー完了とは扱いません。

- ソース: book-code `4ce0a1b2fe0fa771e68e17944c4ce0d9b20924ae` の `blink_and_read-ch32fun` を基にした `samples/ch32v003/blink_and_read`。ch32fun `2679ac059f3ada402731e5a10818cc0814e9ec4c`。
- ビルド: `./scripts/ch32fun.sh build`。RISC-V GCC 14.2.0、GNU Make 4.4.1、Ubuntu 26.04 x86-64。`main.bin` 1056 bytes、SHA-256 `2edca10fa40bac56fa2131db88eeb1b47199408413ee2b2a85d42a1c12d83783`。
- 書き込み: `./scripts/ch32fun.sh flash` が `Image written` と成功を報告。その後 `minichlink -T` で `blink_and_read started` と `PC0 high` / `PC0 low` の繰り返しを取得。別途 11:13 に読み戻し照合を実施した。
- GPIO 観測: 人間が PC0 に接続した抵抗付き LED の点滅を確認。Pico の GP0 を用いた `python3 hardware/pico-tester/measure.py` は PASS、完全区間は 49〜50 サンプル。測定間隔は約 10 ms。PC0 High は 3.1 V（ユーザー実測）、Pico GP0 との間は 1 kΩ（ユーザー申告）。
- 電源制御確認: 固定 minichlink の `-t` 実行後、Pico の300サンプルはすべて Low で MISMATCH。続く `-3` 実行後は High/Low とも完全区間50サンプルで PASS に戻った。これは PC0 の観測であり、その時点の DUT VDD は測定していない。
- 別の停止時に VDD–VSS 間をユーザーが測定し 0.606 V を確認した。今回の GPIO 観測では供給経路の切り分けを行わない。PC0 の Low は CPU 停止を直接証明せず、完全な電源遮断が必要な用途には使えない。
- 配線案と安全上の確認項目は [wiring.md](wiring.md)。測定方法と許容範囲は [Pico 観測手順](pico-tester/README.md)。
- 11:13 の再検証では flash 読み戻し一致、再起動ログ、Pico 測定 PASS を確認。詳細は [作業ログ](../okf/log/2026-11-07-1113-ch32v003-flash-readback-measure.md)。

対象型番はユーザーによる確認です。電源と配線の未確認事項は残っています。
