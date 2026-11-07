---
type: Reference
title: Pico の USB 書き換えと GPIO 観測の作業記録
description: Pico の自動 BOOTSEL 移行と GPIO サンプル・判定の確認。
tags: [work-log, pico, gpio, measurement]
devices: [CH32V003, RP2040]
evidence: hypothesis
status: draft
---

# 記録について

作業日: 2026-11-07（日本時間）。個々の実行時刻は不明。ファイル名の 11:01 は記録作成時刻であり、実行時刻ではない。

# 目的と条件

Pico の BOOT ボタンを毎回押さずに USB で書き換え、CH32V003 の PC0 の変化を取得する。ユーザー申告では、DUT は WCH-LinkE の 3.3 V から給電され、PC0 と Pico GP0 の間に 1 kΩ がある。ユーザー実測の PC0 High は GND 基準 3.1 V。DUT VDD の実測、実物の型番・パッケージ、信号切断の方法は未記録。

Pico SDK 2.2.0 `a1438dff1d38bd9c65dbd693f0e5db4b9ae91779`、TinyUSB `86ad6e56c1700e85f1c5678607a762cfe3aa2f47`、picotool 2.1.1。Pico は RP2040 として認識された。

# 実施と結果

1. BOOTSEL 状態から `picotool load -v -x hardware/pico-tester/build/pico_gpio_tester.uf2` で書き込みと照合に成功。
2. 起動直後の `picotool info -a -f` は再起動中のエラーになった。USB 再認識後、`picotool load -f -v -x hardware/pico-tester/build/pico_gpio_tester.uf2` で BOOT ボタンを使わず再書き込み・照合に成功。
3. `python3 hardware/pico-tester/measure.py` で GP0 を約10 ms間隔で300点取得。完全な High/Low 区間は49〜50点で PASS。
4. 模擬入力で正常、一定値・周期違い、応答なしを PASS、MISMATCH、TIMEOUT に区別した。異常なフレームもテストした。

# レビュー用の注意

間隔はソフトウェアによる要求値で精密な周期測定ではない。判定は両端を除く3区間以上が40〜60点であることを確認する。書き換え中にファームウェアが応答しなくなった場合の復旧には手動 BOOTSEL またはデバッガーが必要。配線の安全レビューは完了していない。

関連: [Pico の手順](../../hardware/pico-tester/README.md)、[配線案](../../hardware/wiring.md)。
