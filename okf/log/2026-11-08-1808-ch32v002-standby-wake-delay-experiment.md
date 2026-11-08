# CH32V002 standby_wake: SystemInit() 後の待ちで起床後の文字化けが変わるか

作業日時: 2026-11-08 18:0x JST頃（ホストdate 18:08 時点で記録、作業は直前の約10分）。ユーザー依頼「ちょっとやってみて」。

## 目的
002 の起床後の先頭約14バイトの化け（原因未特定、`2026-11-08-0802-wch-sdk-ch32v002-hil.md`）が、クロック安定前の送信によるかを切り分ける。

## 条件
- DUT: CH32V002（`minichlink -a` で Detected CH32V002 を確認）、固定治具（WCH-LinkE 3.3 V給電、Pico観測）。ユーザーが差し替えたままの状態と仮定（未確認）。
- 変更（一時、記録後に元へ復元済み）: `samples_ch32v002_wch/standby_wake/main.c` の `SystemInit();` 直後に `Delay_Ms(N);` を追加。

## 実行
```sh
uv run pytest --hil --hil-device ch32v002 --hil-framework wch tests/hil/wch/test_standby_wake.py -q -s --hil-run-dir <scratchpad>/runs
```
N=10 と N=100 でそれぞれ1回。

## 結果（実測）
- 基準（以前の実測）: 先頭約14バイトが化け（`58 d6 4c 58 b4 37 ...`）。
- N=10: 1 passed。化けは各wake 1〜2バイトのみ（`e1`, `e1`, `58 fe`、その後 `\r\nAuto wake up` は正常）。
- N=100: 1 passed。同様に 1〜2バイト（`58 fe`, `e1`, `58 fe`）。10 ms から 100 ms に増やしても変化なし。
- 各試験の最後に blink 再書き込み・読み戻しの復旧は成功（テストの cleanup が通過）。

## 解釈（推定）
- 約14バイトの化けは「起床直後〜SystemInit後のクロック不安定期間に printf した」ことが主因とみられる（待ちで消える）。
- 1〜2バイトは待ちの長さに依存しない。`printf` 前に出ているため、起床時の TX ライン変動か Pico 受信側の拾い方など、別要因の可能性が高い（未特定）。

## 未確認
- 1回ずつの試行で再現回数が少ない（各3 wake）。N=0 の同日再測定は未実施。
- 1〜2バイトの出所（USART、ピン状態、Pico 側）。待ちを `SystemInit` 前に入れる案、USART 再初期化は未試行。
- ソースは元に戻した（恒久修正は未適用）。
