# CH32V003F4P6 HIL 固定配線案

これは未実測の提案であり、実配線の指示として確定したものではない。対象は CH32V003F4P6/TSSOP20 と Raspberry Pi Pico/RP2040。参照 book-code revision は `4ce0a1b2fe0fa771e68e17944c4ce0d9b20924ae`。SPI NSS を AFIO で PC0 に移し、通常の周辺機能試験は信号ジャンパを切り替えずに実施する。元サンプルの別リマップ配置を試すときは後段の手動試験とし、電源を切って配線を変更する。

## book-code とカバー範囲

| 対象 | 本の実設定と基本構成での扱い |
|---|---|
| `blink_and_read-ch32fun` | PC0 出力、PA1 入力。そのまま対応 |
| `adc-ch32fun` | PA1/A1 と PA2/A0 の2入力に対応。コメントの PA0 は誤記とみられ、実際の定義は PA2。標準 API 分岐と固定 ch32fun の適合は別途確認 |
| `i2c_slave-ch32fun` | デフォルト PC1 SDA、PC2 SCL。配線は対応するが helper 依存のため現計画では直接検証対象外 |
| `i2c_oled-ch32fun` | I2C の接続を提供。helper 依存と画面表示の検証は現計画の対象外 |
| `spi_master-ch32fun` | PC1 NSS、PC5 SCK、PC6 MOSI、PC7 MISO、mode 0、設定 1 MHz。基本構成は NSS を PC0 にリマップし、helper 依存のため同等機能を新規実装 |
| `neopixel-ch32fun` | PC6 出力は引き出せるが helper と発光内容の検証は対象外 |
| `i2c_master-register` | 実設定はリマップ先 PC6/PC5。基本構成では PC1/PC2 の同等機能を試し、元のリマップ設定は後日手動配線 |
| `uart-register` | 実設定はリマップ先 PC0 TX/PC1 RX。基本構成では PD5 TX/PD6 RX の同等機能を試し、元の設定は後日手動配線。実際の BRR は 9600 baud |
| `pwm-register` | 実設定はリマップ先 PC6/PD3。基本構成では PD2/PC4 の同等機能を試し、元の設定は後日手動配線 |
| `timer_blink`、`sleep_mode_blink`、`standby_mode_blink` | PC1 の変化を I2C pull-up と Pico 高インピーダンス入力を残した状態で観測する案。sleep の参照コードは WFI がコメントアウトされているので、そのまま sleep 成功と判断しない |
| `watchdogtimer-register` | PA1 入力、PC1/PC2 出力に対応。再起動パターンを観測 |
| `adc_dma-register`、`timer_dma-register` | PA1/PA2 は引き出す。DMA 自体と、後者の12本の表示駆動全体の検証は対象外 |

直接移植できるものと、同じ周辺機能の新規サンプルは区別する。ADC の入力電圧を与えるだけでは変換結果は取得できないので、新規サンプルに UART などの機械可読な出力が必要。既存コードの SWIO `printf` を使う場合は WCH-LinkE の取得手段との共存を別途検証する。

## ポートマップ案

Pico の番号はボード上の物理ピン。試験は同時に行わず、PC0 を GPIO 観測と SPI NSS、PA1 を ADC と低速ボタン刺激に共用する。全 GPIO の網羅と高速な GPIO 入力試験は対象外。値は初期案で、実機の電圧・負荷・波形確認後に決定する。

| ネット | DUT F4P6（物理） | Pico（物理） | 用途・初期部品 |
|---|---|---|---|
| `GPIO_SPI_NSS` | PC0 (10) | GP5 (7) | GPIO 観測 / SPI NSS、1 kΩ。既存 LED の負荷を確認 |
| `I2C_SDA` | PC1 (11) | GP10 (14) | I2C SDA、220 Ω、DUT VDD へ 4.7 kΩ pull-up |
| `I2C_SCL` | PC2 (12) | GP11 (15) | I2C SCL、220 Ω、DUT VDD へ 4.7 kΩ pull-up |
| `SPI_SCK` | PC5 (15) | GP6 (9) | SPI SCK、1 kΩ |
| `SPI_MOSI` | PC6 (16) | GP7 (10) | SPI MOSI、1 kΩ |
| `SPI_MISO` | PC7 (17) | GP4 (6) | SPI MISO、1 kΩ |
| `UART_TX` | PD5 (2) | GP9 (12) | DUT TX → Pico RX、1 kΩ |
| `UART_RX` | PD6 (3) | GP8 (11) | Pico TX → DUT RX、1 kΩ |
| `PWM_CH1` | PD2 (19) | GP14 (19) | DUT → Pico、1 kΩ |
| `PWM_CH4` | PC4 (14) | GP15 (20) | DUT → Pico、1 kΩ |
| `ADC_A1_BUTTON` | PA1 (5) | GP12 (16) | PWM → 10 kΩ → PA1、PA1 から 1 µF → GND。低速ボタン刺激にも使う |
| `ADC_A0` | PA2 (6) | GP13 (17) | PWM → 10 kΩ → PA2、PA2 から 1 µF → GND |
| `GND` | VSS (7) | GND (3) | 共通 GND |
| `SWIO` | PD1 (18) | WCH-LinkE SWIO | Pico には接続しない |

