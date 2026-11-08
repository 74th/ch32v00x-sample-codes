# i2c_slave（Arduino Core CH32、CH32V006F8P6）

CH32V002 版 `../../samples_ch32v002_arduino/i2c_slave/` と同じソース（ピン・ライブラリは同一）。ボード定義は公式 core 1.0.6 の `CH32VM00X_EVT`（`pnum=CH32V006K8`）をそのまま使い、002 用の Flash/RAM・スタック・ヒープ上書きは持たない。観測状態は `hil/matrix_ch32v006_arduino.json` と `okf/log/` の実測ログを参照（002/003 の結果は継承しない）。
