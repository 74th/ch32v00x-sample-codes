# pwm（公式WCH SDK、CH32V003）

書籍`pwm-wch_sdk`の移植。TIM1のPWM（公式`TIM_TimeBaseInit`/`TIM_OC1Init`/`TIM_OC4Init`/`TIM_SetCompare*`/`TIM_CtrlPWMOutputs`）。
1周期256カウント（プリスケーラ1）なので周期は48 MHz/2/256＝約10.67 µs（93.75 kHz）。1/32秒ごとにCH1のdutyを1/32刻みで上げ、CH4は書籍の式`128*(33-i)-1`、その後上下を入れ替える。`up`/`down`をUSART1 TX（PD5）へ出力。Flash 5,296 B／RAM 696 B。

書籍との差: `USE_REMAP 0`（CH1=**PD2**、CH4=**PC4**。治具はPD2→GP14、PC4→GP15。書籍既定のPC6/PD3リマップは配線がない）。他は書籍のコード。

## CH4（PC4）の範囲
書籍のCH4式は12bit向けの値（128刻み）で、8bit周期（0..255）を超えるため、上昇区間のほとんどでPC4は常時High（エッジなし）になる。
実測でもPC4は常時High（GPIO_PULSEがtimeout）が多く、ランプするのは区間の終わりと下降区間のみ。これは書籍のままの挙動でCH1のランプとは対称でない。

## 観測（HIL、実測）
`uv run pytest --hil --hil-framework wch tests/hil/wch/test_pwm.py`（最終判定条件で12回連続成功）
- PD2: 周期は9..12 µs（Picoは10/11 µsに量子化）、dutyが約17〜73 %にわたり複数段階。
- PC4: ランプ読み（数段階）と常時Highの読みが両方ある。
- 判定は粗い。GPIO_PULSEは1 µs分解能・未校正で、High幅2 µs未満・Low幅3 µs未満、またはdutyが15〜95 %の外の読みはエッジを落とし周期が意味を持たない（33、43、86、22、235 µs等を観測）ため「分解不能」として数えて判定から除外する。
- 実周期の精密値（93.75 kHz）、デューティの精度、ランプの方向は検証していない。
