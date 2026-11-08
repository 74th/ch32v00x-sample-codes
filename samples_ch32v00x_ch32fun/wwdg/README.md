# wwdg（標準ch32fun、CH32V002/CH32V006共通）

WWDG（ウィンドウウォッチドッグ）を、固定 `externals/ch32fun` のレジスタ定義（`WWDG->CTLR`/`CFGR`、`RCC->PB1PCENR`）で操作するサンプル。**書籍にない内容**で、`hil/matrix_ch32v00{2,6}.json` では書籍由来でない行として扱う。動作・窓・分周・`-DWWDG_MODE`（0 窓の内側でフィード、1 早すぎるフィード、2 フィードしない）・UART の出力（PD5）は、WCH SDK 版（`../../samples_ch32v002_wch/wwdg/README.md`）と同じ。

```sh
make -C samples_ch32v00x_ch32fun/wwdg clean TARGET_MCU=CH32V002
make -C samples_ch32v00x_ch32fun/wwdg build PREFIX=riscv64-unknown-elf TARGET_MCU=CH32V002 EXTRA_CFLAGS=-DWWDG_MODE=1
```

観測状態: CH32V002 は **hil-verified**（`tests/hil/test_wwdg.py`、3ビルド、記録は `../../okf/log/2026-11-09-0013-add-wwdg-sample.md`）。CH32V006 も **hil-verified**（同じ試験、記録は `../../okf/log/2026-11-09-0751-ch32v006-wwdg-hil.md`）。未確認の項目（EWI、デバッグ中の動作、リセット時間の絶対精度）は WCH SDK 版と同じ。
