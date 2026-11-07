# WCH公式SDK周辺サンプルの一括ビルド・回帰・表の整合確認（タスク4.1〜4.3）

作業日時: 2026-11-08 01:56 JST（ホストdateで確認、記録は作業直後）。実機はCH32V003（WCH-LinkE 2.22、Pico fw v2、既存固定配線）。**CH32V002の実機は無し**。

## 4.1 一括ビルド（実測）
`uv run python scripts/wch-sdk.py build --all`（新規追加。毎回clean）: CH32V003 14個＋CH32V002 14個（13例＋blink）が全て成功、問題0件。
各ELFのデバッグ情報（`nm -l`）で、使用ソースが当該デバイスの`samples_<device>_wch`のみで`externals/`や他デバイスが無いこと、mapのメモリ配置がCH32V003=16K/2K、CH32V002=16K/4Kであることを検査。コードサイズ: 003は最大7,944 B（i2c_master）、002は最大8,680 B（i2c_master）で16 KBに収まる。
matrix（003/002）の13行は、ビルドされるサンプル集合（blinkを除く）と一致（単体テスト）。

## 4.2 回帰（実測）
- ホスト: `uv run pytest tests` → 271件成功（HIL以外）。`pytest --collect-only`はch32fun/arduino/wchのどれでも39件。
- CH32V003実機のwch HIL全13件を、試験の修正後に実行して全件成功。その過程で `blink_and_read` が約3〜4割の確率で失敗していた（原因: `minichlink -b`がDUTを0.5秒以内に2回起動し、32 B捕捉が`init start loop 0 init start`で埋まる）。テストを「先頭3行（init/start/loop 0）」の判定に改め、settle 1.5 sを加えて10回連続成功。DUT側の不具合ではない。
- 既存ch32fun回帰: `pytest --hil tests/hil/test_blink_and_read.py`（blink_and_read/button）3件成功。Arduino HIL、ch32fun/Arduinoのその他のHILは実機では再実行していない（既定の選択・判定を変更していない。collection結果と単体テストのみ）。
- standby_wake後は毎回、既知blinkへの復旧と検出（`Detected CH32V003`）を確認。

## 4.3 READMEとmatrixの照合
READMEの対応表を`hil/matrix_wch.json`から再生成し、単体テスト（`test_wch_readme_table_matches_matrix`）で、003・002のREADME表の13行の状態、003は根拠ログのファイル名がmatrixと一致することを確認。003は全13行が`hil-verified`（各行の制限・未観測事項はREADME表の「制限・残課題」に記載）、002は全13行が`build-only`（003の状態は参照のみで継承せず）。

## 未確認・未完了
- **タスク3.16（CH32V002実機）は未完了**: 実機のCH32V002が接続されていないため、002の検出・書き込み・読み戻し・HILは実施していない。接続後に`uv run pytest --hil --hil-device ch32v002 --hil-framework wch tests/hil/wch`を実行する（ADCは12-bit用の閾値を定義済みだが未実行）。
- 003の各サンプルの未観測事項（実センサー、オシロでの精度、消費電力、表示器など）は各README・matrixに記載のとおり。
