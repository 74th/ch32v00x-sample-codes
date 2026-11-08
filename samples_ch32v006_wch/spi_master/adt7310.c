#include "adt7310.h"

adt7310_temp_t adt7310_convert(uint16_t raw)
{
    adt7310_temp_t t;
    raw = raw >> 3;  /* 13 bit */
    if (raw & 0x1000) {
        t.raw_int = (int32_t)raw - 0x2000;
    } else {
        t.raw_int = raw;
    }
    t.int_temp = t.raw_int >> 4;
    t.frac_temp = t.raw_int & 0x0f;
    return t;
}
