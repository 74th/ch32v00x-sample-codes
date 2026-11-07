# arduino-cli 環境の構築と書籍 Blink の compile（verify-arduino-core-with-arduino-cli 1.1〜1.4）

- 作業日時: 2026-11-07 20:55〜21:01 JST（コマンド実行時刻は `date` の実測。記録は 21:02 頃）
- change: `openspec/changes/verify-arduino-core-with-arduino-cli`
- 範囲: ビルドのみ。書き込み・実機観測はしていない。

## 目的

書籍 2.1 節の Arduino IDE 手順を arduino-cli で再現するため、バージョン固定・リポジトリ内に閉じた arduino-cli 環境を作り、3つの core 供給元を並べて CH32V003 向けに compile できる状態にする。

## 条件

- ホスト: Linux x86_64。PATH 上に `arduino-cli` はない（`command -v arduino-cli` が空）。ホームに `~/.arduino15` が既に存在する（13 エントリ）。
- 追加・変更したファイル: `scripts/arduino.sh`（新規）、`scripts/arduino-sketches/book_blink/book_blink.ino`（新規。書籍 2.2 節のコードを写したもの）、`.gitignore`（`.arduino/` を追加）。
- 導入物はすべて `.arduino/`（gitignore 対象）。

## 1.1 arduino-cli の固定

- 選んだ版: **arduino-cli 1.5.1**（`gh release list -R arduino/arduino-cli` で 2026-06-05 の Latest。v1.5.2-rc.1 は pre-release なので除外）。
- 配布 URL: `https://github.com/arduino/arduino-cli/releases/download/v1.5.1/arduino-cli_1.5.1_Linux_64bit.tar.gz`
- SHA-256（リリースの `1.5.1-checksums.txt` から取得）:
  - Linux_64bit: `28a8e119c498a25607821c36cb2dc49e8463941b261a0d99091baa7bc692dd2b`
  - Linux_ARM64: `1e69e077479f300614d4551334e0a33f08ee40b04315d83b8e7e0e94f0d0ee62`（aarch64 では未実行）
- `./scripts/arduino.sh setup` は `.arduino/cache/` に取得 → `sha256sum -c` で照合 → `.arduino/bin/arduino-cli` に展開 → `version --format json` が 1.5.1 であることを確認する。以後の全サブコマンドも呼び出し前に同じ版チェックを行い、`--config-file .arduino/<supplier>/arduino-cli.yaml` を必ず付ける。

実行と結果（実測）:

```
$ ./scripts/arduino.sh setup
arduino-cli: .../.arduino/bin/arduino-cli (arduino-cli  Version: 1.5.1 Commit: 01f3d4f2b Date: 2026-06-05T10:22:17Z)
$ .arduino/bin/arduino-cli version
arduino-cli  Version: 1.5.1 Commit: 01f3d4f2b Date: 2026-06-05T10:22:17Z
$ command -v arduino-cli   → 出力なし（PATH 上には存在しない）
```

## 1.2 供給元の index（実測取得 2026-11-07 20:57 頃）

| 供給元 | index URL | 取得物の SHA-256 |
| --- | --- | --- |
| thirdparty | `https://raw.githubusercontent.com/robinjanssens/WCH32V_board_manager_files/main/package_ch32v_index.json`（書籍 2.1 節） | `a6bd39f1...e487b113` |
| official | `https://github.com/openwch/board_manager_files/raw/main/package_ch32v_index.json`（`externals/arduino_core_ch32/README.md` 記載） | `70907e4b...a3215ea4` |

index は可変（同じ URL で内容が書き換わる）。実際、official の 1.0.5 エントリは追加後に beforeinstall 2.0.0 に差し替えられている（下記コミット履歴）。

- vendor:arch は **両方とも `WCH:ch32v`**（パッケージ名が衝突するため、design D2 のとおり data ディレクトリを供給元ごとに分けた）。
- thirdparty の提供版: 1.0.0, 1.0.1, 1.0.2, 1.0.3, 1.0.4, 1.0.5-alpha, 1.0.5-beta
  - 1.0.5-alpha / 1.0.5-beta の platform は `robinjanssens/arduino_core_ch32` のタグ 1.0.5a / 1.0.5b。ツールは riscv-none-embed-gcc 8.2.0、openocd 1.0.0、beforeinstall 1.0.0、wchisp 0.2.3。
  - index リポジトリの履歴（GitHub API）: 1.0.5-alpha 追加 2024-12-04、**1.0.5-beta 追加 2025-05-03**。書籍執筆時（2025年3月）に Board Manager で入るのは 1.0.5-alpha だったと推定する（推定。書籍に版の記載はない）。今日 IDE で同じ手順を踏むと最新の 1.0.5-beta が入る。
