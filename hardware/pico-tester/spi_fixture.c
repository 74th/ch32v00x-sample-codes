#include <stdio.h>
#include <string.h>
#include "pico/stdlib.h"
#include "pico/stdio_usb.h"
#include "hardware/spi.h"
#include "hardware/pio.h"
#include "fixture.h"
#include "spi_fixture.h"
#include "spi_loopback.pio.h"

void spi_fixture_selftest(unsigned long id, char *args) {
    char *save = NULL, *mode = strtok_r(args, " ", &save), *extra = strtok_r(NULL, " ", &save);
    if (!mode || strcmp(mode, "MODE0") || extra) {
        fixture_safe(); printf("%lu ERR INVALID spi_selftest_arguments\n", id); return;
    }
    fixture_safe();
    unsigned offset = pio_add_program(pio0, &spi_loopback_slave_program);
    int sm = pio_claim_unused_sm(pio0, false);
    if (sm < 0) { pio_remove_program(pio0, &spi_loopback_slave_program, offset); fixture_safe();
        printf("%lu ERR BUSY pio_unavailable\n", id); return; }
    pio_sm_config c = spi_loopback_slave_program_get_default_config(offset);
    sm_config_set_in_pins(&c, 20); sm_config_set_out_pins(&c, 26, 1);
    sm_config_set_in_shift(&c, false, false, 32); sm_config_set_out_shift(&c, false, false, 32);
    pio_gpio_init(pio0, 20); pio_gpio_init(pio0, 21); pio_gpio_init(pio0, 22); pio_gpio_init(pio0, 26);
    pio_sm_set_consecutive_pindirs(pio0, sm, 20, 3, false);
    pio_sm_set_consecutive_pindirs(pio0, sm, 26, 1, true);
    pio_sm_init(pio0, sm, offset, &c);
    pio_sm_put_blocking(pio0, sm, 0x3c000000u);
    unsigned baud = spi_init(spi0, 100000);
    spi_set_format(spi0, 8, SPI_CPOL_0, SPI_CPHA_0, SPI_MSB_FIRST);
    gpio_set_function(16, GPIO_FUNC_SPI); gpio_set_function(18, GPIO_FUNC_SPI); gpio_set_function(19, GPIO_FUNC_SPI);
    gpio_init(17); gpio_put(17, 1); gpio_set_dir(17, GPIO_OUT);
    sleep_ms(1);
    pio_sm_set_enabled(pio0, sm, true);
    sleep_ms(1);
    gpio_put(17, 0);
    uint64_t deadline = time_us_64() + 100000;
    bool sent = false, got = false, connected = true;
    uint8_t rx = 0;
    while (time_us_64() < deadline && !got) {
        if (!stdio_usb_connected()) { connected = false; break; }
        if (!sent && spi_is_writable(spi0)) { spi_get_hw(spi0)->dr = 0xa5; sent = true; }
        if (spi_is_readable(spi0)) { rx = (uint8_t)spi_get_hw(spi0)->dr; got = true; }
    }
    gpio_put(17, 1);
    while (time_us_64() < deadline && pio_sm_is_rx_fifo_empty(pio0, sm)) tight_loop_contents();
    bool pio_got = !pio_sm_is_rx_fifo_empty(pio0, sm);
    uint32_t slave_rx = pio_got ? pio_sm_get(pio0, sm) : 0;
    pio_sm_set_enabled(pio0, sm, false); spi_deinit(spi0);
    pio_sm_unclaim(pio0, sm); pio_remove_program(pio0, &spi_loopback_slave_program, offset);
    fixture_safe();
    if (!connected) return;
    if (!got || !pio_got) { printf("%lu ERR TIMEOUT spi_loopback safe=1\n", id); return; }
    if (rx != 0x3c || (slave_rx & 0xffu) != 0xa5) {
        printf("%lu ERR SPI master_rx=%02x slave_rx=%02x safe=1\n", id, rx, (unsigned)(slave_rx & 0xffu)); return;
    }
    printf("%lu OK mode=0 bit_order=msb baud=%u master_tx=a5 master_rx=%02x slave_rx=%02x safe=1\n", id, baud, rx, (unsigned)(slave_rx & 0xffu));
}

#include "spi_dut_slave.pio.h"
static int hex_value(char c) {
    if (c >= '0' && c <= '9') return c - '0';
    if (c >= 'a' && c <= 'f') return c - 'a' + 10;
    if (c >= 'A' && c <= 'F') return c - 'A' + 10;
    return -1;
}
void spi_fixture_slave(unsigned long id, char *args) {
    char *save = NULL, *response = strtok_r(args, " ", &save), *mode = strtok_r(NULL, " ", &save);
    char *extra = strtok_r(NULL, " ", &save);
    if (mode && strcmp(mode, "MODE0")) {
        fixture_safe(); printf("%lu ERR UNSUPPORTED spi_mode\n", id); return;
    }
    if (!response || strlen(response) != 4 || extra) {
        fixture_safe(); printf("%lu ERR INVALID spi_slave_arguments\n", id); return;
    }
    uint8_t bytes[2];
    for (unsigned i=0; i<2; i++) {
        int hi = hex_value(response[i*2]), lo = hex_value(response[i*2+1]);
        if (hi < 0 || lo < 0) { fixture_safe(); printf("%lu ERR INVALID spi_slave_arguments\n", id); return; }
        bytes[i] = (uint8_t)((hi << 4) | lo);
    }
    fixture_safe();
    unsigned offset = pio_add_program(pio0, &spi_dut_slave_program);
    int sm = pio_claim_unused_sm(pio0, false);
    if (sm < 0) { pio_remove_program(pio0, &spi_dut_slave_program, offset); fixture_safe();
        printf("%lu ERR BUSY pio_unavailable\n", id); return; }
    pio_sm_config c = spi_dut_slave_program_get_default_config(offset);
    sm_config_set_in_pins(&c, 7); sm_config_set_out_pins(&c, 4, 1);
    sm_config_set_in_shift(&c, false, false, 32); sm_config_set_out_shift(&c, false, false, 32);
    for (unsigned p = 4; p <= 7; p++) pio_gpio_init(pio0, p);
    pio_sm_set_consecutive_pindirs(pio0, sm, 5, 3, false);
    pio_sm_set_consecutive_pindirs(pio0, sm, 4, 1, true);
    pio_sm_init(pio0, sm, offset, &c);
    pio_sm_put_blocking(pio0, sm, (uint32_t)bytes[0] << 24);
    pio_sm_put_blocking(pio0, sm, (uint32_t)bytes[1] << 24);
    pio_sm_set_enabled(pio0, sm, true);
    uint64_t deadline = time_us_64() + 3000000; unsigned count = 0; uint8_t rx[2]; bool connected = true;
    while (time_us_64() < deadline && count < 2) {
        if (!stdio_usb_connected()) { connected = false; break; }
        if (!pio_sm_is_rx_fifo_empty(pio0, sm)) rx[count++] = (uint8_t)pio_sm_get(pio0, sm);
    }
    pio_sm_set_enabled(pio0, sm, false); pio_sm_unclaim(pio0, sm);
    pio_remove_program(pio0, &spi_dut_slave_program, offset); fixture_safe();
    if (!connected) return;
    if (count != 2) { printf("%lu ERR TIMEOUT spi_slave received=%u safe=1\n", id, count); return; }
    printf("%lu OK mode=0 bit_order=msb received=%u rx=%02x%02x tx=%02x%02x safe=1\n", id, count, rx[0], rx[1], bytes[0], bytes[1]);
}
