---
type: Device Difference
title: CH32V002 用 ch32fun サンプル 12 件を CH32V006F8P6 へ再利用するときの差分と判定
description: CH32V002F4P6 と CH32V006（TSSOP20）の資料照合。固定配線のピン互換、メモリ・クロック・周辺機能の差分、12 サンプル別の再利用判定。資料確認と実機確認を区別する。
tags: [porting, wiring, adc, timer, gpio, ch32v006]
devices: [CH32V002, CH32V006]
evidence: document
status: draft
generated: { by: claude-code/claude-sonnet-5-5, at: 2026-11-08 }
sources:
  - id: v006-ds
    resource: /sources/ch32v006-datasheet.md
    title: CH32V006 データシート V2.0（CH32V006DS0-EN）
  - id: v002-ds
    resource: /sources/ch32v002-datasheet.md
    title: CH32V002 データシート V1.7
  - id: v00x-rm
    resource: /sources/ch32v00x-reference-manual.md
    title: CH32V00X リファレンスマニュアル V1.5
---

# 前提と区分

- ページは `PDF p.N`（通しページ）。非公開の変換資料を読んで照合した。本文は引用せず、事実とページだけを記録する。
- 区分: **資料確認**（資料にその記載がある）、**推定**（資料・ch32fun ヘッダ・サンプルコードからの推論）、**未確認**（資料で確かめられていない）。実機での確認はこの文書の範囲外で、`hil/matrix_ch32v006.json` と `okf/log/` に別に残す。この時点で CH32V006 の**実機確認は一つもない**。
- ユーザー申告: 手元の DUT は CH32V006F8P6。

# 最重要の未確認: 「F8P6」という型番

既存の記録: [CH32V006 TSSOP20品の型番](../devices/ch32v006-tssop20-part-number.md)（刻印は F8P6、V2.0 の表には F8P7 のみ。仮説は温度グレード違い）。

- V006 データシート V2.0 の製品表（PDF p.2）、ピン配置（p.16）、パッケージ表（p.56 以降）に載っている TSSOP20 品は **CH32V006F8P7**（105℃品）で、**F8P6 という型番は見つからない**。同表の他の `…6` 品は 85℃品（F4U6 や E8R6）なので、F8P6 は 85℃品の TSSOP20 と推測できるが、これは**推定**であり資料確認ではない。
- したがって次の 3 点を前提にせず、実物の刻印と購入元の表記で確認する（タスク 1.2）。
  1. F8P6 が F8P7 と同一ダイ・同一ピン配置か（推定: 温度グレード違い）。
  2. 識別領域 `0x1ffff704` の読取値が型番 `0x006` を示すか（タスク 1.3、実機）。
  3. 手元の個体が V005 や他の品でないこと（V005F6P6 も TSSOP20 で、Flash 32K/RAM 6K の別品。同 p.2）。
- 以降の表の「V006 TSSOP20」は、資料にある **F8P7 のピン定義**を F8P6 に当てはめた仮置きである。

# 固定配線のピン互換（資料確認、F8P7 として）

V006F8P7 の物理ピン（データシート PDF p.16 の図と、ピン定義表 PDF p.19–24）は、`ch32hil/devices.py` の `_TSSOP20`（V003F4P6/V002F4P6）と全 20 ピンで同じ番号・同じポート名。VSS=7、VDD=9、SWIO(PD1)=18、PD7(RST 兼用)=4 も同じ。

| ネット | DUT ピン (物理) | V006 の既定機能（ピン定義表） | V002 の既定機能との差 |
| --- | --- | --- | --- |
| BLINK / 同期 | PC0 (10) | 汎用 GPIO（既定の副機能は TIM2_CH3） | 差なし（GPIO として使う） |
| I2C_SDA / SCL | PC1 (11) / PC2 (12) | I2C_SDA / I2C_SCL（既定） | 差なし。リマップ表は V006 のほうが多いが既定は同じ |
| SPI_SCK / MOSI / MISO | PC5 (15) / PC6 (16) / PC7 (17) | SPI_SCK / SPI_MOSI / SPI_MISO（既定） | 差なし。PC5 は RST 機能と兼用（注 5、下記） |
| UART_TX / RX | PD5 (2) / PD6 (3) | USART1_TX / USART1_RX（既定） | 差なし |
| PWM_CH1 / CH4 | PD2 (19) / PC4 (14) | TIM1_CH1 / TIM1_CH4（既定） | 差なし |
| ADC_A0 / A1 | PA2 (6) / PA1 (5) | ADC_IN0 / ADC_IN1 | 差なし。PA1/PA2 は XI/XO・OPA と兼用 |
| SWIO | PD1 (18) | SWIO（既定） | 差なし |

