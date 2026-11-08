# WCH公式SDKのCLIビルド（CH32V006）

CH32V002用（[../samples_ch32v002_wch/README.md](../samples_ch32v002_wch/README.md)）を起点に、CH32V006F8P6向けの公式SDK（`openwch/ch32v002_004_005_006_007`、固定revisionは [PROVENANCE.md](PROVENANCE.md)）で維持する。
基準の `blink` と書籍 13 例すべてを build でき、実機で確認済み（機能のみ）。基準 blink の build→flash→observe は別コマンドで実行し、証跡は[ログ](../okf/log/2026-11-08-1549-ch32v006-wch-blink-hil.md)。進捗の正本は `hil/matrix_ch32v006_wch.json`。

```sh
# リポジトリルートから。build / flash / observe は別段階。CH32V006が接続されている場合だけ flash する
make -C samples_ch32v006_wch/blink build
uv run python scripts/wch-sdk.py build --device ch32v006 --sample blink    
uv run python scripts/wch-sdk.py flash --device ch32v006 --sample blink     # 実機がある場合のみ（識別領域0x1ffff704の上位型番0x006を確認）
```

## 設定（`wch.mk`、`sdk`）
- **`-DCH32V006`**: 公式`ch32v00X.h`の既定でもあるが、`wch.mk`で明示する。002用の `-DCH32V002` は使わない。
- **メモリ**: 公式`Link.ld`を**無改変**で使用（Flash 62K / RAM 8K、`__stack_size=512`）。blinkのmapで`FLASH 0xf800`、`RAM 0x2000`、`_eusrstack=0x20002000`、`_heap_end=0x20001e00`を確認。
- **クロック**: 公式`system_ch32v00X.c`は既定で`SYSCLK_FREQ_48MHZ_HSI`（無改変）。
- **ISA/ABI**: `-march=rv32ec_zmmul_zicsr -mabi=ilp32e`（生成ELFのISAタグ`rv32e2p0_c2p0_zmmul1p0_zca1p0`）。002向けに採用した指定をそのまま使う。coreの`boards.txt`は006K8に`rv32ecxw`を指定しており、WCH公式資料でのzmmul適用根拠は未確認（実機動作で確認する）。
- F8P6は資料上のF8P7と同一ダイとして扱う前changeのユーザー判断を引き継ぐ（独立には未検証）。

## 書籍の公式 SDK 例との対応（CH32V006）
正本は `hil/matrix_ch32v006_wch.json`。全 13 例が `hil-verified`（002/003 の結果は継承せず 006 で観測）。006 だけの例外は次の 3 つ（ユーザー判断あり、いずれも PC4 などの 006 の DUT での観測結果による。原因は未特定）:
- `pwm`: PC4（TIM1_CH4）が無信号のため、第 2 チャネルを TIM2_CH3 on PC0 にした（書籍からの逸脱）。PC4 版は参考試験（XFAIL）。
- `timer_dma`: PC4（SA）は記録のみで判定しない（他の 7 ピンは判定）。
- `watchdog`: IWDG が約 2.3〜3.1 s でリセットされるため、PA1 の保持を 3.5 s にして確認（要因フラグ IWDGRSTF は判定）。

実行: `uv run python scripts/wch-sdk.py build --all`（006 の 14 例すべてでメモリ・SDK 参照元の検査を通る）、`uv run pytest --hil --hil-device ch32v006 --hil-framework wch -m 'hil and wch' tests/hil/wch --hil-port=/dev/serial/by-id/<PicoのID> --hil-run-dir=<run用ディレクトリ>`。

## 書籍にない追加サンプル（種別 `additional-not-in-book`）
上の13例は書籍との1対1の対応。次は書籍にない、このリポジトリ独自の追加で、`hil/matrix_ch32v006_wch.json` に別の種別で載る。

| サンプル | 内容 | 状態（CH32V006） |
|---|---|---|
| [`wwdg`](wwdg/README.md) | WWDG（ウィンドウウォッチドッグ）。公式EVTの `EXAM/WWDG` が出典。`-DWWDG_MODE` の3ビルドで切り替える | hil-verified（CH32V006 実機、[ログ](../okf/log/2026-11-09-0751-ch32v006-wwdg-hil.md)） |
