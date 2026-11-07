---
type: Reference
title: CH32V003F4P6 GPIO 観測ピンの資料照合
description: book-code の GPIO サンプルと対象パッケージのピンを照合した記録。
tags: [work-log, ch32v003, gpio, document]
devices: [CH32V003F4P6]
evidence: document
status: draft
---

# 目的と方法

2026-11-07 11:04（日本時間）に、固定 book-code `4ce0a1b2fe0fa771e68e17944c4ce0d9b20924ae` の `blink_and_read-ch32fun/main.c` と、WCH CH32V003 データシート V1.8、同リファレンスマニュアル V1.9 を照合した。データシートの表は変換テキストだけでなく元 PDF のテキスト抽出でも確認した。

# 結果

- 移植元は PC0 を出力、PA1 をプルアップ入力に用いる。プロジェクト版 `samples/ch32v003/blink_and_read` はその動作を引き継ぐ。
- [データシート V1.8](../sources/ch32v003-datasheet.md) 表2-1、PDF p.13–14: F4P6 の TSSOP20 では PC0 は物理10番、PA1 は5番、VSS は7番、VDD は9番、PD1/SWIO は18番。PC0 は SWIO と別ピンであり、観測の候補にできる。別機能との共有は表を参照する。
- [リファレンスマニュアル V1.9](../sources/ch32v003-reference-manual.md) §7.3.1.1–7.3.1.4 は GPIO の設定・入力・出力・ビット設定を扱う。サンプルは ch32fun の GPIO API を用いて PC0 をプッシュプル出力、PA1 を入力に設定する。

# 未確認と注意

現在の DUT の実物刻印・パッケージはまだ確認されていない。物理ピン番号は F4P6 の資料上の値であり、接続済み基板をその型番と断定しない。PC0 が使用できるかは基板の配線・負荷も確認する。観測と電圧は [GPIO 観測記録](../../hardware/ch32v003-observation.md) を参照。

同日、`python3 -m unittest discover -s hardware/pico-tester -p 'test_*.py' -v` を再実行し、正常・不一致・不正フレーム・模擬タイムアウトの4件が成功した。実機上の PASS と電源停止時の MISMATCH は別の[測定記録](2026-11-07-1101-wch-link-power-cycle.md)にある。
