# CH32V002F4P6 の build → flash → measure

この手順は [CH32V003 の再現手順](ch32v003-reproduction.md) と同じホストと固定 ch32fun を使う。電源・配線は [配線案](wiring.md) を確認する。F4P6 の PC0=10番、PA1=5番、VSS=7番、VDD=9番、SWIO=18番は CH32V003F4P6 と同じ。今回の開発ボードはユーザー申告でピン互換。

```sh
./scripts/ch32fun.sh check
./scripts/ch32fun.sh build ch32v002
./scripts/ch32fun.sh flash ch32v002
```

下記の記録で使った `python3 hardware/pico-tester/measure.py` は、v1 firmware と PC0–GP0 配線専用である。現在の Pico は protocol v2 firmware と固定配線（PC0–GP5）なので、そのままでは使えない。CH32V002 の Pico 観測は、デバイスを選択した HIL で行う（[HIL 設定](../hil/README.md#対象デバイスの選択)）。

```sh
uv run pytest --hil --hil-device ch32v002 -q tests/hil --hil-port=/dev/serial/by-id/<PicoのID>
```

2026-11-07 の実機で、GPIO、UART、I2C master/slave、SPI、PWM、ADC、watchdog、sleep の 11 テストが成功した（機能確認のみ。条件・ADC のトリガ設定の差分・未確認事項は [実測ログ](../okf/log/2026-11-07-1926-ch32v002-hil.md)）。別環境での再現は未確認。

## DUT の差し替え

CH32V003F4P6 から CH32V002F4P6 へ DUT を替えるときの手順。人が行う作業で、自動化しない。DUT は一度に一つだけ接続する。

1. Pico と WCH-LinkE の USB を抜く。WCH-LinkE の通常操作は DUT へ 3.3 V を出力する場合があるため、DUT を外す前に必ず抜く。
2. Pico の信号線と DUT の信号線を接続したまま DUT を抜き差ししない。DUT 側の電源が切れていることを確認する。
3. DUT を CH32V002F4P6 に交換する。ピン 1 の向きと、VDD=9番、VSS=7番、SWIO=18番を目視で確認する。固定配線の変更は不要（[根拠](../okf/peripherals/ch32v002-port-differences.md)）。
4. WCH-LinkE だけを接続し、VDD–VSS が 3.3 V（公称）、SWIO–VSS が 0 V であることをテスターで確認する。値を記録する。
5. `./scripts/ch32fun.sh flash ch32v002` の検出確認が通ることを確認する（`Detected CH32V002` と、識別領域 `0x1ffff704` の型番 `0x002`）。DUT が CH32V003 のままだとここで失敗する。
6. Pico を接続し、安全状態（出力なし・プルなし）を確認してから HIL を実行する。最初の HIL は GPIO（`-m 'hil and gpio'`）とする。

CH32V002 で異なる点（資料確認。[詳細](../okf/peripherals/ch32v002-port-differences.md)）: Flash 16 KB / RAM 4 KB、GPIO の MODE が 1 ビット、ADC が 12 ビットで校正ビットなし、AFIO_PCFR1 のレイアウトが異なる（本構成では書かない）。

書き込みは既存ファームウェアを上書きする。現在の submodule の minichlink は WCH-LinkE firmware 2.22 で CH32V002 と 16 KB を正しく報告した。スクリプトは書き込み前に `0x1ffff704` の識別値の型番部分が `0x002` であることも確認する。旧 minichlink の誤表示については過去の実機記録を参照。

CH32V003 からの主な変更: `TARGET_MCU=CH32V002`、16 KB Flash / 4 KB RAM、`HSI_VALUE=24000000` と既定 PLL、PC0 の MODE を 1 にする。GPIO MODE の根拠は [資料照合](../okf/peripherals/gpio/cfglr-mode-field.md)。差分・ビルドは [作業ログ](../okf/log/2026-11-07-1130-ch32v002-port-build.md)を参照。

2026-11-07、build・write・1060バイトの読み戻し一致・リセット後の起動ログ・Pico 測定 PASS を確認した。詳細と条件は [実機記録](../okf/log/2026-11-07-1156-ch32v002-flash-measure.md) を参照。測定は約10 ms間隔であり精密な周波数検証ではない。別環境での再現は未確認。

上記は旧 ch32fun での記録。新 submodule `b28d285` では成果物 1068 bytes、書き込み後 Pico PASS を確認したが読み戻しは未実施。詳細は [移行ログ](../okf/log/2026-11-07-1330-standalone-ch32fun.md)。
