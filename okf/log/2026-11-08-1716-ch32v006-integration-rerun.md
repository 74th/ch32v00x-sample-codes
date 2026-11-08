# CH32V006 Arduino / WCH の統合再実行（タスク 6.1）

- 作業日時: 2026-11-08 17:10:49〜17:30:45 JST（`date` で確認。Arduino 通し 17:16:29〜17:18:22、WCH 通し 17:18〜17:21 と 17:28〜17:30、基準 blink 17:30:40〜17:30:45）。記録は 17:35 JST 頃。
- 対象: CH32V006F8P6（ユーザー申告）。固定配線、電圧未測定。F8P6=F8P7 は前 change の仮定のまま。ツール・ソースは前ログと同じ（HEAD 532bf54＋未コミット変更）。結果は専用の保存先 `xprivate/runs/2026-11-08-1930-ch32v006-arduino-final/` と `…-1950-ch32v006-wch-final2/`（公開しない）。

## 途中で見つかった不具合（実測）と修正
1. Arduino 通し（17:10〜）で `i2c_slave_test_master` が失敗。同期用の取り込み（5 バイト上限）が、先頭の「20」の後で書き込みの 1 バイト手前（`rx=20 10 02 03 04`）で終わる回があった（8 回中 1 回。以前の単独実行でも 1 回）。DUT の挙動ではなく、同期の不成立。同期を最大 3 回まで取り直す形に修正し（各試行は結果に残す）、判定本体（read・次の書き込み・カウンタ増加）は厳密なまま。修正後、単独で 12 回すべて合格（うち 1 回は取り直し発生）。
2. WCH 通し（17:18〜）で `test_wch_pwm` が失敗。PD2 の 1 読みが周期 20 µs（公称 10.67 µs の約 2 倍、Pico のソフトウェア取り込みのエッジ取りこぼし）。単独で 12 回中 1 回再現（21 µs）。公称周期の 2〜4 倍付近の読みは取りこぼしとして分解能外に分類（記録はする、有効な PD2 読み 10 件以上は従来どおり必須）。修正後 15 回すべて合格（分解能外の読みは 17〜22 件）。**このテスト変更は全機種に適用される**（003/002 の過去結果は未再判定）。

## 結果（実測、最終の通し実行）
- Arduino（`--hil-device ch32v006 --hil-framework arduino`）: **10 passed、1 skipped、2 xfailed**（112 s）。
  - 必須通常 8 件（`blink_and_read`、`adc`、`i2c_master`、`i2c_slave_test_master`、`spi_master`、`i2c_oled`、`neopixel`、`pwm`）と `uart`（複合）が PASSED。`pwm` は PD2＋PC0（ユーザー判断）。
  - `i2c_slave`（通常対象の成功には数えない）も PASSED（取引間隔 0.3 s）。
  - 参考試験は XFAIL で別ファイル保存: PATTERN 3（PC6/PC5 リマップ）、PD2＋PC4（PC4 無信号、原因未特定）。XPASS はなし。
  - SKIPPED は 003 専用の `i2c_oled_96x16`（006 にはサンプルなし）。
- WCH（`--hil-framework wch`）: **14 passed、1 xfailed**（167 s）。13 例（`timer_blink` は tim1/tim2 の 2 件）が PASSED、`wch_pwm_pc4_reference` が XFAIL。基準 blink は build→flash→readback 一致→observe（PC0 半周期 400〜600 ms、`pass: true`）。
- 全結果ファイル（Arduino 12、WCH 15）を機械的に確認: `chip_id=0x00630620`（0x006）、`dut_readback`・`cleanup` はすべて pass。`primary_failure` が残るのは参考試験の 3 件（XFAIL）のみ。

## 整合レビュー
- README（ルート・各サンプル）、`hardware/ch32v006-reproduction.md`、`hil/matrix_ch32v006_{arduino,wch}.json`、このログ群が同じ状態を表している（Arduino 10 スケッチ・WCH 13 例が機能確認済み、例外はユーザー判断として明記、`i2c_slave` は通常対象外）。
- 範囲外のものを確認済みにしていない: ADC の精度・校正、時間の精度、Sleep/Standby の消費電流、実 OLED・実 LED・実センサー、WS2812 規格適合、PC4 の原因、F8P6 の資料上の位置付け、PC5/PD7 の RST 設定。

## 未確認
- 6.2（003/002 の実機回帰、006 ch32fun の回帰）は未実施。
