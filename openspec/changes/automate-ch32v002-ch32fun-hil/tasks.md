# タスク

## 1. HIL ホスト層のデバイス選択

- [x] 1.1 `ch32hil` にデバイス定義（device 名、`TARGET_MCU`、minichlink 期待型番、識別領域の期待型番、TSSOP20 物理ピン表、サンプルディレクトリ、既定設定、マトリクス）を追加し、`ch32v003` と `ch32v002` を登録する。不明なデバイス名が実機操作前にエラーになることを単体テストで確認する。
- [x] 1.2 `conftest.py` に `--hil-device`（既定 `ch32v003`）を追加し、`--hil-config` 未指定時は選択デバイスの既定設定を使う。設定の `dut.device` と選択デバイスの不一致を実機操作前に拒否し、`--hil-device` 未指定の既存コマンドで選ばれる設定・サンプル・期待型番が従来どおりであることを単体テストで確認する。
- [x] 1.3 `ch32hil/config.py` の `CH32V003F4P6` 固定チェックと `DUT_PHYSICAL` をデバイス定義参照へ置き換える。CH32V002F4P6 の物理ピン番号はデータシート V1.7 のピン定義と照合して記録し、既存の CH32V003 設定検証テストが全て通ることを確認する。
- [x] 1.4 `ch32hil/dut.py` に CH32V002 の識別領域 `0x1ffff704` 読み出しと型番 `0x002` 照合を追加し、flash 前に実行する。正常、型番不一致、読み出し失敗、終了コード 0 の空出力を模擬した単体テストで、いずれも flash 前に `flash` 段階の失敗になることを確認する。
- [x] 1.5 `tests/hil/*.py` のサンプルパスと結果メタデータの `target` を選択デバイスから導出するよう書き換え、選択デバイスにサンプル・設定がないかマトリクスで対象外のテストは理由付き skip にする。`--hil` なしの `uv run pytest` が実機へ書き込まず成功することと、skip 理由の表示を確認する。
- [x] 1.6 `hil/README.md` に `--hil-device` の使い方、既定値、DUT 差し替えの前提を記載し、記載したコマンドを `--collect-only` で実行してオプションが認識されることを確認する。

## 2. CH32V002 の配線成立確認と設定

- [x] 2.1 固定配線の各ネット（PC0、PC1/PC2 I2C、PC5/PC6/PC7 SPI と PC0 NSS リマップ、PD5/PD6 USART、PD2/PC4 TIM1、PA1/PA2 ADC、SWIO、VDD/VSS）について、CH32V002 データシート V1.7 のピン定義と CH32V00X RM V1.5 の AFIO リマップを照合し、ページ付きで `okf/peripherals/` または `okf/log/` に記録する。成立しないネットがあれば配線変更案を `hardware/wiring-proposal.md` に追記し、ユーザーレビュー待ちとして以降の該当サンプルを止める。
- [x] 2.2 `hil/configs/` に CH32V002F4P6 用の設定を追加し、2.1 の結果とネット名・物理ピン・部品値を一致させる。`uv run pytest -q tests/unit/test_config_matrix.py tests/unit/test_wiring_consistency.py` が通り、意図的に CH32V003 用の値を混ぜた設定を検出できることを確認する。
- [ ] 2.3 `hardware/wiring.md` と `hardware/ch32v002-reproduction.md` に、CH32V003 から CH32V002 へ DUT を差し替える手順（電源断、WCH-LinkE の 3.3 V 出力、交換、電圧確認、`./scripts/ch32fun.sh flash ch32v002` による検出確認、Pico 安全状態確認）と、CH32V002 で異なる点を記載する。ユーザーがレビューして差し替えを実施できることを確認する。
- [x] 2.4 `hil/matrix_ch32v002.json` を追加し、CH32V003 マトリクスの各サンプルに対応する行を「未移植」状態で用意する。CH32V003 で `hil-verified` のサンプルが CH32V002 側に欠けたら失敗する整合性テストを追加し、`hil-verified` に `hil_tests` と `evidence` を要求する既存検証が CH32V002 マトリクスにも適用されることを確認する。

## 3. GPIO（blink_and_read）

