---
type: Device Difference
title: CH32V003 サンプルを CH32V002F4P6 へ移植するときの差分と固定配線の照合
description: 固定配線 17 ネットが CH32V002F4P6 で成立するかの資料照合と、周辺機能サンプル 9 件の移植差分。資料確認と実機確認を区別する。
tags: [porting, wiring, adc, timer, gpio]
devices: [CH32V003, CH32V002]
evidence: document
status: draft
generated: { by: claude-code/claude-sonnet-5-5, at: 2026-11-07T10:30:00Z }
sources:
  - id: v002-ds
    resource: /sources/ch32v002-datasheet.md
    title: CH32V002 データシート V1.7
  - id: v00x-rm
    resource: /sources/ch32v00x-reference-manual.md
    title: CH32V00X リファレンスマニュアル V1.5
---

# 前提

- 資料のページは `PDF p.N`（通しページ）。データシートの印字ページは PDF−2。
- 区分: **資料確認**（資料にその記載がある）、**推定**（資料と ch32fun ヘッダからの推論）、**実機確認**（CH32V002F4P6 での HIL 成功、機能確認のみ。[ログ](../log/2026-11-07-1926-ch32v002-hil.md)）。
- 照合は非公開の変換資料を読んで行った。本文は引用せず、事実とページだけを記録した。
- ch32fun は固定 submodule の `ch32x00xhw.h`（CH32V002 では `-DCH32V00x=1`）を使う。

# 固定配線の照合（タスク 2.1）

結論: CH32V003F4P6 の固定配線は、CH32V002F4P6 でもピン番号・機能とも成立する（資料確認）。配線変更は不要で、`hardware/wiring-proposal.md` の変更案はない。

| ネット | DUT ピン | CH32V002 での機能 | 根拠 |
| --- | --- | --- | --- |
| BLINK / 同期 | PC0 (10) | 汎用 GPIO、SPI の CS は GPIO で駆動 | DS PDF p.16–19 |
| I2C_SDA / SCL | PC1 (11) / PC2 (12) | I2C1 既定（I2C1_RM=000） | DS p.17、RM PDF p.80 |
| SPI_SCK / MOSI / MISO | PC5 (15) / PC6 (16) / PC7 (17) | SPI1 既定（SPI1_RM=000）。NSS の既定は PC1 | DS p.18、RM p.80 |
| UART_TX / RX | PD5 (2) / PD6 (3) | USART1 既定（USART1_RM=0000） | DS p.16、RM p.79 |
| PWM_CH1 / CH4 | PD2 (19) / PC4 (14) | TIM1_CH1 / CH4 既定（TIM1_RM=0000） | DS p.17–18、RM p.78 |
| ADC_A0 / A1 | PA2 (6) / PA1 (5) | ADC_IN0 / IN1 | DS p.16、p.20 |
| SWIO | PD1 (18) | SWIO 既定。SDI は reset 後に有効 | DS p.12、p.18 |
| 電源 | VSS 7、VDD 9 | VDD 2.0–5.5 V（ADC は 2.4 V 以上） | DS p.1、p.8 |

- **SPI NSS を PC0 へリマップする件**: 固定配線の「NSS→PC0」は、V003 のサンプルでも SPI の NSS をハードウェアでは使わず、PC0 をソフトウェア CS（GPIO）として駆動している。したがって AFIO のリマップを書く必要がない。CH32V002 でも同様に PC0 を GPIO として使う。資料確認（SPI1 の NSS 既定は PC1 で、I2C の SDA と共有するが、SSM=1 で NSS ピンを使わない構成のため競合しない。この SSM の判断は推定）。
- **AFIO_PCFR1 のレイアウトは V003 と異なる**（TIM1_RM は bit 13:10、PA1PA2_RM は bit 17 など。RM PDF p.85–87）。9 件のサンプルは AFIO を書かないので影響はない。リマップを使う将来のサンプルでは V003 の値を流用しない。
- PD7 は既定で TIM2_CH4/RST（DS p.12、p.16）。固定配線では使わない。PD1 は SWIO のため試験に使わない（`config.py` が禁止）。
- 開発ボードのピン互換は、これまでどおりユーザー申告。

