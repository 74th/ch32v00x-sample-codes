# Proposal

## Why

change `fix-ch32v00x-sample-findings` の調査で、今の Pico 治具では次の3つを確かめられないと分かりました（`okf/log/2026-11-08-2137-fix-ch32v00x-sample-findings.md` の 5.4、7.4、7.5）。

- **周期を測れない**: `GPIO_PULSE` は CPU のポーリングで 1 µs 単位のため、周期が 1 µs 前後の信号を測れない。分周が既知の 750 kHz の SCK（周期 1.33 µs）が 4〜5 µs と出た。SPI の SCK、I2C の SCL（100/400 kHz）の周期は確認できていない。
- **取引と同時に UART を受信できない**: Pico は1度に1つのコマンドしか実行しない。DUT は I2C/SPI の取引の直後にログを出すため、取引のコマンドが終わってから UART の受信を始めると、ログはもう送信済みで取り逃がす。WCH `i2c_slave` の `printf()` は4回とも0バイト、Arduino のログは断片だけだった。
- **I2C のバスエラーを起こせない**: DUT の I2C（GP10/GP11）を Low に保つ機能がない。`I2C_FAULTTEST` は Pico 内部の GP16〜19 のループバック用。

周期とログの値は、サンプルが正しく動いているかの重要な根拠です。そのため、治具を改善し、それを使う試験を足します。

## What Changes

**Pico 治具（`hardware/pico-tester/` のファームウェア）**

- **エッジ時刻の測定**: PIO を使って、指定したピンのエッジの時刻を約 8 ns 単位（125 MHz）で記録し、周期、High の幅、エッジの数を返す。今の `GPIO_PULSE` は残し、新しいコマンドとして追加する。
- **バックグラウンドの取り込み**: エッジ時刻の測定と UART の受信を、開始（arm）と読み出しの2つのコマンドに分ける。開始してから別のコマンド（`I2C_SLAVE`、`SPI_SLAVE`、`I2C_MASTER` など）を実行し、後でまとめて読み出せるようにする。PIO と DMA で受け、メインループを止めない。
- **UART の受信の拡張**: バッファを今の 32 バイトから増やし、受信ピンを固定配線の範囲で選べるようにする（例: PD5→GP9 の既定、PD2→GP14 など）。ボーレートの上限を 115200 から引き上げる（DUT と Pico の両方で成立する範囲）。
- **I2C のバスを Low に保つ**: GP10（SDA）または GP11（SCL）を、指定時間だけオープンドレインで Low に保つコマンドを追加する。
- プロトコルの能力表示（`CAPS`）に新しいコマンドと上限を加える。既存のコマンドの動作は変えない。
- 新しい能力は、DUT の判定に使う前に、Pico 単体のループバック（Pico の PWM や UART を Pico の別ピンで受ける）で自己検証する。

**HIL 試験の改善（`tests/hil/`）**

- 周期の判定を加える: SPI の SCK（ch32fun・Arduino は 750 kHz、WCH SDK は 187.5 kHz）、I2C の SCL（ch32fun 100 kHz、WCH SDK 400 kHz、Arduino の既定値）。PWM の周期とデューティ比も、新しい測定で判定し直す。
- ログの値の判定を加える: Arduino の `i2c_master`（温度・湿度）、`spi_master`（温度）、`i2c_slave_test_master`（読み出した値）の Serial 出力と、WCH SDK `i2c_slave` の `printf()` を、取引と同時に取り込んで期待値と比べる。
- I2C のバスエラーからの復旧を観測する: DUT が master のサンプルで、バスを Low に保ったときの動作と、解放後に通信が戻るかを記録する。
- 治具を更新した後、002 と 006 で全 HIL を実行し、既存の状態が悪化しないことを確かめる。

## Capabilities

### New Capabilities

なし。

### Modified Capabilities

- `pico-peripheral-fixture`: エッジ時刻の測定、バックグラウンドの取り込み、UART の受信の拡張、I2C のバスを Low に保つ機能の要件を加える。
- `hil-test-runner`: 周期の判定、取引と同時に取り込んだログの値の判定、I2C のバスエラーの観測を、HIL 試験の要件として加える。

## Impact

- 変更するコード
  - `hardware/pico-tester/`（新しい PIO プログラム、コマンドの追加、`protocol.c` の `CAPS`、`protocol.md`、自己検証のスクリプト）。Pico への再書き込みが必要（AGENTS.md のとおり、書き込み後の再認識を待つ）。
  - `ch32hil/pico.py`（新しいコマンドの呼び出し）、`tests/hil/`（新しい判定）、ホスト単体テスト。
  - `hil/matrix_*.json` の判定条件（criteria）と根拠。
- 配線: 変更しない（固定配線の範囲で行う）。
- 対象外
  - 時間の絶対精度の校正（Pico の水晶は校正しない。測った値は「Pico の時計基準、未校正」と記録する）。
  - SPI のモード 1〜3 の slave、DUT のリマップしたピン、配線の追加が要る項目。
  - DUT のサンプルの変更（試験側だけを直す。サンプルの不具合が見つかったら記録して別に扱う）。
