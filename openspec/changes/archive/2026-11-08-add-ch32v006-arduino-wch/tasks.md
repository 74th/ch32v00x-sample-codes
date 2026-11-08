# Tasks

実機作業は各frameworkの基準GPIO成功後に周辺機能へ進む。実験・環境構築は日本時間の `okf/log/YYYY-MM-DD-HHMM-<内容>.md` に目的・型番・配線・ツール/ソース条件・コマンド・結果・失敗・未確認を記録し、実測・ユーザー申告・推定を区別する。実機未実施の検証タスクは未完了のまま残す。

## 1. ビルド設定と移植根拠

- [x] 1.1 固定coreのCH32V006K8 variant/pin map・起動/LDと既存F8P6配線を照合し、使用ピン・FQBN・48 MHz HSI・62/8 KiBの適用根拠、前changeから引き継ぐ型番の仮定をOKFに記録する。対象ピン・メモリ・初期化について判定根拠が揃うことを確認する。
- [x] 1.2 `samples_ch32v006_arduino/` に共通makeと `blink_and_read`・profileを追加する。公式1.0.6・CLI 1.5.1でbuildし、ELF/mapで62/8 KiB、RAM内のスタック/ヒープ、002用上書き不在、006専用キャッシュ/成果物を確認する。READMEにbuildコマンド・依存条件を記載する。
- [x] 1.3 固定revisionのCH32V00X SDK必要ファイルを `samples_ch32v006_wch/sdk/` に維持し、PROVENANCEに元パス・元ハッシュ・利用条件・ローカル変更を記録する。`wch.mk`・006用LD・基準blinkを作り、`-DCH32V006`、クロック・ISA/ABI、62/8 KiB、起動・スタック/ヒープをbuild結果と単体検査で確認する。各READMEに条件とコマンドを記載する。

## 2. HIL選択と独立マトリクス

- [x] 2.1 `FRAMEWORK_MATRICES` に006/arduino・006/wchを登録し、未移植・未確認を区別した専用マトリクスを作る。Arduino10行、WCH13行の網羅性・根拠必須条件を単体テストで検査し、他デバイスの確認済み状態を転記していないことを確認する。`hil/README.md` に両frameworkの選択方法を記載する。
- [x] 2.2 選択・成果物・書込の単体テストを追加/更新し、006の各frameworkが専用サンプルと成果物を使うこと、002/006設定不一致・未接続・識別0x006不一致・偽成功では書き込まないこと、全量readback不一致が観測前に失敗することを確認する。既定003/ch32funと既存frameworkの挙動を維持する。
- [x] 2.3 `scripts/wch-sdk.py` のLAYOUT・CLI・一括build検査に006を追加する。基準blinkでメモリ・ELF参照元検査を通し、002設定やexternals/他デバイスSDK混入を拒否する単体テストを確認する。WCH READMEにbuild/flash/observeの独立したコマンドを記載する。
- [x] 2.4 Arduino/WCHのHIL証跡をdevice/framework/sample/variant/runで区別し、core/FQBN/ライブラリまたはSDK/コンパイラ、source revision、BIN hash、段階別結果を保存する。同名サンプルで証跡が衝突しないことを模擬結果で検査し、保存先指定例をHIL文書に記載する。

## 3. CH32V006の基準GPIO

- [x] 3.1 関連ホスト単体テストを通した後、従来の配線・給電条件を確認してArduino `blink_and_read` のHILを実行する。識別0x006・flash・全量readback・PC0点滅/PA1入力・RESET_SAFEを確認し、実測ログ・マトリクス・再現手順を更新する。
- [x] 3.2 WCH基準blinkのbuild→flash/readback→observeを実行し、続いて `blink_and_read` のHILを通す。既存のGPIO判定で成功することを確認し、基準blinkはREADME/ログ、書籍例は専用マトリクスに証跡を残す。

## 4. Arduino 10スケッチへの展開

- [x] 4.1 adc、pwm、i2c_master、spi_master、i2c_slave_test_masterを002版から移植し、006のADC SCALEなど必要な期待値を追加する。各buildと対応HILを実行し、12-bit値・バス上の処理・通常PWMパターンが既存条件で合格することを確認する。結果・移植差分をログとマトリクスに反映する。
- [x] 4.2 i2c_oledを固定ライブラリ1.0.7で移植する。buildとPico SSD1306模擬の内容比較を通し、実表示未確認をREADME・マトリクス・ログへ明記する。
- [x] 4.3 neopixelを移植し、006の生成コード・クロックと送信処理を確認する。パルス取得と既知バイト列・フレーム長一致を検証し、必要な送信設定/テスト条件の根拠を残す。既存閾値の無根拠な緩和がないことを確認し、実発光・WS2812規格適合未確認を記録する。
- [x] 4.4 i2c_slaveを移植し、他機種のxfailを006へ自動適用せず、リセットを挟む3回以上の系列で連続取引・timeout・cleanupを観測する。回数・取引間隔・SCL固着/復旧・成功/失敗を記録し、006で再現した場合だけデバイス別の既知制限と根拠を追加する。通常対象の成功に数えない。
- [x] 4.5 uart複合スケッチも固定依存でbuildし、HIL対象外理由を記録する。PWM PATTERN 3の参考結果も独立に保存し、全10スケッチのbuildと通常8スケッチの必須HILが揃うことを確認する。Arduino READMEとルートREADMEの006/Arduino状況を実績に合わせる。

## 5. WCH公式SDK 13例への展開

- [x] 5.1 uart、i2c_master/slave、spi_master、pwm、adcを移植する。006 ADC SCALE・API/AF/ピン差分を反映してbuildとHILを通し、通信処理の意味と12-bit報告を確認する。結果を各サンプルREADME・ログ・マトリクスへ反映する。
- [x] 5.2 adc_dmaとtimer_blinkを移植する。DMA割当・IRQ/ベクタ・ハンドラとELFの静的根拠を確認し、既存HILの観測と組み合わせて機能を判定する。ポーリング等への代替をしていないことを確認し、各README・ログ・マトリクスへ記録する。
- [x] 5.3 timer_dmaを移植し、006のDMA要求と設定・生成ELFを照合してHILを通す。書籍相当のDMA処理が使われている根拠と観測結果を各README・ログ・マトリクスに記録する。
- [x] 5.4 watchdog、sleep_wake、standby_wakeを移植する。reset/復帰の機能シーケンスをHILで確認し、002の既知文字化けを006へ自動免除せず、異常時は独立に切り分ける。消費電流未確認を保持し、各README・ログ・マトリクスを更新する。
- [x] 5.5 `scripts/wch-sdk.py build --all` を実行し、006の14例すべてと既存対象でメモリ・SDK参照元の検査が通ることを確認する。006書籍13例の必須実機証跡と基準blink観測が揃うことを確認し、ルートREADMEのWCH対応状況を更新する。

## 6. 統合と回帰確認

- [x] 6.1 006のArduino/WCHを専用run保存先で再実行し、必須機能成功、Wire slaveとPWM参考試験の独立結果、uart対象外、全量readback・cleanupを確認する。README・hardware再現手順・マトリクス・OKFが同じ状態を表すこと、範囲外の精度/表示/RST等を確認済みにしていないことをレビューする。
- [x] 6.2 CH32V003/002の既存Arduino/WCHの影響箇所とCH32V006/ch32funを実機回帰し、ホスト全単体テスト `uv run pytest`、通常実行の実機非操作、`openspec validate add-ch32v006-arduino-wch --strict` を確認する。既存の既知制限以外に回帰がなく、未実施や新規必須失敗は未完了のままであることをログに記録する。
