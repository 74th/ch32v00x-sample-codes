#ifndef CAPTURE_FIXTURE_H
#define CAPTURE_FIXTURE_H
#include <stdbool.h>

/* Edge-time measurement and background capture (PIO1 + DMA). See protocol.md. */
void capture_fixture_edge_measure(unsigned long id, char *args);
void capture_fixture_edge_selftest(unsigned long id, char *args);
void capture_fixture_start(unsigned long id, char *args);
void capture_fixture_read(unsigned long id, char *args);
void capture_fixture_stop(unsigned long id, char *args);
void capture_fixture_i2c_hold(unsigned long id, char *args);

/* True while a background capture owns the PIO1 state machine. */
bool capture_fixture_active(void);
/* Stop and release the background capture hardware (RESET_SAFE, USB disconnect). The captured data stays readable. */
void capture_fixture_halt(void);

#define CAPTURE_EDGE_WORDS 4096
#define CAPTURE_UART_BYTES 4096
#define CAPTURE_READ_MAX 256
#define CAPTURE_UART_BAUD_MIN 1200
#define CAPTURE_UART_BAUD_MAX 921600
#define EDGE_PERIODS_MAX 255
#endif
