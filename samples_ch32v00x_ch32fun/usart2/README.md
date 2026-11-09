# usart2（標準ch32fun、CH32V006専用）

USART2 の TX をリマップ 3（`AFIO_PCFR1.USART2_RM` = 011）で PD2 に出し、`usart2 0123456789\r\n` を 200 ms ごとに 115200 8N1 で送る。**書籍にない内容**で CH32V006 だけに USART2 がある。固定 `externals/ch32fun` の `USART2`、`RCC_USART2EN`、`AFIO_PCFR1_USART2_RM_*` だけで書く。動作・ピンは WCH SDK 版（`../../samples_ch32v006_wch/usart2/`）と同じ。CH32V002 を指定すると `#error` で build が止まる。

```sh
make -C samples_ch32v00x_ch32fun/usart2 build PREFIX=riscv64-unknown-elf TARGET_MCU=CH32V006
```

観測状態: CH32V006 は **hil-verified**（`../../tests/hil/test_v006_only_ch32fun.py`、記録は `../okf/log/2026-11-09-2056-ch32v006-only-ch32fun-samples.md`）。
