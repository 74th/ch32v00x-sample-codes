#include <stdio.h>
#include "pico/stdlib.h"

/* Protocol v1: send 's' to sample GP0 every 10 ms for 3 seconds. */
int main(void) {
    stdio_init_all();
    gpio_init(0);
    gpio_set_dir(0, GPIO_IN);
    gpio_disable_pulls(0);
    for (;;) {
        int c = getchar_timeout_us(10000);
        if (c != 's') continue;
        char samples[301];
        for (unsigned i = 0; i < 300; ++i) {
            samples[i] = gpio_get(0) ? '1' : '0';
            sleep_ms(10);
        }
        samples[300] = '\0';
        printf("PICO_GPIO_V1 10000 %s\n", samples);
    }
}
