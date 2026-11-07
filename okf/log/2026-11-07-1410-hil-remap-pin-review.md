# AFIO を利用した HIL ピン配置の検討

- 作業・記録日時: 2026-11-07 14:10 JST。
- 目的: ADC の RC を他の周辺機能と共有せず、試験ごとの配線切替を減らす案を確認する。
- 条件: CH32V003F4P6、RP2040 Pico、参照 `externals/ch32v003-book-code` revision `4ce0a1b2fe0fa771e68e17944c4ce0d9b20924ae`。回路は未構築、実機や電圧の操作・測定なし。
- コマンド: `rg -n 'AFIO_PCFR1_(I2C|USART|TIM1|SPI)' externals/ch32fun/ch32fun/ch32v003hw.h`、`curl -Ls https://ch32-riscv-ug.github.io/CH32V003/datasheet_en/CH32V003RM.PDF -o /tmp/ch32v003-rm.pdf`、`pdftotext -layout /tmp/ch32v003-rm.pdf /tmp/ch32v003-rm.txt`、`rg -n -i -A 14 'SPI1_RM|SPI1 remap' /tmp/ch32v003-rm.txt`。
- 結果: RM 表 7-11 と AFIO_PCFR1 の記述では SPI1 remap で NSS のみ PC1 から PC0 に移り、SCK/MOSI/MISO は PC5/PC6/PC7 のまま。I2C は PC1/PC2 の既定配線を使える。UART PD5/PD6、PWM PD2/PC4、ADC PA1/PA2 と共存する案を検討。
- 失敗: 既存サンプルのファイル名を `blink_and_read.c` と誤認し `sed` が失敗。回路検討にそのファイルの内容は使っていない。
- 未確認: 実サンプルの remap 対応と SPI NSS 波形、既存 PC0 LED の負荷、GPIO 入力刺激の RC による遅延、電源断時の逆流、Pico ファームウェアと実機自己検証。全ての book-code の無変更実行を意味しない。
