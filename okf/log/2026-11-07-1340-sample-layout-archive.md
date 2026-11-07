---
type: Reference
title: サンプル配置の変更と仕様 archive
description: MCU・フレームワーク別の配置とビルド・実機確認。
tags: [work-log, samples, openspec]
devices: [CH32V003F4P6, CH32V002F4P6]
evidence: hardware
status: draft
---

2026-11-07 13:38〜13:40 日本時間、サンプルを `samples_ch32v003_ch32fun/blink_and_read` と `samples_ch32v002_ch32fun/blink_and_read` に移し、Makefile、操作スクリプト、現行手順を更新。両者の `./scripts/ch32fun.sh build` が成功。接続中の CH32V003 に対し `./scripts/ch32fun.sh flash ch32v003` が成功し、Pico の `measure.py` は完全区間50サンプルで PASS。CH32V002 は移動後の build のみで、移動後の flash・測定は未実施。移動前の最新 ch32fun での実機確認は[移行記録](2026-11-07-1330-standalone-ch32fun.md)を参照。

Pico 側の6テストと OpenSpec のメイン仕様 strict 検証は成功。新規 capability `ch32fun-sample-workflow` をメイン仕様へ同期し、全20タスク完了の change を archive した。過去の作業ログは当時のパスと revision を保持する。
