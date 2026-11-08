# i2c_slave（Arduino Core CH32、CH32V006F8P6）

CH32V002 版 `../../samples_ch32v002_arduino/i2c_slave/` と同じソース（ピン・ライブラリは同一）。ボード定義は公式 core 1.0.6 の `CH32VM00X_EVT`（`pnum=CH32V006K8`）をそのまま使い、002 用の Flash/RAM・スタック・ヒープ上書きは持たない。観測状態は `hil/matrix_ch32v006_arduino.json` と `okf/log/` の実測ログを参照（002/003 の結果は継承しない）。

## 書籍のコードとの差（範囲判定）
`on_request` の範囲判定を、実際に読む添字で行い範囲外は `0xFF` を返すように直した（002 版と同じソース。詳細は 002 の README）。
