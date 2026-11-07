/* Official-SDK port of book-code standby_mode_blink-wch_sdk (CH32V003): Standby mode woken by the auto wake-up (AWU).
 * After 5 s ("wait", then "init"/"start") the loop prints "go to standby: N", enters Standby with
 * PWR_EnterSTANDBYMode(PWR_STANDBYEntry_WFE) and is woken by the AWU 80 ms x 25 = 2 s later (LSI ~128 kHz, prescaler
 * 10240, window 25; EXTI line 9 event, the same setup as the official EVT PWR/Standby_Mode example). Execution then
 * resumes after the WFE (not a reset): SystemInit() restores the clocks, "Auto wake up: N" is printed and the LED toggles.
 * The first 5 s ("wait") leave time to re-flash or recover before the chip first enters Standby, in which a debugger
 * may not be able to attach (see README).
 * Changes from the book: the LED is PC0 (fixture BLINK -> GP5; the book's PC1 is the fixture's I2C SDA) and the
 * NMI/HardFault declarations/handlers are dropped (official startup defaults). The rest is the book's code. */
#include <ch32v00x.h>
#include <debug.h>
#include <stdio.h>

#define BLINKY_GPIO_PORT GPIOC
#define BLINKY_GPIO_PIN GPIO_Pin_0

#define ENABLE_UART_PRINT 1

int main(void)
{
  GPIO_InitTypeDef GPIO_InitStructure = {0};
  EXTI_InitTypeDef EXTI_InitStructure = {0};

  NVIC_PriorityGroupConfig(NVIC_PriorityGroup_1);
  SystemCoreClockUpdate();
  Delay_Init();

#if ENABLE_UART_PRINT
  USART_Printf_Init(115200);

  printf("wait\r\n");
#endif

  Delay_Ms(5000);

#if ENABLE_UART_PRINT
  printf("init\r\n");
#endif

  RCC_APB2PeriphClockCmd(RCC_APB2Periph_GPIOC | RCC_APB2Periph_AFIO, ENABLE);
  RCC_APB1PeriphClockCmd(RCC_APB1Periph_PWR, ENABLE);
  RCC_LSICmd(ENABLE);

  GPIO_InitStructure.GPIO_Pin = BLINKY_GPIO_PIN;
  GPIO_InitStructure.GPIO_Mode = GPIO_Mode_Out_PP;
  GPIO_InitStructure.GPIO_Speed = GPIO_Speed_10MHz;
  GPIO_Init(BLINKY_GPIO_PORT, &GPIO_InitStructure);

  EXTI_InitStructure.EXTI_Line = EXTI_Line9;
  EXTI_InitStructure.EXTI_Mode = EXTI_Mode_Event;
  EXTI_InitStructure.EXTI_Trigger = EXTI_Trigger_Falling;
  EXTI_InitStructure.EXTI_LineCmd = ENABLE;
  EXTI_Init(&EXTI_InitStructure);

  while (RCC_GetFlagStatus(RCC_FLAG_LSIRDY) == RESET)
    ;

  // LSI 128kHz
  // Prescaler 10240 -> 128kHz / 10240 = 12.5Hz = 80ms
  // window value 31
  // 80ms * 31 = 2000ms = 2s
  PWR_AWU_SetPrescaler(PWR_AWU_Prescaler_10240);
  PWR_AWU_SetWindowValue(25);
  // Prescaler 61440 -> 128kHz / 61440 = 2Hz = 500ms
  // window value 4
  // 500ms * 4 = 2000ms = 2s
  // PWR_AWU_SetPrescaler(PWR_AWU_Prescaler_61440);
  // PWR_AWU_SetWindowValue(4);
  PWR_AutoWakeUpCmd(ENABLE);

  GPIO_WriteBit(BLINKY_GPIO_PORT, BLINKY_GPIO_PIN, 1);

#if ENABLE_UART_PRINT
  printf("start\r\n");
#endif

  int count = 0;
  uint8_t ledState = 0;

  while (1)
  {
#if ENABLE_UART_PRINT
    printf("go to standby: %d\r\n\r\n", count);
#endif

    PWR_EnterSTANDBYMode(PWR_STANDBYEntry_WFE);
    SystemInit();

#if ENABLE_UART_PRINT
    printf("\r\nAuto wake up: %d \r\n", count);
#endif

    GPIO_WriteBit(BLINKY_GPIO_PORT, BLINKY_GPIO_PIN, ledState);
    ledState ^= 1;

    count++;
  }
}