- PC5 と PD7 はデータシートで注 (5) 付き。ピン定義表では RST 機能を持つピンとして示される。どちらを RST にするかはオプションバイトに依る可能性があるが、**資料の該当箇所の確認は未了**。固定配線では PC5 を SPI_SCK に使うため、RST が PC5 に割り当てられていないことを実機で確認する必要がある（タスク 4.3、SPI 試験で検出される）。
- 開発時の誤接続を避けるため、この表は「資料の F8P7 定義と一致した」までを意味し、F8P6 実物のピン互換は未確認。

# 共通の差分

| 項目 | CH32V002 | CH32V006 | 区分 |
| --- | --- | --- | --- |
| コア | QingKe V2C（RV32EC） | QingKe V2A（RV32EmC）。DS p.1、p.8（1.4.1 節） | 資料確認。m 拡張の有無はコンパイラ -march の差になり得る（ch32fun.mk が選択）。サンプルは乗除算に依存しないはずだが **未確認** |
| Flash / RAM | 16 KiB / 4 KiB | 62 KiB / 8 KiB（F8P7、DS p.2）。ch32fun.ld も 62/8（design 記載） | 資料確認（実容量の実測は対象外） |
| 最大システム周波数 | 48 MHz | 48 MHz（DS p.1） | 資料確認 |
| HSI | 24 MHz | 24 MHz。PLL は ×2（クロックツリー DS p.7、RM p.27） | 資料確認 |
| 電源電圧 | 2.0–5.5 V（既存資料）。RM は V002/005/006/007 を 1.9–5.5 V とする | 2.0–5.5 V（DS p.1）。RM p.16（ch 2 電源） | 資料間で下限が異なる。3.3 V 運用に影響なし |
| Flash 待ち | 25 MHz 超で 2 | RM: SYSCLK 24 MHz 超 48 MHz 以下は 2 wait を推奨（RM Flash 章 PDF p.251 の LATENCY 欄）。ch32fun の設定に依存 | 資料確認＋ヘッダ読み。V002 と同じ |
| GPIO CFGLR の MODE | 1 ビット | V00x 共通の RM の GPIO 章（ch 7、PDF p.78 以降）は同一レイアウトを記載 | 資料確認（RM 共通章）。V006 固有の相違の記載は見つからず、V002 の `funPinMode(.., 1 \| GPIO_CNF_OUT_PP)` 流用で良いと**推定** |
| AFIO / リマップ | V002 のレイアウト | RM のリマップ表に「CH32V002/004/005/006 のみ」と書かれた項目がある（TIM2_RM の 010、I2C1_RM の 010 など）。V002 と V006 は同じ区分 | 資料確認。サンプルは AFIO を書かない（V002 差分文書の記載） |
| ADC | 12 ビット、校正ビットなし | 12 ビット、最大 3 Msps（DS p.1、p.10）。RM の ADC 章（ch 9、PDF p.100 以降）は V00x 共通 | 資料確認。DS の節名（3.3.14、PDF p.50）は「10-bit ADC Characteristics」だが本文は 12 ビット（PDF p.51 の式の N=12）。表記の揺れとして記録 |
| ADC クロック | HCLK/2 から | RM クロックツリーに ADCPRE（/2…/128）。V006 は ADC_CLK_MODE を持つ | 資料確認。サンプルは `RCC->CFGR0 &= ~RCC_ADCPRE` のみで同じ式。**未確認**: ADC_CLK_MODE の既定値の差 |
| 追加ペリフェラル | — | USART2、GPIOB、TIM3 相当（streamlined timer）、OPA、TKEY、7ch DMA | 資料確認。サンプルは使わないので既存配線に影響しない |
| 識別領域 `0x1ffff704` | 上位 12 bit = `0x002` | 上位 12 bit = `0x006` と**期待**（minichlink の CH32V006 分岐が使う）。RM の ESIG 章は `0x1FFFF7E0`（Flash 容量）や UID を挙げるが `0x1ffff704` は未記載 | **未確認**（実機読取で確定する） |

# サンプル別の再利用判定

判定: **A** = ソース無変更で再利用できると資料から見込む。**B** = 資料上の疑念があり実機で確かめる。**C** = ソース変更が必要と判明（この表では該当なし）。いずれも実機結果ではなく、`hil/matrix_ch32v006.json` は全項目を未実測から始める。

