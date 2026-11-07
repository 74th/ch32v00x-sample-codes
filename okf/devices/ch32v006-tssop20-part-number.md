---
type: Open Question
title: CH32V006 TSSOP20品の型番（F8P6とF8P7）
description: 手持ちのCH32V006F8P6は、CH32V006/005データシートV2.0の型番表に載っていない。V2.0に載っているTSSOP20品はF8P7だけ。
tags: [device, part-number, open-question]
devices: [CH32V006]
evidence: hypothesis
status: draft
generated: { by: claude-code/claude-opus-5-5, at: 2026-11-07T01:49:23Z }
sources:
  - id: v006-ds
    resource: /sources/ch32v006-datasheet.md
    title: CH32V006/005 Datasheet V2.0
---

# 事実（資料確認済み）

- 手持ちの部品の刻印は `CH32V006F8P6`（TSSOP20）。
- データシートV2.0の型番表に載っているCH32V006のTSSOP20品は `CH32V006F8P7` だけで、最高動作周囲温度は105℃。[^v006-ds]
- 同じ表では、型番末尾の数字が最高動作周囲温度と対応している。CH32V006には `E8R6`（85℃）と `E8R7`（105℃）が並んで載っている。CH32V005の各品（末尾6）と `CH32V006F4U6` は85℃。[^v006-ds]
- ピン定義表（表2-1-1）の列見出しも `V006F8P7` になっている。[^v006-ds]

# 仮説

- `F8P6` は、`F8P7` と同じダイとピン配置で、最高動作周囲温度が85℃の品種（または旧品種）である可能性がある。根拠は、末尾の数字と温度の対応だけ。

# 確認方法

1. 旧版のデータシートか、WCHの製品ページにF8P6の記載があるかを確認する。
2. 実機で、チップ情報（フラッシュ容量、ESIG）とピン機能が、F8P7の記載と一致するかを確認する。
3. 結果が出るまでは、F8P7の記載をF8P6にも当てはまるものとして使い、その旨を試験記録に残す。

[^v006-ds]: CH32V006/005 Datasheet V2.0, 型番表 PDF p.2、表2-1-1 PDF p.19（印字p.17）
