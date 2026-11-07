# Tasks

## 1. 共通CLI・SDK・HIL

- [ ] 1.1 designの13行をhil/matrix_wch.jsonへ登録し、全book-codeのwch_sdk例が一対一で追跡できる単体チェックとREADME対応表を追加する。
- [ ] 1.2 samples_ch32v003_wch/wch.mkに共通ビルド設定を抽出し、blinkのビルド・成果物サイズと、SDKヘッダ更新時の再ビルドを確認して使い方を記録する。
- [ ] 1.3 scripts/wch-sdk.pyへdevice/sample選択を追加し、不正指定・型番不一致・成果物不足で書き込まない単体チェックを追加する。既定のblinkコマンドの互換性を確認し文書化する。
- [ ] 1.4 ch32hil/devices.pyとconftest.pyへwch frameworkを追加し、WCH GCC buildと既存flash/readback/Runを接続する。選択・matrix整合性の単体テストとpytest --collect-onlyで既存frameworkも保たれることを確認する。
- [ ] 1.5 追加の公式ドライバを必要分だけコピーし、SDK revision・元パス・SHA-256・利用条件・変更点をPROVENANCEへ追記する。externalsの公式SDKがビルド依存に入らないことを確認する。

## 2. CH32V003の周辺サンプル（各行で実装・テスト・文書を揃える）

各タスクでは公式APIと書籍src/main.cを参照し、期待値・許容差を先に明記する。build、検出付きflash、全量readback、可能な観測を順に実施する。失敗と未観測をmatrix/okf/logへ記録し、成功と混同しない。実機確認が不可能な行は実装と制限の記録まで進め、実測完了タスクを偽って完了しない。

- [ ] 2.1 `blink_and_read`: 公式GPIO入力とDelayを使用し、PA1刺激でPC0点滅の停止・再開をHIL確認し、個別README・HIL/変換テスト・matrix・作業ログに結果を残す。
- [ ] 2.2 `uart`: 書籍のCO2コマンドと応答変換を実装し、既知応答・checksum異常・timeoutのテストとUART線の競合回避を確認し、個別README・HIL/変換テスト・matrix・作業ログに結果を残す。
- [ ] 2.3 `adc`: 公式ADCでPA1/PA2の校正・変換を実装し、既知刺激と2チャネル値・単調性を確認し、個別README・HIL/変換テスト・matrix・作業ログに結果を残す。
- [ ] 2.4 `adc_dma`: 公式ADC scanとDMA転送を実装し、バッファ順序・継続更新・2チャネル刺激を確認し、個別README・HIL/変換テスト・matrix・作業ログに結果を残す。
- [ ] 2.5 `i2c_master`: SHT31コマンド・応答と温湿度変換を実装し、既知データを使うテストと治具での対応範囲を確認し、個別README・HIL/変換テスト・matrix・作業ログに結果を残す。
- [ ] 2.6 `i2c_slave`: 公式I2C割り込みでレジスタslaveを実装し、0x10へのwrite/read・ポインタ更新・repeated STARTを確認し、個別README・HIL/変換テスト・matrix・作業ログに結果を残す。
- [ ] 2.7 `spi_master`: 公式SPIで書籍のreset/config/readと符号付き温度変換を実装し、既知応答とCS配線の観測可否を確認し、個別README・HIL/変換テスト・matrix・作業ログに結果を残す。
- [ ] 2.8 `pwm`: 公式TIM PWMのduty変化を実装し、PD2等の観測可能チャネルで周期と複数dutyをHIL確認し、個別README・HIL/変換テスト・matrix・作業ログに結果を残す。
- [ ] 2.9 `timer_blink`: TIM1/TIM2の割り込みを実装し、各タイマの周期・GPIO出力と割り込み属性を確認し、個別README・HIL/変換テスト・matrix・作業ログに結果を残す。
- [ ] 2.10 `timer_dma`: 書籍の4桁走査に相当するTimer→GPIO DMAを実装し、DMA設定・転送列と観測可能範囲を確認。不足配線と表示未確認の条件を明記し、個別README・HIL/変換テスト・matrix・作業ログに結果を残す。
- [ ] 2.11 `watchdog`: 公式IWDGで給餌/停止を実装し、正常稼働・リセット時間窓・reset要因を確認し、個別README・HIL/変換テスト・matrix・作業ログに結果を残す。
- [ ] 2.12 `sleep_wake`: 公式のsleepとTimer復帰を実装し、復帰イベントの時系列を確認して消費電力未測定を明記し、個別README・HIL/変換テスト・matrix・作業ログに結果を残す。
- [ ] 2.13 `standby_wake`: 公式AWU/Standbyを実装し、初期待機・復旧手順と復帰動作を確認。終了後に既知blinkで再検出を確認し、個別README・HIL/変換テスト・matrix・作業ログに結果を残す。

