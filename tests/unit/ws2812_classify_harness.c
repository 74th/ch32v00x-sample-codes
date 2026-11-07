/* Text harness: stdin "<ns_per_count> <word> <word> ..." (hex words, ffffffff = marker). Prints the decode result. */
#include <stdio.h>
#include <stdlib.h>
#include "ws2812_classify.h"
int main(void) {
    static uint32_t words[2000]; unsigned n = 0, npc; uint8_t out[96]; ws2812_decode_t r;
    if (scanf("%u", &npc) != 1) return 1;
    unsigned v;
    while (n < 2000 && scanf("%x", &v) == 1) words[n++] = v;
    ws2812_classify(words, n, npc, out, sizeof out, &r);
    printf("bits=%u bytes=%u ended=%d partial=%d bad=%u t0h=%u t1h=%u tail_bits=%u tail=%02x last=%u idle=%d rx=", r.bits, r.bytes, r.ended,
           r.partial_byte, r.bad_pulses, r.t0h_ns, r.t1h_ns, r.tail_bits, r.tail, r.last_high_ns, r.idle_high);
    for (unsigned i = 0; i < r.bytes; i++) printf("%02x", out[i]);
    printf(" h0=%u-%u h1=%u-%u l0=%u-%u l1=%u-%u", r.h0_min, r.h0_max, r.h1_min, r.h1_max, r.l0_min, r.l0_max, r.l1_min, r.l1_max);
    printf("\n");
    return 0;
}
