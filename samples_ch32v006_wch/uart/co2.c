#include "co2.h"

uint8_t co2_checksum(const uint8_t frame[CO2_FRAME_LEN])
{
    uint8_t c = 0;
    for (int i = 1; i < 8; i++) c += frame[i];
    return (uint8_t)(0xff - c + 1);
}

co2_status_t co2_parse(const uint8_t frame[CO2_FRAME_LEN], uint16_t *ppm)
{
    if (frame[0] != 0xff || frame[1] != 0x86) return CO2_BAD_HEADER;
    *ppm = (uint16_t)(frame[2] * 256 + frame[3]);
    return co2_checksum(frame) == frame[8] ? CO2_OK : CO2_BAD_CHECKSUM;
}
