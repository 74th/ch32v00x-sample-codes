TARGET := main
TARGET_MCU := CH32V003
CH32FUN := ../../externals/ch32fun/ch32fun
# Helper dependency: pinned submodule's extralibs/ssd1306_i2c.h and ssd1306.h (ch32fun.mk already adds extralibs to -I).
# make HELPER_CLOCK=1  keeps the helper's default 1 MHz I2C clock; the default build lowers it to 100 kHz.
ifeq ($(HELPER_CLOCK),1)
EXTRA_CFLAGS += -DSSD1306_KEEP_HELPER_CLOCK
endif
override GENERATED_LD_FILE := generated_ch32v003.ld
include $(CH32FUN)/ch32fun.mk
all: build
