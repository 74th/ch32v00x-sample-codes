---
okf_version: "0.2"
---

# CH32V00x 移植ナレッジ

CH32V003向けサンプルをCH32V002 / CH32V005 / CH32V006 / CH32V007へ移植する過程で得た知識を、[Open Knowledge Format v0.2](https://github.com/GoogleCloudPlatform/knowledge-catalog/blob/main/okf/SPEC.md) で記録したバンドル。記述ルールは [知識の確度と記述ルール](conventions/knowledge-status.md) に従う。

# 規約

* [知識の確度と記述ルール](conventions/knowledge-status.md) - 確度の区別、出典の書き方、公開してよい範囲

# 一次資料

* [一次資料](sources/) - 参照したデータシートとリファレンスマニュアルの版・識別情報

# デバイス

* [CH32V006 TSSOP20品の型番（F8P6とF8P7）](devices/ch32v006-tssop20-part-number.md) - 手持ちのF8P6が、現行データシートV2.0に載っていない件

# 周辺機能

* [GPIO](peripherals/gpio/) - GPIOレジスタのデバイス間差分
* [CH32V006への再利用差分](peripherals/ch32v006-port-differences.md) - CH32V002用サンプル12件の資料照合と再利用判定（実機未確認）

# 未確認事項

* [CH32V002/CH32V006 の未確認事項の一覧](open-questions/ch32v00x-unverified.md) - 書籍原稿の「確認していない」事項の分類・状態・必要なもの

# 作業記録

* [作業ログ](log/) - 日時と作業ごとの手順、観測、未確認事項
