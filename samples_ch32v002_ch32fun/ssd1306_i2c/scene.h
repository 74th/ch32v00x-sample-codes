/* Fixed drawing used by both the DUT (main.c) and the host expected-frame generator
 * (tests/unit/ssd1306_expected_harness.c). Uses only the pinned ssd1306.h drawing API. */
#ifndef SCENE_H
#define SCENE_H

static const uint8_t scene_sprite[32] = {
	0xff, 0xff, 0x80, 0x01, 0xbf, 0xfd, 0xa0, 0x05, 0xaf, 0xf5, 0xa8, 0x15, 0xab, 0xd5, 0xaa, 0x55,
	0xaa, 0x55, 0xab, 0xd5, 0xa8, 0x15, 0xaf, 0xf5, 0xa0, 0x05, 0xbf, 0xfd, 0x80, 0x01, 0xff, 0xff};

static void scene_draw(void)
{
	ssd1306_setbuf(0);
	ssd1306_drawstr(2, 2, "CH32V003", 1);
	ssd1306_drawstr(2, 14, "ssd1306 helper", 1);
	ssd1306_drawRect(0, 0, 128, 64, 1);
	ssd1306_drawImage(100, 30, scene_sprite, 16, 16, 0);
	for (int i = 0; i < 40; i++)
		ssd1306_drawPixel(4 + i * 2, 28 + (i % 8), 1);
	ssd1306_drawstr(2, 50, "0123456789", 1);
}

#endif
