/* ADT7310 13-bit temperature conversion as in the book (pure function, also compiled on the host for tests).
 * raw = the two bytes read (MSB first). The result is the signed 13-bit value `raw_int` (1/16 degC steps) and its
 * split into integer degrees and 1/16 fractions; the book prints the fraction as frac*625 (0.0001 degC units). */
#ifndef ADT7310_H
#define ADT7310_H
#include <stdint.h>

typedef struct {
    int32_t raw_int;   /* signed 13-bit value after raw >> 3 */
    int32_t int_temp;  /* raw_int >> 4 (arithmetic shift: floor) */
    int32_t frac_temp; /* raw_int & 0x0f */
} adt7310_temp_t;

adt7310_temp_t adt7310_convert(uint16_t raw);
#endif
