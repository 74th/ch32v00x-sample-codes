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

## wwdg（WWDG、書籍にない追加サンプル）

2026-11-09、change `add-wwdg-sample`。詳細は[ログ](../log/2026-11-09-0013-add-wwdg-sample.md)。

- 資料: RM 第5章は V00X 共通で、002 との差はない（窓の下限の 0x3F/0x40 の書き方がそろっていない点も同じ。002 のページの `wwdg` の節を参照）。ソースは 002 と同一（WCH SDK は同じ `main.c`、ch32fun は共通のソース）。
- 実機: **006 で観測済み**（2026-11-09、[ログ](../log/2026-11-09-0751-ch32v006-wwdg-hil.md)）。WCH SDK と ch32fun の 3 ビルドとも、002 と同じ UART 出力（モード 0 はリセットなし、モード 1 は点1個、モード 2 は点9個で `cause=WWDG`）。002 の結果は引き継がず 006 で別に観測した。EWI、デバッグ中の動作、リセット時間の絶対精度は未確認。

# 未確認の一覧

1. F8P6 の刻印・製品資料上の型番、F8P7 との同一性（実物と購入元表記で確認）。
2. `0x1ffff704` の実読取値と上位 12 bit。
3. V006 の `-march` と ch32fun が選ぶ命令セットがサンプルのコードで問題ないこと（build とリンクで確認、タスク 2.1）。
4. ADC_CLK_MODE と ADC 結果の意味（タスク 4.4）。→ 2026-11-08 資料確認: リセット値 0（分周する）で、SDK の `RCC_ADCCLKConfig()` も 0 にする。006 固有の違いは資料に見当たらない（[ログ](../log/2026-11-08-2137-fix-ch32v00x-sample-findings.md) 4.4）。
5. PC5/PD7 の RST 機能の既定状態（タスク 4.3）。→ 2026-11-08 実測: 手元の個体のオプションバイト USER=0xF7、RST_MODE=10（PD7 を外部リセット、12 ms 以内の変化を無視）。RM の USER バイトの定義に PC5 のリセット機能は見当たらない（[006 のログ](../log/2026-11-08-2237-ch32v006-sample-findings.md) 6.1、7.6）。
6. 全ての実機動作・電圧・消費電流・タイミング精度。
7. PC4（TIM1_CH4）の無信号: 2026-11-08 に、PC4 を通常の GPIO 出力にしても Pico の GP15 で変化が見えないことを確認した（PC0 は同時に変化）。タイマー設定の問題ではなく、ピン〜GP15 の経路（接触・配線・個体・Pico 側）の問題。別個体での確認はユーザーの TODO（[006 のログ](../log/2026-11-08-2237-ch32v006-sample-findings.md) 6.1）。
8. IWDG の時間: 2026-11-08 の推定で LSI は約 115.6 kHz、設定（/128、2000）でのリセットは約 2.3〜2.4 s（002 と同じ）。以前の 2.3〜3.1 s は測り方の幅による、と考える（[006 のログ](../log/2026-11-08-2237-ch32v006-sample-findings.md) 6.2）。

## 実測した SCK・SCL の周期（2026-11-09、Pico の PIO 測定、Pico の時計は未校正）

出典: `okf/log/2026-11-09-0805-extend-pico-fixture-measurement.md`。値は設定値からの差（期待値は SPI が 48 MHz の分周、I2C が各サンプルの設定）。

| 項目 | 設定 | 測定 | 差 |
|---|---|---|---|
| SPI SCK（ch32fun、Arduino） | 750 kHz | 744.05 kHz | −0.79 % |
| SPI SCK（WCH SDK） | 187.5 kHz | 186.29 kHz | −0.65 % |
| I2C SCL（ch32fun、Arduino） | 100 kHz | 98.19 kHz | −1.81 % |
| I2C SCL（WCH SDK） | 400 kHz | 379.94 kHz | −5.02 % |
| PWM 周期（ch32fun、Arduino） | 1 kHz | 992.8 / 991.9 Hz | −0.72 / −0.81 % |
| PWM 周期（WCH SDK） | 93.75 kHz | 93.02 kHz | −0.78 % |


