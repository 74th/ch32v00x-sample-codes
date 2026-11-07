#ifndef UART_FIXTURE_H
#define UART_FIXTURE_H
/* Parses the arguments after UART_XFER; all exits release UART and fixture pins. */
void uart_fixture_xfer(unsigned long id, char *args);
#endif
