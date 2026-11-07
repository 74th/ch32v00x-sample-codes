/* Host stub of Arduino's Print (see Arduino.h in this directory). */
#pragma once
#include <stdint.h>
#include <stddef.h>
class Print {
public:
    virtual ~Print() {}
    virtual size_t write(uint8_t c) = 0;
    virtual size_t write(const uint8_t *buffer, size_t size) {
        size_t n = 0;
        while (size--) n += write(*buffer++);
        return n;
    }
};
