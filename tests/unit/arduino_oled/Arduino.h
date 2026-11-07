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
