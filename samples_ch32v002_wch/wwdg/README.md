# wwdg（公式WCH SDK、CH32V002）

WWDG（ウィンドウウォッチドッグ）のサンプル。**書籍にない内容**で、書籍の移植ではない（`hil/matrix_ch32v002_wch.json` では種別 `additional-not-in-book`）。出典は公式 EVT の `EXAM/WWDG`（`externals/ch32v002_004_005_006_007`、調査用）で、ドライバ `ch32v00X_wwdg.{c,h}` を `../sdk` にコピーしている（出所は `../PROVENANCE.md`）。

## 動作
HCLK 48 MHz、分周 /8（1カウント約 683 µs）、カウンタ 0x7F、窓 0x5F。ビルド時に `-DWWDG_MODE=<n>`（変更したら `make clean`）で切り替える。

| MODE | 動作 | 期待 |
| --- | --- | --- |
| 0（既定） | 5 ms ごとのループでカウンタを読み、窓の値を下回っているときだけフィード | リセットされず `.` が増え続ける |
| 1 | 5 ms ごとに無条件でフィード（カウンタ約 0x77 > 窓 0x5F） | 早すぎるフィードで WWDG リセット。`.` は1個 |
| 2 | フィードしない | 約 43.7 ms（0x40 を下回る）で WWDG リセット。`.` は9個 |

UART（USART1 TX = PD5、115200）に、起動時 `cause=WWDG|IWDG|other`（`RCC` のリセットフラグを読んで消す。改行は `\n`）、1.5 s 待った後（`-DWWDG_WAIT_MS` で変更可）に WWDG を有効化し、ループごとに `.` を出す。出力は、Pico の UART の1回の取得（32バイト）に起動2回分が入る長さにしてある。待ちは、有効化した WWDG が止められず、起動直後にリセットを繰り返すと書き込み器から接続できなくなるおそれがあるため。

## 公式 EVT の例との違い
- 早期割り込み（EWI）と NVIC の設定を使わない。
- 出力は `USART_Printf_Init`（USART1 PD5）。点は stdio ではなく USART に直接書く。
- 起動時のリセット要因の表示と有効化前の待ちを加えた。窓と分周は公式例と同じ（`WWDG_Config(0x7f, 0x5f, WWDG_Prescaler_8)`）。

## 観測状態
**hil-verified**（CH32V002 実機、3ビルド）。書き込み・全量読み戻し・Pico による UART 観測を別の段階で実行し、モード 0 はリセットされず、モード 1 は点1個で `cause=WWDG`、モード 2 は点9個で `cause=WWDG` を観測した（`tests/hil/wch/test_wwdg.py`、記録は `../../okf/log/2026-11-09-0013-add-wwdg-sample.md`）。EWI、デバッグ中の動作、リセットまでの時間の絶対精度は未確認。
