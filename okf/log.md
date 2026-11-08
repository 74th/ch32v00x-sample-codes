# Directory Update Log

## 2026-11-08
* **Regression**: [CH32V003のch32fun HIL回帰](log/2026-11-08-1400-ch32v003-regression.md)を記録した。14 passed、1 xfailed。
* **Measurement**: [新配置からのCH32V006 HIL](log/2026-11-08-1354-ch32v006-hil-new-layout.md)を記録した。移動前と結果・成果物hashが一致。
* **Measurement**: [新配置からのCH32V002 HIL](log/2026-11-08-1352-ch32v002-hil-new-layout.md)を記録した。移動前と成果物hash・結果が一致。
* **Decision**: [CH32V002/CH32V006の共通化判定](log/2026-11-08-1340-ch32v00x-shared-source-decision.md)を記録した。両機の必須HILが同一ソースで合格し、成立。
* **Measurement**: [CH32V006F8P6のHIL](log/2026-11-08-1335-ch32v006-hil.md)を記録した。GPIO・通信・周辺機能・helper必須3試験が合格、SSD1306 1MHzは参考(XFAIL)。
* **Measurement**: [CH32V006F8P6の検出と識別領域の読取](log/2026-11-08-1326-ch32v006-identifier-read.md)を記録した。識別値の上位型番は0x006。
* **Porting**: [CH32V006検証changeのホスト側基盤](log/2026-11-08-1315-ch32v006-host-foundation.md)を記録した。[差分表](peripherals/ch32v006-port-differences.md)を追加。実機は未操作。

## 2026-11-07
* **Migration**: [サンプル配置の変更と仕様 archive](log/2026-11-07-1340-sample-layout-archive.md)を記録した。
* **Migration**: [独立 ch32fun submodule と両デバイスの実機検証](log/2026-11-07-1330-standalone-ch32fun.md)を記録した。
* **Integration**: [段階別検証と公開対象](log/2026-11-07-1159-integration-publication-check.md)を確認した。
* **Measurement**: [CH32V002 の識別・書き込み・GPIO 観測](log/2026-11-07-1156-ch32v002-flash-measure.md)を記録した。
* **Diagnosis**: [CH32V002 の SWIO 検出](log/2026-11-07-1140-ch32v002-detection-diagnosis.md)で電源再投入後も未検出だった結果を記録した。
* **Porting**: [CH32V002 の差分調査と build-only](log/2026-11-07-1130-ch32v002-port-build.md)を記録した。実機の検出は未成功。
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
* **Update**（2026-11-08）: [未確認事項の一覧](/open-questions/ch32v00x-unverified.md) を作成。[GPIO CFGLRの差分](/peripherals/gpio/cfglr-mode-field.md) と [GPIOプルダウン](/peripherals/gpio/ch32v00x-pull-down.md) に CH32V002/CH32V006 の実測を追記。CH32V002/CH32V006 の差分文書に ADC・IWDG・PC4 などの調査結果を追記（[ログ](/log/2026-11-08-2137-fix-ch32v00x-sample-findings.md)）。
