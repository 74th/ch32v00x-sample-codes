# CH32V003 と Raspberry Pi Pico の配線と安全手順

現行の HIL は [周辺機能 HIL 固定配線](wiring-proposal.md)（PC0–GP5 ほか、Pico protocol v2）を使う。DUT 固定配線は実機 HIL で機能確認済み（GPIO、UART、I2C、SPI、PWM/timer、ADC、watchdog/sleep）。これは機能確認であり、電圧・波形・タイミング精度の実測や、逆給電を防ぐ保護の検証ではない。対応する設定は [gpio_blink](../hil/configs/gpio_blink.json)、実行方法は [HIL 設定](../hil/README.md)。

電源・GND の規則、接続前のレビュー、接続・切断と異常時の復旧は、下記「安全手順」を現行配線にも適用する。その際、文中の「PC0–GP0 の 1 kΩ とスイッチ」は固定配線表の各信号線に読み替え、Pico の安全状態は `RESET_SAFE` 後の `GPIO_STATE`（output=0、pull 無効）で確認する。

## 安全手順（最初の GPIO v1 構成で記述）

以下の配線図と手順は、Pico firmware `PICO_GPIO_V1` と `hardware/pico-tester/measure.py` で使った最初の単一 GPIO 観測配線を例に書かれている。電源・GND・接続順の規則は現行構成にも適用する。v1 firmware は現行の v2 と互換がなく、PC0 の接続先も異なる（v1 は GP0、現行は GP5）。

対象は Raspberry Pi Pico / Pico W（RP2040）と、PC0 で LED が点滅している CH32V003 です。実機はユーザー申告で CH32V003F4P6、WCH-LinkE の 3.3 V で給電し、PC0–GP0 間に 1 kΩ を使用。PC0 High は 3.1 V と測定されています。スイッチの有無と VDD の給電中実測値は未確認です。

```text
 PC ──USB── WCH-LinkE ── SWIO / GND / 電源 ── CH32V003
                                                   │ PC0
                                                   ├── 既存の抵抗付き LED ── GND
                                                   └── 1 kΩ ── スイッチ ── GP0 (物理1番) ── Pico
 CH32V003 GND ─────────────────────────────────── GND (物理3番) ── Pico
 PC ──USB──────────────────────────────────────────────────────── Pico
```

