/* CH32V002 port of the CH32V003 sample; details: okf/peripherals/ch32v002-port-differences.md
 *
 * Differences from the CH32V003 version: none in code. LSI is nominally 128 kHz but spans 90-172 kHz on CH32V002,
 * so only the 3+6 pulse signature is checked, not the absolute IWDG period.
 * - GPIO MODE is 1 bit on CH32V00x (V003: 2 bits). GPIO_Speed_10MHz (=1) sets it and works as output;
 *   GPIO_Speed_2MHz (=2) would only set a reserved bit and leave the pin an input. Use 10MHz.
 *
 * Standard-ch32fun test sample (no extralibs). Related book-code intent: watchdogtimer-register (CC0-1.0).
 * Contract (PC0 signature): after power-on: 3 pulses (100 ms) then the IWDG (~1 s) is started and not fed -> reset.
 * After an IWDG reset: 6 pulses are emitted instead, then the sample idles with PC0 low.
 * Sleep modes are NOT covered by this sample. */
#include "ch32fun.h"

static void pulses(int n)
{
    for (int i = 0; i < n; ++i) {
        funDigitalWrite(PC0, FUN_HIGH);
        Delay_Ms(100);
        funDigitalWrite(PC0, FUN_LOW);
        Delay_Ms(100);
    }
}

int main(void)
{
    SystemInit();
    funGpioInitAll();
    funPinMode(PC0, GPIO_Speed_10MHz | GPIO_CNF_OUT_PP);
    if (RCC->RSTSCKR & RCC_IWDGRSTF) {
        RCC->RSTSCKR |= RCC_RMVF;
        pulses(6);
        while (1) {}
    }
    pulses(3);
    IWDG->CTLR = 0x5555;  /* unlock PSCR/RLDR */
    IWDG->PSCR = 3;       /* LSI(128 kHz)/32 */
    IWDG->RLDR = 4000;    /* ~1 s */
    IWDG->CTLR = 0xCCCC;  /* start */
    while (1) {}
}
