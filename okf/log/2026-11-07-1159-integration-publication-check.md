---
type: Reference
title: 段階別の実機記録と公開対象の確認
description: 依存順の検証記録と Git 対象の確認。
tags: [work-log, integration, review]
devices: [CH32V003F4P6, CH32V002F4P6, RP2040]
evidence: hardware
status: draft
---

2026-11-07 11:59 日本時間、検証記録を依存順に確認した。環境・CH32V003 build/flash/readback/GPIO は [11:13 記録](2026-11-07-1113-ch32v003-flash-readback-measure.md)、未接続時の偽成功と対策は [未接続記録](2026-11-07-1113-disconnected-flash-preparation.md)、Pico の USB 再書き込み・タイムアウトは [Pico 記録](2026-11-07-1121-pico-reflash-discovery.md)、CH32V002 の build/flash/readback/GPIO は [11:56 記録](2026-11-07-1156-ch32v002-flash-measure.md)。Pico 側の模擬テスト6件を再実行し成功した。

CH32V003 は LinkE firmware 2.9、CH32V002 は更新後 2.22 で測定した。両デバイスを同一の firmware 2.22 で一続きに再測定した結果ではない。各段階の失敗は各記録で区別した。

`git status --short --ignored` は `xprivate/`、`externals/`、ビルド出力を無視対象として表示。`git ls-files --cached --others --exclude-standard` を PDF、画像、`xprivate/`、`externals/`、変換ディレクトリ名で照合し該当なし。公開対象の OKF は資料の識別・要約・参照・実測ログとして整理し、PDF・全文変換・抽出画像や表は追加していない。確認時点の Git 対象に限るため、公開直前にも再確認する。
