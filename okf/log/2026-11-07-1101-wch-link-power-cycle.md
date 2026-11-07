---
type: Reference
title: WCH-LinkE の電源制御と PC0 観測の作業記録
description: 3.3 V 出力の停止・再開と Pico による信号観測。
tags: [work-log, wch-link, power, gpio]
devices: [CH32V003, RP2040]
evidence: hypothesis
status: draft
---

# 記録について

作業日: 2026-11-07（日本時間）。実行時刻は不明。ファイル名の 11:01 は記録作成時刻であり、実行時刻ではない。

# 目的と条件

WCH-LinkE の 3.3 V 出力制御に伴う CH32V003 PC0 の変化を、接続済み Pico の GP0 で確認する。DUT 電源は WCH-LinkE から、PC0〜GP0 に 1 kΩ というユーザー申告。PC0 High は 3.1 V とユーザーが測定。DUT VDD の電源断時電圧は未測定。

# 実施と結果

1. 固定 ch32fun の `minichlink -t` を実行後、`python3 hardware/pico-tester/measure.py` で300点を取得。すべて Low で MISMATCH。
2. 同じ minichlink の `-3` で 3.3 V 出力を戻した。続く測定は High/Low とも完全区間50点で PASS。終了時は出力を戻した状態。

# レビュー用の注意

この結果は PC0 の変化を示し、DUT VDD が 0 V になったことや逆流がないことの証明ではない。VDD の実測と電源断時の信号線の扱いは未確認。固定版 minichlink の通常の初期化は 3.3 V を有効にする場合があるため、電源停止状態を保つ操作では注意する。

関連: [暫定観測記録](../../hardware/ch32v003-observation.md)、[配線案](../../hardware/wiring.md)。
