#include "pico/stdlib.h"
#include "pico/stdio_usb.h"
#include "fixture.h"
#include "protocol.h"
#define LINE_MAX 128
#define LINE_TIMEOUT_US 1000000

int main(void) {
    fixture_safe(); stdio_init_all();
    char line[LINE_MAX]; unsigned len = 0; bool overflow = false, connected = false;
    absolute_time_t deadline = nil_time;
    for (;;) {
        bool now = stdio_usb_connected();
        if (!now) {
            if (connected || len || overflow) fixture_safe();
            connected = false; len = 0; overflow = false;
            sleep_ms(10); continue;
        }
        connected = true;
        if ((len || overflow) && absolute_time_diff_us(get_absolute_time(), deadline) <= 0) {
            protocol_error(0, "TIMEOUT", "incomplete_frame"); len = 0; overflow = false;
        }
        int c = getchar_timeout_us(10000);
        if (c == PICO_ERROR_TIMEOUT) continue;
        if (c == '\r') continue;
        if (c == '\n') {
            if (overflow) protocol_error(0, "INVALID", "frame_too_long");
            else if (len) { line[len] = 0; protocol_process(line); }
            len = 0; overflow = false; continue;
        }
        if (!len && !overflow) deadline = make_timeout_time_us(LINE_TIMEOUT_US);
        if (c < 32 || c > 126 || len >= LINE_MAX - 1) overflow = true;
        else if (!overflow) line[len++] = (char)c;
    }
}
