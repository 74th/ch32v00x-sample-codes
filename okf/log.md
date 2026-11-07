# Directory Update Log

## 2026-11-07
* **Reproduction**: [Pico の再書き込みと USB 再認識](log/2026-11-07-1121-pico-reflash-discovery.md)を確認し、検出待ちを追加した。
* **Reproduction**: [初回コミットの別 checkout](log/2026-11-07-1120-clean-checkout-reproduction.md)で build・flash・measure を実施した。
* **Review**: [CH32V003 再現手順](log/2026-11-07-1119-ch32v003-repro-review.md)とコミット未作成の制約を記録した。
* **Review**: [Pico 配線手順](log/2026-11-07-1116-wiring-review.md)のレビューと未確認事項を記録した。
* **Preparation**: [DUT 未接続時の書き込み確認](log/2026-11-07-1113-disconnected-flash-preparation.md)に向け電源停止を指示した。
* **Measurement**: [CH32V003F4P6 の書き込み・読み戻し・起動・GPIO 観測](log/2026-11-07-1113-ch32v003-flash-readback-measure.md)を記録した。
* **Measurement preparation**: [CH32V003F4P6 の電源停止指示](log/2026-11-07-1105-dut-power-off.md) を記録した。
* **Investigation**: [CH32V003F4P6 の GPIO ピン選定](log/2026-11-07-1104-ch32v003-gpio-pin-selection.md) の資料上の根拠を記録した。
* **Creation**: [作業ログ](log/) に ch32fun のビルド・書き込み、Pico の測定、WCH-LinkE の電源制御の記録を追加した。
* **Initialization**: OKF v0.2のバンドルを作成し、[記述ルール](/conventions/knowledge-status.md) を定めた。
* **Creation**: 5つの一次資料（[一次資料一覧](/sources/)）の版と識別情報を登録した。
* **Creation**: [GPIO CFGLRの差分](/peripherals/gpio/cfglr-mode-field.md)、[CH32V00xのGPIOプルダウン](/peripherals/gpio/ch32v00x-pull-down.md)、[CH32V006 TSSOP20品の型番](/devices/ch32v006-tssop20-part-number.md) を、一次資料と照合して記録した（いずれも実機では未確認）。
