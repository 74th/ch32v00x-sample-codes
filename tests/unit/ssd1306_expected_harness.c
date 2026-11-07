/* Host expected-frame generator: runs the pinned ssd1306.h with the same scene.h as the DUT, with
 * ssd1306_pkt_send() redirected into the Pico fixture's SSD1306 model. Prints CRC and the frame buffer. */
#include <stdio.h>
#include <string.h>
#define SSD1306_128X64
#include "ssd1306_model.h"

static ssd1306_model_t model;
uint8_t ssd1306_pkt_send(const uint8_t *data, int sz, uint8_t cmd)
{
	uint8_t pkt[33];
	if (cmd) { pkt[0] = 0; pkt[1] = *data; ssd1306_model_transfer(&model, pkt, 2); }
	else { pkt[0] = 0x40; memcpy(&pkt[1], data, sz); ssd1306_model_transfer(&model, pkt, (size_t)sz + 1); }
	return 0;
}
void ssd1306_rst(void) {}

#include "ssd1306.h"
#include "scene.h"

int main(void)
{
	ssd1306_model_init(&model);
	ssd1306_init();            /* init commands + one blank frame */
	unsigned after_init_frames = (unsigned)model.frames;
	uint32_t blank_crc = ssd1306_model_crc32(&model);
	scene_draw();
	ssd1306_refresh();
	printf("init_frames=%u blank_crc32=%08x frames=%u unknown=%u bad_control=%u display_on=%d charge_pump=%d crc32=%08x\n",
	       after_init_frames, (unsigned)blank_crc, (unsigned)model.frames, (unsigned)model.unknown, (unsigned)model.bad_control,
	       model.display_on, model.charge_pump, (unsigned)ssd1306_model_crc32(&model));
	for (int p = 0; p < SSD1306_MODEL_PAGES; p++) {
		printf("P%d ", p);
		for (int i = 0; i < SSD1306_MODEL_W; i++) printf("%02x", model.fb[p * SSD1306_MODEL_W + i]);
		printf("\n");
	}
	return 0;
}
