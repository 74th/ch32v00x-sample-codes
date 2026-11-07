/* CH32V002 port of samples_ch32v003_ch32fun/i2c_slave_helper/main.c (same source). Device differences: okf/peripherals/ch32v002-port-differences.md. */
/* helper verification sample: i2c_slave.h (SetupI2CSlave) from the pinned externals/ch32fun.
 * Source helper : externals/ch32fun/examples/i2c_slave/i2c_slave.h (not copied, not modified; submodule revision b28d285)
 * Related book  : externals/ch32v003-book-code/i2c_slave-ch32fun (CC0-1.0)
 * Changes       : no UART printf; callbacks record observable state in the register array so a
 *                 Pico master can read it back; PC0 is latched High when the expected write was seen.
 * Helper config : unchanged defaults (I2C bus clock rate 1 MHz fast mode in the helper; a Pico master
 *                 at 100 kHz still works as the slave follows the master's clock).
 * Contract (I2C1 slave address 0x42, SDA=PC1, SCL=PC2, 0x30 byte register array):
 *   0x00 write-callback count   0x01 last write reg   0x02 last write length   0x03 read-callback count
 *   0x04 last read reg
 *   0x10-0x1F  master writable scratch
 *   0x20-0x2F  initialised to 0x10*i (low byte) at start
 * PC0 goes High and stays High after a write callback with reg=0x10, length=4. */
#include "ch32fun.h"
#include "i2c_slave.h"

#define I2C_ADDRESS 0x42
#define REG_WRITE_COUNT 0x00
#define REG_WRITE_REG 0x01
#define REG_WRITE_LEN 0x02
#define REG_READ_COUNT 0x03
#define REG_READ_REG 0x04

volatile uint8_t i2c_registers[0x30] = {0x00};

static void on_write(uint8_t reg, uint8_t length)
{
	/* The helper reports every STOP, including after read-only transactions (then length = bytes read). */
	i2c_registers[REG_WRITE_COUNT]++;
	i2c_registers[REG_WRITE_REG] = reg;
	i2c_registers[REG_WRITE_LEN] = length;
	if (reg == 0x10 && length == 4)
		funDigitalWrite(PC0, FUN_HIGH);
}

static void on_read(uint8_t reg)
{
	i2c_registers[REG_READ_COUNT]++;
	i2c_registers[REG_READ_REG] = reg;
}

int main()
{
	SystemInit();
	funGpioInitAll();

	funPinMode(PC0, GPIO_CFGLR_OUT_10Mhz_PP);
	funDigitalWrite(PC0, FUN_LOW);
	funPinMode(PC1, GPIO_CFGLR_OUT_10Mhz_AF_OD); // SDA
	funPinMode(PC2, GPIO_CFGLR_OUT_10Mhz_AF_OD); // SCL

	for (int i = 0x20; i < 0x30; i++)
		i2c_registers[i] = 0x10 * i;

	SetupI2CSlave(I2C_ADDRESS, i2c_registers, sizeof(i2c_registers), on_write, on_read, false);

	while (1)
		;
}