Pico の物理番号は [Raspberry Pi 公式ピン配置](https://datasheets.raspberrypi.com/pico/Pico-R3-A4-Pinout.pdf) を参照してください。CH32V003 の PC0 は LED を接続する同じ信号点を使います。F4P6 の PC0 は物理10番、VSS は7番です。他のパッケージではピン配置を確認してください。

### 接続前のレビュー

- DUT と Pico をそれぞれ給電した状態で、DUT の VDD と PC0 の High 電圧を GND 基準で測り、どちらも約 3.3 V であることを確認する。5 V 動作や電圧不明の場合は接続しない。1 kΩ は電圧変換器ではない。
- Pico の GP0 は入力に設定する。出力ファームウェアが動いている可能性がある場合は接続しない。
- DUT の電源は既存の WCH-LinkE 側、Pico は USB 側とし、両者の電源ピンを接続しない。給電元が実際にそうなっていることを確認する。
- 片方だけ電源が入ると信号線から逆流する可能性がある。信号線に手動スイッチを設け、両電源が安定している間だけスイッチを閉じる。電源断前に開く。
- 実機では WCH-LinkE の出力を停止した後、VDD–VSS 間が 0.606 V と測定された。電源の完全遮断を意味しない。残留電圧の経路は未確認で、今回の GPIO 試験では追究しない。

### 人間による接続手順

1. 上記の電圧と電源経路を確認し、両方の USB 電源を外す。
2. DUT の GND と Pico の GND（物理3番）を接続する。
3. DUT の PC0 と Pico GP0（物理1番）の間に 1 kΩ の直列抵抗と開いたスイッチを入れる。既存 LED の抵抗はそのまま残す。
4. 両方を給電し、Pico の GP0 が入力であることと電圧を確認する。両電源が安定してからスイッチを閉じて測定する。
5. 終了時はスイッチを開いてから両方を電源断する。

v1 の Pico ファームウェアと PC 側の判定手順は [pico-tester](pico-tester/README.md) の「過去の GPIO v1」にあります。接続前に上記レビューを済ませてください。

### 接続・切断と異常時の復旧

この GPIO 構成は Pico 側が入力専用の場合に限る。現行 `PICO_GPIO_V1` は起動時に GP0 を入力、pull 無効に設定するが、USB 応答だけではピンの電気的状態を確認できない。既知のファームウェアを選び、信号スイッチを開いた状態で Pico を起動し、必要に応じて計測器で確認する。ファームウェアや状態が不明な場合は DUT の信号線を接続しない。`RESET_SAFE` は v1 にはなく、現行 v2 で利用できる。

1. 信号スイッチを開く。DUT と Pico の給電を切り、それぞれの電源が十分に下がったことを測定する。残留電圧がある場合は原因を確認してから作業する。
2. DUT VSS（F4P6 物理7番）と Pico GND（物理3番）を接続し、PC0（物理10番）と GP0（物理1番）の間に 1 kΩ と開いたスイッチを接続する。DUT の VDD と Pico の 3V3、VSYS、VBUS を互いに接続しない。
3. Pico を USB から給電し、既知の入力専用ファームウェアと GP0 の安全状態を確認する。WCH-LinkE を接続・操作すると DUT 3.3 V 出力が有効になる場合があるので、DUT 電源の状態を改めて確認する。
4. 両側の給電が安定した後、共通 GND を基準に DUT VDD、PC0 の High、Pico 3V3 を測定し、いずれも 3.3 V 系で信号が双方の許容範囲内であることを確認する。電圧が不明、5 V、または範囲外ならスイッチを閉じない。
5. スイッチを閉じて測定する。終了時は先にスイッチを開き、両側を電源断する。電圧が下がったことを確認してから信号線、最後に GND を外す。

測定中に応答が途絶えた、配線や電圧が想定と異なる、または Pico の出力状態が不明になった場合は、まず信号スイッチを開く。両側を電源断して電圧を測定し、配線と給電経路を修正する。Pico を既知のファームウェアへ戻して安全状態を確認するまで再接続しない。USB から復旧できない場合は Pico の BOOTSEL を使う。スイッチを操作できない場合は感電や短絡を避けられる方法で両側の給電を停止し、電圧を確認してから切り離す。

## Pico 単体の loopback 配線（DUT とは接続しない）

Pico の自己検証用で、DUT 固定配線とは別の GPIO を使う。電源ピン（3V3、VSYS、VBUS）には接続しない。I2C と SPI の loopback は GP16–GP19 を共有するため同時には構成できず、切り替えは Pico を USB から外して行う。

| 構成 | 接続（各 1 kΩ、特記を除く） | 検証スクリプト |
|---|---|---|
| I2C | GP16–GP18 を SDA、GP17–GP19 を SCL とし、それぞれ 3V3 へ 4.7 kΩ pull-up | `hardware/pico-tester/i2c_loopback.py`、`ssd1306_selftest.py` |
| SPI | GP19→GP20（MOSI）、GP18→GP21（SCK）、GP17→GP22（CS）、GP26→GP16（MISO） | `hardware/pico-tester/spi_loopback.py` |
| WS2812 | GP19→GP20（1 kΩ）のみ。GP16〜19 に pull-up を残さない（SPI loopback 配線の一部で足りる） | `hardware/pico-tester/ws2812_selftest.py` |
| UART | [pico-tester README](pico-tester/README.md) と `uart_loopback.py` を参照 | `hardware/pico-tester/uart_loopback.py` |
| PWM 測定 | GP16→GP18（I2C 配線が残っていれば兼用可） | `hardware/pico-tester/pwm_selftest.py` |

DUT 試験（`tests/hil`）は loopback 配線の有無に依存しない。2026-11-07 20:02 JST の SSD1306 自己検証時は I2C 配線、20:21 JST の WS2812 自己検証時は GP19→GP20 の SPI 系配線に切り替えた（いずれもユーザー申告。それ以前の最後の確認時は SPI 配線）。
