# change `add-wwdg-sample`（WWDG サンプルの追加）の作業記録

- 記録の開始: 2026-11-09 00:13 JST（`TZ=Asia/Tokyo date` で取得）。各作業の時刻は、特に書かない限りこの前後。
- 対象: change `add-wwdg-sample`（proposal・design・tasks は `openspec/changes/` 配下）。
- 固定 ch32fun: `b28d285460ce052a179dba8f4a22c6f73ff8e328`（`git -C externals/ch32fun rev-parse HEAD`、`scripts/ch32fun.sh` の `revision` と一致）。
- 実機: ユーザー申告で「CH32V002 が刺さっている」。実測で確認: `minichlink -r + 0x1ffff704 4` が `20 06 20 00`（型 0x002）、`Detected CH32V002`、Flash 16 kB、WCH-LinkE 2.22、Pico（2e8a:000a）が接続。CH32V006 の実機は接続されていない（6.3 は未実施）。

## 1. 変更前の成果物のハッシュ（タスク 1.1、実測）

- 002/006 の WCH SDK 全例（各 14 例）と ch32fun 全例（12 例 × 002/006）を、clean から build し `.bin` の SHA-256 を記録した（`make -C <dir> clean && make -C <dir> build`、ch32fun は `PREFIX=riscv64-unknown-elf TARGET_MCU=...`）。合計 52 個、build の失敗なし。
- SDK へのドライバ追加（2 節）の後に同じ手順で再計測し、52 個すべてが一致した（`diff` で差なし）。WCH 例のハッシュは「`wwdg` を除いた既存サンプル」の範囲。
- Arduino 3 例の build は行っていない。この change は `samples_*_arduino` にも、Arduino が使う ch32fun/SDK にも触れないため（理由による省略。ハッシュの比較はしていない）。

## 2. 資料の照合（タスク 1.2、1.3）

資料は `xprivate/converted/ch32v00x-rm`（本文は転載しない）と、公式 EVT `EXAM/WWDG`、`EXAM/SRC/Peripheral/{inc,src}/ch32v00X_wwdg.*`。

- RM 第5章（V00X 共通）: WWDG は 7 ビットのカウンタ、クロックは HCLK/4096 を WDGTB（1/2/4/8）で分周。リセットは「T6 が 0 になる（0x40→0x3F）」と「ウィンドウ（W 以上）でのフィード」の 2 条件。EWI は 0x40 で発生。デバッグ時は debug モジュールのレジスタで停止/継続を設定できる（DBGMCU の WWDG_STOP ビットがあることを確認。今回は触らない）。
- 002 と 006 で、第5章の記述に差はない（V00X 全品種共通の章）。RCC のクロックゲート（WWDGEN）、リセットフラグ（WWDGRSTF）も同じ。
- 資料の食い違い（RM 内）: Figure 5-2 は窓の下限を 0x3F とし、本文のリセット条件は「0x40 を下回る」（T6=0）、W[6:0] の説明は「カウンタが窓の値より小さく 0x3F より大きいときだけフィードできる」。いずれも T6 が 0 になる点を境にしており、実質は同じだが、0x3F/0x40 の書き方がそろっていない。サンプルは公式例と同じ「0x40 を下回る前にフィード」で扱う。
- 公式 EVT の例: `WWDG_Config(0x7f, 0x5f, WWDG_Prescaler_8)`（コメントは 48M/8/4096）、10 ms ごとに `T < W` ならフィード、EWI も有効。例の冒頭コメントは「0x40–0x5f の間にフィード」。
- 固定 ch32fun のヘッダ（`ch32x00xhw.h`）: `WWDG_TypeDef`（CTLR、CFGR、STATR、16 ビット）、`WWDG_BASE`（APB1 + 0x2C00）、`RCC_WWDGEN`（0x800、`PB1PCENR`）、`RCC_WWDGRSTF`（bit 30）、`RCC_IWDGRSTF`、`RCC_RMVF`、`WWDG_IRQn = 16`、`WWDG_CTLR_*`、`WWDG_CFGR_WDGTB` がそろっている。ch32fun 版に必要な定義は足りる。

