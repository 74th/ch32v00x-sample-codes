include ../target.mk
CH32FUN := ../../externals/ch32fun/ch32fun
# Helper dependency: pinned submodule's examples/i2c_slave/i2c_slave.h (not copied, not modified).
EXTRA_CFLAGS += -I../../externals/ch32fun/examples/i2c_slave
# CH32V002 (V00x header) names the register PB1PRSTR; CH32V003 compatibility alias APB1PRSTR does not exist.
# RM V1.5 3.4.5: RCC_PB1PRSTR (0x10) bit 21 = I2C1RST, same bit as RCC_APB1Periph_I2C1. The helper source is not changed.
EXTRA_CFLAGS += -DAPB1PRSTR=PB1PRSTR
include $(CH32FUN)/ch32fun.mk
include ../target-post.mk
all: build
