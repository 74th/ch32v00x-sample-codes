#include "sht31.h"

void sht31_convert(const uint8_t dac[6], uint32_t *temperature, uint32_t *humidity)
{
    uint32_t t = (uint32_t)((dac[0] << 8) | dac[1]);
    uint32_t h = (uint32_t)((dac[3] << 8) | dac[4]);
    *temperature = (((uint32_t)(t) * 175) >> 16) - 45;
    *humidity = (((uint32_t)(h) * 100) >> 16);
}
