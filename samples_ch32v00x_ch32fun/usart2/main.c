/* USART2 sample, plain ch32fun register access (CH32V006 only; not in the book). Same behaviour as samples_ch32v006_wch/usart2
 * (based on the official EVT example EXAM/USART, which only uses USART1): USART2 is transmit-only, TX remapped to PD2
 * (AFIO_PCFR1.USART2_RM = 011: TX/PD2, RX/PD3; RM Table 7-11; the WCH SDK's GPIO_PartialRemap3_USART2 writes 0x30 << 16).
 * Every 200 ms it sends the fixed text "usart2 0123456789\r\n" (115200 8N1). USART1 (PD5) prints one line at start.
 * CH32V002 has no USART2: the build stops with #error. */
#include "ch32fun.h"

#ifndef CH32V006
#error "usart2 needs USART2, which only the CH32V006 has (CH32V002 has none); build with TARGET_MCU=CH32V006"
#endif

#define BAUD 115200
#define MESSAGE "usart2 0123456789\r\n"

static void put1(uint8_t c)
{
    while (!(USART1->STATR & USART_FLAG_TXE)) {}
    USART1->DATAR = c;
}

static void put2(uint8_t c)
{
    while (!(USART2->STATR & USART_FLAG_TXE)) {}
    USART2->DATAR = c;
}

int main(void)
{
    SystemInit();
    RCC->APB2PCENR |= RCC_APB2Periph_GPIOD | RCC_APB2Periph_AFIO | RCC_APB2Periph_USART1 | RCC_USART2EN;
    GPIOD->CFGLR &= ~((0xf << (4 * 5)) | (0xf << (4 * 2)));
    GPIOD->CFGLR |= ((GPIO_Speed_10MHz | GPIO_CNF_OUT_PP_AF) << (4 * 5)) | ((GPIO_Speed_10MHz | GPIO_CNF_OUT_PP_AF) << (4 * 2));
    AFIO->PCFR1 = (AFIO->PCFR1 & ~AFIO_PCFR1_USART2_RM) | AFIO_PCFR1_USART2_RM_0 | AFIO_PCFR1_USART2_RM_1; /* 011 */

    USART1->CTLR1 = USART_WordLength_8b | USART_Parity_No | USART_Mode_Tx;
    USART1->CTLR2 = USART_StopBits_1;
    USART1->CTLR3 = USART_HardwareFlowControl_None;
    USART1->BRR = (FUNCONF_SYSTEM_CORE_CLOCK + BAUD / 2) / BAUD;
    USART1->CTLR1 |= CTLR1_UE_Set;
    for (const char *s = "usart2 remap=3 tx=PD2 baud=115200\r\n"; *s; ++s) put1(*s);

    USART2->CTLR1 = USART_WordLength_8b | USART_Parity_No | USART_Mode_Tx;
    USART2->CTLR2 = USART_StopBits_1;
    USART2->CTLR3 = USART_HardwareFlowControl_None;
    USART2->BRR = (FUNCONF_SYSTEM_CORE_CLOCK + BAUD / 2) / BAUD;
    USART2->CTLR1 |= CTLR1_UE_Set;

    while (1) {
        for (const char *s = MESSAGE; *s; ++s) put2(*s);
        while (!(USART2->STATR & USART_FLAG_TC)) {}
        Delay_Ms(200);
    }
}
