# Design

## Context

動機と、資料で確かめた機能とピンの表は `proposal.md` を参照。設計に関わる追加の事実は次のとおり。

- 公式 EVT の `EXAM/SRC/Peripheral/` には `ch32v00X_opa.c` と `ch32v00X_wwdg.c`、`ch32v00X_dbgmcu.c`、`ch32v00X_flash.c` があるが、維持している 006 の SDK のコピー（`samples_ch32v006_wch/sdk/`）にはない。USART・TIM・ADC・DMA のドライバは入っている。
- OPA の PGA の増幅率は、ドライバの列挙で 4、8、16、32 倍（`CHN_PGA_4xIN` など）。RM 第17章では、OPA の出力は I/O ピンと ADC の内部チャネルの両方へ出せる。
- TIM3（簡易タイマー）は、SDK のヘッダでは TIM の構造体の中の `TIM3_CTLR`、`TIM3_DMAINTENR`、`TIM3_CNT`、`TIM3_ATRLR`、`TIM3_CH1CVR` などとして定義され、専用の割り込み番号（`TIM3_IRQn`）は見当たらない。公式 EVT の例は `SLTIM_DMA`（TIM3 で DMA を動かす）。
- 固定配線: PA1←GP12、PA2←GP13（どちらも 10 kΩ＋1 µF、Pico が High/Low に駆動して充放電できる）、PC0→GP5、PD2→GP14、PD5→GP9（いずれも 1 kΩ）。PD3、PD4 は未配線。
- 手元の 006 の個体は、PC4 の経路が通らない（`okf/log/2026-11-08-2237-ch32v006-sample-findings.md` の 6.1）。PC4 を使う設計は避ける。

## Goals / Non-Goals

**Goals:**
- 006 だけの機能を、今の配線のまま、Pico で判定できる形で動かす。
- 判定できないことは、理由とともに未確認として残す。

**Non-Goals:**
- 電圧の絶対値、OPA のオフセットやノイズ、帯域の測定。
- 実物のタッチパッドでのタッチの検出。
- CH32V002 への適用。

## Decisions

### 1. USART2 は、送信だけを PD2 で観測する

USART2 の TX をリマップ3で PD2 に出し、既知の文字列を一定間隔で送る。Pico は change `extend-pico-fixture-measurement` で追加する UART 受信（受信ピンの選択）で GP14 を受ける。RX（PD3）は未配線なので扱わない（配線を足せば、同じサンプルにエコーを加えられる）。
代替案の PA2（リマップ2）は、PA2 が Pico から DUT への向きの RC 回路に繋がっていて、送信の波形が崩れるので採らない。PC4（リマップ5）は、手元の 006 で経路が通らないので採らない。
USART1（PD5）のログには、USART2 の設定（リマップ番号、ボーレート）だけを出す。

### 2. OPA は PGA の比で判定する

OPA を単端の PGA（例: 4 倍）にし、入力を PA2（P0）にする。Pico が GP13 で PA2 の 1 µF を短いパルスで少しだけ充電し、入力を低い電圧（増幅後も飽和しない範囲）にする。DUT は ADC で入力（ADC_IN0）と OPA の出力（内部チャネル、使えなければ PD4 の ADC_IN7）を続けて読み、両方の値を USART1 に出す。
判定は「出力÷入力」が設定した倍率の許容範囲（例: ±15 %）に入るかで行う。電圧は校正しないので、比だけを使う。入力を高くしたときは出力が飽和することも記録する。複数の倍率（4 倍と 8 倍）を、ビルドの切り替え（`-D`）で確かめる。
代替案の「Pico の ADC で OPA の出力を直接測る」は、PD4 が未配線で、配線の追加が要るので採らない。

### 3. TIM3 は、DMA で GPIO を反転させて周期を観測する

TIM3 には専用の割り込みがないので、公式の `SLTIM_DMA` と同じく、TIM3 の DMA 要求で、DMA が GPIOC の BSHR に「PC0 の High/Low」を交互に書く（既存の `timer_dma` サンプルと同じ方式）。Pico は PC0（GP5）の周期を測る。周期は ms 程度にし、今の `GPIO_PULSE` でも判定できるようにする（change `extend-pico-fixture-measurement` の後は、細かい測定で判定し直す）。
TIM3 の DMA 要求の割当（DMA のチャネル）は、RM の DMA 要求表で確かめてから決める。

### 4. TKEY は、参考の観測にする

TKEY の値を、未配線のピンのチャネル（例: PD4 の ADC_IN7）と、1 µF の付いたチャネル（PA2 の ADC_IN0、Pico 側は解放）で読み、USART1 に出す。値に差が出ることだけを記録し、合否は付けない。タッチの検出は、実物のパッドが要るので未確認として残す。

### 5. マトリクスでは、書籍由来でない種別で追跡する

`hil/matrix_ch32v006_wch.json` に、change `add-wwdg-sample` と同じ種別（`additional-not-in-book`）で行を加える。006 だけの行なので、「002 と 006 の WCH のマトリクスの行が同じ並び」という単体テストの前提を、書籍由来の行に限るように直す（`add-wwdg-sample` と重なる変更は、先に実装した方に合わせる）。

### 6. SDK へのドライバの追加は、出所の記録とともに行う

`ch32v00X_opa.{c,h}` などを EVT からコピーし、`samples_ch32v006_wch/PROVENANCE.md` にコピー元と SHA-256 を記録し、`ch32v00X_conf.h` を更新する。既存のサンプルの成果物が変わらないことを、ハッシュで確かめる。

## Risks / Trade-offs

- [`extend-pico-fixture-measurement` が先に終わらない] → `usart2` は build のみとし、観測を保留にする。ほかの3つは今の治具で観測できる。
- [RC の充電で作った入力が、ADC で読む間に下がる] → 入力と出力を続けて読み、短い時間で何回か繰り返す。差が大きいときは、待ちを入れずに読む順番を入れ替えて確かめる。
- [OPA の内部チャネルが、資料の記述どおりに読めない] → PD4（ADC_IN7）で読む方法に切り替え、どちらで読んだかを記録する。
- [TIM3 の DMA 要求の割当が、資料から読み取れない] → TIM3 の CNT を CPU が読んで反転する方法に切り替え、その場合は「DMA を使っていない」と記録する。
- [CMP についての資料の食い違い] → 実装せず、食い違いを `okf/` に記録する。

## Open Questions

- PGA の許容範囲（±15 % は仮の値）。最初の実測と、資料の増幅率の誤差の記載を見て決める。
