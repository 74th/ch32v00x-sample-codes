# CH32V003F4P6 の build → flash → measure

この手順は Ubuntu 26.04 x86-64 での検証を基にする。WCH-LinkE と Raspberry Pi Pico (RP2040) が必要。書き込みは DUT の既存ファームウェアを上書きする。配線・電源は [配線手順](wiring.md) の接続前レビューを済ませる。

## ソースとツール

このリポジトリの `samples/ch32v003/blink_and_read/` と `scripts/ch32fun.sh` を使う。[ビルド環境](../README.md#ch32v003-のビルド環境)の依存パッケージを導入する。Pico 用には [Pico 観測手順](pico-tester/README.md) の SDK と pyserial が必要。検証時の RISC-V GCC は 14.2.0、Make は 4.4.1、WCH-LinkE の firmware は 2.9。

固定 book-code `4ce0a1b2fe0fa771e68e17944c4ce0d9b20924ae` と、その gitlink の ch32fun `2679ac059f3ada402731e5a10818cc0814e9ec4c` を用意する。すでに checkout がある場合、切り替える前にその変更を確認する。

```sh
./scripts/setup-externals.sh
git -C externals/ch32v003-book-code checkout 4ce0a1b2fe0fa771e68e17944c4ce0d9b20924ae
git -C externals/ch32v003-book-code submodule update --init ch32fun
git -C externals/ch32v003-book-code rev-parse HEAD
git -C externals/ch32v003-book-code/ch32fun rev-parse HEAD
./scripts/ch32fun.sh check
```

このリポジトリ自体は記録時点で初回コミット前のため、プロジェクト側のコミット ID はまだない。コミット後はその ID も実行記録に残す。サンプルやコンパイラの差異によりバイナリのハッシュは変わり得る。

## ビルド

```sh
./scripts/ch32fun.sh build
sha256sum samples/ch32v003/blink_and_read/main.bin
```

`BUILD OK` と終了コード 0 を確認する。2026-11-07 の成果物は 1056 bytes、SHA-256 `2edca10fa40bac56fa2131db88eeb1b47199408413ee2b2a85d42a1c12d83783`。ビルド成功は実機動作を意味しない。

## 書き込みと読み戻し

Pico のファームウェアを [手順](pico-tester/README.md) で用意し、配線レビューを終えてから実行する。

```sh
./scripts/ch32fun.sh flash
readback_file=$(mktemp)
externals/ch32v003-book-code/ch32fun/minichlink/minichlink -r "$readback_file" flash 1056 -b
cmp samples/ch32v003/blink_and_read/main.bin "$readback_file"
sha256sum "$readback_file"
```

書き込みの終了コードと `FLASH OK`、読み戻しの終了コード、`cmp` の終了コード 0 を別々に確認する。1056 は上記の成果物のバイト数であり、異なる成果物を使う場合は `stat -c %s samples/ch32v003/blink_and_read/main.bin` の値に合わせる。一時ファイルの場所は `$readback_file` で確認し、不要になったら個別に削除できる。固定 minichlink は DUT 未検出でも終了コード 0 を返す場合があるため、スクリプトはデバイス検出も確認する。読み戻しでもデバイス検出を確認する。

## 起動と測定

```sh
timeout 5s stdbuf -oL -eL externals/ch32v003-book-code/ch32fun/minichlink/minichlink -b -T
python3 hardware/pico-tester/measure.py
```

起動ログ `blink_and_read started` と `PC0 high` / `PC0 low` の繰り返しを確認する。timeout の終了コード 124 は5秒でログ取得を止めたことを示す。測定コマンドは PASS、MISMATCH、TIMEOUT、通信・プロトコルエラーを区別する。PA1 が Low だと点滅しない。

結果と限界は [11:13 の作業ログ](../okf/log/2026-11-07-1113-ch32v003-flash-readback-measure.md)、[未接続時の確認](../okf/log/2026-11-07-1113-disconnected-flash-preparation.md) を参照。実際の電源、接続、部品値、ツール、ソース、各コマンドの結果を別途記録する。