| サンプル | 判定 | 根拠（資料確認） | 未確認 |
| --- | --- | --- | --- |
| blink_and_read | A | PC0 出力、PA1 入力。ピン定義は V002 と同じ。起動表示の文字列は「CH32V002」固定なので両機の共通表記に直す（タスク 2.2） | RST 兼用ピンの設定 |
| uart | A | USART1 は PD5/PD6 既定。BRR 式は共通（RM USART 章） | 48 MHz での誤差は V002 と同じ式だが実機未確認 |
| i2c_master | A | I2C は PC1/PC2 既定。CTLR2.FREQ 48 が有効範囲（RM I2C 章（PDF p.202）は V002/004/005/006/007 共通と明記） | ACK/NACK・タイミングの実機 |
| i2c_slave | A | 同上 | 同上 |
| spi_master | A | SPI は PC5/PC6/PC7 既定、PC0 は GPIO の CS | PC5 が RST に割り当てられていないこと |
| timer_pwm | A | TIM1_CH1(PD2)/CH4(PC4) 既定。TIM1 は ADTM（RM ch 11）で V002 と同系 | 周波数の実測差 |
| adc | B | ADC_IN0(PA2) 既定。ADC 章は共通で、サンプルは RSTCAL なし・12→10 ビットに `>>2`。V006 の ADC_CLK_MODE 既定が V002 と異なると結果が変わり得る | ADC クロックの差、精度 |
| watchdog | A | IWDG は LSI 約 128 kHz（DS、RM ch 4）。V002 も同系 | 周期の校正はしない |
| sleep_wake | B | 低消費電力モード（Sleep/Standby）の仕様は DS 1.4.6 節（PDF p.9）。V006 は PWR の LDO モード等が追加（RM ch 2） | 起床要因・電流 |
| i2c_slave_helper | A | ch32fun helper。I2C は上と同じ | クロック |
| ssd1306_i2c | A | I2C master。100 kHz が主判定、1 MHz は参考 | 実 OLED 表示 |
| ws2812_spi | A | SPI MOSI(PC6) で整形。48 MHz 前提の分周が V002 と同じか | 実 LED 発光、SPI タイミングの余裕 |

- 判定 A は「ソースを分岐せずに build して実機試験にかける価値がある」という意味で、動作確認済みを意味しない。
- 判定 B の 2 件が失敗した場合、ソースのデバイス別分岐が必要になる可能性がある。その場合は design の方針どおり共通化の移行を保留し、阻害差分を記録する（タスク 5.1）。

# 未確認の一覧

1. F8P6 の刻印・製品資料上の型番、F8P7 との同一性（実物と購入元表記で確認）。
2. `0x1ffff704` の実読取値と上位 12 bit。
3. V006 の `-march` と ch32fun が選ぶ命令セットがサンプルのコードで問題ないこと（build とリンクで確認、タスク 2.1）。
4. ADC_CLK_MODE と ADC 結果の意味（タスク 4.4）。→ 2026-11-08 資料確認: リセット値 0（分周する）で、SDK の `RCC_ADCCLKConfig()` も 0 にする。006 固有の違いは資料に見当たらない（[ログ](../log/2026-11-08-2137-fix-ch32v00x-sample-findings.md) 4.4）。
5. PC5/PD7 の RST 機能の既定状態（タスク 4.3）。→ 2026-11-08 実測: 手元の個体のオプションバイト USER=0xF7、RST_MODE=10（PD7 を外部リセット、12 ms 以内の変化を無視）。RM の USER バイトの定義に PC5 のリセット機能は見当たらない（[006 のログ](../log/2026-11-08-2237-ch32v006-sample-findings.md) 6.1、7.6）。
6. 全ての実機動作・電圧・消費電流・タイミング精度。
7. PC4（TIM1_CH4）の無信号: 2026-11-08 に、PC4 を通常の GPIO 出力にしても Pico の GP15 で変化が見えないことを確認した（PC0 は同時に変化）。タイマー設定の問題ではなく、ピン〜GP15 の経路（接触・配線・個体・Pico 側）の問題。別個体での確認はユーザーの TODO（[006 のログ](../log/2026-11-08-2237-ch32v006-sample-findings.md) 6.1）。
8. IWDG の時間: 2026-11-08 の推定で LSI は約 115.6 kHz、設定（/128、2000）でのリセットは約 2.3〜2.4 s（002 と同じ）。以前の 2.3〜3.1 s は測り方の幅による、と考える（[006 のログ](../log/2026-11-08-2237-ch32v006-sample-findings.md) 6.2）。
