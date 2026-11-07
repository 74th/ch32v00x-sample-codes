#include <string.h>
#include "ssd1306_model.h"

void ssd1306_model_init(ssd1306_model_t *m) {
    memset(m, 0, sizeof *m);
    m->mode = 2;                        /* power-on default: page addressing */
    m->col_end = SSD1306_MODEL_W - 1;
    m->page_end = SSD1306_MODEL_PAGES - 1;
}

static void unknown_cmd(ssd1306_model_t *m, uint8_t c) {
    if (m->unknown < SSD1306_MODEL_UNKNOWN_KEEP) m->unknown_first[m->unknown] = c;
    m->unknown++;
}

static unsigned arg_count(uint8_t c, bool *known) {
    *known = true;
    switch (c) {
    case 0x20: case 0x81: case 0x8D: case 0xA8: case 0xD3: case 0xD5: case 0xD9: case 0xDA: case 0xDB: return 1;
    case 0x21: case 0x22: case 0xA3: return 2;
    case 0x26: case 0x27: return 6;
    case 0x29: case 0x2A: return 5;
    case 0xA0: case 0xA1: case 0xA4: case 0xA5: case 0xA6: case 0xA7: case 0xAE: case 0xAF:
    case 0xC0: case 0xC8: case 0xE3: case 0x2E: case 0x2F: return 0;
    default:
        if (c <= 0x1F || (c >= 0x40 && c <= 0x7F) || (c >= 0xB0 && c <= 0xB7)) return 0;
        *known = false; return 0;
    }
}

static void window_reset(ssd1306_model_t *m) {
    m->col = m->col_start; m->page = m->page_start; m->frame_bytes = 0;
}

static void finish_cmd(ssd1306_model_t *m) {
    const uint8_t *a = m->pending_args;
    switch (m->pending_cmd) {
    case 0x20: if (a[0] <= 2) m->mode = a[0]; else unknown_cmd(m, 0x20); break;
    case 0x21:
        if (a[0] < SSD1306_MODEL_W && a[1] < SSD1306_MODEL_W && a[0] <= a[1]) {
            m->col_start = a[0]; m->col_end = a[1]; window_reset(m);
        } else unknown_cmd(m, 0x21);
        break;
    case 0x22:
        if (a[0] < SSD1306_MODEL_PAGES && a[1] < SSD1306_MODEL_PAGES && a[0] <= a[1]) {
            m->page_start = a[0]; m->page_end = a[1]; window_reset(m);
        } else unknown_cmd(m, 0x22);
        break;
    case 0x8D: m->charge_pump = (a[0] & 0x04) != 0; break;
    default: break;
    }
}

static void command_byte(ssd1306_model_t *m, uint8_t c) {
    m->cmds++;
    if (m->pending_left) {
        m->pending_args[m->pending_n++] = c;
        if (--m->pending_left == 0) finish_cmd(m);
        return;
    }
    bool known; unsigned n = arg_count(c, &known);
    if (!known) { unknown_cmd(m, c); return; }
    if (c == 0xAE || c == 0xAF) { m->display_on = (c == 0xAF); m->display_on_seen = true; }
    else if (c <= 0x0F && m->mode == 2) m->col = (uint8_t)((m->col & 0xF0) | c);
    else if (c >= 0x10 && c <= 0x1F && m->mode == 2) m->col = (uint8_t)((m->col & 0x0F) | ((c & 0x0F) << 4));
    else if (c >= 0xB0 && c <= 0xB7 && m->mode == 2) m->page = c & 7;
    if (n) { m->pending_cmd = c; m->pending_left = (uint8_t)n; m->pending_n = 0; }
}

static void data_byte(ssd1306_model_t *m, uint8_t d) {
    m->data_bytes++;
    m->fb[(size_t)m->page * SSD1306_MODEL_W + m->col] = d;
    m->frame_bytes++;
    unsigned area = (unsigned)(m->col_end - m->col_start + 1) * (m->page_end - m->page_start + 1);
    if (m->mode != 2 && m->frame_bytes == area) m->frames++;
    if (m->mode == 0) {
        if (++m->col > m->col_end) {
            m->col = m->col_start;
            if (++m->page > m->page_end) m->page = m->page_start;
        }
    } else if (m->mode == 1) {
        if (++m->page > m->page_end) {
            m->page = m->page_start;
            if (++m->col > m->col_end) m->col = m->col_start;
        }
    } else {
        m->col = (uint8_t)((m->col + 1) % SSD1306_MODEL_W);
    }
}

void ssd1306_model_transfer(ssd1306_model_t *m, const uint8_t *buf, size_t len) {
    m->transfers++;
    size_t i = 0;
    while (i < len) {
        uint8_t ctrl = buf[i++];
        if (ctrl & 0x3F) { m->bad_control++; return; }       /* reserved bits must be 0 */
        bool co = (ctrl & 0x80) != 0, data = (ctrl & 0x40) != 0;
        do {
            if (i >= len) return;                             /* control byte without payload */
            if (data) data_byte(m, buf[i++]); else command_byte(m, buf[i++]);
        } while (!co && i < len);
    }
}

uint32_t ssd1306_model_crc32(const ssd1306_model_t *m) {
    uint32_t crc = 0xFFFFFFFFu;
    for (size_t i = 0; i < SSD1306_MODEL_FB_SIZE; i++) {
        crc ^= m->fb[i];
        for (int b = 0; b < 8; b++) crc = (crc >> 1) ^ (0xEDB88320u & (0u - (crc & 1u)));
    }
    return ~crc;
}
