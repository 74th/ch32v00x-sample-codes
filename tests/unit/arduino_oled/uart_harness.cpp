/* Host harness for the uart sketch (CO2 sensor over UART, result drawn with the pinned OLED library).
 * Runs setup() and then one loop() per argument. Each argument is the hex of the bytes the sensor "answers" with
 * before that loop() ("-" = no answer, i.e. readBytes() times out). After every loop() the library frame buffer is
 * printed as one hex line per page. Build like harness.cpp (see tests/hil/arduino/oled_expected.py). */
#include <Arduino.h>
#define private public
#include "oled.h"
#undef private
#include SKETCH

int main(int argc, char **argv) {
    setup();
    for (int i = 1; i < argc; i++) {
        if (argv[i][0] != '-') {
            for (const char *p = argv[i]; p[0] && p[1]; p += 2) {
                unsigned v;
                sscanf(p, "%2x", &v);
                Serial.rx.push_back((uint8_t)v);
            }
        }
        loop();
        for (unsigned p = 0; p < oled.pages; p++) {
            for (unsigned c = 0; c < oled.width; c++) printf("%02x", oled.buffer[p * oled.width + c]);
            printf("\n");
        }
    }
    return 0;
}
