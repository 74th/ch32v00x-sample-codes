/* helper verification sample: SSD1306 over I2C using the pinned externals/ch32fun extralibs
 *   extralibs/ssd1306_i2c.h + extralibs/ssd1306.h (+ font_8x8.h), not copied, not modified (submodule revision b28d285).
 * Related book  : externals/ch32v003-book-code/i2c_oled-ch32fun (CC0-1.0)
 * Changes       : fixed drawing (scene.h, shared with the host expected-frame generator) instead of the bitmap/text demo;
 *                 refresh every 500 ms. funconfig.h is the book's default (the helper
 *                 printf()s on I2C errors, which needs the default debug printf).
 * Helper config : 128x64, address 0x3C, PC1 SDA / PC2 SCL. The helper hard-codes SSD1306_I2C_CLKRATE 1000000 (no #ifndef),
 *                 so it cannot be overridden by a define. By default this sample re-programs I2C1 CKCFGR to 100 kHz
 *                 standard mode after ssd1306_i2c_init(); build with HELPER_CLOCK=1 (-DSSD1306_KEEP_HELPER_CLOCK)
 *                 to keep the helper's 1 MHz setting. */
#define SSD1306_128X64

#include "ch32fun.h"
#include <stdio.h>
#include "ssd1306_i2c.h"
#include "ssd1306.h"
#include "scene.h"

#ifndef SSD1306_KEEP_HELPER_CLOCK
static void i2c_use_100khz(void)
{
	I2C1->CTLR1 &= ~I2C_CTLR1_PE;
	I2C1->CKCFGR = (FUNCONF_SYSTEM_CORE_CLOCK / (2 * 100000)) & I2C_CKCFGR_CCR; // standard mode, no FS/DUTY
	I2C1->CTLR1 |= I2C_CTLR1_PE;
	I2C1->CTLR1 |= I2C_CTLR1_ACK;
}
#endif

int main()
{
	SystemInit();
	Delay_Ms(100);

	if (ssd1306_i2c_init())
		while (1)
			;
#ifndef SSD1306_KEEP_HELPER_CLOCK
	i2c_use_100khz();
#endif
	ssd1306_init(); // sends the init commands and one blank frame

	while (1)
	{
		scene_draw();
		ssd1306_refresh();
		Delay_Ms(500);
	}
}
