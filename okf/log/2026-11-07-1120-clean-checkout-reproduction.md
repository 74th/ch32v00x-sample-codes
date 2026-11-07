---
type: Reference
title: CH32V003 基準の別 checkout での再現
description: 固定コミットからの build・flash・measure の再実行。
tags: [work-log, ch32v003, reproduction]
devices: [CH32V003F4P6, RP2040]
evidence: hardware
status: draft
---

2026-11-07 11:20 日本時間、同一ホスト上の別ディレクトリにプロジェクトの初回コミット `df9d42d442da91b9313d42665d1ef8d875fa4b97` を clone。book-code はローカル checkout から clone して `4ce0a1b2fe0fa771e68e17944c4ce0d9b20924ae` に固定し、ch32fun は submodule の記録済み `2679ac059f3ada402731e5a10818cc0814e9ec4c` を新規取得した。これは同じホストでの再現であり、別の人・マシンによる独立検証ではない。

別 checkout で `./scripts/ch32fun.sh build`、`./scripts/ch32fun.sh flash`、`python3 hardware/pico-tester/measure.py` を順に実行し、全て終了コード 0。成果物は 1056 bytes、SHA-256 `2edca10fa40bac56fa2131db88eeb1b47199408413ee2b2a85d42a1c12d83783`。flash は CH32V003 を検出し `Image written.` を報告。Pico の完全区間は 49〜50 サンプルで PASS。

Pico は事前に書き込み済みのファームウェアを使用したため、この実行では Pico SDK の取得からの手順を再検証していない。DUT 型番と接続条件は[実機観測記録](../../hardware/ch32v003-observation.md)を参照。再現用 checkout は `/tmp/tmp.XIOLie2AYN/project` に残した。今回の実行後 DUT は給電・動作状態。
