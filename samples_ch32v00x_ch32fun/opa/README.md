# opa（標準ch32fun、CH32V006専用）

OPA を PGA（4 倍または 8 倍）にして PA2→OPA→PD4 とし、ADC で PA2（ch0）と PD4（ch7）を読んで `opa gain=<g> in=<raw> out=<raw>` を USART1（PD5）に出す。WCH SDK 版（`../../samples_ch32v006_wch/opa/`）の `OPA_Unlock`/`OPA_Init`/`OPA_Cmd` が書く値（`CTLR1` は 4 倍で `0x00100B01`、8 倍で `0x00100C01`）を `OPA->…` へ直接書く。値の根拠は `main.c` の冒頭。利得は `-DOPA_GAIN=4|8`（変更時は `make clean`）。CH32V002 を指定すると `#error` で build が止まる。

```sh
make -C samples_ch32v00x_ch32fun/opa build PREFIX=riscv64-unknown-elf TARGET_MCU=CH32V006 EXTRA_CFLAGS=-DOPA_GAIN=8
```

観測状態: CH32V006 は **hil-verified**（`../../tests/hil/test_v006_only_ch32fun.py`、記録は `../okf/log/2026-11-09-2056-ch32v006-only-ch32fun-samples.md`）。
