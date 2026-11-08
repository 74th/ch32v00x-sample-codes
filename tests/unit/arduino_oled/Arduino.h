/* Host stub of the Arduino API, just enough to run the "OLED SSD1306 - SH1106" library's drawing code and the
 * i2c_oled sketch on the host (tests/hil/arduino/test_oled.py). The bit-banged I2C reads every line as high,
 * so the bus routines return immediately; the frame buffer is read directly. */
#pragma once
#include <stdint.h>
#include <stddef.h>
#include <string.h>
#include <stdlib.h>
#include <stdio.h>
#include <stdarg.h>
#include "Print.h"
#define PROGMEM
#define pgm_read_byte(p) (*(const uint8_t *)(p))
#define HIGH 1
#define LOW 0
#define INPUT 0
#define OUTPUT 1
enum { PC1 = 16, PC2 = 17 };
static inline void pinMode(uint32_t, uint32_t) {}
static inline void digitalWrite(uint32_t, uint32_t) {}
static inline int digitalRead(uint32_t) { return 1; }
static inline void delay(uint32_t) {}
static inline void delayMicroseconds(uint32_t) {}
static inline void yield(void) {}
static inline uint32_t millis(void) { return 0; }  /* used only by scroll_up(), which the sketch does not call */

/* Scripted Serial for the uart sketch: bytes queued by the harness are what readBytes() returns; an empty queue
 * behaves like the real 1 s timeout (returns the bytes read so far). */
#include <deque>
struct HostSerial {
    std::deque<uint8_t> rx;
    void begin(uint32_t) {}
    size_t write(const uint8_t *, size_t n) { return n; }
    size_t readBytes(uint8_t *buf, size_t n) {
        size_t got = 0;
        while (got < n && !rx.empty()) { buf[got++] = rx.front(); rx.pop_front(); }
        return got;
    }
};
static HostSerial Serial;
