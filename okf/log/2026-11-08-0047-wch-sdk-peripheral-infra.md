# WCH公式SDK周辺サンプルの共通基盤（add-wch-sdk-peripheral-samples タスク1.1〜1.5）

作業日時: 2026-11-08 00:47 JST（ホストdate確認）前後。記録は作業直後。実機（DUT・Pico・書き込み器）には一切触れていない。

## 目的・条件

changeの共通CLI・SDK・HIL部分（セクション1）。ホスト上のbuildと単体テストのみ。WCH GCC 15.2.0、SDK revision 4e1b7437ada5d3ae8831a6f4b811a6320e4e23c7。

## 実施内容（実測）

- 1.1: `hil/matrix_wch.json`に書籍`*-wch_sdk`全13行を`not-ported`で登録。単体テストで書籍dirと一対一照合（欠落・余分の検出も）、READMEの対応表との整合を確認。
- 1.2: `samples_ch32v003_wch/wch.mk`へ共通ビルド設定を抽出。blinkはFlash 1,092 B／RAM 268 Bで変化なし。`ch32v00x_rcc.h`をtouchすると再ビルドされることを確認。
- 1.3: `scripts/wch-sdk.py`に`--device`/`--sample`。不正指定・存在しないサンプル・未対応device（ch32v002）はビルド前にexit 2。型番不一致・成果物不足で書き込みコマンドが実行されないことを偽runnerの単体テストで確認。引数なしのbuildは従来のblinkのまま。
- 1.4: `ch32hil`に`wch` framework（matrixはch32v003のみ、ch32v002は`DeviceError`）、`Dut(framework="wch")`はPREFIXを渡さない、`conftest.py`は`wch`マーカーで選別。`pytest --collect-only`はch32fun/arduino/wchで25件。単体テスト237件成功。
- 1.5: 公式ドライバ adc/dma/i2c/spi/tim/iwdg/pwr/exti/misc の.c/.hを無改変コピーし、SHA-256をPROVENANCEへ追記。`ch32v00x_conf.h`に集約。全ドライバ込みのblinkビルドが通り、`main.map`に`externals`の参照が無いことを確認。

## 未実施・未確認

- セクション2（003の13サンプル）、3（CH32V002）、4は未着手。matrixは全て`not-ported`で、実機観測は無い。
- 追加ドライバは全てコンパイルのみ確認。各APIの実機動作は未確認。
- `--hil-framework wch`で実機に流す経路（flash/readback）は単体テスト（偽runner）のみで、実機では未実行。
