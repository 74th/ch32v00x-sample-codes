---
type: Open Question
title: CH32V00XのGPIO入力でプルダウンを使えるか
description: CH32V00Xリファレンスマニュアルには、プルダウンを使えるとする記述と、プルアップだけとする記述が混在している。
tags: [gpio, pull-down, porting, open-question]
devices: [CH32V002, CH32V004, CH32V005, CH32V006, CH32V007]
evidence: hypothesis
status: draft
generated: { by: claude-code/claude-opus-5-5, at: 2026-11-07T01:49:23Z }
sources:
  - id: v003-rm
    resource: /sources/ch32v003-reference-manual.md
    title: CH32V003 Reference Manual V1.9
  - id: v00x-rm
    resource: /sources/ch32v00x-reference-manual.md
    title: CH32V00X Reference Manual V1.5
---

# 問題

CH32V003では、`CNFy=10b`（入力時）を「プルアップ・プルダウン付き」とし、`OUTDR` の対応ビットでプルアップ（1）とプルダウン（0）を選ぶ。[^v003-rm]

CH32V00Xリファレンスマニュアルでは、記述が食い違っている。[^v00x-rm]

| 箇所 | 記述の要旨 | プルダウン |
| --- | --- | --- |
| 7.1 GPIOの概要（PDF p.73） | 入力モードの一覧にプルアップ入力とプルダウン入力がある | あり |
| 7.1 IOポート構造（PDF p.73–74） | 入力ドライバには弱いプルアップ抵抗がある、とだけ書かれている | 言及なし |
| `CFGLR` の `CNFy=10b`（PDF p.82） | 「プルアップ付き」モード | 言及なし |
| `OUTDR` の `ODRy`（PDF p.83） | プルアップ付き入力モードのとき、1でプルアップ、0でプルダウン | あり |

# 影響

CH32V003向けサンプルのうち、入力ピンをプルダウンにしているものは、CH32V00Xでは期待どおりに動かない可能性がある。

# 解決方法

実機で確かめる。対象ピンを `CNFy=10b`、`ODRy=0` に設定し、外部を開放したまま、弱い外部駆動を与えたときの入力値を測定する。プルダウンが働くかを、デバイスごと（まずCH32V002F4P6とCH32V006）に記録する。

# 実機での確認（2026-11-08、実測）

CH32V002F4P6 と CH32V006F8P6（各 1 個体）で、PA1 を `CNFy=10b` にして確かめた（[ログ](../../log/2026-11-08-2137-fix-ch32v00x-sample-findings.md) の 7.3）。PA1 は治具で 10 kΩ＋1 µF を介して Pico に繋がる。Pico で 1 µF を充電・放電した後、Pico 側を開放し、DUT が 1 ms ごとに PA1 を読んだ。

| 設定 | 002 | 006 |
| --- | --- | --- |
| 浮動入力（`CNFy=01b`） | 1 s 変化なし | 1 s 変化なし |
| `CNFy=10b`、`ODRy=0`（High に充電した後） | 57 ms で Low | 56 ms で Low |
| `CNFy=10b`、`ODRy=1`（Low に放電した後） | 25 ms で High | 24〜25 ms で High |

→ 両デバイスとも、`ODRy=0` でプルダウンが働く（抵抗値は測っていない。データシートの等価抵抗 35〜55 kΩ と時定数の桁は合う）。各 2 回、同じ結果。このファイルの `evidence` は他の型番（004/005/007）を含むため `hypothesis` のままにする。

[^v003-rm]: CH32V003 Reference Manual V1.9, 7.3.1.1 / 7.3.1.3, PDF p.56–57
[^v00x-rm]: CH32V00X Reference Manual V1.5, 7.1 / 7.3.1.1 / 7.3.1.3, PDF p.73–74, 82, 83（印字p.71–72, 76, 77）