- [x] 3.1 既存 `samples_ch32v002_ch32fun/blink_and_read` を CH32V003 版の現行実装（ボタン入力を含む）と比較し、不足があれば追従する。デバイス差分（`TARGET_MCU`、HSI 24 MHz、GPIO MODE 等）を根拠付きで記録し、`make` で build できることを確認する。
- [x] 3.2 `hil/matrix_ch32v002.json` の `gpio_input` 行を、CH32V003 と同じ理由（固定配線で PC4 を Pico から駆動しない）で HIL 対象外として記録し、マトリクス整合性テストが通ることを確認する。
- [x] 3.3 DUT を CH32V002 へ差し替え、`uv run pytest --hil --hil-device ch32v002 -m 'hil and gpio' tests/hil --hil-port=<Pico>` を実行する。識別付き flash、readback 一致、PC0 パターン、意図的不一致、PA1 ボタン入力、後始末を別々に確認し、`okf/log/` に記録してマトリクスを更新する。

## 4. UART

- [x] 4.1 `uart` を移植し、HSI 24 MHz と既定 PLL での USART ボーレート設定値を RM V1.5 と照合して記録する。build を確認する。
- [x] 4.2 CH32V002 で UART HIL を実行し、Pico→DUT、DUT→Pico、タイムアウト、後始末を確認して記録する。

## 5. I2C

- [x] 5.1 `i2c_master` と `i2c_slave` を移植し、I2C クロック設定値とレジスタ差分を RM V1.5 と照合して記録する。両方の build を確認する。
- [x] 5.2 CH32V002 で両方の役割の I2C HIL を実行し、アドレス、データ、ACK/NACK、誤ったアドレスの場合を確認して記録する。

## 6. SPI

- [x] 6.1 `spi_master` を移植し、2.1 で確認した NSS→PC0 リマップ設定と SPI レジスタ差分を記録する。build を確認する。
- [x] 6.2 CH32V002 で SPI HIL を実行し、転送データと mode 不一致の検出を確認して記録する。

## 7. timer/PWM と ADC

- [x] 7.1 `timer_pwm` を移植し、TIM1 のクロック前提から CH32V002 での期待周期・デューティと許容範囲を決めて記録する。build を確認する。
- [x] 7.2 CH32V002 で PWM HIL を実行し、実測の周期・デューティと採用した許容範囲を記録する。
- [x] 7.3 `adc` を移植し、ADC の分解能・チャネル・サンプリング設定の差分と、CH32V002 での粗い値域判定条件を資料から決めて記録する。build を確認する。
- [x] 7.4 CH32V002 で ADC HIL を実行し、PWM 設定ごとの報告値の変化と後始末を確認して記録する。電圧や精度は主張しない。

## 8. watchdog と sleep

- [x] 8.1 `watchdog` と `sleep_wake` を移植し、IWDG のクロック源・分周、sleep/wake の PFIC・EXTI 差分と、CH32V002 での期待パルス数・時間条件を記録する。両方の build を確認する。
- [x] 8.2 CH32V002 で watchdog/sleep HIL を実行し、reset 署名、sleep 中のトグル、テスト後の復旧可能性を確認して記録する。

## 9. 統合受け入れ

- [ ] 9.1 `uv run pytest -q` を実機なしで実行して全単体テストが通ることを確認し、`openspec validate automate-ch32v002-ch32fun-hil --strict` を通す。
- [ ] 9.2 CH32V002 で `uv run pytest --hil --hil-device ch32v002 -q --hil-port=<Pico>` を単一コマンドで実行し、全 HIL が成功または理由付き skip になることを確認して記録する。
- [ ] 9.3 DUT を CH32V003 へ戻し、`--hil-device` なしの全 HIL を再実行して回帰がないことを確認して記録する。
- [ ] 9.4 `hil/matrix_ch32v002.json`、`hardware/ch32v002-reproduction.md`、README の状態が実測ログと一致し、実測・ユーザー申告・推定が区別され、`xprivate/` の内容を含まないことをレビューする。

## Workflow follow-up

- CH32V002 の HIL 受け入れを実機で観測し、メイン仕様を同期できる状態になってから change をアーカイブする。
