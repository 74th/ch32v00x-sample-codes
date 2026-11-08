---
type: Device Difference
title: GPIOx_CFGLRのMODEフィールド（CH32V003とCH32V00X）
description: CH32V003ではMODEyが2ビットで出力速度を3段階選べるが、CH32V00Xでは1ビットで出力/入力の切り替えだけになり、上位ビットは予約になっている。
tags: [gpio, register, porting]
devices: [CH32V003, CH32V002, CH32V004, CH32V005, CH32V006, CH32V007]
evidence: document
status: draft
generated: { by: claude-code/claude-opus-5-5, at: 2026-11-07T01:49:23Z }
sources:
  - id: v003-rm
    resource: /sources/ch32v003-reference-manual.md
    title: CH32V003 Reference Manual V1.9
  - id: v00x-rm
    resource: /sources/ch32v00x-reference-manual.md
    title: CH32V00X Reference Manual V1.5
---

# 要点

`GPIOx_CFGLR`（オフセット0x00、リセット値 `0x44444444`）は、どちらのデバイスでもピン1本につき4ビットを割り当てている。違うのは、そのうちMODEの部分。

| ピンyの4ビット | CH32V003 | CH32V00X |
| --- | --- | --- |
| 上位2ビット | `CNFy[1:0]` | `CNFy[1:0]` |
| 3ビット目 | `MODEy[1]` | 予約（RO、0） |
| 最下位ビット | `MODEy[0]` | `MODEy` |

MODEの値の意味:

| MODE | CH32V003 `MODEy[1:0]`[^v003-rm] | CH32V00X `MODEy`[^v00x-rm] |
| --- | --- | --- |
| 入力 | `00` | `0` |
| 出力（最大10MHz） | `01` | なし |
| 出力（最大2MHz） | `10` | なし |
| 出力（最大30MHz） | `11` | `1`（最大30MHz） |

CNFの意味（入力時はアナログ、フローティング、プル付き。出力時はプッシュプル、オープンドレイン、およびそれぞれの代替機能版）は、両デバイスで同じ並び。ただし、CH32V00Xの入力 `10` の説明には違いがある（[プルダウンの件](/peripherals/gpio/ch32v00x-pull-down.md)）。

# 移植への影響

以下は、レジスタの記述から導いた推論で、実機では未確認（`hypothesis`）。

- CH32V003向けのコードで出力速度を2MHz（`MODE=10b`）にしているピンをそのままCH32V00Xへ持っていくと、`MODEy` に当たる最下位ビットが0になる。そのため、そのピンは**出力にならず入力のまま**になると考えられる。
- 10MHz（`01b`）と30MHz（`11b`）の場合は最下位ビットが1なので、出力になる。`11b` の上位ビットは予約ビットへの書き込みになる。
- 移植するときは、出力ピンの設定値が最下位ビットを1にしているかを確認する。予約ビットには0を書く。ch32funやWCH SDKの速度定数がCH32V00X向けにどう定義されているかは、まだ確認していない。

# 照合記録

- 2026-11-07、claude-code/claude-opus-5-5が、両リファレンスマニュアルのビットマップ図とフィールド表を、PDFページ画像およびテキスト層と照合した（CH32V003: PDF p.56–57、CH32V00X: PDF p.81–82）。

[^v003-rm]: CH32V003 Reference Manual V1.9, 7.3.1.1, PDF p.56–57（印字p.57–58）
[^v00x-rm]: CH32V00X Reference Manual V1.5, 7.3.1.1, PDF p.81–82（印字p.75–76）

# 実機での確認（2026-11-08、実測）

CH32V002F4P6 と CH32V006F8P6（各 1 個体）で、PC0 を `CNFy=00b`（プッシュプル）にし、MODE の 2 ビットに 1／2／3 を書いて High と Low を出し、Pico で読んだ（[ログ](../../log/2026-11-08-2137-fix-ch32v00x-sample-findings.md) の 7.3）。

- MODE=1（ch32fun の `GPIO_Speed_10MHz`）と MODE=3（`GPIO_Speed_50MHz` の値）: High・Low とも出力された。
- MODE=2（`GPIO_Speed_2MHz` の値）: High を書いても出力されなかった（Low のまま＝入力のまま）。

上位ビットが予約で、bit 0 だけが出力/入力を決める、という資料の読みと一致する（この 2 個体で確認）。
