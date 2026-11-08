# CH32V002/006 ピンチェックファームウェアの作成とビルド検証

- 記録日時: 2026-11-08T08:54:13+09:00 (JST)。作業開始の正確な時刻は未記録。
  本セッション中の時刻取得は 2026-11-08 08:47:45〜08:53:23 JST。
- 作業対象: `/home/nnyn/ghq/github.com/74th/mcu-pin-check-firmware`。
- 目的: 手実装後にピンを GND に接触させて GPIO の変化を読み、導通・ブリッジを調べる
  ファームウェアを CH32V002F4P6 / CH32V002J4M6 / CH32V006K8U7 / CH32V006F8P7 に用意する。
- ユーザー確認: 当初指定の CH32V008F8P7 は CH32V006F8P7 の誤記。
  UART RX版は MCU TX → アダプター RX のログ出力版という指定。
- 実機・配線: 使用せず。既存の接続機器は調査・操作していない。flash と観測は未実施。

## 条件と参照

- `ch32v003-swd/firmware.c`、旧 MounRiverStudio の `ch32v002-uart/User/main.c` と
  `ch32v006-uart/User/main.c` を読み、プルアップ入力と変化時ログの方式を参照した。
- サンプル集 `samples_ch32v002_ch32fun/uart/main.c` のレジスタ設定を参考にした。
- upstream: https://github.com/cnlohr/ch32fun.git
- `git ls-remote https://github.com/cnlohr/ch32fun.git HEAD` は
  `b28d285460ce052a179dba8f4a22c6f73ff8e328` を返し、
  `externals/ch32fun` の HEAD と一致した（今回取得した事実）。参照 submodule は変更していない。
- WCH 公開中国語版データシートを `/tmp/pin-check-datasheets/` に取得し、pdftotext で確認:
  https://file.wch.cn/download/file?id=473 (CH32V002DS0 V1.7)、
  https://file.wch.cn/download/file?id=475 (CH32V006DS0 V2.0)。公開リポジトリには PDF 本文を追加しない。
- J4M6 の内部接続 PA1/PD6、PD1/PD4/PD5、および F8P7 の PA4/PD7 と
  K8U7 の PA7 リセットを資料から照合した。実測ではない。
- コンパイラ: `riscv64-unknown-elf-gcc (14.2.0+19) 14.2.0`。
  GNU Make 4.4.1、newlib ヘッダ `/usr/include/newlib`、ホスト C コンパイラ、Python 3。
- unifdef 2.12-1 を `apt-get download unifdef` で `/tmp` に取得し、dpkg-deb で展開して使用。
  システムへのパッケージインストールは行っていない。

## 実装とコマンド

追加ディレクトリ: `mcu-pin-check-firmware/ch32v00x-ch32fun/`。
4品種 × SDI/UART の8構成。SDI は ch32fun debug printf、UART はアプリケーションで初期化。
upstream SetupUART は CH32V00x 分岐がなく PA9 を設定してしまうため使用していない。
J4M6 では SWIO を保持するため UART TX を remap 1 の PD6（物理1番、PA1共用）へ出す。
SWIO・リセット・UART 出力と内部接続の別名を監視から外す。
初期状態を全監視ピン分出力し、以後10msポーリングで変化を出力する。

vendor には必要な C/H、ファミリー共通ハードウェアヘッダ、2種の展開済み LD、MIT ライセンスのみを置く。
対象外アーキテクチャ分岐の除去手順は同梱 `tools/vendor_ch32fun.py`、
固定リビジョン・ファイルハッシュは `vendor/ch32fun/PROVENANCE.md` に残した。
再生成コマンド（サンプル集ルートから実行）:

```sh
python3 ../mcu-pin-check-firmware/ch32v00x-ch32fun/tools/vendor_ch32fun.py \
  externals/ch32fun --unifdef /tmp/pin-check-datasheets/unifdef/usr/bin/unifdef
make -C ../mcu-pin-check-firmware/ch32v00x-ch32fun test release
```