Pico は SPI0 GP4–GP7、I2C1 GP10/GP11、UART1 GP8/GP9 を候補とする。GPIO v1 の現行配線は PC0–GP0 であり、この案の PC0–GP5 と異なる。対応ファームウェア・ホスト側を準備し、安全に電源を切って配線を変更するまで既存手順を維持する。

## 概略回路図

```text
 WCH-LinkE 3.3V ───────── DUT VDD (9)          Pico USB 給電
 WCH-LinkE SWIO ───────── PD1 (18)             Pico 電源と DUT VDD は接続しない
 WCH-LinkE GND ───────┬── VSS (7) ─────────── Pico GND (3)
                      │
 DUT                                              Pico
 PC0 (10) ─────────────── 1k ─────────────────── GP5  (7) GPIO観測 / SPI NSS
 PC1 (11) ────┬────────── 220R ───────────────── GP10 (14) I2C SDA
              └─ 4.7k ── DUT VDD
 PC2 (12) ────┬────────── 220R ───────────────── GP11 (15) I2C SCL
              └─ 4.7k ── DUT VDD
 PC5 (15) ─────────────── 1k ─────────────────── GP6  (9) SPI SCK
 PC6 (16) ─────────────── 1k ─────────────────── GP7  (10) SPI MOSI
 PC7 (17) ─────────────── 1k ─────────────────── GP4  (6) SPI MISO
 PD5  (2) ─────────────── 1k ─────────────────── GP9  (12) UART RX
 PD6  (3) ─────────────── 1k ─────────────────── GP8  (11) UART TX
 PD2 (19) ─────────────── 1k ─────────────────── GP14 (19) PWM入力
 PC4 (14) ─────────────── 1k ─────────────────── GP15 (20) PWM入力
 PA1  (5) ─────┬───────── 10k ────────────────── GP12 (16) PWM / ボタン
               └─ 1uF ── GND
 PA2  (6) ─────┬───────── 10k ────────────────── GP13 (17) PWM
               └─ 1uF ── GND
```

図は論理接続で、電源断・異常時の信号一括切断手段は設計・レビューが必要。通常試験間でジャンパを変更しないことと、片側無給電時にも安全であることは別問題。Pico の GPIO を入力にしても、無給電側への逆流や RC の残留電圧はなくならない。

## 電源と電気的条件

- DUT は WCH-LinkE の 3.3 V、Pico は USB から給電する案。電源ピンは互いに接続せず GND を共通にする。信号は両電源が安定し電圧を確認した後に接続し、どちらかの電源を切る前に開く。WCH-LinkE の操作で出力が有効になる場合がある。詳細は [wiring.md](wiring.md)。
- I2C は各線を open-drain とし、DUT 側 3.3 V への 4.7 kΩ pull-up を各1本。既存モジュールの pull-up と並列にならないようにする。100 kHz から開始し、400 kHz 以上は波形、立上り、Low 電圧、容量と双方の電圧を実測後に決める。220 Ω や 1 kΩ はレベル変換器でも電源断時の逆流防止回路でもない。
- ADC の RC は 10 kΩ × 1 µF = 公称 10 ms。PA1 のボタン入力はこの RC を経由するため、DUT の内蔵 pull-up と 10 kΩ による分圧を含め、PA1 実測 Low が DUT の入力 Low 規格を満たすか、High・応答遅延も含めて測り、満たす場合に限って低速操作に使う。満たさない場合は抵抗値や駆動回路の再設計が必要。設定変更後 100 ms 以上を初期待ち時間とし、PWM 周波数、リップル、サンプリング負荷と DUT の VDD を踏まえて再評価する。両電源と入力電圧が許容範囲内であることを確認し、RC の測定点を独立した電圧計で測る。Pico は校正済み DAC ではない。切断後のコンデンサの残留電圧も測定する。
- 使用前に各 Pico 機能を DUT とは独立に自己検証し、timeout、USB 切断、異常時の safe state を確認する。現行ファームウェアは GP0 入力の v1 のみで、提案の出力・バス機能は未実装。

## AFIO リマップを後で検証するとき

信号を安全に切り離し、両側の電源を切り、電圧と安全状態を確認してから、対象に合わせて一時的に配線する。I2C master は PC6 SDA / PC5 SCL、UART は PC0 TX / PC1 RX、PWM は PC6 / PD3 を使う。PC0 の LED 負荷や各試験での電源・pull-up を再確認し、毎回手動で戻す。PD1 は SWIO に使用中なので、そのリマップ先としての使用は別途設計する。

次段階では、この案を HIL 設定、KiCad 回路図と出力に反映し、実配線と電圧・波形を確認する。現時点で一致確認や実機動作の成功は主張しない。
