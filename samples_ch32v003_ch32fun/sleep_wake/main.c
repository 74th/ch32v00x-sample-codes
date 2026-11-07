/* Standard ch32fun sleep/wake test, informed by book-code sleep_mode_blink-register (CC0-1.0).
 * TIM1 update wakes WFI every ~500ms; main toggles PC0 after return. Does not measure current. */
#include "ch32fun.h"

void TIM1_UP_IRQHandler(void) __attribute__((interrupt));
void TIM1_UP_IRQHandler(void) {
    TIM1->INTFR = (uint16_t)~TIM_IT_Update;
}
int main(void) {
    SystemInit();
    funGpioInitAll();
    funPinMode(PC0, GPIO_Speed_10MHz | GPIO_CNF_OUT_PP);
    funDigitalWrite(PC0, FUN_LOW);
    RCC->APB2PCENR |= RCC_APB2Periph_TIM1;
    PFIC->SCTLR &= ~((1 << 2) | (1 << 3)); /* sleep, WFI */
    TIM1->CTLR1 = 0;
    TIM1->PSC = FUNCONF_SYSTEM_CORE_CLOCK / 1000 - 1;
    TIM1->ATRLR = 499;
    TIM1->RPTCR = 0;
    TIM1->SWEVGR = TIM_UG;
    TIM1->INTFR = (uint16_t)~TIM_IT_Update;
    TIM1->DMAINTENR |= TIM_IT_Update;
    NVIC_EnableIRQ(TIM1_UP_IRQn);
    TIM1->CTLR1 |= TIM_CEN;
    unsigned level = 0;
    while (1) {
        __WFI();
        level ^= 1;
        funDigitalWrite(PC0, level ? FUN_HIGH : FUN_LOW);
    }
}
