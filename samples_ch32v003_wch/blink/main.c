/* Minimal WCH SPL sample: PC0 toggles every 500 ms. */
#include "debug.h"

int main(void)
{
    /* The official startup has already called SystemInit(). */
    Delay_Init();
    RCC_APB2PeriphClockCmd(RCC_APB2Periph_GPIOC, ENABLE);
    GPIO_InitTypeDef pin = {
        .GPIO_Pin = GPIO_Pin_0,
        .GPIO_Speed = GPIO_Speed_10MHz,
        .GPIO_Mode = GPIO_Mode_Out_PP,
    };
    GPIO_Init(GPIOC, &pin);
    for (;;) {
        GPIO_SetBits(GPIOC, GPIO_Pin_0);
        Delay_Ms(500);
        GPIO_ResetBits(GPIOC, GPIO_Pin_0);
        Delay_Ms(500);
    }
}
