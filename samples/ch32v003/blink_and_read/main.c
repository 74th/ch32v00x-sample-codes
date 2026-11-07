/* Based on 74th/ch32v003-book-code blink_and_read-ch32fun (CC0-1.0). */
#include "ch32fun.h"
#include <stdio.h>

int main(void)
{
    SystemInit();
    funGpioInitAll();
    funPinMode(PC0, GPIO_Speed_10MHz | GPIO_CNF_OUT_PP);
    funPinMode(PA1, GPIO_CNF_IN_PUPD);
    funDigitalWrite(PA1, FUN_HIGH);
    printf("blink_and_read started\n");
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