## 3. WCH SDK へのドライバの追加（タスク 2.1、2.2）

- `ch32v00X_wwdg.h`（SHA-256 `1784101e…bed3`）と `ch32v00X_wwdg.c`（`d68fd78e…fb7`）を、公式 EVT（`a835ede` の `EVT/EXAM/SRC/Peripheral/`）から `samples_ch32v00{2,6}_wch/sdk/Peripheral/{inc,src}/` へ無改変でコピー。`PROVENANCE.md`（002/006）に行を追記。`sdk/System/ch32v00X_conf.h` に `#include <ch32v00X_wwdg.h>` を追加。
- 既存の 52 成果物のハッシュが変わらないことを 1 節のとおり確認した（実測）。

## 4. サンプルの実装と build の確認（タスク 3.1〜3.4）

- `samples_ch32v002_wch/wwdg/`、`samples_ch32v006_wch/wwdg/`（同一の `main.c`、`Makefile`: `PERIPH := wwdg misc`）、`samples_ch32v00x_ch32fun/wwdg/`（レジスタ直接、002/006 共通）。`-DWWDG_MODE`（0/1/2、範囲外は `#error`）。窓 0x5F、分周 /8、5 ms ごとのループ、有効化の前に `WWDG_WAIT_MS`（既定 1500 ms）の待ち。
- 実装中の判断: 点（`.`）は stdio ではなく USART1 に直接書く（newlib の標準出力が改行まで保持する可能性があるため。実機で確かめるまでは仮定）。
- build: 3 モード × {WCH 002、WCH 006、ch32fun 002、ch32fun 006} がすべて成功（WCH 002 は Flash 約 7.3 KB、ch32fun は約 0.9 KB）。
- 逆アセンブル（`objdump -d`）の確認（実測）:
  - ch32fun（002）: 3 モードとも `RCC->PB1PCENR |= 0x800`、`WWDG->CTLR=0x7F`、`CFGR=0x1DF`（窓 0x5F | WDGTB=3）、`CTLR=0xFF`（WDGA | 0x7F）の順。モード 0 だけループ内で `CTLR` を読み `& 0x7F` が 94（0x5E）以下のときに `CTLR=0xFF` を書く。モード 1 はループ内で毎回 `CTLR=0xFF`。モード 2 はループ内に書き込みなし。待ちは 9,000,000 カウント（HCLK/8 = 6 MHz で 1.5 s）、ループの 5 ms は 30,000 カウント。
  - WCH SDK（002）: 3 モードとも `WWDG_SetCounter(127)`、`SetPrescaler`、`SetWindowValue(95)`、`WWDG_Enable(127)` の順。モード 0 は `& 127` と 94 の比較で `WWDG_SetCounter(127)`、モード 1 は無条件、モード 2 はなし。

## 5. マトリクスと単体テスト（タスク 5.1、5.2）

- `ch32hil/matrix.py`: 種別 `additional-not-in-book` を追加（`book_sample` は null、`sample`/`peripheral`/`note`/`criteria` が必須）。`book_rows()`/`additional_rows()` を追加し、書籍由来の行と分けて数えられるようにした。
- 4 つのマトリクス（WCH 002/006、ch32fun 002/006）に `wwdg` の行を、状態 `build-only` で追加（それぞれ元ファイルの整形を保った）。ch32fun の行は、既存の行と同じく `book_sample` キーなし。
- 単体テストの前提を直した: 002 の WCH で「003 と同じ名前の集合」「003 の状態の継承の確認」、006 の WCH/ch32fun で「002 と同じ行の並び・13 行」を、書籍由来の行（`book_rows`）に限定。追加の行の判定とマトリクス 4 つの `wwdg` の行の確認を足した。WCH の README の対応表（13 行）は書籍の表のままにし、追加サンプルは別の節で示した。
- 追加前（`uv run pytest`）: 3 件の失敗（`wwdg` ディレクトリの追加で 003 との集合比較などが壊れたもの）。修正後: 359 passed、43 skipped（HIL は `--hil` なしで skip）。

