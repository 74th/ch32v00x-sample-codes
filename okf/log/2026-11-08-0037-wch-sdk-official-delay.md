# WCH公式Delay関数への変更

作業日時: 2026-11-08 00:37 JSTのホストdate確認後に実施。記録は作業完了後（正確な完了時刻は未記録）。

## 目的・条件

ユーザー指示: 公式SDKの使い方を検証するため、自作delay_msではなく公式Delay_Init/Delay_Msを使う。
CH32V003、WCH-LinkE、Pico、既存配線PC0→1 kΩ→GP5・共通GNDは直前の環境構築と同じ前提。今回も電圧・配線の物理的再測定はしていない。
SDK revision 4e1b7437ada5d3ae8831a6f4b811a6320e4e23c7、WCH GCC 15.2.0、固定ch32fun b28d285460ce052a179dba8f4a22c6f73ff8e328。

## 変更

自作delay_msを削除し、mainでDelay_Initを一度呼んだ後、Delay_Ms(500)を使用。公式Debug/debug.c・debug.hおよび依存するUSARTドライバの.c/.hを無改変コピー。Makefileとconfヘッダを更新。元の著作権・使用条件を保持、出所・SHA-256はPROVENANCE.mdに追記。計14ファイル。

## コマンド・結果（実測）

```sh
uv run python scripts/wch-sdk.py build
uv run python scripts/wch-sdk.py flash
uv run python scripts/wch-sdk.py observe --output /tmp/wch-sdk-official-delay.json
.arduino/official/data/packages/WCH/tools/riscv-wch-gcc/15.2.0/bin/riscv32-wch-elf-nm samples_ch32v003_wch/blink/main.elf
git diff --check
```

- build成功。Flash 1092 B、RAM 268 B（data 8 B、通常BSS 4 B、stack 256 B）。sizeはtext 1084 / data 8 / bss 260。
- 公式debug.cの_writeにunused parameter fd警告1件。エラーなし。元ソースを保つため警告抑制・改変はしなかった。
- 固定minichlinkでDetected CH32V003とImage written.を確認。1092 B全量の読み戻し照合成功。リセット成功。
- nmでDelay_Init/Delay_Msを確認。USART実装・_write・_sbrkは未使用として除去されている（USART1_IRQHandlerは既定の弱い割り込みハンドラとして残る）。
- Pico観測は300点・10 ms間隔。完全な5区間はいずれも50点＝500 msで判定pass。電圧・精密波形測定ではない。

```json
{
  "port": "/dev/ttyACM0",
  "pin": "PC0 -> Pico GP5",
  "count": 300,
  "interval_us": 10000,
  "runs": [
    [
      "1",
      42
    ],
    [
      "0",
      50
    ],
    [
      "1",
      50
    ],
    [
      "0",
      50
    ],
    [
      "1",
      50
    ],
    [
      "0",
      50
    ],
    [
      "1",
      8
    ]
  ],
  "pass": true,
  "criterion": "at least 4 complete half-periods, each 400..600 ms"
}
```

main.bin SHA-256: `01255b9ae447777c94e408215bfcda5c62ff27aed6f9ca0b09452f57d283a1b2`

## 未確認事項

Delay_Us、UART、他周辺、CH32V002は今回未検証。書き込んだ公式Delay版blinkをDUTに残した。PicoはfinallyのRESET_SAFEで終了。
