/* Host harness: execute the real request parser with hardware actions stubbed. */
#include <stdio.h>
#include <string.h>
#include "protocol.h"
#include "ssd1306_fixture.h"
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
/* Stub hardware hook: timeout_ms==77 simulates silence; otherwise feed `frames` full frames of a known pattern. */
bool ssd1306_hw_capture(ssd1306_model_t *m, unsigned frames, unsigned timeout_ms, bool wait_init, unsigned *overflow) {
    ssd1306_model_init(m); *overflow = 0; (void)wait_init;
    if (timeout_ms == 77) return true;
    const uint8_t off[] = {0x00, 0xAE}, mode[] = {0x00, 0x20, 0x00}, on[] = {0x00, 0xAF};
    ssd1306_model_transfer(m, off, 2); ssd1306_model_transfer(m, mode, 3); ssd1306_model_transfer(m, on, 2);
    for (unsigned f = 0; f < frames; f++) {
        const uint8_t win[] = {0x00, 0x21, 0, 127}, pg[] = {0x00, 0x22, 0, 7};
        ssd1306_model_transfer(m, win, 4); ssd1306_model_transfer(m, pg, 4);
        for (unsigned i = 0; i < 1024; i += 32) {
            uint8_t b[33] = {0x40};
            for (unsigned j = 0; j < 32; j++) b[1 + j] = (uint8_t)((i + j) * 3);
            ssd1306_model_transfer(m, b, 33);
        }
    }
    return true;
}
/* Stub: pretend the loopback self-test saw a correct run (real behaviour needs hardware). */
void ssd1306_hw_selftest(ssd1306_selftest_result_t *r) {
    r->frames = 2; r->unknown = 1; r->crc32 = r->expected_crc32 = 0x12345678; r->wrong_address_rc = -1;
}
int main(void) {
    char line[256];
    while (fgets(line, sizeof line, stdin)) {
        line[strcspn(line, "\n")] = 0;
        protocol_process(line);
    }
    return 0;
}
