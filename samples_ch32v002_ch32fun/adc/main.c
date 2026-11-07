/* CH32V002 port of the CH32V003 sample; details: okf/peripherals/ch32v002-port-differences.md
 *
 * Differences from the CH32V003 version (measured on hardware unless noted):
 * - 12-bit result (V003: 10-bit). The DUT reports result >> 2 (10-bit equivalent) because the Pico fixture accepts 0..1023.
 * - CTLR2.EXTTRIG must be set for the software trigger (EXTSEL=111 + SWSTART). Without it conversions complete only
 *   on every other attempt and the EOC wait stalls (observed with SWIO printf; reason not in the manual we read).
 * - No RSTCAL/CAL bits (reserved), so no calibration step. SMP=7 is 239.5 cycles (V003: 241). ADC_LP stays default.
 * - GPIO MODE is 1 bit on CH32V00x (V003: 2 bits). GPIO_Speed_10MHz (=1) sets it and works as output;
 *   GPIO_Speed_2MHz (=2) would only set a reserved bit and leave the pin an input. Use 10MHz.
 *
 * Standard-ch32fun test sample (no extralibs, no ch32v003_GPIO_branchless.h). Related book-code intent: adc-ch32fun (CC0-1.0).
 * Contract: ADC1 channel 0 (PA2), 12-bit conversion every 200 ms (VDD reference),
 * reported as result >> 2 (10-bit equivalent) because the Pico fixture accepts 0..1023 only.
 * Result is sent on USART1 TX (PD5, 115200 8N1) as 3 hex digits + '\n'. */
#include "ch32fun.h"

static void put(uint8_t c)
{
    while (!(USART1->STATR & USART_FLAG_TXE)) {}
    USART1->DATAR = c;
}

int main(void)
{
    SystemInit();
    RCC->APB2PCENR |= RCC_APB2Periph_GPIOA | RCC_APB2Periph_GPIOD | RCC_APB2Periph_ADC1 | RCC_APB2Periph_USART1;
    RCC->CFGR0 &= ~RCC_ADCPRE; /* ADC clock = HCLK/2 */
    GPIOA->CFGLR &= ~(0xf << (4 * 2)); /* PA2 analog input */
    GPIOD->CFGLR &= ~(0xf << (4 * 5));
    GPIOD->CFGLR |= (GPIO_Speed_10MHz | GPIO_CNF_OUT_PP_AF) << (4 * 5);
    USART1->CTLR1 = USART_WordLength_8b | USART_Parity_No | USART_Mode_Tx;
    USART1->CTLR2 = USART_StopBits_1;
    USART1->CTLR3 = USART_HardwareFlowControl_None;
    USART1->BRR = (FUNCONF_SYSTEM_CORE_CLOCK + 115200 / 2) / 115200;
    USART1->CTLR1 |= CTLR1_UE_Set;
    ADC1->RSQR1 = 0;
    ADC1->RSQR3 = 0;                    /* channel 0 */
    ADC1->SAMPTR2 = 7 << (3 * 0);       /* 239.5 cycles */
    ADC1->CTLR2 = ADC_ADON | ADC_EXTSEL | ADC_EXTTRIG; /* software trigger; CH32V00x needs EXTTRIG too */
    /* CH32V00x ADC has no RSTCAL/CAL bits (reserved), so no calibration step. */
    while (1) {
        ADC1->CTLR2 |= ADC_SWSTART;
        while (!(ADC1->STATR & ADC_EOC)) {}
        uint16_t v = (ADC1->RDATAR & 0xfff) >> 2; /* 12-bit result reported as 10-bit equivalent */
        for (int sh = 8; sh >= 0; sh -= 4) put("0123456789ABCDEF"[(v >> sh) & 0xf]);
        put('\n');
        Delay_Ms(200);
    }
}
