# tim3（標準ch32fun、CH32V006専用）

TIM3（SLTM）の CC3 の DMA 要求で DMA1 チャネル 1 を動かし、PC0 を 500 Hz で反転する（ATRLR 47999、HCLK 48 MHz）。動作は WCH SDK 版（`../../samples_ch32v006_wch/tim3/`）と同じ。CH32V002 を指定すると `#error` で build が止まる。

固定 ch32fun（`b28d285`）は `TIM3` を `ALTM_TypeDef` として宣言するが、その型はどのヘッダにも定義がなく `TIM3->…` はコンパイルできない。そのためサンプル内に RM 第13章 Table 13-2 のレジスタ構造体（16 ビットのレジスタが 4 バイト間隔）を定義して `TIM3_BASE` に当てている。固定 ch32fun は変更しない。ch32fun を更新したら見直す。

```sh
make -C samples_ch32v00x_ch32fun/tim3 build PREFIX=riscv64-unknown-elf TARGET_MCU=CH32V006
```

観測状態: CH32V006 は **hil-verified**（`../../tests/hil/test_v006_only_ch32fun.py`、記録は `../okf/log/2026-11-09-2056-ch32v006-only-ch32fun-samples.md`）。
