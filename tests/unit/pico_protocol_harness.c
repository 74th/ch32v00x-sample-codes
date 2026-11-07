/* Host harness: execute the real request parser with hardware actions stubbed. */
#include <stdio.h>
#include <string.h>
#include "protocol.h"
void fixture_safe(void) {}
void gpio_fixture_command(unsigned long id, const char *cmd, char *args) {(void)id;(void)cmd;(void)args;}
#define STUB(name) void name(unsigned long id, char *args) {(void)id;(void)args;}
STUB(uart_fixture_xfer)
STUB(adc_fixture_observe)
STUB(i2c_fixture_selftest)
STUB(i2c_fixture_faulttest)
STUB(i2c_fixture_probe)
STUB(i2c_fixture_master)
STUB(i2c_fixture_slave)
STUB(spi_fixture_selftest)
STUB(spi_fixture_slave)
int main(void) {
    char line[256];
    while (fgets(line, sizeof line, stdin)) {
        line[strcspn(line, "\n")] = 0;
        protocol_process(line);
    }
    return 0;
}
