# WCH公式SDKのCLIビルド（CH32V002）

CH32V003用（[../samples_ch32v003_wch/README.md](../samples_ch32v003_wch/README.md)）を基準に、CH32V002専用の公式SDK（`openwch/ch32v002_004_005_006_007`）へ移植した13サンプルと、基準の`blink`。
**CH32V002実機で観測済み**（13例は`hil-verified`、blinkはPico観測）。003側の結果は参照のみで、002へは継承せず002で再観測した。

```sh
# リポジトリルートから。CH32V002が接続されている場合だけ flash する（型番識別領域0x1ffff704が0x002でなければ書き込まない）
make -C samples_ch32v002_wch/blink build
uv run python scripts/wch-sdk.py build --device ch32v002 --sample blink
uv run python scripts/wch-sdk.py flash --device ch32v002 --sample blink     # 実機がある場合のみ
uv run pytest --hil --hil-device ch32v002 --hil-framework wch tests/hil/wch/<test>.py   # 実機がある場合のみ
```

## CH32V003との設定の違い（`wch.mk`、`sdk`）
- **`-DCH32V002`**: 公式`ch32v00X.h`は既定で`CH32V006`を選ぶ。`-DCH32V002`で`CH32V002`が定義され`CH32V006`は定義されない（プリプロセッサ出力で確認、未指定だと`CH32V006`になる）。
- **メモリ**: 公式`Link.ld`は既定でCH32V006（Flash 62K/RAM 8K）。CH32V002（**Flash 16 KB／RAM 4 KB**）のブロックを有効にし、他を無効化した（変更はPROVENANCEに記録）。blinkのmapで`FLASH 0x4000`、`RAM 0x1000`、スタック上端`0x20001000`を確認。スタックは公式の512 B（003は256 B）。
- **スタートアップ**: 公式`startup_ch32v00X.S`（CH32V002/4/5/6/7共通）。先頭40スロットの割り込み配置は003と同じ（SysTick 12、TIM1_UP 35、TIM2 38など）で、以降にUSART2・OPCMなどが加わる。
- **クロック（HSI）**: 公式`system_ch32v00X.c`は既定で`SYSCLK_FREQ_48MHZ_HSI`（外部水晶不要、HSI＋PLL 48 MHz）。無改変。`HSI_VALUE`は24 MHz。
- **ISA/ABI**: `-march=rv32ec_zmmul_zicsr -mabi=ilp32e`（生成物のISAタグ`rv32e2p0_c2p0_zmmul1p0_zca1p0`）。003は`rv32ec_zicsr`。`zmmul`はch32funが003以外のCH32V00x（GCC 13以上）で使う指定に従ったもので、WCHの公式資料では未確認。ただしこの指定でビルドした14例はCH32V002実機で動作を観測した（zmmul命令が使われているかは未調査）。
- **ADC**: 12-bit（0..4095、003は10-bit）。002 SDKにADC校正APIが無く校正を省略。サンプル時間は`ADC_SampleTime_CyclesMode0..7`（003の`_241Cycles`相当は`Mode7`＝239.5サイクル）。公式例に倣い`RCC_ADCCLKConfig(RCC_PCLK2_Div8)`。
- **APIの名前**: `RCC_APB2Periph_*`→`RCC_PB2Periph_*`、`RCC_APB1Periph_*`→`RCC_PB1Periph_*`、`RCC_AHBPeriph_*`→`RCC_HBPeriph_*`。GPIO速度は`GPIO_Speed_30MHz`のみ。SDKのファイル名は`ch32v00X`（大文字X）。サンプルは`<ch32v00x.h>`のまま使えるよう、`sdk/Compat/ch32v00x.h`（1行）で橋渡しする。
- `__WFI`/`__WFE`が参照する`WFE`のため、公式`core_riscv.c`もビルドに含める（003と同様）。

CH32V003用のヘッダやStartupを型番だけ変えて流用していない（単体テスト`tests/unit/test_wch_ch32v002.py`で、003の設定・ファイルが混入していないこと、型番識別領域のガードを確認）。

## 書籍の公式SDK例との対応（CH32V002）
正本は`hil/matrix_ch32v002_wch.json`。

| 書籍ディレクトリ | 維持名 | 002の状態 | 003の状態（参照のみ） |
|---|---|---|---|
| `blink_and_read-wch_sdk` | `blink_and_read` | hil-verified | hil-verified |
| `uart-wch_sdk` | `uart` | hil-verified | hil-verified |
| `adc-wch_sdk` | `adc` | hil-verified | hil-verified |
| `adc_dma-wch_sdk` | `adc_dma` | hil-verified | hil-verified |
| `i2c_master-wch_sdk` | `i2c_master` | hil-verified | hil-verified |
| `i2c_slave-wch_sdk` | `i2c_slave` | hil-verified | hil-verified |
| `spi_master-wch_sdk` | `spi_master` | hil-verified | hil-verified |
| `pwm-wch_sdk` | `pwm` | hil-verified | hil-verified |
| `timer_blink-wch_sdk` | `timer_blink` | hil-verified | hil-verified |
| `timer_dma-wch_sdk` | `timer_dma` | hil-verified | hil-verified |
| `watchdogtimer-wch_sdk` | `watchdog` | hil-verified | hil-verified |
| `sleep_mode_blink-wch_sdk` | `sleep_wake` | hil-verified | hil-verified |
| `standby_mode_blink-wch_sdk` | `standby_wake` | hil-verified | hil-verified |

## 書籍にない追加サンプル（種別 `additional-not-in-book`）
上の13例は書籍との1対1の対応。次は書籍にない、このリポジトリ独自の追加で、`hil/matrix_ch32v002_wch.json` に別の種別で載る。

| サンプル | 内容 | 状態（CH32V002） |
|---|---|---|
| [`wwdg`](wwdg/README.md) | WWDG（ウィンドウウォッチドッグ）。公式EVTの `EXAM/WWDG` が出典。`-DWWDG_MODE` の3ビルドで切り替える | hil-verified（[ログ](../okf/log/2026-11-09-0013-add-wwdg-sample.md)） |

出所revision、コピー元SHA-256、利用条件、変更箇所は[PROVENANCE.md](PROVENANCE.md)。
