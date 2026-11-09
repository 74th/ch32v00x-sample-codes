## ADDED Requirements

### Requirement: 周期の判定

HIL試験は、SPIのSCK、I2CのSCL、PWMの周期を、エッジ時刻の測定で得た値と、サンプルの設定から計算した期待値で判定しなければならない（SHALL）。許容幅とその根拠（Picoの時計が未校正であること、HSIの許容差）を記録しなければならない（SHALL）。

#### Scenario: SPIのSCKを判定する
- **WHEN** SCKの分周が既知のSPIのサンプルを実行し、取引の間の周期を測る
- **THEN** 測った周期が期待値（例: 48 MHz / 64 = 750 kHz）の許容幅に入るかで判定し、測った値を記録する

#### Scenario: I2CのSCLを判定する
- **WHEN** DUTがmasterのI2Cのサンプルを、Picoの相手側の動作と同時に測る
- **THEN** SCLの周期が、サンプルの設定（100 kHzまたは400 kHz）の許容幅に入るかで判定する

### Requirement: ログの値の判定

HIL試験は、DUTが取引の直後に出すログ（Serial、`printf()`）を、取引と同時に取り込み、模擬した相手の値から計算した期待値と比べなければならない（SHALL）。取り込めなかった場合は、成功として扱ってはならない（SHALL NOT）。

#### Scenario: センサーの模擬の値をログで確かめる
- **WHEN** PicoがSHT31を模擬して既知の値を返し、DUTが温度と湿度をSerialに出す
- **THEN** 取り込んだログの値が、既知の値から計算した温度と湿度に一致するかで判定する

### Requirement: I2Cのバスエラーの観測

HIL試験は、DUTがmasterのI2Cのサンプルで、バスをLowに保ったときの動作と、解放後に通信が戻るかを観測して記録しなければならない（SHALL）。書籍のサンプルに復旧の処理がない場合は、合否ではなく観測結果として記録しなければならない（SHALL）。

#### Scenario: SDAをLowに保って解放する
- **WHEN** DUTがmasterの取引を繰り返す間に、PicoがSDAを一定時間Lowに保って解放する
- **THEN** 保持中のDUTの出力（エラー表示や停止）と、解放後に取引が戻るかが記録される
