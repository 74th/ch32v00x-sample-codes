#include "fixture.h"
#include "pico/stdlib.h"

/* GP0 is retained for the legacy v1 wiring; GP4..15 are the proposed fixture; GP16/17 are isolated loopback pins. */
static const unsigned fixture_pins[] = {0, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 26};
static uint32_t claimed;
bool fixture_allowed(unsigned pin) {
    for (unsigned i = 0; i < sizeof fixture_pins / sizeof fixture_pins[0]; i++)
        if (fixture_pins[i] == pin) return true;
    return false;
}
bool fixture_claim(unsigned pin) {
    if (!fixture_allowed(pin) || (claimed & (1u << pin))) return false;
    claimed |= 1u << pin;
    return true;
}
void fixture_safe(void) {
    claimed = 0;
    for (unsigned i = 0; i < sizeof fixture_pins / sizeof fixture_pins[0]; i++) {
        unsigned pin = fixture_pins[i];
        gpio_set_dir(pin, GPIO_IN);
        gpio_init(pin);
        gpio_disable_pulls(pin);
    }
}
