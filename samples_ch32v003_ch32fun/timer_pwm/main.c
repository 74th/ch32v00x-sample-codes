/* Standard-ch32fun test sample (no extralibs). Related book-code intent: pwm-register (CC0-1.0).
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
    TIM1->CHCTLR1 = TIM_OC1M_2 | TIM_OC1M_1 | TIM_OC1PE;
    TIM1->CH1CVR = 250;
    TIM1->CCER = TIM_CC1E;
    TIM1->BDTR = TIM_MOE;
    TIM1->CTLR1 = TIM_ARPE | TIM_CEN;
    TIM1->SWEVGR = TIM_UG;
    while (1) {}
}
