/* Hardware-independent SSD1306 (128x64) command/data interpreter used by the Pico fixture and host tests.
 * Feed it one I2C transfer (the bytes after the address byte, START..STOP) at a time.
 * Scope: addressing modes (horizontal/vertical/page), column/page windows, display on/off, charge pump.
 * Other known commands are accepted and counted; unknown commands are counted and their first values kept.
 * Not modelled: scrolling, contrast, inversion, remap effects on the stored frame buffer. */
#ifndef SSD1306_MODEL_H
#define SSD1306_MODEL_H
#include <stdbool.h>
#include <stddef.h>
#include <stdint.h>

#define SSD1306_MODEL_W 128
#define SSD1306_MODEL_PAGES 8
#define SSD1306_MODEL_FB_SIZE (SSD1306_MODEL_W * SSD1306_MODEL_PAGES)
#define SSD1306_MODEL_UNKNOWN_KEEP 8

typedef struct {
    uint8_t fb[SSD1306_MODEL_FB_SIZE];
    uint8_t mode;                       /* 0 horizontal, 1 vertical, 2 page */
    uint8_t col_start, col_end, page_start, page_end;
    uint8_t col, page;
    uint8_t pending_cmd, pending_left, pending_n, pending_args[6];
    bool display_on, charge_pump, display_on_seen;
    uint32_t transfers, cmds, data_bytes, unknown, bad_control;
    uint32_t frame_bytes;               /* data bytes since the last 0x21/0x22 window command */
    uint32_t frames;                    /* completed windows (frame_bytes reached the window area) */
    uint8_t unknown_first[SSD1306_MODEL_UNKNOWN_KEEP];
} ssd1306_model_t;

void ssd1306_model_init(ssd1306_model_t *m);
/* One I2C transfer: bytes after the address byte. A transfer that ends inside a command's arguments keeps
 * the pending command for the next transfer (the SSD1306 sees one byte stream per control byte). */
void ssd1306_model_transfer(ssd1306_model_t *m, const uint8_t *buf, size_t len);
uint32_t ssd1306_model_crc32(const ssd1306_model_t *m);
#endif
