# CH32V003 sleep/wake サンプル build

- 作業・記録日時: 2026-11-07 17:17 JST（終了時刻未記録）。
- 目的: TIM1 割り込みによる WFI 復帰を GPIO で観測する標準 ch32fun サンプルを準備する。
- ソース・ツール: `samples_ch32v003_ch32fun/sleep_wake/main.c`、book-code `sleep_mode_blink-register` の意図を参照し独自に実装。固定 `externals/ch32fun` revision `b28d285460ce052a179dba8f4a22c6f73ff8e328`、riscv64-unknown-elf-gcc 14.2.0。実験後ソース SHA-256 `edaa92356f511c1679858c5e379e4ef58ad1afe9ade53bdc78dbfadc91eb3b9e`。
- コマンド: `make -C samples_ch32v003_ch32fun/sleep_wake build PREFIX=riscv64-unknown-elf`。
- 結果: build 成功、FLASH 732 B。実機への書き込み・観測は行っていない。
- 失敗: なし。未確認: timer 割り込み・WFI 復帰・PC0 の実機動作と電力消費。GPIO の変化だけでは消費電流の低下を証明しない。
