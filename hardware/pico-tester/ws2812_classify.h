/* Hardware-independent WS2812 pulse classifier (host-testable).
 * Input is the word stream of ws2812_decode.pio: pairs (high_count, low_remaining). A pair whose second word is
 * WS2812_MARKER ends the frame (the line stayed Low for the reset time after that bit). */
#ifndef WS2812_CLASSIFY_H
#define WS2812_CLASSIFY_H
#include <stdbool.h>
#include <stdint.h>

#define WS2812_MARKER 0xFFFFFFFFu
#define WS2812_MAX_BITS 768                 /* 96 bytes */
/* High-width classes in ns. Inside [ZERO] -> 0, inside [ONE] -> 1, anything else is an out-of-range pulse. */
#define WS2812_ZERO_MIN_NS 190u
#define WS2812_ZERO_MAX_NS 480u
#define WS2812_ONE_MIN_NS 830u
#define WS2812_ONE_MAX_NS 1150u
#define WS2812_IDLE_HIGH_NS 100000u         /* a last pulse wider than this is the line idling High, not data */
#define WS2812_THRESHOLD_NS 655u            /* bit value of an out-of-range pulse: High wider than this -> 1 */
#define WS2812_GAP_LIMIT_COUNTS 3125u       /* initial Low counter of ws2812_decode.pio (50 us at 16 ns/count) */

typedef struct {
    unsigned bits;                          /* bits decoded (including out-of-range ones) */
    bool ended;                             /* the frame was terminated by a reset gap */
    unsigned bad_pulses;
    unsigned t0h_ns, t1h_ns;                /* median High width of in-range 0 / 1 bits, 0 when none */
    unsigned bytes;                         /* complete bytes written to out */
    bool partial_byte;                      /* bits is not a multiple of 8 */
    unsigned tail_bits;                     /* bits % 8: bits after the last complete byte */
    uint8_t tail;                           /* those bits, left-aligned in a byte */
    unsigned last_high_ns;                  /* High width of the last decoded data pulse */
    bool idle_high;                         /* the frame ended with the line idling High (not counted as a bit) */
    /* Ranges over all decoded bits, split by the bit value (threshold), in ns; 0 when there is no such bit.
     * High: every pulse including out-of-range ones. Low: the Low after the bit, only when another bit follows
     * (the Low before the reset gap is not a bit time). Software-counted PIO loops: about +-1 count. */
    unsigned h0_min, h0_max, h1_min, h1_max;
    unsigned l0_min, l0_max, l1_min, l1_max;
} ws2812_decode_t;

void ws2812_classify(const uint32_t *words, unsigned nwords, unsigned ns_per_count,
                     uint8_t *out, unsigned out_max, ws2812_decode_t *r);
#endif
