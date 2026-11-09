# tkey（標準ch32fun、CH32V006専用）

ADC の TKEY で PD4（ch7）と PA2（ch0）を読み、`tkey pd4=<n> pa2=<n>` を 500 ms ごとに USART1（PD5）に出す。充電時間 `IDATAR1` = 0x20、放電時間 `RDATAR` = 0x8 は WCH SDK 版（`../../samples_ch32v006_wch/tkey/`）と同じ。値の参考観測のみで合否は付けない（マトリクスは `build-only`）。CH32V002 を指定すると `#error` で build が止まる。

```sh
make -C samples_ch32v00x_ch32fun/tkey build PREFIX=riscv64-unknown-elf TARGET_MCU=CH32V006
```

観測状態: **build-only**（値の参考観測のみ。PD4≈4082、PA2≈52。PD4 のリードを指で触ると下がり離すと戻ることを手作業で 1 回確認、記録は `../okf/log/2026-11-09-2056-ch32v006-only-ch32fun-samples.md`）。
