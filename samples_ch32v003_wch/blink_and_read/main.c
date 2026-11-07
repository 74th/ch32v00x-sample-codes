/* Official-SDK port of book-code blink_and_read-wch_sdk (CH32V003).
 * PC0: LED output, PA1: pull-up button input. While PA1 is low the LED stays low and the loop waits 1 s.
 * Change from the book: log text goes out on USART1 TX (PD5) with USART_Printf_Init() instead of SDI printf,
 * so the fixture can observe it. Timing uses the official Delay_Ms(). */
#include <ch32v00x.h>
#include <debug.h>
#include <stdio.h>

#define LED_PIN GPIO_Pin_0
#define BUTTON_PIN GPIO_Pin_1

int main(void)
{
    NVIC_PriorityGroupConfig(NVIC_PriorityGroup_1);
    SystemCoreClockUpdate();
    Delay_Init();
    USART_Printf_Init(115200);
    printf("init\r\n");

    RCC_APB2PeriphClockCmd(RCC_APB2Periph_GPIOC | RCC_APB2Periph_GPIOA, ENABLE);
    GPIO_InitTypeDef pin = {0};
    pin.GPIO_Pin = LED_PIN;
    pin.GPIO_Mode = GPIO_Mode_Out_PP;
    pin.GPIO_Speed = GPIO_Speed_50MHz;
    GPIO_Init(GPIOC, &pin);
    pin.GPIO_Pin = BUTTON_PIN;
    pin.GPIO_Mode = GPIO_Mode_IPU;
    GPIO_Init(GPIOA, &pin);
    printf("start\r\n");

    int count = 0;
    for (;;) {
        printf("loop %d\r\n", count++);
        if (GPIO_ReadInputDataBit(GPIOA, BUTTON_PIN) == 0) {
            Delay_Ms(1000);
            continue;
        }
        Delay_Ms(500);
        GPIO_WriteBit(GPIOC, LED_PIN, Bit_SET);
        Delay_Ms(500);
        GPIO_WriteBit(GPIOC, LED_PIN, Bit_RESET);
    }
}
