include ../target.mk
CH32FUN := ../../externals/ch32fun/ch32fun
# Helper dependency: pinned submodule's extralibs/ssd1306_i2c.h and ssd1306.h (ch32fun.mk already adds extralibs to -I).
# make HELPER_CLOCK=1  keeps the helper's default 1 MHz I2C clock; the default build lowers it to 100 kHz.
ifeq ($(HELPER_CLOCK),1)
EXTRA_CFLAGS += -DSSD1306_KEEP_HELPER_CLOCK
endif
# CH32V002 (V00x header) names the register PB1PRSTR; CH32V003 compatibility alias APB1PRSTR does not exist.
# RM V1.5 3.4.5: RCC_PB1PRSTR (0x10) bit 21 = I2C1RST, same bit as RCC_APB1Periph_I2C1. The helper source is not changed.
EXTRA_CFLAGS += -DAPB1PRSTR=PB1PRSTR
include $(CH32FUN)/ch32fun.mk
include ../target-post.mk
all: build
