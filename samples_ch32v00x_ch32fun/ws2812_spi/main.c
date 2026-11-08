/* CH32V002 port of samples_ch32v003_ch32fun/ws2812_spi/main.c (same source). Device differences: okf/peripherals/ch32v002-port-differences.md. */
/* helper verification sample: WS2812 over SPI1 + DMA using the pinned externals/ch32fun
 *   extralibs/ws2812b_dma_spi_led_driver.h, not copied, not modified (submodule revision b28d285).
 * Related book  : externals/ch32v003-book-code/neopixel-ch32fun (CC0-1.0)
 * Changes       : fixed colours instead of the HSV animation (no color_utilities.h); one frame every 100 ms.
 * Helper config : WSGRB, 6 LEDs, SPI1 MOSI = PC6 at 48 MHz / 16 = 3 MHz, one data bit = 4 SPI bits (1 -> 1110, 0 -> 1000).
 * Wire order    : read from the helper source (WSGRB branch of WS2812FillBuffSec): the 24-bit callback value is sent as
 *                 byte bits 15:8, then bits 7:0, then bits 23:16. With value = R | G<<8 | B<<16 the wire order is G, R, B.
 *                 (The book's comment says "red | blue<<8 | green<<16"; that would put B first on the wire.)
 *                 Which physical LED colour results was not observed (no LED involved). */
#include "ch32fun.h"
#include <stdint.h>

#define WS2812DMA_IMPLEMENTATION
#define WSGRB
#define LED_NUM 6

#include "ws2812b_dma_spi_led_driver.h"

#define COLOR(g, r, b) ((uint32_t)(r) | ((uint32_t)(g) << 8) | ((uint32_t)(b) << 16))

static const uint32_t colors[LED_NUM] = {
	COLOR(0x00, 0xFF, 0xA5), COLOR(0x5A, 0x01, 0x80), COLOR(0xFF, 0x00, 0x0F),
	COLOR(0xF0, 0x33, 0xCC), COLOR(0x55, 0xAA, 0x7E), COLOR(0x81, 0x18, 0xC3)};

uint32_t WS2812BLEDCallback(int ledno)
{
	return colors[ledno];
}

int main()
{
	SystemInit();
	WS2812BDMAInit();

	while (1)
	{
		while (WS2812BLEDInUse)
			;
		WS2812BDMAStart(LED_NUM);
		Delay_Ms(100);
	}
}
