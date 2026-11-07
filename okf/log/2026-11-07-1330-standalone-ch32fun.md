---
type: Reference
title: 独立 ch32fun submodule への移行と両デバイスの実機検証
description: book-code のビルド依存を除き最新 ch32fun を固定した結果。
tags: [work-log, ch32fun, ch32v003, ch32v002]
devices: [CH32V003F4P6, CH32V002F4P6, RP2040]
evidence: hardware
status: draft
---

2026-11-07 13:30〜13:34 日本時間。取得時点の ch32fun upstream HEAD `b28d285460ce052a179dba8f4a22c6f73ff8e328` を `externals/ch32fun` の Git submodule とし、ビルド・書き込みを直接そこへ向けた。book-code は出典および調査用であり実行依存ではない。WCH-LinkE firmware 2.22、RISC-V GCC 14.2.0、GNU Make 4.4.1。旧版での結果は過去ログを参照。

- CH32V002: `./scripts/ch32fun.sh build ch32v002`、`./scripts/ch32fun.sh flash ch32v002`、`python3 hardware/pico-tester/measure.py` が成功。最新 minichlink は `Detected CH32V002` と Flash 16 KB を報告。ビルド成果物 1068 bytes、SHA-256 `3758de381815fe650f2d64b8babc15af29f4683bfadfdd6c2bd039b2004419a7`。Pico の完全区間は各50サンプルで PASS。今回の書き込み後の flash 読み戻しは未実施。
- CH32V003: 3.3 V 出力をオフ指示後ユーザーがボードを差し替え。`build ch32v003`、`flash ch32v003`、Pico 測定が成功。完全区間は50〜51サンプル。成果物 1056 bytes、SHA-256 `5688ff09715f63c04a6855129f7b3d6c85359a56ae3ba6cbd31130e9894561dc`。flash 1056 bytes の読み戻しは `cmp` で一致。
- Pico PC 側の6テストは成功。GPIO のサンプル間隔は約10 msであり精密な時間測定ではない。

新しい minichlink は CH32V002 の識別領域読み出し時に `Something went wrong and we couldn't detect memory region` と表示するが、4 bytes の値 `0x00200620` は取得でき、その後の書き込み・GPIO 動作は成功した。この警告の原因は未調査。実行終了時は CH32V003 が接続・動作中。
