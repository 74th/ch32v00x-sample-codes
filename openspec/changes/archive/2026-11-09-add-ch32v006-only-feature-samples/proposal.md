# Proposal

## Why

CH32V006 には、CH32V002 にない周辺機能（USART2、OPA、簡易タイマー TIM3、タッチキー TKEY）があります。書籍の原稿ではこれらを使っておらず、「006 だけにある機能は実機では確認していない」と書いています（`okf/open-questions/ch32v00x-unverified.md` の C4、U5）。
ユーザーは、Pico の治具で測れるものは確かめたい、と判断しました。

資料（`xprivate/` の変換物、本文は転載しない）で、手元の CH32V006F8P6（F8P7 として扱う、TSSOP20）について次を確認しました。

| 機能 | 資料での適用 | TSSOP20 のピン | 今の治具で観測できるか |
| --- | --- | --- | --- |
| USART2 | RM 第14章: V005/006/007 | TX は PA2（リマップ2）、PC4（5）、PD2（3）。RX は PD3（3）、PD1（5、SWIO と共用） | TX を PD2→GP14 で受ければ観測できる（治具の UART 受信のピン選択が要る）。RX は PD3 が未配線 |
| OPA（PGA） | RM 第17章: V005/006/007（ポーリングは V005 を除く） | P0=PA2、N0=PA1、出力 OUT0=PD4（ADC_IN7 と共用）。内部出力は ADC の内部チャネルへ | 入力 PA1/PA2 は Pico が RC 経由で駆動できる。出力は DUT 自身の ADC で読める（PD4 は未配線でもよい） |
| 簡易タイマー TIM3 | RM 第13章: V006/007 | 出力ピンなし（TIM1・ADC と組むための内部用） | 割り込みで GPIO（PC0→GP5）を反転すれば、周期を観測できる |
| TKEY | RM 第10章: V006/007 | ADC の外部チャネルを使う | タッチは模擬できない。負荷の違い（未配線のピンと、1 µF のある PA2）で値が変わることだけは観測できる |
| CMP | RM 第17章: **V007/M007 のみ**（006 のデータシートの機能一覧は「OPA/PGA/CMP」と書き、食い違う） | − | 対象外（資料の食い違いは記録する） |
| 2 線の SDI、PB ポートなど | − | TSSOP20 にはピンがない | 対象外 |

## What Changes

**サンプルの追加（CH32V006 のみ、WCH SDK）**

- `usart2`: USART2 の TX をリマップして PD2 から出す（RX は配線がないので扱わない）。
- `opa`: OPA を PGA として使い、PA2 の入力を増幅した値を、DUT の ADC で入力（ADC_IN0）と出力（内部チャネルまたは ADC_IN7）の両方から読み、USART1（PD5）に出す。
- `tim3`: TIM3 の更新割り込みで PC0 を反転する。
- `tkey`: TKEY の値を、負荷の違うチャネル（PD4 と PA2 など）で読み、USART1 に出す（参考の観測）。
- 各サンプルは公式 EVT（`EXAM/USART`、`EXAM/OPA/OPA_PGA`、`EXAM/TIM`、`EXAM/TOUCHKEY/TKEY`）を元にする。006 の `sdk/` に、必要なドライバ（`ch32v00X_opa.{c,h}` など）を EVT からコピーし、出所を記録する。

**HIL（実機観測）**

- `usart2`: 治具の UART 受信で GP14 を受信ピンに選び、既知の文字列を受け取る。
- `opa`: Pico が PA2 と PA1 を既知のレベルにし、DUT が報告する入力と出力の比が、設定した増幅率の範囲に入るかを判定する（電圧は校正しないので、比で判定する）。
- `tim3`: PC0 の反転の周期が、設定から計算した値の範囲に入るかを判定する。
- `tkey`: 負荷の違うチャネルで値に差が出ることを記録する（タッチの判定ではない）。

**対象外**

- CH32V002（これらの機能がない）、Arduino、ch32fun。
- USART2 の受信、CMP、2 線の SDI、PB ポート、実物のタッチパッド。

## Capabilities

### New Capabilities

なし。

### Modified Capabilities

- `wch-sdk-sample-workflow`: 書籍にない CH32V006 だけの周辺機能のサンプルを、治具で観測できる範囲で追加し、観測できない機能を理由とともに記録する要件を加える。

## Impact

- 追加するコード: `samples_ch32v006_wch/{usart2,opa,tim3,tkey}/`、`samples_ch32v006_wch/sdk/` のドライバと `PROVENANCE.md`、`tests/hil/wch/` の試験、`hil/matrix_ch32v006_wch.json` の行（書籍由来でない種別）。
- 依存する change
  - `extend-pico-fixture-measurement`: USART2 の観測（GP14 での UART 受信）に必要。先に実装されていない場合、`usart2` は build のみとし、観測は保留にする。
  - `add-wwdg-sample`: 書籍にないサンプルの種別（`additional-not-in-book`）を共有する。どちらを先に実装しても矛盾しないようにする。
- 配線: 変更しない。
- 書籍原稿の更新は別作業。