# 共通の差分

| 項目 | CH32V003 版 | CH32V002 版 | 区分 |
| --- | --- | --- | --- |
| `TARGET_MCU` | `CH32V003` | `CH32V002`（Makefile）。生成リンカスクリプトは `generated_ch32v002.ld` | 資料確認 |
| クロック | HSI 24 MHz、PLL ×2 → 48 MHz | HSI 24 MHz、固定 ×2 の PLL、最大 48 MHz。`funconfig.h` で `HSI_VALUE 24000000`（ch32fun の `FUNCONF_SYSTEM_CORE_CLOCK` は 48 MHz になる、ヘッダ読み） | 資料確認＋推定 |
| GPIO MODE | 2 ビット（出力速度） | 1 ビット（1=出力）。`GPIO_Speed_10MHz`(=1) は MODE ビットを立てるので動く。`GPIO_Speed_2MHz`(=2) は予約ビットのみで入力になるため使わない | 資料確認（RM PDF p.81–82）、[cfglr-mode-field.md](gpio/cfglr-mode-field.md) |
| フラッシュ待ち | 1 | 25 MHz 超で 2（ch32fun が設定） | ヘッダ読み |

「変更不要」と判断した根拠は、サンプルごとの次の節に書く。

# サンプル別

## blink_and_read（GPIO）

- 差分: `funPinMode(PC0, 1 | GPIO_CNF_OUT_PP)`（MODE が 1 ビットのため）、起動メッセージ。
- 変更不要の部分: PA1 の入力は `GPIO_CNF_IN_*` のみで MODE=0 に対応する。
- 既存の手動確認ログ: `okf/log/2026-11-07-1156-ch32v002-flash-measure.md`。自動 HIL は未実施。

## uart

- コード変更なし。`BRR = HCLK / baud`（DIV_M [15:4] + DIV_F [3:0]）は V003 と同じ式（資料確認、RM PDF p.192、p.198）。48 MHz / 115200 の丸めは V003 と同じ計算。
- 実機: HIL で機能確認済み（[ログ](../log/2026-11-07-1926-ch32v002-hil.md)）。

## i2c_master / i2c_slave

- コード変更なし。CTLR2.FREQ[5:0] は 8–48 MHz を許容し 48 が有効、CKCFGR.CCR は 12 ビットで 240 が入る（RM PDF p.213、p.218）。100 kHz、標準モード。
- 実機: HIL で機能確認済み（[ログ](../log/2026-11-07-1926-ch32v002-hil.md)）。

## spi_master

- コード変更なし。CTLR1.BR の符号化は同じで、`BR=0b101`（/64）は 48 MHz / 64 = 750 kHz。V00x で追加の `HSRXEN` は reset 値 0 のまま使わない（RM PDF p.228、p.232）。
- 実機: HIL で機能確認済み。mode 不一致の検出は CH32V003 と同じく Pico 側の制限で行わない。

## timer_pwm

- 差分: ch32fun の V00x ヘッダには `TIM_CEN` などの短い名前がなく、`TIM1_CTLR1_CEN`、`TIM1_SWEVGR_UG`、`TIM1_CTLR1_ARPE`、`TIM1_CCER_CC1E`、`TIM1_BDTR_MOE`、`TIM1_CHCTLR1_OC1M_1/2`、`TIM1_CHCTLR1_OC1PE` を使う。ビット値は同じ（ヘッダを grep で確認）。
- PSC = 48 − 1 で 1 MHz、ATRLR = 999 で 1 kHz、CH1CVR = 250 で 25 %。レジスタ名とアドレスは同じ（RM PDF p.133）。HIL の許容範囲（周期 800–1200 µs、デューティ 20–30 %）は CH32V003 の値を流用する。クロック前提（48 MHz）が同じ式で成立するため。
- 実機: HIL で機能確認済み（[ログ](../log/2026-11-07-1926-ch32v002-hil.md)）。