## 006 だけの機能（USART2、OPA、TIM3、TKEY。2026-11-09、書籍にない追加サンプル）

出典: `okf/log/2026-11-09-0854-ch32v006-only-feature-samples.md`、サンプルは `samples_ch32v006_wch/{usart2,opa,tim3,tkey}`（公式 EVT を元にした自作）。

| 機能 | 資料（RM、DS） | ピン（TSSOP20） | 実機の結果（CH32V006、Pico で観測） |
|---|---|---|---|
| USART2 | RM 第14章（V005/006/007/M007）。AFIO_PCFR1 の USART2_RM=011 で TX=PD2、RX=PD3（RM Table 7-11） | TX=PD2（19番、固定配線で GP14）。RX=PD3 は未配線 | 送信のみ確認。115200 8N1 の `usart2 0123456789` を 1.2 s に 6 回、欠けなく受信 |
| OPA（PGA） | RM 第17章。P0=PA2、出力 OUT0=PD4（ADC_IN7）、利得 4/8/16/32 倍（SDK の列挙） | PA2 入力、PD4 出力（ADC で読む） | out/in の中央値: 利得4が 3.92（入力 356 のとき）〜3.99（入力 763）、利得8が 7.81（入力 356）。高入力は飽和（4095） |
| TIM3（SLTM） | RM 第13章（V006/007/M007）。分周なし、出力ピンなし、CH3 の DMA 要求は 006 では DMA1 のチャネル 1 のみ（RM Table 8-1） | PC0（DMA で BSHR を書いて反転、GP5 で観測） | 期待 500 Hz に対し 496.6 Hz（−0.68 %）、duty 50 %（500 000 ppm 前後）。HSI の誤差と整合 |
| TKEY | RM 第10章（V006/007/M007）。ADC の外部チャネル | PD4（未配線）、PA2（10 kΩ＋1 µF） | 参考値: PD4 が 4086〜4087、PA2 が 50〜52（負荷が大きいと値が小さい）。タッチは未確認 |
| CMP | RM 第17章は V007/M007 のみ。006 の DS の機能一覧は「OPA/PGA/CMP」と書き、食い違う | − | 対象外（資料の食い違いのみ記録） |

- OPA の出力の ADC 内部チャネルは、資料・EVT に記述がなく、PD4（ADC_IN7）で読んだ。
- OPA の許容幅（±10 %）は実測の偏差（約 2 %）の 5 倍の余裕で、資料に利得誤差の記載を見つけられなかったため。電圧は未校正。

### 標準 ch32fun 版（2026-11-09、`samples_ch32v00x_ch32fun/{usart2,tim3,opa,tkey}`、CH32V006 専用）

出典: `okf/log/2026-11-09-2056-ch32v006-only-ch32fun-samples.md`。固定 ch32fun（`b28d285`）のレジスタ定義だけで、WCH SDK 版と同じ動作・同じ判定にした。CH32V002 を指定した build は `#error` で止まる。

- 実機（CH32V006）: USART2 は 1.2 s に 6 回受信、TIM3 は 496.5 Hz（−0.7 %）・duty 50 %、OPA の比は利得 4 で 3.76〜3.97、利得 8 で 7.57（±10 % 内、高入力は飽和）。TKEY は PD4≈4082、PA2≈52 で、PD4 のリードを指で触ると約 555〜3418 に下がり離すと戻った（手作業 1 回）。
- **固定 ch32fun のヘッダの不足・食い違い**: (1) `TIM3` マクロが参照する `ALTM_TypeDef` はどのヘッダにも未定義 → サンプル内に RM 第13章の構造体を定義。(2) `RCC_TIM3EN` は 0x2 だが SDK の `RCC_PB1Periph_TIM3` と ch32fun 自身の `RCC_TIM3RST` は 0x4 で、0x2 では TIM3 にクロックが入らなかった（実測）→ bit2 を直接書く。(3) TKEY は ADC の SWSTART を与えると 0 を返した（WCH 版は与えない）。固定 ch32fun は変更していない。

