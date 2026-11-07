# WCH公式SDKのCLIビルド事例調査

訂正（2026-11-08の後続環境構築時）: cjackerの説明から公式SDKをApache-2.0と一般化してはいけない。実際のopenwch/ch32v003 revision `4e1b7437ada5d3ae8831a6f4b811a6320e4e23c7`の対象ファイルにはWCH製マイコンへの使用条件が記載されている。後続の`2026-11-08-0030-wch-sdk-cli-setup.md`および`samples_ch32v003_wch/PROVENANCE.md`参照。

- 調査・記録: 2026-11-08 00:02 JST頃（ホストの `date '+%Y-%m-%d-%H%M %Z'` で確認）。調査開始時刻は未記録。
- 目的: MounRiver StudioのGUIなしで公式SDKをビルドする公開事例とCH32V002への適用可否を確認。
- 条件: Webの一次資料とローカルの公式SDK参照元を読んだ。機器接続・配線・ビルド・書き込み・実行観測は行っていない。

## 公開資料

- https://github.com/wuxx/CH32V003-makefile-example : vendorのCore/Debug/Peripheral/Startup/UserをgccでコンパイルするMakefile。rv32ec / ilp32e、nano.specs / nosys.specs、公式系Link.ldを使用。CH32V003用であり002対応の根拠にはしない。
- https://github.com/cjacker/opensource-toolchain-ch32v : 公式EVTをMakefile化する手順、MRS単体Linuxツールチェーン利用方法。
- https://github.com/cjacker/ch32v_evt_makefile_gcc_project_template : generate_project_from_evt.shからmakeでELF/HEX/BIN生成。掲載対応一覧に002はない。
- https://github.com/azhel12/wch_cmake : READMEがCH32V002–007 / V003対応を明記。CMSIS/SPLとデバイス別リンカスクリプト生成、WCH GCC/xPack対応。ソースはwch_libsから取得する構成。この調査では002の実ビルドや実機確認を裏付けていない。READMEのV0用ISA表記はrv32ecで、公式の乗算拡張設定との照合が必要。
- https://github.com/openwch/ch32v002_004_005_006_007 : 002の公式SDK。

## ローカル確認

実行した主なコマンド:

```sh
rg -n 'openwch|MounRiver|CH32V002' README* .gitmodules okf --glob '*.md'
rg --files externals/ch32v002_004_005_006_007
rg -n 'march|mabi|CH32V002|WCH-Interrupt|LENGTH' externals/ch32v002_004_005_006_007/EVT/EXAM/{GPIO/GPIO_Toggle,SRC} --hidden
sed -n '1,65p' externals/ch32v002_004_005_006_007/EVT/EXAM/SRC/Ld/Link.ld
sed -n '15,32p' externals/ch32v002_004_005_006_007/EVT/EXAM/SRC/Peripheral/inc/ch32v00X.h
sed -n '314,337p' externals/ch32v002_004_005_006_007/EVT/EXAM/GPIO/GPIO_Toggle/GPIO_Toggle.wvproj
sed -n '20,32p' externals/ch32v002_004_005_006_007/EVT/EXAM/GPIO/GPIO_Toggle/.cproject
```

確認結果（ソースの記述であり実測ではない）:

- Link.ldには002用Flash 16K / RAM 4K設定があるがコメントアウト。既定は006等用62K / 8K。
- Peripheral/inc/ch32v00X.hはCH32V002等が外から定義されないとCH32V006を定義する。002用には-DCH32V002が必要。
- GPIO_Toggleの設定はrv32e、compressed、WCH拡張、Zmmul、ilp32e、GCC15を指定。
- 割り込み関数にinterrupt("WCH-Interrupt-fast")がある。汎用GCCへの無修正適用は仮定しない。

## 判断・未確認

公式SDK + Makefile + MRS付属GCCをCLIから呼ぶ構成が、公式コードを保ちたい目的に適していると判断。002用SDKのstartup/core/peripheralとメモリ設定を使う必要がある。公開された003向けMakefileは構造の参考になるが、そのまま002に使える証拠ではない。

このリポジトリではexternalsの公式SDKは参照専用、build/flashは固定ch32funとする現行ルールがある。実装を行う際はユーザーのSDK対応指示とルールの整合を取る必要がある。本調査では依存・スクリプトの変更なし。

Web取得ではwuxxのmainブランチMakefile取得に失敗し、masterのページで内容を確認。wch_cmakeのraw mainファイルと推測したwch_libs URLの取得にも失敗し、詳細実装は未確認。ツールチェーンのダウンロード可否・バージョン互換性、002のビルド成功・実動作は未確認。
