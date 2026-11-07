/* Host harness: runs the i2c_oled sketch's setup() and one loop() with the pinned OLED library and prints the
 * library's frame buffer (pages x 128 bytes) as one hex line per page. Expected values for the HIL test therefore
 * come from the sketch and library sources themselves.
 * Build: g++ -I<this dir> -I<library src> harness.cpp <library src>/oled.cpp -DSKETCH='"<path to .ino>"' */
#include <Arduino.h>
#define private public
#include "oled.h"
#undef private
#include SKETCH

int main() {
    setup();
    loop();
    for (unsigned p = 0; p < oled.pages; p++) {
        for (unsigned c = 0; c < oled.width; c++) printf("%02x", oled.buffer[p * oled.width + c]);
        printf("\n");
    }
    return 0;
}