## 3. CH32V002への展開

- [ ] 3.1 002用公式SDKの固定revisionと利用条件を確認して必要分をsamples_ch32v002_wch/sdkへコピーし、-DCH32V002・16K/4K・startup・HSI・ISA/ABI・ADC差分を文書化する。blinkのビルドとmapで設定を確認する。
- [ ] 3.2 hil/matrix_ch32v002_wch.jsonとデバイス別期待値を追加し、型番識別領域ガードと003設定の混入防止を単体テストで確認する。
- [ ] 3.3 `blink_and_read`を002公式SDKで移植・ビルドし、003版との差分・個別README・matrixを揃える。対応する003の観測状態を参照し、未観測を継承して記録する。
- [ ] 3.4 `uart`を002公式SDKで移植・ビルドし、003版との差分・個別README・matrixを揃える。対応する003の観測状態を参照し、未観測を継承して記録する。
- [ ] 3.5 `adc`を002公式SDKで移植・ビルドし、003版との差分・個別README・matrixを揃える。対応する003の観測状態を参照し、未観測を継承して記録する。
- [ ] 3.6 `adc_dma`を002公式SDKで移植・ビルドし、003版との差分・個別README・matrixを揃える。対応する003の観測状態を参照し、未観測を継承して記録する。
- [ ] 3.7 `i2c_master`を002公式SDKで移植・ビルドし、003版との差分・個別README・matrixを揃える。対応する003の観測状態を参照し、未観測を継承して記録する。
- [ ] 3.8 `i2c_slave`を002公式SDKで移植・ビルドし、003版との差分・個別README・matrixを揃える。対応する003の観測状態を参照し、未観測を継承して記録する。
- [ ] 3.9 `spi_master`を002公式SDKで移植・ビルドし、003版との差分・個別README・matrixを揃える。対応する003の観測状態を参照し、未観測を継承して記録する。
- [ ] 3.10 `pwm`を002公式SDKで移植・ビルドし、003版との差分・個別README・matrixを揃える。対応する003の観測状態を参照し、未観測を継承して記録する。
- [ ] 3.11 `timer_blink`を002公式SDKで移植・ビルドし、003版との差分・個別README・matrixを揃える。対応する003の観測状態を参照し、未観測を継承して記録する。
- [ ] 3.12 `timer_dma`を002公式SDKで移植・ビルドし、003版との差分・個別README・matrixを揃える。対応する003の観測状態を参照し、未観測を継承して記録する。
- [ ] 3.13 `watchdog`を002公式SDKで移植・ビルドし、003版との差分・個別README・matrixを揃える。対応する003の観測状態を参照し、未観測を継承して記録する。
- [ ] 3.14 `sleep_wake`を002公式SDKで移植・ビルドし、003版との差分・個別README・matrixを揃える。対応する003の観測状態を参照し、未観測を継承して記録する。
- [ ] 3.15 `standby_wake`を002公式SDKで移植・ビルドし、003版との差分・個別README・matrixを揃える。対応する003の観測状態を参照し、未観測を継承して記録する。
- [ ] 3.16 CH32V002実機接続後、各13例の検出・flash・全量readback・可能なHILを実施してログに残す。未観測は理由と必要条件を記録し、実機がなければ本タスクを未完了に保つ。

## 4. 統合確認

- [ ] 4.1 両デバイスの全サンプルをCLIで一括ビルドし、メモリ超過・期待SDKの使用・matrixとの対応を確認する。
- [ ] 4.2 既存ホスト単体テスト、wchテスト、およびch32fun/Arduinoのcollectionが通ることを確認し、必要な実機回帰だけを明示選択して行う。
- [ ] 4.3 READMEの対応表とmatrixを照合し、全13行の状態・根拠・残課題が一致することを確認する。実装のみ・実機確認済みを区別して引き継ぎ可能な状態にする。
