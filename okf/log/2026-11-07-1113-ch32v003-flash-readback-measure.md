---
type: Reference
title: CH32V003F4P6 書き込み・読み戻し・起動・GPIO 測定
description: ビルド済み成果物の実機書き込みから観測までの記録。
tags: [work-log, ch32v003, flash, gpio]
devices: [CH32V003F4P6, RP2040]
evidence: hardware
status: draft
---

2026-11-07 11:13:00〜11:13:17 日本時間。型番はユーザー確認。WCH-LinkE firmware 2.9、ch32fun `2679ac059f3ada402731e5a10818cc0814e9ec4c`、Pico RP2040。DUT の 3.3 V は WCH-LinkE、PC0 と Pico GP0 は 1 kΩ 経由とユーザー申告。直前の `-t` 後の VDD–VSS は 0.606 V（ユーザー実測）。

1. `./scripts/ch32fun.sh flash`: CH32V003 を検出し `Image written`、終了コード 0。前段の停止状態から書き込み時の初期化で給電された。
2. `minichlink -r <一時ファイル> flash 1056 -b`（固定 checkout のバイナリ）で1056バイトを読み戻し、`cmp samples/ch32v003/blink_and_read/main.bin <一時ファイル>` が一致。読み戻し SHA-256 `2edca10fa40bac56fa2131db88eeb1b47199408413ee2b2a85d42a1c12d83783`。
3. `timeout 5s stdbuf -oL -eL <固定minichlink> -b -T` で再起動し、`blink_and_read started` と `PC0 high` / `PC0 low` の繰り返しを取得。終了コード 124 は取得時間を5秒で打ち切った timeout によるもの。
4. `python3 hardware/pico-tester/measure.py`: PASS。連続区間は `1:37, 0:50, 1:50, 0:50, 1:50, 0:50, 1:13` サンプル。両端は部分区間。10 ms は要求間隔であり精密測定ではない。

読み戻し、起動ログ、GPIO 信号は独立した結果として記録する。未確認: 配線保護の全条件と残留電圧の経路。残留電圧の切り分けは今回必須としないというユーザー判断。終了時は書き込み済みファームウェアが動作している。
