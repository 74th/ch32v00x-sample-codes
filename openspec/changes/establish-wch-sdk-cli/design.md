# Design

## Context

今回の実装・実測を追記仕様として記録する。詳細な根拠はokf/log/2026-11-08-0030-wch-sdk-cli-setup.mdと0037-wch-sdk-official-delay.md。既存Arduino用に導入したWCH GCC 15.2.0が利用できる。

## Goals / Non-Goals

Goals: 公式SDKとCLIでの基準blinkを再現可能にする。Non-Goals: 周辺サンプル全体・CH32V002の対応。

## Decisions

- SDKをsamples_ch32v003_wch/sdkへ必要分コピーし、externalsは参照専用のままにする。直接リンクする案はリポジトリ方針に合わない。
- Makefileを新規作成し、既存WCH GCCを共用する。MRS GUIには依存しない。
- 公式debug.cを無改変で利用してDelay_Init/Delay_Msを呼ぶ。自作delayは公式API検証の目的に合わないため削除済み。
- 起動時にSystemInitが呼ばれる。HSI+PLL 48 MHzのみローカル変更。
- scripts/wch-sdk.pyでbuild/flash/observeを分け、flashは既存Dutの検出・照合ロジックを共用する。

## Risks / Trade-offs

- 公式debug.cにはUARTも同居 → 依存ドライバを含めてコンパイルし、未使用部分をGC。nmで除去を確認。
- 公式コードに未使用引数警告 → 原本を維持し警告を記録。
- SDK全体のライセンスを一般化できない → コピー対象の条件を保持しPROVENANCEに記録。