- official の提供版: 1.0.0〜1.0.4, **1.0.5（index 追加 2026-11-03）**, **1.0.6（index 追加 2026-11-07）**
  - 1.0.5 以降はツールが riscv-wch-gcc 15.2.0、openocd-wch 2.10.0、beforeinstall 2.0.0 に変わった。これらのツール配布元は `github.com/medtty/board_manager_files` の release（openwch ではない）。Linux は x86_64 のみ。
  - 1.0.6 の platform アーカイブは `openwch/arduino_core_ch32` の release asset（submodule の TinyUSB を含む）。
- CH32V00x / CH32VM00X のボード（`board listall`、両供給元とも同じ）:
  - `CH32V00x` → `WCH:ch32v:CH32V00x_EVT`（Board Select は `pnum=CH32V003F4` のみ）
  - `CH32VM00X` → `WCH:ch32v:CH32VM00X_EVT`（Board Select は `pnum=CH32V006K8` のみ）
  - メニュー（両供給元同じ）: clock（48MHz_HSI 既定 / 24MHz_HSI / 8MHz_HSI / 48・24・8MHz_HSE）、opt、dbg、rtlib、upload_method（swdMethod 既定 / ispMethod）。
- 固定した core: thirdparty `WCH:ch32v@1.0.5-beta`、official `WCH:ch32v@1.0.6`（いずれも現時点の最新）。

生成した設定（`./scripts/arduino.sh config <supplier>`、core-install でも自動生成）は `directories.data/downloads/user` と `build_cache.path` をすべて `.arduino/<supplier>/` 以下に向ける。official-git だけは data/downloads を official と共有する。

```
$ ./scripts/arduino.sh core-install thirdparty
... Platform WCH:ch32v@1.0.5-beta installed
WCH:ch32v 1.0.5-beta 1.0.5-beta CH32 MCU EVT Boards
$ ./scripts/arduino.sh core-install official
... Platform WCH:ch32v@1.0.6 installed
WCH:ch32v 1.0.6     1.0.6  CH32 MCU EVT Boards
```

- core install には `--skip-post-install` を付けた。beforeinstall の post_install（udev ルール導入など、OpenOCD/WCH-LinkE 用と思われる）は実行していない。書き込みは固定 minichlink で行うので不要と判断した（中身は未確認）。
- `~/.arduino15` の変化確認: 開始前に `find ~/.arduino15 -printf '%p %s %T@\n'` を保存し、core install 後と compile 後に diff → **差分なし**（実測）。`~/.cache/arduino` と `/tmp/arduino` も作られていない。

## 1.3 official-git

- 参照用 clone `externals/arduino_core_ch32` の HEAD は `d62c6b1646d7f139f1ac750ddfbd56120102ac5d`（2026-11-03、PR #279 のマージ）。これは **上流タグ 1.0.5 と同じコミット**（`git describe --tags` → `1.0.5`）。
- 上流（`git ls-remote origin`）の main / HEAD はすでに `7927c06`（= タグ 1.0.6、配布 1.0.6 と同じ）で、1.0.5→1.0.6 は 14 コミット（Serial RX バッファ、micros()/delay() の修正、Boards Manager 用アーカイブ添付など）。clone は fetch していない（clone を変えない制約のため）。
- したがって、この change の 3 供給元は「thirdparty 1.0.5-beta / official 配布 1.0.6 / official-git = 公式 1.0.5 のソース」となる。official-git は記録済み revision のまま固定した（タスク記載どおり）。
- export は `git archive d62c6b1 | tar -x` で `.arduino/official-git/user/hardware/WCHgit/ch32v/` に置いた。配布版 `WCH:ch32v` と FQBN が衝突しないよう vendor を `WCHgit` に変えた。ツールチェーンは official の data（riscv-wch-gcc 15.2.0）を共有。
- 確認（実測）:
  - clone の HEAD、`git status --porcelain`、`.git/index` の mtime を前後で比較 → 変化なし。
  - `git ls-tree -r d62c6b1` の blob 633 件すべてについて、export 先のファイルの `git hash-object` が一致（mismatch 0）。
  - 例外: submodule `libraries/Adafruit_TinyUSB_Arduino`（commit 1f9da49）は git archive に含まれず空ディレクトリになる。TinyUSB を使うスケッチは official-git では compile できない可能性がある（CH32V003 の book スケッチは USB を使わないので影響は 2.1 で確認する）。
  - `core list`（official-git 設定）に `WCHgit:ch32v 1.0.5 CH32V EVT Boards Support` と、共有 data の `WCH:ch32v 1.0.6` が並んで表示される。比較では FQBN の vendor で区別する。

