# CH32V003F4P6 の build → flash → measure

この手順は Ubuntu 26.04 x86-64 での検証を基にする。WCH-LinkE と Raspberry Pi Pico (RP2040) が必要。書き込みは DUT の既存ファームウェアを上書きする。配線・電源は [配線手順](wiring.md) の接続前レビューを済ませる。

## ソースとツール

このリポジトリの `samples/ch32v003/blink_and_read/` と `scripts/ch32fun.sh` を使う。[ビルド環境](../README.md#ch32v003-のビルド環境)の依存パッケージを導入する。Pico 用には [Pico 観測手順](pico-tester/README.md) の SDK と pyserial が必要。検証時の RISC-V GCC は 14.2.0、Make は 4.4.1、WCH-LinkE の firmware は 2.9。

ch32fun はプロジェクトの submodule `externals/ch32fun` を用いる。記録時の gitlink は `b28d285460ce052a179dba8f4a22c6f73ff8e328`。book-code はビルドに不要。

```sh
git submodule update --init externals/ch32fun
git -C externals/ch32fun rev-parse HEAD
./scripts/ch32fun.sh check
```

以前の別 checkout 再現はプロジェクト `df9d42d442da91b9313d42665d1ef8d875fa4b97` と旧 ch32fun を使用した。現在の submodule での確認は作業ログを参照。サンプルやコンパイラの差異によりバイナリのハッシュは変わり得る。

## ビルド

```sh
./scripts/ch32fun.sh build
sha256sum samples/ch32v003/blink_and_read/main.bin
```

`BUILD OK` と終了コード 0 を確認する。ch32fun `b28d285` での成果物は 1056 bytes、SHA-256 `5688ff09715f63c04a6855129f7b3d6c85359a56ae3ba6cbd31130e9894561dc`。ビルド成功は実機動作を意味しない。

## 書き込みと読み戻し

Pico のファームウェアを [手順](pico-tester/README.md) で用意し、配線レビューを終えてから実行する。

```sh
./scripts/ch32fun.sh flash
readback_file=$(mktemp)
externals/ch32fun/minichlink/minichlink -r "$readback_file" flash 1056 -b
cmp samples/ch32v003/blink_and_read/main.bin "$readback_file"
sha256sum "$readback_file"
```

書き込みの終了コードと `FLASH OK`、読み戻しの終了コード、`cmp` の終了コード 0 を別々に確認する。1056 は上記の成果物のバイト数であり、異なる成果物を使う場合は `stat -c %s samples/ch32v003/blink_and_read/main.bin` の値に合わせる。一時ファイルの場所は `$readback_file` で確認し、不要になったら個別に削除できる。固定 minichlink は DUT 未検出でも終了コード 0 を返す場合があるため、スクリプトはデバイス検出も確認する。読み戻しでもデバイス検出を確認する。

## 起動と測定

```sh
timeout 5s stdbuf -oL -eL externals/ch32fun/minichlink/minichlink -b -T
python3 hardware/pico-tester/measure.py
```

起動ログ `blink_and_read started` と `PC0 high` / `PC0 low` の繰り返しを確認する。timeout の終了コード 124 は5秒でログ取得を止めたことを示す。測定コマンドは PASS、MISMATCH、TIMEOUT、通信・プロトコルエラーを区別する。PA1 が Low だと点滅しない。

結果と限界は [11:13 の作業ログ](../okf/log/2026-11-07-1113-ch32v003-flash-readback-measure.md)、[未接続時の確認](../okf/log/2026-11-07-1113-disconnected-flash-preparation.md) を参照。実際の電源、接続、部品値、ツール、ソース、各コマンドの結果を別途記録する。
