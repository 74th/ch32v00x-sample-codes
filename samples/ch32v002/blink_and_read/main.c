/* Adapted from the project CH32V003 baseline, itself based on book-code (CC0-1.0). */
#include "ch32fun.h"
#include <stdio.h>

int main(void)
{
    SystemInit();
    funGpioInitAll();
    /* CH32V00x MODE has one writable bit; 1 selects push-pull output. */
    funPinMode(PC0, 1 | GPIO_CNF_OUT_PP);
    funPinMode(PA1, GPIO_CNF_IN_PUPD);
    funDigitalWrite(PA1, FUN_HIGH);
    printf("blink_and_read CH32V002 started\n");
    while (1) {
        if (funDigitalRead(PA1) == FUN_LOW) {
            printf("PA1 low: waiting\n");
            Delay_Ms(1000);
            continue;
        }
        funDigitalWrite(PC0, FUN_HIGH);
        printf("PC0 high\n");
        Delay_Ms(500);
        funDigitalWrite(PC0, FUN_LOW);
        printf("PC0 low\n");
        Delay_Ms(500);
    }
}
