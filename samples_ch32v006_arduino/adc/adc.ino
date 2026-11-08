#define VRX_PIN PA1
#define VRY_PIN PA2

void setup()
{
  Serial.begin(115200);

  Serial.println("init");

  // ADC
  pinMode(VRX_PIN, INPUT_ANALOG);
  pinMode(VRY_PIN, INPUT_ANALOG);
}

uint32_t count = 0;

void loop()
{
  Serial.print("loop ");
  Serial.println(count);

  // CH32V002/CH32V006 では 12 ビットなので 0~4095 が取得できる（書籍の CH32V003 では 0~1023）
  uint32_t x = analogRead(VRX_PIN);
  uint32_t y = analogRead(VRY_PIN);

  Serial.print("X: ");
  Serial.print(x);
  Serial.print(", Y: ");
  Serial.println(y);

  delay(100);
  count++;
}
