# CH32V002 サンプル 8 件の移植と build（Issue #11 前半）

- 作業日時: 2026-11-07 19:1x–19:20 JST。開始時刻は記録していない。終了は `date` で取得した。
- 目的: `automate-ch32v002-ch32fun-hil` のタスク 2.1、3.1、3.2、4.1、5.1、6.1、7.1、7.3、8.1。固定配線の資料照合と、`uart`、`i2c_master`、`i2c_slave`、`spi_master`、`timer_pwm`、`adc`、`watchdog`、`sleep_wake` の移植・build。
- 条件: 実機は操作していない。flash・読み戻し・実行観測はしていない。build のみのため、すべて**実機未確認**。ソースは `samples_ch32v003_ch32fun/<sample>/main.c`、ツールは固定 `externals/ch32fun`（`b28d285`）と `riscv64-unknown-elf` GCC。

## 資料照合

CH32V002 データシート V1.7 と CH32V00X リファレンスマニュアル V1.5 の変換資料を subagent が読み、事実とページ番号を報告した。要点と区分は [okf/peripherals/ch32v002-port-differences.md](../peripherals/ch32v002-port-differences.md) に記録した。subagent の報告は model 出力であり、私は資料を直接読み直していない。ch32fun ヘッダのマクロ名は自分で grep して確認した。

- 固定配線 17 ネットは、ピン番号・既定の周辺機能とも CH32V003 と同じで成立する（資料確認、subagent 報告）。配線変更案はない。
- サンプルの差分は 3 件。`adc`（12 ビット、RSTCAL/CAL なし）、`timer_pwm` と `sleep_wake`（ch32fun V00x ヘッダに `TIM_*` マクロがなく `TIM1_*` を使う）。

## 実行コマンドと結果（実測）

- 8 サンプルの `make -C samples_ch32v002_ch32fun/<sample> build PREFIX=riscv64-unknown-elf`: すべて成功。成果物サイズは uart 696、i2c_master 948、i2c_slave 772、spi_master 796、timer_pwm 664、adc 824、watchdog 704、sleep_wake 740 bytes。
- 最初の build で、`TIM_*` の置換後にエラーは出なかった（置換前のコードは build していない）。
- `uv run pytest -q`: 113 passed、11 skipped。ADC の値域を `Device.adc_max`（CH32V003 は 1023、CH32V002 は 4095）に分け、`tests/hil/test_adc.py` に反映した。
- `gpio_input` は CH32V003 と同じ理由（固定配線で PC4 を Pico から駆動しない）で移植せず、`hil/matrix_ch32v002.json` に `excluded` として記録した。他の 8 件は `build-only` にした。

## 未確認・残件

- すべてのサンプルの flash、readback、実行観測（HIL）。
- 差し替え手順（タスク 2.3）は `hardware/ch32v002-reproduction.md` と `hardware/wiring-proposal.md` に書いた。ユーザーのレビューが済むまでタスクは完了にしない。
- SPI の NSS が PC1 と共有される点（SSM=1 のため競合しないという判断）は推定。
