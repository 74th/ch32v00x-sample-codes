# CH32V003公式SDKのCLI環境構築

記録日時: 2026-11-08 00:33 JST以降。作業中のホストdateは00:30、00:32、00:33 JSTを確認。開始時刻は未記録。ファイル名は最初に確認した00:30を使用。

## 目的・条件

ユーザー依頼: CH32V003で公式SDKのCLI構築を試す。他者コードの転用を最小にする。CH32V003を接続したとの申告あり。
既存AGENTS.mdのbuildをch32funに固定する原則に対し、今回は明示された公式SDKビルドの依頼に基づく追加構成。書き込み器は固定ch32funのまま。

- SDK: openwch/ch32v003 `4e1b7437ada5d3ae8831a6f4b811a6320e4e23c7`。出所とコピー元SHA-256はsamples_ch32v003_wch/PROVENANCE.md。
- コンパイラ: 既存Arduino公式パッケージ内WCH GCC 15.2.0、表示`riscv32-wch-elf-gcc (g5115c7e44-dirty) 15.2.0`。追加ダウンロード・インストールなし。
- 書き込み: externals/ch32fun revision b28d285460ce052a179dba8f4a22c6f73ff8e328。minichlinkの表示versionは97580959847cc7757bf6052db82c7b41476f02fd。scripts/ch32fun.sh programmerで固定revisionを照合、makeはup to date。
- 検出実測: WCH LinkE version 2.22、Detected CH32V003、Flash 16 kB、Part Type 00-30-05-00。
- Pico: USB 2e8a:000a、/dev/ttyACM0、serial E661AC8863223539、プロトコル2のCAPS確認。
- 配線は既存固定治具のPC0→1 kΩ→Pico GP5、共通GNDを前提。PC0の信号観測が成立。今回配線の物理的再確認や電圧実測はしていない。給電条件は既存設定のWCH-LinkE 3.3 V／Pico USB（設定上の条件であり今回の実測値ではない）。

## 実装

公式SDKから10ファイルのみコピー（GPIO/RCC、Coreヘッダ、Startup、System、Link.ld）。Systemの外部水晶設定をHSI＋PLL 48 MHzに変更。ヘッダの著作権・WCH製マイコン使用条件を保持。Apache-2.0表記は実際の対象ファイルにないためApacheとして再配布しない。前回調査ログにも訂正を追記。
第三者のCLI Makefileは構造の参考のみでコードコピーなし。Makefile、main.c、最小confヘッダ、操作用Pythonを新規作成。Debug、printf、UART、ボタン、不要な周辺ドライバは含めない。

## コマンド・結果

```sh
make -C samples_ch32v003_wch/blink build
.arduino/official/data/packages/WCH/tools/riscv-wch-gcc/15.2.0/bin/riscv32-wch-elf-gcc --version
externals/ch32fun/minichlink/minichlink -i
lsusb
ls -l /dev/serial/by-id
./scripts/ch32fun.sh programmer
uv run python scripts/wch-sdk.py flash
uv run python scripts/wch-sdk.py observe --output /tmp/wch-sdk-blink-observation.json
git diff --check
```

ビルド成功: Flash 1,024 B、RAM 264 B（data 8＋stack 256）。GCC size: text 1016 / data 8 / bss 256。警告なし。
flashは既存ch32hil.dut.Dutを共用。-iで検出を確認後、次を実行（絶対パスで指定）:

```sh
externals/ch32fun/minichlink/minichlink -w samples_ch32v003_wch/blink/main.bin flash -b
# 検出確認後、実行時TemporaryDirectory下へ読み戻し
externals/ch32fun/minichlink/minichlink -r <一時ディレクトリ>/readback.bin flash 1024 -b
externals/ch32fun/minichlink/minichlink -b
```

CH32V003検出とImage written.を確認し、全1,024 Bの読み戻しがmain.binと一致。リセット成功。
その後の独立した観測フェーズでGPIO_SAMPLEを実施。両端以外の5区間はすべて50サンプル＝500 ms。400～600 msの機能判定に合格。

観測結果:

```json
{
  "port": "/dev/ttyACM0",
  "pin": "PC0 -> Pico GP5",
  "count": 300,
  "interval_us": 10000,
  "runs": [
    [
      "1",
      32
    ],
    [
      "0",
      50
    ],
    [
      "1",
      50
    ],
    [
      "0",
      50
    ],
    [
      "1",
      50
    ],
    [
      "0",
      50
    ],
    [
      "1",
      18
    ]
  ],
  "pass": true,
  "criterion": "at least 4 complete half-periods, each 400..600 ms"
}
```

main.bin SHA-256: `9280fb1f00c65f73aef99bb7e258587a6e22b26309fadb4b21ecde8e9a883ab4`

## 失敗・未確認

初回のサンドボックス内ではlsusbがlibusb -99、ttyACMなし。権限拡張要求はユーザー中断。ユーザーがyolo modeで再開後、通常コマンドでUSB検出・実験を継続できた。失敗時の書き込み実行なし。

GPIO点滅のみ実機確認。CH32V002移植、UART、割り込み関数、他周辺、クリーン環境へのツール導入は未検証。時間は10 ms間隔のGPIOサンプルに基づく機能確認であり精密波形測定ではない。DUTには公式SDKのblinkを残し、PicoはfinallyでRESET_SAFE済み。
