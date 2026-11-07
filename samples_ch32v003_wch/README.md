# WCH公式SDKのCLIビルド（CH32V003）

MounRiver StudioのGUIなしで、WCH公式SDKをWCH GCC 15.2.0からビルドする最小サンプル。
2026-11-08にCH32V003でビルド、固定minichlinkによる書き込み・全量読み戻し、PicoでのGPIO点滅観測を実施した。
CH32V002はこの構成では未対応・未検証。

```sh
# リポジトリルートから。各段階は独立して実行する。
uv run python scripts/wch-sdk.py build
uv run python scripts/wch-sdk.py flash
uv run python scripts/wch-sdk.py observe
```

`flash`は接続中のCH32V003のプログラムを書き換える。ビルドは別途先に行う。
書き込み器は`externals/ch32fun`に固定し、`scripts/ch32fun.sh programmer`でrevisionと環境を確認する。
既存HILの`Dut.flash`を共用し、期待チップの検出と`Image written.`の確認を通し、全量読み戻し照合後にリセットする。
SDKのビルドは今回の公式SDK対応の依頼に基づく別構成であり、ch32funの起動コードやヘッダには依存しない。

観測は既存固定配線のPC0（DUT）→1 kΩ→GP5（Pico）、共通GNDを前提とする。
Pico firmware v2の`discover`、`CAPS`、`RESET_SAFE`、`GPIO_SAMPLE`を使う。
300点を10 ms間隔で取得し、窓の両端を除いた完全なHigh/Low区間が4個以上、各400～600 msであることを確認する。
電圧や波形の精度測定ではない。サンプルはPC0の500 msごとの点滅だけで、ボタンやUARTは含めない。

## ツールチェーン

既存の公式Arduino環境が導入したWCH GCCを共用する。Arduino coreのコードはリンクしない。
既定パスは`.arduino/official/data/packages/WCH/tools/riscv-wch-gcc/15.2.0`。
未導入環境では既存のセットアップ手順を利用できる（ネットワーク接続が必要）。

```sh
./scripts/arduino.sh setup
./scripts/arduino.sh core-install official
```

別のWCH GCCを使う場合は直接Makeに指定する。検証済みは上記15.2.0だけ。

```sh
make -C samples_ch32v003_wch/blink build TOOLCHAIN=/path/to/toolchain
```

`-march=rv32ec_zicsr -mabi=ilp32e`。公式Startupが`SystemInit()`を呼ぶ。
クロックは外部水晶不要のHSI＋PLL 48 MHz、Flash 16 KB／RAM 2 KB、スタック256 B。
ビルド結果は`blink/main.elf`、`main.bin`、`main.hex`、`main.map`。
公式Delay関数版の結果はFlash 1,092 B、RAM 268 B（初期化データ8 B＋BSS 4 B＋スタック256 B）。

## SDKの転用範囲

GPIO/RCC、Coreヘッダ、Startup、System、リンカスクリプトと、公式Delay関数のためのDebug・USARTの計14ファイルを公式SDKからコピーした。
起動時のクロック設定後に`Delay_Init()`を一度呼び、`Delay_Ms(500)`で待機する。
`debug.c`は無改変で、UART関連の宣言・ドライバも一緒にコンパイルするが、未使用関数はリンク時に除去される。
`nm`で`Delay_Init`/`Delay_Ms`の存在と、USART関数・`_write`・`_sbrk`が残らないことを確認した。
公式`debug.c`の`_write`に未使用引数`fd`の警告が1件出るが、コピー元を保持している。
`System`だけHSI設定に変更し、その他のコピー元は無改変。第三者のMakefileや変換スクリプトのコードはコピーしていない。
出所revision、コピー前SHA-256、利用条件、参考URLは[PROVENANCE.md](PROVENANCE.md)に記録した。
ビルド時に`externals/ch32v003`を参照しない。

現行のコピー対象にはWCH製マイコンへの使用条件が記載されている。Apache-2.0として扱わない。