単独ビルド検証は Python の TemporaryDirectory で対象ディレクトリのみをコピーし、
`build/` を除外した状態から `make -j4 all test` を実行。
8 BIN すべてについて元のビルド結果とバイト一致を assert した。
元リポジトリへのリンク、ch32fun checkout、submodule、MounRiverStudio への依存はない。

## 結果（ホスト上での実行結果）

- 8構成のビルドが成功し、最終ビルドの warning/error はゼロ。
- 実際の main.c をホストのレジスタ代替と組み合わせたテストが8構成で成功。
  パッケージ別の監視範囲、プルアップ設定、非対象ピン設定の保持、UART 端子と remap、
  baud rate レジスタ、起動時から L のピン、L/H 変化、変化なし、除外ピンの無視を検証。
  これはホスト上のロジック検証であり、電気特性や実機動作の確認ではない。
- 単独コピーでの8構成の並列ビルド・ホストテストが成功し、BIN も一致。
- `release/<device>-<mode>.bin/.hex` を8種類ずつ生成。
- 使用量は FLASH 2068〜2356 B、静的 RAM 32 B（スタック使用量の実測ではない）。

| 構成 | BIN bytes | SHA-256 |
| --- | --- | --- |
| ch32v002f4p6-sdi | 2356 | `11ce89e4f90a26a43a26761c565fe86130b551ac2f7696f3109169b5e684e6c9` |
| ch32v002f4p6-uart | 2068 | `9d8a3a2d8c3922f1c96b43e5f0ed5e837b739f2c4866fedfc757b82353aa7b6d` |
| ch32v002j4m6-sdi | 2356 | `4ecb4eaae2cbe8f48f89be0f3d75fcb06da1d357f448ecc79a3db65b24b03ecd` |
| ch32v002j4m6-uart | 2072 | `ba1cde51c8194323183ad1d62f3579f3daa412d46b2974890cf159df9c54e2b3` |
| ch32v006f8p7-sdi | 2356 | `1317325e897d7ffe5923147bfa7b7e48d0a883b6cb618fa154b38809556fa5e6` |
| ch32v006f8p7-uart | 2068 | `b6d5583f10fbfeec8a7a5a4e7806da6c7c63baa0b6a733ea164bf49ecd3aa868` |
| ch32v006k8u7-sdi | 2356 | `5c50027251d68a46cf8c1ebffeff82a959eaf5edf9b81cd2f1b0a0c6c20779b7` |
| ch32v006k8u7-uart | 2068 | `471e25aa3cfefbe5eb85917ae5a871ff557b5580d88ead6c3b4fb04bc627828f` |

## 失敗と未確認事項

- 初回ビルドは main.c の stdio.h 不足で printf の暗黙宣言エラー。include を追加して解消。
- `-Wextra` で upstream setjmp/longjmp の naked 関数引数に unused warning。
  `-Wno-unused-parameter` を指定し、そのほかの警告を維持した。
- 対象リポジトリ全体の `git diff --check` は、開始前から変更されていた
  `ch32v203c8t6/src/main.c:74` の末尾空白を報告。既存変更は編集していない。
- 実機書き込み、識別、読み戻し、SDI 接続時のログ、UART 波形・baud rate、GPIO 入力、
  プルアップ電圧、リセット動作は未確認。動作確認済みとはしない。
- GCC 12以前の `ARCH=rv32ec` は手順の記載のみで未検証。
- 旧 ch32v002-uart / ch32v006-uart は残した。既存ファイルの削除やコミットは行っていない。

## 8構成の生成物の再確認 (2026-11-08T08:57:01+09:00)

ユーザーの指示により実機検証を進めず、8構成の作成・生成物確認を優先。
`ch32v00x-ch32fun` で `make test release` を実行して成功。
4品種 × sdi/uart の各 BIN が build と release でバイト一致し、HEX も存在することを確認。
実機の書き込み・観測は実施していない。
