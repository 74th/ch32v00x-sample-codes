/* Standard-ch32fun test sample (no extralibs). Related book-code intent: i2c_slave-register (CC0-1.0).
 * Contract: I2C1 slave address 0x42 on PC2(SCL)/PC1(SDA). Master writes are stored (last 2 bytes);
 * master reads return the stored bytes (0x00,0x00 before any write). Polling implementation. */
#include "ch32fun.h"

int main(void)
{
    uint8_t buf[2] = {0, 0}, wi = 0, ri = 0;
    SystemInit();
    RCC->APB2PCENR |= RCC_APB2Periph_GPIOC;
    RCC->APB1PCENR |= RCC_APB1Periph_I2C1;
    GPIOC->CFGLR &= ~((0xf << (4 * 1)) | (0xf << (4 * 2)));
    GPIOC->CFGLR |= ((GPIO_Speed_10MHz | GPIO_CNF_OUT_OD_AF) << (4 * 1)) | ((GPIO_Speed_10MHz | GPIO_CNF_OUT_OD_AF) << (4 * 2));
    I2C1->CTLR2 = FUNCONF_SYSTEM_CORE_CLOCK / 1000000;
    I2C1->CKCFGR = FUNCONF_SYSTEM_CORE_CLOCK / (2 * 100000);
    I2C1->OADDR1 = 0x42 << 1;
    I2C1->CTLR1 = I2C_CTLR1_PE | I2C_CTLR1_ACK;
    while (1) {
        uint16_t s1 = I2C1->STAR1;
        if (s1 & I2C_STAR1_ADDR) {
            (void)I2C1->STAR2;
            wi = ri = 0;
        } else if (s1 & I2C_STAR1_RXNE) {
            buf[wi++ & 1] = I2C1->DATAR;
        } else if (s1 & I2C_STAR1_TXE) {
            I2C1->DATAR = buf[ri++ & 1];
        } else if (s1 & I2C_STAR1_STOPF) {
            I2C1->CTLR1 |= I2C_CTLR1_PE; /* clears STOPF */
        } else if (s1 & I2C_STAR1_AF) {
            I2C1->STAR1 &= ~I2C_STAR1_AF;
        }
    }
}
