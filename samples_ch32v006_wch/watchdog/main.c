/* Official-SDK port of book-code watchdogtimer-wch_sdk (CH32V003): IWDG with a 2 s timeout, fed while the button is up.
 * PA1 (pull-up input) low = "button pressed": the loop stops feeding, so the independent watchdog resets the chip about
 * 2 s after the last feed. LED1 blinks 250/250 ms while fed; LED2 lights for 500 ms after every start to show a reset.
 * Changes from the book:
 *  - LED1 = PC0 (fixture BLINK -> GP5), LED2 = PC4 (-> GP15); the book's PC1/PC2 are the fixture's I2C pair.
 *  - the book calls IWDGSetReload(2000), which is not in the official SDK; the official name is IWDG_SetReload.
 *  - logs go to USART1 TX (PD5) with USART_Printf_Init instead of SDI printf.
 *  - added: the reset cause is read once from RCC (RCC_FLAG_IWDGRST, then RCC_ClearFlag) and printed at start and in
 *    every "loop" line (" cause=IWDG" or " cause=other"), so a watchdog reset can be recognised from the UART text alone.
 * The IWDG setup is the book's: prescaler 128 on the ~128 kHz LSI gives ~1 kHz, reload 2000 = ~2 s. */
#include <ch32v00x.h>
#include <debug.h>
#include <stdio.h>

#define LED1_PIN GPIO_Pin_0
#define LED2_PIN GPIO_Pin_4
#define BUTTON_PIN GPIO_Pin_1

int main(void)
{
  NVIC_PriorityGroupConfig(NVIC_PriorityGroup_1);
  SystemCoreClockUpdate();
  Delay_Init();

  // USART1 printf (PD5)
  USART_Printf_Init(115200);

  // Reset cause: IWDG reset flag (cleared afterwards so that the next reset shows its own cause)
  const char *cause = RCC_GetFlagStatus(RCC_FLAG_IWDGRST) == SET ? "IWDG" : "other";
  RCC_ClearFlag();

  printf("init\r\n");
  printf("reset cause: %s\r\n", cause);

  GPIO_InitTypeDef GPIO_InitStructure = {0};

  RCC_PB2PeriphClockCmd(RCC_PB2Periph_GPIOC, ENABLE);
  GPIO_InitStructure.GPIO_Pin = LED1_PIN | LED2_PIN;
  GPIO_InitStructure.GPIO_Mode = GPIO_Mode_Out_PP;
  GPIO_InitStructure.GPIO_Speed = GPIO_Speed_30MHz;
  GPIO_Init(GPIOC, &GPIO_InitStructure);

  RCC_PB2PeriphClockCmd(RCC_PB2Periph_GPIOA, ENABLE);
  GPIO_InitStructure.GPIO_Pin = BUTTON_PIN;
  GPIO_InitStructure.GPIO_Mode = GPIO_Mode_IPU;
  GPIO_InitStructure.GPIO_Speed = GPIO_Speed_30MHz;
  GPIO_Init(GPIOA, &GPIO_InitStructure);

  printf("start\r\n");

  // Independent Watch Dog Timerを2sのカウンタでセット
  IWDG_WriteAccessCmd(IWDG_WriteAccess_Enable);
  // LSIは128kHzにつき、128分周でミリ秒になる
  IWDG_SetPrescaler(IWDG_Prescaler_128);
  // 2,000ms = 2s でリセット
  IWDG_SetReload(2000);
  // 最初のカウンタリセット
  IWDG_ReloadCounter();
  // IDWGを有効化
  IWDG_Enable();

  int count = 0;

  // リセットされたことが分かるようにLED2を点滅
  GPIO_WriteBit(GPIOC, LED2_PIN, Bit_SET);
  Delay_Ms(500);
  GPIO_WriteBit(GPIOC, LED2_PIN, Bit_RESET);

  printf("start loop\r\n");

  while (1)
  {
    printf("loop %d cause=%s\r\n", count++, cause);

    uint8_t btn = GPIO_ReadInputDataBit(GPIOA, BUTTON_PIN);
    if (btn == 0)
    {
      // ボタンが押された場合、LED1を点灯せず、Watch Dog Timerのカウンタもリロードしない
      // これによりWatch Dog Timerによるリセットが発生する
      printf("Button pressed %d\r\n", count);
      Delay_Ms(500);
      continue;
    }

    // ボタンが押されない場合、LED1を点滅
    GPIO_WriteBit(GPIOC, LED1_PIN, Bit_SET);
    Delay_Ms(250);
    GPIO_WriteBit(GPIOC, LED1_PIN, Bit_RESET);
    Delay_Ms(250);

    // Watch Dog Timerをリロード
    IWDG_ReloadCounter();
  }
}