## adc

- 差分 1: 分解能は **12 ビット**（V003 は 10 ビット）。結果マスクは `0x3ff` → `0xfff`（RM PDF p.100、p.103）。Pico 治具のファームウェア（`hardware/pico-tester/adc_fixture.c`）は報告値が 1023 を超えると捨てるため、サンプルは 12 ビット結果を `>> 2` した 10 ビット相当を送る。治具のファームウェアは変更していない（実測: `>> 2` なしの最初の実行は、DUT 側の問題と合わせて ADC_OBSERVE が TIMEOUT になった。治具側の 1023 上限が単独で原因かどうかは切り分けていない）。
- 差分 2: **RSTCAL / CAL ビットがない**（CTLR2 の bit 3:2 は予約、RM PDF p.112）。ch32fun のヘッダにはマクロが残るが、キャリブレーションの手順は削除した（実機で変換は動作した）。
- 差分 3（**実測で判明、資料からは読み取れていなかった**）: ソフトウェアトリガ（`EXTSEL=111`＋`SWSTART`）でも `CTLR2.EXTTRIG`（bit 20、`ADC_EXTTRIG`）を立てる必要がある。立てないと SWSTART を書いても変換が 1 回おきにしか完了せず、`EOC` を待つループが止まった。診断用ビルドの SWIO printf で、`EXTTRIG` なしは `STATR=0x3f10`（`EOC` なし）で 200 万回のポーリングが尽き、`EXTTRIG` ありは毎回 34 回前後で `EOC` が立つことを確認した（2026-11-07、`okf/log/2026-11-07-1926-ch32v002-hil.md`）。`ADC_LP`（CTLR3 bit 0）を 0 にしても改善しなかった。
- 差分 4: SAMPTR2 の SMP0=7 は 239.5 サイクル（V003 は 241、RM PDF p.113）。ADC 電源は低消費電力モードが既定（CTLR3.ADC_LP、RM PDF p.118）。サンプルは既定のまま使う。
- 変更不要: ADCPRE を 0 にして HCLK/2（24 MHz）。範囲内（DS p.38、RM PDF p.34–35）。
- 実機確認: PWM デューティ 10/20/50/80/90 % で報告値 91/192/497/805/907（単調増加）。電圧と精度は主張しない。

## watchdog

- コード変更なし。IWDG は PR=3（/32）、RLDR=4000、LSI 約 128 kHz（90–172 kHz の範囲、DS p.29）で約 1 s。鍵と `RCC_IWDGRSTF`（RSTSCKR bit 29）、`RCC_RMVF`（bit 24）は V003 と同じ（RM PDF p.40–45）。HIL は 3 パルス＋6 パルスの署名と間隔だけを確認し、周期の精度は測らない。LSI の範囲が広いため、周期の絶対値は主張しない。
- 実機: HIL で機能確認済み（[ログ](../log/2026-11-07-1926-ch32v002-hil.md)）。

## sleep_wake

- 差分: `TIM_*` マクロを `TIM1_*` に置換（timer_pwm と同じ）。`TIM1_UP_IRQn = 35`（RM PDF p.52、ヘッダ確認）、`PFIC->SCTLR` の SLEEPDEEP=bit 2、WFITOWFE=bit 3（RM PDF p.68）は同じ。PSC = 48000 − 1 は 16 ビットに収まる。
- sleep 中の電流は測らない。実機: HIL で機能確認済み。

# 未確認

- 実機確認（機能確認のみ）は 9 サンプルの HIL 成功で、`okf/log/2026-11-07-1926-ch32v002-hil.md` に記録した。個別の「実機未確認」の記述は、この記録の時点で HIL が成功したものについては機能確認済みに読み替える。電圧・波形・クロックの精度は未確認。
- `GPIO_Speed_*` の `2MHz`/`50MHz` の挙動は推定で、サンプルでは `10MHz`(=1) だけを使う。
