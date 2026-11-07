# Tasks

## 1. CLI基準環境（実装済みの記録）

- [x] 1.1 SDKの必要ファイルを配置し、PROVENANCEでrevision・ハッシュ・変更箇所を追跡できることを確認する。
- [x] 1.2 Makefileとbuildコマンドを追加し、WCH GCC 15.2.0でELF/BIN/HEX生成を確認する。
- [x] 1.3 公式Delay_Init/Delay_Msを利用するblinkへ変更し、nmで公式関数がリンクされたことを確認する。

## 2. 実機確認と文書

- [x] 2.1 固定minichlinkでCH32V003を検出して書き込み、1092 B全量の読み戻し一致を確認する。
- [x] 2.2 Pico GP5で500 ms High/Lowを観測し、0037の作業ログへ結果を保存する。
- [x] 2.3 READMEに再実行コマンド・依存関係・未確認範囲を記載し、記載コマンドが実行できることを確認する。