## 6. 実機の診断（タスク 4.1、実測。各実行の時刻は記録していない。`date` の読み取りは 00:13 と 00:24 JST で、その間の作業）

使い捨てのスクリプトは作業用ディレクトリに置いた（リポジトリには含めない）。手順と結果は次のとおり。全て CH32V002（識別 0x00200620）。

1. `Dut`（`framework=wch`、`make_args=("EXTRA_CFLAGS=-DWWDG_MODE=2",)`）で build → `flash`（識別領域の確認つき）→ `readback`。WWDG が有効なままリセットを繰り返す「フィードしない」ビルドでも、書き込み 1.4 s、読み戻し 0.6 s で一致し、続けて `minichlink -i` を 0.7 s 間隔で 6 回実行して 6 回とも `Detected CH32V002`（各 0.17〜0.18 s）。待ち 1.5 s の間にデバッガが接続できる、という想定どおり。復旧の手順は、既知のサンプルを書き込む（下記 HIL の最後）だけで足りた。電源の入れ直しは不要だった。
2. Pico の `UART_XFER DUT`（GP9、115200、32 バイト）を、デバッガのリセット（`reset_and_capture_uart`、先行 0.3 s）の中で取得した。初期の実装（`wait\r\n` 行あり、点は 5 ms 待ってから出す）の結果:
   - モード 2: `cause=other\r\nwait\r\n........cause`（点 8 個。2 回目の `cause=` の値が 32 バイトの外）。
   - 仕様どおり動いたが、起動 2 回分が 32 バイトに入らないため、`wait` の行を削り、改行を `\n` のみにした（12 + 点 + 11 バイト）。
3. 変更後のモード 1: `cause=other\ncause=WWDG\ncause=WWD`（**点が 0 個**）。原因は、点を送った直後にフィードしてリセットされ、送信中の点が切れるため（予想外。design の「点が1〜2個」は誤り）。ループを「点を出す → 5 ms 待つ → フィード」の順に変えて、モード 1 は点 1 個、モード 2 は点 9 個（0、5、…、40 ms）になった（実測で一致）。
4. 診断スクリプトで、WCH SDK 版と ch32fun 版の 3 モードを各 3 回観測した結果は、7 節の HIL と同じ。モード 0 は 3 秒おきの 2 回の取得（点のみ）でもリセットの「cause」は現れなかった。

## 7. HIL（CH32V002、タスク 4.2、6.1、6.2、実測。実行時刻は記録していない。`date` が 00:24 JST を示した時点で実行済み）

- 試験: `tests/hil/wch/test_wwdg.py::test_wch_wwdg`（WCH SDK）、`tests/hil/test_wwdg.py::test_wwdg`（ch32fun）。それぞれ `mode` 0/1/2 のパラメータ。共通の流れは `tests/hil/wwdg_flow.py`、判定は `ch32hil/wwdg.py`、ホストの単体テストは `tests/unit/test_wwdg_judge.py`。
- コマンド:
  - `uv run pytest --hil --hil-device ch32v002 --hil-framework wch tests/hil/wch/test_wwdg.py -q --hil-run-dir <dir>` → 3 passed（41.7 s）。
  - `uv run pytest --hil --hil-device ch32v002 tests/hil/test_wwdg.py -q --hil-run-dir <dir>` → 3 passed（39.1 s）。
- 各ビルドの手順: `make clean` → build（`EXTRA_CFLAGS=-DWWDG_MODE=<n>`）→ 書き込み（識別領域 0x1ffff704 と chip 名の確認つき）→ 全量の読み戻し照合 → 3 回の「デバッガのリセット + 32 バイトの UART 取得」（モード 0 は 1 回 + 3 秒おきの 3 回の取得）→ 最後に既知のサンプル（WCH は `blink`、ch32fun は `blink_and_read`）を書き込み、検出と読み戻しと reset を確認（復旧）。全 6 試験で復旧に成功。
- 観測した UART（改行は `\n`。`<run>` は `wch` と `ch32fun` で同一）:

