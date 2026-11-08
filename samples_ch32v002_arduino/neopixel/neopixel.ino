// 変更点: 固定配線の WS2812 デコードは PC6（→ Pico GP7）にあるため、データピンを PC0 から PC6 に変えた。
#define LED PC6

#define LED_PIN_NO 0
#define LED_NUM 6

// 変更点（book-code からの修正）:
// - 各バイトを MSB から送る。WS2812 は MSB 先頭で受け取るが、元のコードは LSB から送っていた（c & 0x1、c >> 1）。
// - High/Low の時間を WS2812B データシートの中央（T0H 0.4us、T1H 0.8us、T0L 0.85us、T1L 0.45us、各 +-150ns）に
//   合わせるため、nop の数をデバイス系列ごとに定数にした。値は Pico の WS2812 デコーダで実測しながら決めた
//   （okf/log/2026-11-07-2310-arduino-neopixel-timing.md）。CPU と Flash の待ちで時間が変わるので系列ごとに異なる。
// - 送信中は割り込みを止める（SysTick の割り込みで High が伸びるのを防ぐ）。
#if defined(CH32VM00X)
// CH32V002/CH32V006（CH32VM00X 系列。002 は CH32V006K8 の定義を流用。006 でも同じ機械語になり、同じ時間を実測）
#define T0H_NOPS 7
#define T0L_NOPS 11
#define T1H_NOPS 24
#define T1L_NOPS 2
#else
// CH32V003
#define T0H_NOPS 12
#define T0L_NOPS 22
#define T1H_NOPS 37
#define T1L_NOPS 8
#endif

#define NOPS_(n) asm volatile(".rept " #n "\n\tc.nop\n\t.endr")
#define NOPS(n) NOPS_(n)

// NeoPixelの制御
// digital_pin: NeoPixelのデータピン
// data: NeoPixelのデータ
// led_num: NeoPixelのLEDの数
void write_neopixel(uint32_t digital_pin, uint8_t *data, uint32_t led_num)
{
  uint32_t pin_name = digitalPinToPinName(digital_pin);
  GPIO_TypeDef *gpio = get_GPIO_Port(CH_PORT(pin_name));
  uint32_t pin_mask = CH_GPIO_PIN(pin_name);
  uint32_t h = pin_mask;
  uint32_t l = pin_mask << 16;
  uint32_t data_size = led_num * 3;

  noInterrupts();
  for (uint32_t i = 0; i < data_size; i++)
  {
    uint8_t c = data[i];
    for (int j = 0; j < 8; j++)
    {
      if (c & 0x80)
      {
        gpio->BSHR = h;
        NOPS(T1H_NOPS);
        gpio->BSHR = l;
        NOPS(T1L_NOPS);
      }
      else
      {
        gpio->BSHR = h;
        NOPS(T0H_NOPS);
        gpio->BSHR = l;
        NOPS(T0L_NOPS);
      }
      c = c << 1;
    }
  }
  interrupts();
}

void setup()
{
  Serial.begin(115200);

  Serial.println("init");

  // 出力
  pinMode(LED, OUTPUT);

  Serial.println("start");
}

int count = 0;

void loop()
{
  Serial.print("loop ");
  Serial.println(count++);

  uint8_t data[LED_NUM * 3];

  for (int i = 0; i < LED_NUM; i++)
  {
    switch ((count + i) % 6)
    {
    case 0:
      data[i * 3] = 0x20;
      data[i * 3 + 1] = 0x00;
      data[i * 3 + 2] = 0x00;
      break;
    case 1:
      data[i * 3] = 0x20;
      data[i * 3 + 1] = 0x20;
      data[i * 3 + 2] = 0x00;
      break;
    case 2:
      data[i * 3] = 0x00;
      data[i * 3 + 1] = 0x20;
      data[i * 3 + 2] = 0x00;
      break;
    case 3:
      data[i * 3] = 0x00;
      data[i * 3 + 1] = 0x20;
      data[i * 3 + 2] = 0x20;
      break;
    case 4:
      data[i * 3] = 0x00;
      data[i * 3 + 1] = 0x00;
      data[i * 3 + 2] = 0x20;
      break;
    case 5:
      data[i * 3] = 0x20;
      data[i * 3 + 1] = 0x00;
      data[i * 3 + 2] = 0x20;
      break;
    }
  }

  write_neopixel(LED, data, LED_NUM);
  delay(300);
}
