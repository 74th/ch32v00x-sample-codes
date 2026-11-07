#include <string.h>
#include "ws2812_classify.h"

static unsigned median(uint16_t *v, unsigned n) {
    if (!n) return 0;
    for (unsigned i = 1; i < n; i++) {          /* insertion sort: n <= 768 */
        uint16_t x = v[i]; unsigned j = i;
        while (j && v[j - 1] > x) { v[j] = v[j - 1]; j--; }
        v[j] = x;
    }
    return v[n / 2];
}

static void range(unsigned v, unsigned *lo, unsigned *hi) {
    if (!*hi || v < *lo) *lo = v;
    if (v > *hi) *hi = v;
}

void ws2812_classify(const uint32_t *words, unsigned nwords, unsigned ns_per_count,
                     uint8_t *out, unsigned out_max, ws2812_decode_t *r) {
    static uint16_t zeros[WS2812_MAX_BITS], ones[WS2812_MAX_BITS];
    unsigned nz = 0, no = 0;
    memset(r, 0, sizeof *r);
    memset(out, 0, out_max);
    for (unsigned i = 0; i + 1 < nwords && r->bits < WS2812_MAX_BITS; i += 2) {
        uint32_t h = words[i], l = words[i + 1];
        if (h == WS2812_MARKER) { r->ended = true; break; }
        unsigned ns = (unsigned)(h > 0xFFFFu ? 0xFFFFu : h) * ns_per_count;
        if (l == WS2812_MARKER && (h > 0xFFFFu || ns > WS2812_IDLE_HIGH_NS)) { r->idle_high = true; r->ended = true; break; }
        bool bit = ns > WS2812_THRESHOLD_NS;
        r->last_high_ns = ns;
        if (bit) range(ns, &r->h1_min, &r->h1_max); else range(ns, &r->h0_min, &r->h0_max);
        if (l != WS2812_MARKER && l <= WS2812_GAP_LIMIT_COUNTS) {
            unsigned low_ns = (WS2812_GAP_LIMIT_COUNTS - l) * ns_per_count;
            if (bit) range(low_ns, &r->l1_min, &r->l1_max); else range(low_ns, &r->l0_min, &r->l0_max);
        }
        if (ns >= WS2812_ZERO_MIN_NS && ns <= WS2812_ZERO_MAX_NS) { if (nz < WS2812_MAX_BITS) zeros[nz++] = (uint16_t)ns; }
        else if (ns >= WS2812_ONE_MIN_NS && ns <= WS2812_ONE_MAX_NS) { if (no < WS2812_MAX_BITS) ones[no++] = (uint16_t)ns; }
        else r->bad_pulses++;
        if (r->bits / 8 < out_max && bit) out[r->bits / 8] |= (uint8_t)(0x80u >> (r->bits % 8));
        r->bits++;
        if (l == WS2812_MARKER) { r->ended = true; break; }
    }
    r->bytes = r->bits / 8; r->partial_byte = (r->bits % 8) != 0;
    r->tail_bits = r->bits % 8;
    if (r->tail_bits && r->bytes < out_max) r->tail = out[r->bytes];
    if (r->bytes > out_max) r->bytes = out_max;
    r->t0h_ns = median(zeros, nz); r->t1h_ns = median(ones, no);
}