| モード | 観測（3 回とも同一） | 判定 |
| --- | --- | --- |
| 0 窓の内側でフィード | `cause=other\n` + 点 20 個（32 バイトの取得で、リセットの `cause=` なし）。3 秒後の 3 回の取得も点 32 個のみ | リセットされない |
| 1 早すぎるフィード | `cause=other\n.cause=WWDG\n.cause=W` | 点 1 個でリセット、要因は WWDG |
| 2 フィードしない | `cause=other\n.........cause=WWDG\n`（点 9 個） | 約 43.7 ms でリセット、要因は WWDG |

- 判定の許容: モード 1 の点は 1〜2 個、モード 2 は 8〜10 個。時間の絶対値は測っていない（Pico の取得は 5 ms ごとの点の個数だけ）。
- 成果物のハッシュ（`artifact_sha256`、先頭 12 桁）: WCH: モード 0 `1c895f7741b3`、1 `77cc79cccd3c`、2 `88e414de9905`。ch32fun: モード 0 `83a5def85f20`、1 `5d71ee3e82eb`、2 `20cf6bba135b`。
- 実行結果の JSON は作業用ディレクトリにあり、リポジトリには含めない（要点は本ログに転記した）。

## 8. 未確認（観測していないもの）

- CH32V006 の実機（接続されていない。タスク 6.3 は未実施）。002 の結果は 006 に引き継がない。
- EWI（早期割り込み）、デバッグ中の動作（DBGMCU の停止設定）、リセットまでの時間の絶対精度（HSI 未校正、点の個数は 5 ms 刻みの目安）、温度・電源電圧の影響。
- モード 0 の「リセットされない」は、リセットの繰り返しが無いことの確認（32 バイトの取得 4 回、計約 10 秒の間隔）で、間隔の間に 1 回だけリセットが起きた場合は区別できない。起動ごとに 1.5 s の待ちがあるため、連続したリセットなら、どの取得にも `cause=` が現れる。

## 9. 既存サンプルへの影響の確認（タスク 7.3、実測）

- 仕上げの時点で、1 節と同じ手順（`wwdg` を含めて clean から全 build）を再実行した。`wwdg` を除く 52 個の `.bin` の SHA-256 は変更前（1 節）と完全に一致（`diff` で差なし）。build の失敗なし。`wwdg`（既定の MODE 0）は 4 個（WCH 002/006、ch32fun 002/006）が追加され、WCH 002 の `wwdg` の SHA-256 は 7 節のモード 0 のハッシュ（`1c895f77…`）と一致した。
- 既存の HIL（CH32V002）の再実行: `uv run pytest --hil --hil-device ch32v002 --hil-framework wch tests/hil/wch/test_watchdog.py tests/hil/wch/test_blink_and_read.py` → 2 passed（29.8 s）、`uv run pytest --hil --hil-device ch32v002 tests/hil/test_watchdog.py tests/hil/test_blink_and_read.py` → 5 passed（30.8 s）。この change が触れた範囲（IWDG と近い watchdog、GPIO の基本）の再確認で、全 HIL の再実行ではない。
- `uv run pytest`（実機なし）: 377 passed、49 skipped。

## 10. 残り（2026-11-09 時点。6.3、6.4 は後に完了、[006 のログ](2026-11-09-0751-ch32v006-wwdg-hil.md)）

- 6.3（CH32V006 での WWDG の HIL）: 完了（DUT の差し替え後、別ログ）。
- 6.4: CH32V002 の行（WCH SDK、ch32fun）は `hil-verified` に更新した。006 も 6.3 の後に `hil-verified` に更新した。
