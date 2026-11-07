# CH32V002F4P6 の build → flash → measure

この手順は [CH32V003 の再現手順](ch32v003-reproduction.md) と同じホスト、固定 ch32fun、Pico と PC0 の観測経路を使う。電源・配線は [配線案](wiring.md) を確認する。F4P6 の PC0=10番、PA1=5番、VSS=7番、VDD=9番、SWIO=18番は CH32V003F4P6 と同じ。今回の開発ボードはユーザー申告でピン互換。

```sh
./scripts/ch32fun.sh check
./scripts/ch32fun.sh build ch32v002
./scripts/ch32fun.sh flash ch32v002
python3 hardware/pico-tester/measure.py
```

書き込みは既存ファームウェアを上書きする。現在の submodule の minichlink は WCH-LinkE firmware 2.22 で CH32V002 と 16 KB を正しく報告した。スクリプトは書き込み前に `0x1ffff704` の識別値の型番部分が `0x002` であることも確認する。旧 minichlink の誤表示については過去の実機記録を参照。

CH32V003 からの主な変更: `TARGET_MCU=CH32V002`、16 KB Flash / 4 KB RAM、`HSI_VALUE=24000000` と既定 PLL、PC0 の MODE を 1 にする。GPIO MODE の根拠は [資料照合](../okf/peripherals/gpio/cfglr-mode-field.md)。差分・ビルドは [作業ログ](../okf/log/2026-11-07-1130-ch32v002-port-build.md)を参照。

2026-11-07、build・write・1060バイトの読み戻し一致・リセット後の起動ログ・Pico 測定 PASS を確認した。詳細と条件は [実機記録](../okf/log/2026-11-07-1156-ch32v002-flash-measure.md) を参照。測定は約10 ms間隔であり精密な周波数検証ではない。別環境での再現は未確認。

上記は旧 ch32fun での記録。新 submodule `b28d285` では成果物 1068 bytes、書き込み後 Pico PASS を確認したが読み戻しは未実施。詳細は [移行ログ](../okf/log/2026-11-07-1330-standalone-ch32fun.md)。
