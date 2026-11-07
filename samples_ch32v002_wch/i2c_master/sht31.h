/* SHT31 measurement conversion exactly as in the book (pure function, also compiled on the host for tests).
 * dac = 6 bytes: T_hi T_lo T_crc H_hi H_lo H_crc. The CRC bytes are not checked (the book does not check them).
 * Temperature uses unsigned arithmetic as in the book, so a reading below 0 degC wraps to a huge value. */
#ifndef SHT31_H
#define SHT31_H
#include <stdint.h>

void sht31_convert(const uint8_t dac[6], uint32_t *temperature, uint32_t *humidity);
#endif
