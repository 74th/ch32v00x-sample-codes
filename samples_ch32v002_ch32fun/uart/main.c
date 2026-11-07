/* CH32V002 port of the CH32V003 sample; details: okf/peripherals/ch32v002-port-differences.md
 *
 * Differences from the CH32V003 version: none in code (BRR = HCLK/baud is the same formula; HCLK is 48 MHz
 * on both). Differences that exist: only the GPIO MODE note below, and the 24 MHz HSI is set in funconfig.h.
 * - GPIO MODE is 1 bit on CH32V00x (V003: 2 bits). GPIO_Speed_10MHz (=1) sets it and works as output;
 *   GPIO_Speed_2MHz (=2) would only set a reserved bit and leave the pin an input. Use 10MHz.
 *
 * Standard-ch32fun test sample (no extralibs). Related book-code intent: uart-register (CC0-1.0).
 * Contract: USART1 115200 8N1 on PD5(TX)/PD6(RX), no remap. Sends "HELLO\n" once at start, then echoes. */
#include "ch32fun.h"

static void put(uint8_t c)
{
    while (!(USART1->STATR & USART_FLAG_TXE)) {}
    USART1->DATAR = c;
}

int main(void)
{
    SystemInit();
    RCC->APB2PCENR |= RCC_APB2Periph_GPIOD | RCC_APB2Periph_USART1;
    GPIOD->CFGLR &= ~((0xf << (4 * 5)) | (0xf << (4 * 6)));
    GPIOD->CFGLR |= ((GPIO_Speed_10MHz | GPIO_CNF_OUT_PP_AF) << (4 * 5)) | ((GPIO_Speed_In | GPIO_CNF_IN_FLOATING) << (4 * 6));
    USART1->CTLR1 = USART_WordLength_8b | USART_Parity_No | USART_Mode_Tx | USART_Mode_Rx;
    USART1->CTLR2 = USART_StopBits_1;
    USART1->CTLR3 = USART_HardwareFlowControl_None;
    USART1->BRR = (FUNCONF_SYSTEM_CORE_CLOCK + 115200 / 2) / 115200;
    USART1->CTLR1 |= CTLR1_UE_Set;
    for (const char *s = "HELLO\n"; *s; ++s) put(*s);
    while (1) {
        if (USART1->STATR & USART_FLAG_RXNE) put(USART1->DATAR);
    }
}
