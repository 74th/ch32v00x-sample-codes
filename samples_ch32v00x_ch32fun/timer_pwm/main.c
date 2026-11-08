/* CH32V002 port of the CH32V003 sample; details: okf/peripherals/ch32v002-port-differences.md
 *
 * Differences from the CH32V003 version: the ch32fun CH32V00x header has no short TIM_* macros, so TIM1_CTLR1_CEN,
 * TIM1_SWEVGR_UG, TIM1_CTLR1_ARPE, TIM1_CCER_CC1E, TIM1_BDTR_MOE, TIM1_CHCTLR1_OC1M_1/2, TIM1_CHCTLR1_OC1PE are used
 * (same bit values). Timing is the same: PSC for a 1 MHz tick from the 48 MHz HCLK.
 * - GPIO MODE is 1 bit on CH32V00x (V003: 2 bits). GPIO_Speed_10MHz (=1) sets it and works as output;
 *   GPIO_Speed_2MHz (=2) would only set a reserved bit and leave the pin an input. Use 10MHz.
 *
 * Standard-ch32fun test sample (no extralibs). Related book-code intent: pwm-register (CC0-1.0).
 * Contract: TIM1 CH1 on PD2 outputs 1 kHz PWM, 25% duty (PWM mode 1, active high). */
#include "ch32fun.h"

int main(void)
{
    SystemInit();
    RCC->APB2PCENR |= RCC_APB2Periph_GPIOD | RCC_APB2Periph_TIM1;
    GPIOD->CFGLR &= ~(0xf << (4 * 2));
    GPIOD->CFGLR |= (GPIO_Speed_10MHz | GPIO_CNF_OUT_PP_AF) << (4 * 2);
    TIM1->PSC = FUNCONF_SYSTEM_CORE_CLOCK / 1000000 - 1; /* 1 MHz tick */
    TIM1->ATRLR = 999;                                   /* 1 kHz */
    TIM1->CHCTLR1 = TIM1_CHCTLR1_OC1M_2 | TIM1_CHCTLR1_OC1M_1 | TIM1_CHCTLR1_OC1PE;
    TIM1->CH1CVR = 250;
    TIM1->CCER = TIM1_CCER_CC1E;
    TIM1->BDTR = TIM1_BDTR_MOE;
    TIM1->CTLR1 = TIM1_CTLR1_ARPE | TIM1_CTLR1_CEN;
    TIM1->SWEVGR = TIM1_SWEVGR_UG;
    while (1) {}
}
