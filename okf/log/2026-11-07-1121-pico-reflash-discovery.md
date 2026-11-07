---
type: Reference
title: 別 checkout の Pico ビルドと USB 再認識の検証
description: Pico の再書き込み直後の検出失敗と修正後の再試行。
tags: [work-log, pico, usb, reproduction]
devices: [CH32V003F4P6, RP2040]
evidence: hardware
status: draft
---

2026-11-07 11:21〜11:22 日本時間、別 checkout `/tmp/tmp.XIOLie2AYN/project` のコミット `df9d42d442da91b9313d42665d1ef8d875fa4b97` から Pico 側の再現を試した。Pico SDK 2.2.0 `a1438dff1d38bd9c65dbd693f0e5db4b9ae91779` は既存ローカル checkout を使用。CMake・Ninja でファームウェアをビルドし、`picotool load -f -v -x` による自動 BOOTSEL 移行、書き込み、照合に成功した。

直後の `python3 hardware/pico-tester/measure.py` は USB 再認識より先に検出を試み `expected one Pico, found 0`、終了コード 3 となった。プロジェクト側の測定コマンドを修正し、Pico 未検出時は設定時間まで再検出を待ち、時間切れは TIMEOUT とするようにした。複数台検出は従来どおりエラー。検出待ちと応答待ちにはそれぞれタイムアウトを適用する。

修正後、正常・不一致・不正フレーム・測定応答タイムアウト・検出待ち・検出タイムアウトの6テストに成功。`picotool load -f -v -x` の直後に修正済み測定コマンドを実行し、PASS（完全区間49〜50サンプル）。Pico は観測ファームウェア、DUT は点滅プログラムを実行している。

同一ホスト・既存 SDK での検証であり、別環境で SDK の取得からの再現は未確認。初回の失敗と修正後の結果は別々に記録する。
