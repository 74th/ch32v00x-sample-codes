/* MH-Z19-style CO2 sensor frame handling (pure functions, also compiled on the host for unit tests). */
#ifndef CO2_H
#define CO2_H
#include <stdint.h>

#define CO2_FRAME_LEN 9

typedef enum { CO2_OK = 0, CO2_BAD_HEADER = 1, CO2_BAD_CHECKSUM = 2 } co2_status_t;

/* Checksum byte as in the book: 0xff - sum(frame[1..7]) + 1 (mod 256). */
uint8_t co2_checksum(const uint8_t frame[CO2_FRAME_LEN]);
/* Validate a response to the read command (0xff 0x86 ...). `*ppm` is set whenever the header is valid,
 * even on a checksum error, because the book prints the value after reporting the checksum error. */
co2_status_t co2_parse(const uint8_t frame[CO2_FRAME_LEN], uint16_t *ppm);
#endif
