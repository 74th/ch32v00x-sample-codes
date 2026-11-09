/* USART2 sample (CH32V006 only; not in the book). Based on the official EVT example EXAM/USART (USART2 is not used there):
 * USART2 is transmit-only here, TX remapped to PD2 (AFIO_PCFR1 USART2_RM = 011: TX/PD2, RX/PD3; RM Table 7-11).
 * Every 200 ms it sends the fixed text "usart2 0123456789\r\n" (115200 8N1). USART1 (PD5) prints the configuration once.
 * Changes from the EVT USART examples: USART2 instead of USART1, remap 3, no receive (PD3 is not wired on the fixture),
 * no interrupt/DMA. USART_Printf_Init still uses USART1 on PD5 for the log. */
#include <ch32v00x.h>
#include <debug.h>
#include <stdio.h>

#define USART2_BAUD 115200
#define MESSAGE "usart2 0123456789\r\n"

static void usart2_send(const char *s)
{
    for (; *s; s++)
    {
        while (USART_GetFlagStatus(USART2, USART_FLAG_TXE) == RESET)
        {
        }
        USART_SendData(USART2, (uint16_t)*s);
    }
    while (USART_GetFlagStatus(USART2, USART_FLAG_TC) == RESET)
    {
    }
}

int main(void)
{
    NVIC_PriorityGroupConfig(NVIC_PriorityGroup_1);
    SystemCoreClockUpdate();
    Delay_Init();
    USART_Printf_Init(115200);
    printf("usart2 remap=3 tx=PD2 baud=%d\r\n", USART2_BAUD);

    GPIO_InitTypeDef gpio = {0};
    USART_InitTypeDef usart = {0};
    RCC_PB2PeriphClockCmd(RCC_PB2Periph_GPIOD | RCC_PB2Periph_AFIO | RCC_PB2Periph_USART2, ENABLE);
    GPIO_PinRemapConfig(GPIO_PartialRemap3_USART2, ENABLE);

    gpio.GPIO_Pin = GPIO_Pin_2;
    gpio.GPIO_Mode = GPIO_Mode_AF_PP;
    gpio.GPIO_Speed = GPIO_Speed_30MHz;
    GPIO_Init(GPIOD, &gpio);

    usart.USART_BaudRate = USART2_BAUD;
    usart.USART_WordLength = USART_WordLength_8b;
    usart.USART_StopBits = USART_StopBits_1;
    usart.USART_Parity = USART_Parity_No;
    usart.USART_HardwareFlowControl = USART_HardwareFlowControl_None;
    usart.USART_Mode = USART_Mode_Tx;
    USART_Init(USART2, &usart);
    USART_Cmd(USART2, ENABLE);

    while (1)
    {
        usart2_send(MESSAGE);
        Delay_Ms(200);
    }
}
