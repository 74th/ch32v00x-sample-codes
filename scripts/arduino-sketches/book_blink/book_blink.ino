// 書籍『CH32V003開発ガイドブック』2.2 節の Blink（LED_BUILTIN を PC0 に置換したもの）をそのまま写したもの。
// scripts/arduino.sh compile の供給元比較（tasks 1.4）に使う。維持サンプルではない。
void setup() {
  pinMode(PC0, OUTPUT);
}

void loop() {
  digitalWrite(PC0, HIGH);
  delay(1000);
  digitalWrite(PC0, LOW);
  delay(1000);
}
