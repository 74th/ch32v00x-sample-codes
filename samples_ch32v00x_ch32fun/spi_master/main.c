/* CH32V002 port of the CH32V003 sample; details: okf/peripherals/ch32v002-port-differences.md
 *
 * Differences from the CH32V003 version: none in code. SPI1 default pins PC5/PC6/PC7 need no AFIO write. PC0 is a
 * plain GPIO chip select (SSM=1), not the hardware NSS (NSS default pin is PC1). The new HSRXEN bit stays 0.
 * AFIO_PCFR1 layout differs from V003; do not copy V003 remap values.
 * - GPIO MODE is 1 bit on CH32V00x (V003: 2 bits). GPIO_Speed_10MHz (=1) sets it and works as output;
 *   GPIO_Speed_2MHz (=2) would only set a reserved bit and leave the pin an input. Use 10MHz.
 *
 * Standard-ch32fun test sample (no extralibs, no ch32v003_SPI.h). Related book-code intent: spi_master-ch32fun (CC0-1.0).
 * Contract: SPI1 master mode 0, MSB first, 8 bit, ~750 kHz. PC5 SCK, PC6 MOSI, PC7 MISO, PC0 software CS (active low).
 * Every 500 ms: CS low, transfer 0xA5 then 0x5A, CS high. PD2 is high only if MISO returned 0x3C,0xC3. */
#include "ch32fun.h"

static uint8_t xfer(uint8_t v)
{
    while (!(SPI1->STATR & SPI_STATR_TXE)) {}
    SPI1->DATAR = v;
    while (!(SPI1->STATR & SPI_STATR_RXNE)) {}
    return SPI1->DATAR;
}

int main(void)
{
    SystemInit();
    RCC->APB2PCENR |= RCC_APB2Periph_GPIOC | RCC_APB2Periph_GPIOD | RCC_APB2Periph_SPI1;
    GPIOC->CFGLR &= ~((0xf << (4 * 0)) | (0xf << (4 * 5)) | (0xf << (4 * 6)) | (0xf << (4 * 7)));
    GPIOC->CFGLR |= ((GPIO_Speed_10MHz | GPIO_CNF_OUT_PP) << (4 * 0)) | ((GPIO_Speed_10MHz | GPIO_CNF_OUT_PP_AF) << (4 * 5)) |
                    ((GPIO_Speed_10MHz | GPIO_CNF_OUT_PP_AF) << (4 * 6)) | (GPIO_CNF_IN_FLOATING << (4 * 7));
    funDigitalWrite(PC0, FUN_HIGH);
    funPinMode(PD2, GPIO_Speed_10MHz | GPIO_CNF_OUT_PP);
    funDigitalWrite(PD2, FUN_LOW);
    SPI1->CTLR1 = SPI_CTLR1_MSTR | SPI_CTLR1_SSI | SPI_CTLR1_SSM | SPI_CTLR1_BR_2 | SPI_CTLR1_BR_0; /* BR=0b101: /64 -> 750 kHz */
    SPI1->CTLR1 |= SPI_CTLR1_SPE;
    while (1) {
        funDigitalWrite(PC0, FUN_LOW);
        uint8_t a = xfer(0xA5);
        uint8_t b = xfer(0x5A);
        while (SPI1->STATR & SPI_STATR_BSY) {}
        funDigitalWrite(PC0, FUN_HIGH);
        funDigitalWrite(PD2, a == 0x3C && b == 0xC3 ? FUN_HIGH : FUN_LOW);
        Delay_Ms(500);
    }
}
