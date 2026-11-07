/* CH32V002 port of the CH32V003 sample; device differences: okf/peripherals/ch32v002-port-differences.md.
 * Standard-ch32fun test sample (no extralibs). Related book-code intent: i2c_master-register (CC0-1.0).
 * Contract: I2C1 master 100 kHz on PC2(SCL)/PC1(SDA), external pull-ups required.
 * Every 500 ms: write {0x55,0xAA} to address 0x42, then read 2 bytes. PC0 is high only if the read was {0x12,0x34}. */
#include "ch32fun.h"

static int wait(uint32_t flag)
{
    for (uint32_t n = 0; n < 100000; ++n)
        if (I2C1->STAR1 & flag) return 0;
    return -1;
}

static int xfer(void)
{
    uint8_t bytes[2] = {0, 0};
    int success = 0;
    I2C1->CTLR1 |= I2C_CTLR1_START;
    if (wait(I2C_STAR1_SB)) goto stop;
    I2C1->DATAR = 0x42 << 1;
    if (wait(I2C_STAR1_ADDR)) goto stop;
    (void)I2C1->STAR2;
    for (uint8_t i = 0; i < 2; ++i) {
        if (wait(I2C_STAR1_TXE)) goto stop;
        I2C1->DATAR = i ? 0xAA : 0x55;
    }
    if (wait(I2C_STAR1_BTF)) goto stop;
    I2C1->CTLR1 |= I2C_CTLR1_START;
    if (wait(I2C_STAR1_SB)) goto stop;
    I2C1->CTLR1 |= I2C_CTLR1_ACK;
    I2C1->DATAR = (0x42 << 1) | 1;
    if (wait(I2C_STAR1_ADDR)) goto stop;
    (void)I2C1->STAR2;
    for (uint8_t i = 0; i < 2; ++i) {
        if (i == 1) I2C1->CTLR1 &= ~I2C_CTLR1_ACK;
        if (wait(I2C_STAR1_RXNE)) goto stop;
        bytes[i] = I2C1->DATAR;
    }
    success = bytes[0] == 0x12 && bytes[1] == 0x34;
stop:
    I2C1->CTLR1 |= I2C_CTLR1_STOP;
    I2C1->STAR1 &= ~I2C_STAR1_AF;
    return success;
}

int main(void)
{
    SystemInit();
    RCC->APB2PCENR |= RCC_APB2Periph_GPIOC;
    RCC->APB1PCENR |= RCC_APB1Periph_I2C1;
    GPIOC->CFGLR &= ~((0xf << (4 * 1)) | (0xf << (4 * 2)));
    GPIOC->CFGLR |= ((GPIO_Speed_10MHz | GPIO_CNF_OUT_OD_AF) << (4 * 1)) | ((GPIO_Speed_10MHz | GPIO_CNF_OUT_OD_AF) << (4 * 2));
    I2C1->CTLR2 = FUNCONF_SYSTEM_CORE_CLOCK / 1000000;
    I2C1->CKCFGR = FUNCONF_SYSTEM_CORE_CLOCK / (2 * 100000);
    I2C1->CTLR1 = I2C_CTLR1_PE;
    funPinMode(PC0, GPIO_Speed_10MHz | GPIO_CNF_OUT_PP);
    funDigitalWrite(PC0, FUN_LOW);
    while (1) {
        funDigitalWrite(PC0, xfer() ? FUN_HIGH : FUN_LOW);
        Delay_Ms(500);
    }
}
