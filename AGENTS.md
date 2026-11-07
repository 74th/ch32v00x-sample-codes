# 作業上の注意

- `externals/` は参照元。維持するサンプルは `samples/<device>/<sample>/` に置く。
- build と flash と実行観測は別段階として扱う。実機観測なしに動作確認済みとしない。
- ビルド・書き込みは Git submodule `externals/ch32fun` に固定し、PATH 上の minichlink や参照用 book-code 内の ch32fun は使わない。ほかの `externals/` は調査用であり、コードの依存先にしない。
- 旧版 minichlink は未接続でも成功を返し、LinkE 2.22 の CH32V002 を CH32V006 と誤表示した。現在版でも `scripts/ch32fun.sh flash` の検出確認を通し、必要に応じて読み戻しを照合する。CH32V002 の識別領域は `0x1ffff704`。
- Pico の USB 再書き込み直後は再認識に時間がかかる。観測には `hardware/pico-tester/measure.py` の検出待ちを使う。WCH-LinkE の通常操作は DUT の 3.3 V 出力を有効化する場合がある。
- `xprivate/` の資料と変換物は公開しない。
- 実験、測定、環境構築などの作業は `okf/log/` に作業ごとに記録する。ファイル名は日本時間の `YYYY-MM-DD-HHMM-<内容>.md` とし、作業日時と記録日時が異なる場合や実行時刻が不明な場合は本文に明記する。時刻を推測しない。
- ログには目的、対象と配線・ツール・ソースの条件、実行コマンド、結果、失敗、未確認事項を残し、実測・ユーザー申告・推定を区別する。後で手順の妥当性をレビューできる粒度にする。秘密情報や `xprivate/` の資料本文は含めない。
