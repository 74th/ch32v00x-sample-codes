# helper 検証の統合確認（verify-ch32fun-extralibs-with-pico タスク 8.1〜8.3）

- 実行日時（実測）: 2026-11-07 20:39〜20:44 JST（シェルの `date`）。記録は 20:44 頃。
- 目的: CH32V003 へ戻して全 HIL を回し、既存試験に退行がないことを確認し、ドキュメントとマトリクスを実測ログと突き合わせる。
- 条件: DUT の差し替え（CH32V002 → CH32V003）はユーザーが実施（ユーザー申告。実施時刻・電圧測定値は未記録）。Pico は GP19→GP20 の loopback 配線が接続されたまま（ユーザー申告）。ベース `380534f`（作業ツリーにドキュメントの修正のみ）。電圧は未実測。

## 実行と結果（実測）

1. 8.1: `uv run pytest -q`（実機なし）: 201 passed、15 skipped。`openspec validate verify-ch32fun-extralibs-with-pico --strict`: valid。
2. 8.2: `./scripts/ch32fun.sh flash ch32v003`: `Image written.`、`FLASH OK (runtime unverified)`（出力の末尾 6 行のみ確認。HIL の flash 段階で `Detected CH32V003` の検出確認が通った）。続けて `uv run pytest --hil -q -rxXs --hil-port=/dev/serial/by-id/usb-Raspberry_Pi_Pico_E661AC8863223539-if00`（`--hil-device` なし）: **215 passed、1 xfailed**（60.0 秒）。既存の HIL（gpio、uart、i2c、spi、pwm、adc、watchdog/sleep）に失敗なし。xfailed は SSD1306 の helper 既定 1 MHz（参考情報の行）。
3. 参考: V002 でも同じコマンド（`--hil-device ch32v002`）で 215 passed、1 xfailed（[7.2 のログ](2026-11-07-2036-extralibs-ch32v002-hil.md)）。

## 8.3 レビューで直した食い違い

- `hardware/wiring-proposal.md` の 3 行（`i2c_slave-ch32fun`、`i2c_oled-ch32fun`、`neopixel-ch32fun`）が「helper 依存のため対象外」のままだった → 検証サンプルと確認範囲、ログへのリンクに更新。
- `hil/README.md` の「extralibs 依存サンプルは対象外で HIL テストはない」 → 3 つの helper 検証は対象で、実行コマンドと xfail の扱いを追記。
- `spi_master-ch32fun`（`ch32v003_SPI.h`）などその他の extralibs 依存サンプルは今回の対象外のまま（記述は正しいので変更なし）。

## 確認した整合性

- `hil/matrix.json` と `hil/matrix_ch32v002.json` の 3 行はすべて `hil-verified`、各 `evidence` ファイルが存在する（スクリプトで確認）。単体テストのマトリクス整合性検査も通過。
- 実測・ユーザー申告・推定の区別を各ログに記載。`xprivate/` は Git の管理対象外で、本変更のコミットにはパスの言及のみ（RM の本文の転載なし。`git diff` を grep で確認）。
- 未確認事項は README の「ch32fun の helper を使うサンプルの検証状況」に集約。

## 未確認

- 実 OLED の表示、実 LED の発光、I2C 1 MHz、WS2812 のタイミング規格適合、待機 High の原因、電圧・波形、複数回リセットを跨ぐ再現性（README を参照）。
- DUT は CH32V003 に戻った状態で作業を終える。Pico は GP19→GP20 の loopback 配線のまま。
