/* Standard-ch32fun test sample (no extralibs). Related book-code intent: blink_and_read-ch32fun (CC0-1.0).
 * Contract: PC4 is an input (pull-down); PC0 mirrors PC4 level. Pico drives PC4 and observes PC0. */
#include "ch32fun.h"

int main(void)
{
    SystemInit();
    funGpioInitAll();
    funPinMode(PC0, GPIO_Speed_10MHz | GPIO_CNF_OUT_PP);
    funPinMode(PC4, GPIO_CNF_IN_PUPD);
    funDigitalWrite(PC4, FUN_LOW); /* PUPD + ODR=0 -> pull-down */
    while (1)
        funDigitalWrite(PC0, funDigitalRead(PC4));
}
