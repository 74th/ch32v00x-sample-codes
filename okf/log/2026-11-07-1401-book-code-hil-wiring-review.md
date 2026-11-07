# book-code の HIL 配線検討

- 作業日時: 2026-11-07 14:01 JST 前後。記録日時は同日、正確な作業終了時刻は未記録。
- 目的: CH32V003 の参照例に必要な信号を調査し、AFIO リマップを後日の手動試験に分けた配線案を作る。
- 条件: `externals/ch32v003-book-code` revision `4ce0a1b2fe0fa771e68e17944c4ce0d9b20924ae` を参照のみで調査。対象の想定は CH32V003F4P6、RP2040 Pico、WCH-LinkE。配線・電圧・機器の現状は今回測定していない。
- 実行: `rg --files externals/ch32v003-book-code`、各 `*-ch32fun/main.c` と register 版の `rg -n`、`cat` / `sed` による確認、`git -C externals/ch32v003-book-code rev-parse HEAD`。WCH CH32V003 データシートを `curl -Ls https://akizukidenshi.com/goodsaffix/CH32V003.pdf -o /tmp/ch32v003-datasheet.pdf` で取得し `pdftotext -layout` で F4P6 の物理ピンを確認。Pico 公式ピン配置を参照。
- 結果: 構想を `hardware/wiring-proposal.md` に記録。I2C と SPI は PC1 を共有し、GPIO と ADC は PA1 を共有するため排他的切替が必要。book-code の I2C master、UART、PWM の register 例は remap を有効にしており、無 remap の同等サンプルとは区別する。ADC は PA1 と PA2 の2入力。
- 実測: なし。配線案の抵抗・RC・速度・給電条件は提案であって実測値ではない。ユーザー申告による既存構成は `hardware/ch32v003-observation.md` を参照。
- 失敗: なし。未確認: 提案したジャンパと既存回路の実装可否、電圧・波形・RC 出力、Pico の周辺機能と自己試験、KiCad 図面および HIL 設定との照合。
