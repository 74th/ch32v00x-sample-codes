# Proposal

## Why

CH32V002とCH32V006のサンプルおよび検証記録が揃ったため、既存のCH32V003書籍の章立てを使って両デバイス向けの日本語解説を整備する。コードと実測に基づく説明を、書籍のリポジトリで維持できるようにする。

## What Changes

- 独立したGitリポジトリ `externals/ch32v003-book` に `articles-ch32v00x/` を作る。
- 既存 `articles/` のディレクトリ名・章番号を踏襲し、1章の簡潔な導入と2〜15章の本文を作る。1冊内でCH32V002とCH32V006の共通点と差分を説明する。
- 1章では「74thが作ったWCH-LinkE」「ひとまず動く開発ボードが欲しい」「CH32V003開発で知っておくと良いこと」「後継、類似モデル」を省略する。0・16・17・18・99章は作成しない。
- サンプルへの参照、配線、環境条件、ビルド・書き込み・実機観測の区別、既知の制約を記載する。
- 新原稿用の目次を `articles-ch32v00x/README.md` に置く。既存書籍の出版設定変更やPDF制作は今回の対象外とする。
- 実装成果物は `ch32v003-book` リポジトリにコミットする。親の `ch32v00x-sample-codes` リポジトリには原稿を追加・コミットせず、bookを新たなsubmoduleにも変更しない。

## Capabilities

### New Capabilities

なし。原稿整備のみであり、製品・サンプル・検証システムの振る舞いは変更しない。`skip_specs: true` とする。

### Modified Capabilities

なし。

## Impact

- 執筆・コミット先: `externals/ch32v003-book/articles-ch32v00x/` と、必要な公開用補助資料。
- 計画管理先: 本リポジトリの `openspec/changes/write-ch32v00x-book-articles/`。計画をここに置くことと、原稿のコミット先を分ける。
- 参照元: 本リポジトリの `samples_ch32v002_{arduino,wch}`、`samples_ch32v006_{arduino,wch}`、`samples_ch32v00x_ch32fun`、`scripts/`、`hil/matrix*.json`、公開可能な `okf/`。サンプルコードは移動・複製して維持しない。
- 既存 `articles/`、既存出版設定、サンプル実装、実機試験環境の変更は対象外。`xprivate/` の資料と変換物は公開しない。
