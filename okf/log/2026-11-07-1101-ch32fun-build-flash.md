---
type: Reference
title: CH32V003 ch32fun 環境構築と書き込みの作業記録
description: ツール環境、ビルド、書き込み、起動ログの記録。
tags: [work-log, ch32v003, build, flash]
devices: [CH32V003]
evidence: hypothesis
status: draft
---

# 記録について

作業日: 2026-11-07（日本時間）。実行時刻の正確な記録は残っていない。ファイル名の 11:01 はこの記録を作成した時刻であり、実行時刻ではない。会話と既存の検証記録から後日ではなく同日に整理した。

# 目的と条件

CH32V003 の build、flash、実行を区別して確認する。Ubuntu 26.04 x86-64、RISC-V GCC 14.2.0、GNU Make 4.4.1、ホスト GCC 15.2.0。WCH-LinkE firmware 2.9。マイコンのパッケージは未確認。

- book-code: `4ce0a1b2fe0fa771e68e17944c4ce0d9b20924ae`
- ch32fun: `2679ac059f3ada402731e5a10818cc0814e9ec4c`（book-code の gitlink）
- プロジェクト内サンプル: `samples/ch32v003/blink_and_read/`。book-code の CC0 サンプルを基にし、起動・ループのログを追加。

# 実施と結果

1. 固定 ch32fun を初期化し、コミット ID を確認。minichlink はその checkout からビルドした。ホスト GCC 15 の既定モードではビルドできず、`-std=gnu17` を指定して成功した。
2. `./scripts/ch32fun.sh build` で書き込み可能な成果物を生成。`main.bin` は 1056 bytes、SHA-256 は `2edca10fa40bac56fa2131db88eeb1b47199408413ee2b2a85d42a1c12d83783`。
3. `./scripts/ch32fun.sh flash` で CH32V003 の検出と `Image written` を確認。読み戻し照合は未実施。
4. 固定版 minichlink の `-T` で `blink_and_read started` と `PC0 high` / `PC0 low` の繰り返しを取得。LED の点滅はユーザーが目視確認した。
5. クリーンなシェルで環境確認とビルドを実行。`PKG_CONFIG_LIBDIR=/nonexistent` によりライブラリを見えなくすると、不足が表示され終了コード 1 になった。

# レビュー用の注意

書き込み成功ログ、起動ログ、LED の目視は別の証拠。書き込み内容の読み戻しと対象パッケージの確認は未完了。サンプルに追加した printf はタイミングに影響し得る。

関連: [暫定観測記録](../../hardware/ch32v003-observation.md)、[操作手順](../../README.md)。