## 1.4 書籍 Blink の compile

FQBN（書籍の「CH32V00x」「48MHz Internal」「WCH-SWD」に相当）: `<vendor>:ch32v:CH32V00x_EVT:pnum=CH32V003F4,clock=48MHz_HSI,upload_method=swdMethod`

```
./scripts/arduino.sh compile <supplier> scripts/arduino-sketches/book_blink \
  --fqbn "$(./scripts/arduino.sh fqbn <supplier> CH32V00x_EVT pnum=CH32V003F4,clock=48MHz_HSI,upload_method=swdMethod)" \
  --build-path .arduino/build/<supplier>/book_blink
```

| 供給元 | core | コンパイラ | 結果 | Flash | RAM | 備考 |
| --- | --- | --- | --- | --- | --- | --- |
| thirdparty | WCH:ch32v 1.0.5-beta | riscv-none-embed-gcc 8.2.0 | 成功 | 6988 B (42%) | 536 B (26%) | |
| official | WCH:ch32v 1.0.6 | riscv-wch-gcc 15.2.0 (riscv32-wch-elf) | 成功 | 5856 B (35%) | 856 B (41%) | ld 警告「LOAD segment with RWX permissions」 |
| official-git | WCHgit:ch32v @ d62c6b1 (1.0.5) | riscv-wch-gcc 15.2.0 | 成功 | 7312 B (44%) | 752 B (36%) | 同じ ld 警告 |

- 3つとも `.arduino/build/<supplier>/book_blink/book_blink.ino.bin` と `.elf` が生成された（実測）。
- `compile` サブコマンドは arduino-cli の版、固定した platform、`core list` を毎回出力するので、使った core の版がログに残る。
- コンパイラのパスは `-v` 出力で確認（thirdparty は `.arduino/thirdparty/data/.../riscv-none-embed-gcc/8.2.0`、official は `.arduino/official/data/.../riscv-wch-gcc/15.2.0`）。

### 書籍 2.1 節の IDE 操作と CLI の対応

| 書籍の IDE 操作 | arduino-cli での対応 |
| --- | --- |
| 基本設定 → 追加のボードマネージャの URL に robinjanssens の URL を追加 | `.arduino/thirdparty/arduino-cli.yaml` の `board_manager.additional_urls`（`./scripts/arduino.sh config thirdparty`） |
| ボードマネージャで「CH32 MCU EVT Board」をインストール | `./scripts/arduino.sh core-install thirdparty`（= `core update-index` + `core install WCH:ch32v@1.0.5-beta --skip-post-install`）。IDE は最新版を入れるが、CLI では版を固定 |
| ツール → ボード → CH32 MCU EVT Boards → CH32V00x | FQBN `WCH:ch32v:CH32V00x_EVT`（`pnum=CH32V003F4`） |
| Clock Select: 48MHz Internal | FQBN オプション `clock=48MHz_HSI`（既定値） |
| Upload method: WCH-SWD | FQBN オプション `upload_method=swdMethod`（既定値。compile には影響しない。CLI では upload を使わない） |
| ファイル → スケッチ例 → Blink を PC0 に書き換え | `scripts/arduino-sketches/book_blink/book_blink.ino` |
| 「書き込み」（検証 + OpenOCD で書き込み） | 検証 = `./scripts/arduino.sh compile ...`。書き込みは `arduino-cli upload` を使わず固定 minichlink（4 章で実施） |
| 出力タブの「Verified OK」 | IDE（WCH 版 OpenOCD）固有の表示のため確認しない。代わりに minichlink の書き込み確認と readback で判定する |

## 失敗・注意

- 最初の official-git の照合コマンドは書き方を誤り（`sha1sum -c` にプロセス置換を渡した）、照合になっていなかった。`git hash-object` で blob ごとに比較し直し、上記の結果を得た。
- スクリプトの不正な供給元指定は `error: unknown supplier 'bogus'`、終了コード 2 で止まることを確認した。

## 未確認

- core 未導入の状態で compile したときのエラー表示（arduino-cli の標準エラーに任せている。今回は導入後に実行したため未観測）。
- aarch64 ホストでの setup。
- beforeinstall の post_install スクリプトの中身。
- 書き込み・実機での点滅（4 章で実施予定）。
