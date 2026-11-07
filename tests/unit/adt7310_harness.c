/* stdin: 4 hex digits (the 2 bytes read, MSB first). Prints "raw_int=<n> int=<n> frac=<n> text=<printf of the book>". */
#include <stdio.h>
#include "adt7310.h"
int main(void) {
    unsigned v;
    if (scanf("%4x", &v) != 1) return 1;
    adt7310_temp_t t = adt7310_convert((uint16_t)v);
    printf("raw_int=%d int=%d frac=%d text=temp:%3d.%04d\n", (int)t.raw_int, (int)t.int_temp, (int)t.frac_temp,
           (int)t.int_temp, (int)(t.frac_temp * 625));
    return 0;
}
