---
type: Reference
title: DUT 未接続時の書き込み失敗確認の準備
description: SWIO を切り離すための電源出力停止。
tags: [work-log, ch32v003, flash]
devices: [CH32V003F4P6]
evidence: hypothesis
status: draft
---

2026-11-07 11:13:51 日本時間、DUT 未接続時の flash 失敗を確認する準備として、固定 ch32fun 版 minichlink の `-t` を実行。`Found WCH Link` を出力し終了コード 0。SWIO の切り離しをユーザーに依頼した。前回同じ出力停止後の VDD は 0.606 V と測定されているが、今回の電圧は未測定。

11:14:48、ユーザーが SWIO を外したと報告後、`./scripts/ch32fun.sh build` は終了コード 0。続く `flash` は固定版 minichlink が `No detected chip`、`Unknown chip fallback` を出力したにもかかわらず `Image written`、終了コード 0 と返し、スクリプトも誤って `FLASH OK` と表示した。実際には書き込みを確認できない。

スクリプトを修正し、終了コードに加えて `Detected: CH32V003` と `Image written.` を要求し、未検出・未知チップの報告を失敗扱いにした。11:15:05、SWIO を外したまま再試行し `FLASH FAILED`、終了コード 1 を確認した。固定された minichlink の出力形式に依存する判定であり、実際の書き込み内容の照合は別途必要。

各試行後に `minichlink -t` を実行し、終了コード 0。通常の flash 初期化は WCH-LinkE の 3.3 V を有効化し得るため、テスト後は停止を指示した。停止指示のみで DUT が完全に無電源になるとは扱わない。

11:15:54、ユーザーによる SWIO 再接続後、修正済み `./scripts/ch32fun.sh flash` は `Detected: CH32V003`、`Image written.`、`FLASH OK` を出力し終了コード 0。続く `python3 hardware/pico-tester/measure.py` は、完全区間が各50サンプルで PASS。DUT は給電・実行状態。今回の再書き込み後の読み戻しは実施していない（直前の読み戻し照合は[別記録](2026-11-07-1113-ch32v003-flash-readback-measure.md)）。
